import os
import json
import csv
import sys
from google.protobuf.json_format import Parse

from models_datasets.abstract_model_dataset import AbstractModelDataset
from models_indexes.abstract_model import AbstractModel
from pyserini.search import LuceneSearcher

from pyserini.search.hybrid import HybridSearcher
from pyserini.search.faiss import FaissSearcher, TctColBertQueryEncoder

import ir_measures
from ir_measures import *

from taskmap_pb2 import TaskMap

sys.path.insert(0, './pygaggle')
from pygaggle.rerank.base import Query, Text
from pygaggle.rerank.transformer import MonoT5

class HybridSearcherOverride(HybridSearcher):
    def search(self, query_d: str, query_s:str, k0: int = 10, k: int = 10, alpha: float = 0.1, normalization: bool = False, weight_on_dense: bool = False):
        dense_hits = self.dense_searcher.search(query_d, k0)
        sparse_hits = self.sparse_searcher.search(query_s, k0)
        trec_runs = [sparse_hits,dense_hits]
        return self.__reciprocal_rank_fusion(trec_runs=trec_runs, k=60, max_docs=k)
        # return self._hybrid_results(dense_hits, sparse_hits, alpha, k, normalization, weight_on_dense)

    def __reciprocal_rank_fusion(self, trec_runs, k=60, max_docs=1000):
        """
            Implements a reciprocal rank fusion as define in
            ``Reciprocal Rank fusion outperforms Condorcet and individual Rank Learning Methods`` by Cormack, Clarke and Buettcher.
            Parameters:
                trec_runs: a list of TrecRun objects to fuse
                k: term to avoid vanishing importance of lower-ranked documents. Default value is 60 (default value used in their paper).
                max_docs: maximum number of documents in the final ranking
        """

        doc_scores = {}
        for hits in trec_runs:
            for pos, hit in enumerate(hits, start=1):
                doc_scores[hit.docid] = doc_scores.get(hit.docid, 0.0) + 1.0 / (k + pos)

        # Writes out information for this topic
        merged_run = []
        for (docid, score) in sorted(iter(doc_scores.items()), key=lambda x: (-x[1], x[0]))[:max_docs]:
            merged_run.append([score, docid])

        return merged_run


class HybridModel(AbstractModel):

    def __init__(self, domain:str, rm3:bool=False, t5:bool=False):
        self.model_name = "hybrid-tct-bm25"
        if rm3:
            self.model_name += "+rm3"
        if t5:
            self.model_name += "+t5"
        self.domain = domain
        self.rm3 = rm3
        self.t5 = t5
        self.dataset_model: AbstractModelDataset = self.get_dataset_model(domain)()
        if self.t5:
            self.reranker = MonoT5()
        else:
            self.reranker = None
        
        self.output_temp_dir = os.path.join(self.dataset_model.get_index_temp_path(), "system_index_sparse")
        self.output_index_dir = os.path.join(self.dataset_model.get_index_path(), "system_index_sparse")
        self.run_path = os.path.join(self.dataset_model.get_measurements_path(), "run_files")
        
    def build_index(self, overwrite=False):
        pass


    def dense_hits_to_text(self, hits, scores, ids):
        texts = []
        for i in range(0, len(hits)):
            
            doc = json.loads(hits[i].raw())
            # t = hits[i].contents
            t = doc["contents"]
            metadata = {'raw': doc["contents"], 'docid': ids[i]}
            texts.append(Text(t, metadata, scores[i]))
        return texts
    
    ### Works only for DIY!
    
    def convert_search_results_to_run(self, pd_queries):
        # Initialize searcher
        ssearcher = LuceneSearcher(index_dir=f"/home/ubuntu/task-search-quality/indexes/{self.domain.lower()}/system_index_sparse")
        ssearcher.set_bm25(b=0.4, k1=0.9)
        if self.rm3 == True:
            ssearcher.set_rm3(fb_terms=10, fb_docs=10, original_query_weight=0.5)
        
        encoder = TctColBertQueryEncoder('castorini/tct_colbert-v2-hnp-msmarco')
        dsearcher = FaissSearcher(
            index_dir = f"/home/ubuntu/task-search-quality/indexes/{self.domain.lower()}/system_index_colbert",
            query_encoder= encoder,
        )
        
        hsearcher = HybridSearcherOverride(dsearcher, ssearcher)
        
        lines = []
        for idx, query in pd_queries.iterrows():
            print(f"Started {idx+1}/100")
            hits = hsearcher.search(query_d = query["raw query"], query_s = query["target query"], k0=250, k=50)
            if self.t5:
                scores = [res[0] for res in hits]
                ids = [hit[1] for hit in hits]
                retrived_hits = [ssearcher.doc(hit[1]) for hit in hits]
                print("converted to pygaggle")
                hits = self.reranker.rerank(Query(query["target query"]), self.dense_hits_to_text(retrived_hits, scores, ids))
            for rank, hit in enumerate(hits[:50]):
                if type(hit) == Text:
                    id = hit.metadata["docid"]
                    line = f'{query["id"]} Q0 {id} {rank+1} {hit.score} {self.model_name}\n'
                else:
                    line = f'{query["id"]} Q0 {hit[1]} {rank+1} {hit[0]} {self.model_name}\n'
                lines.append(line)
            print(f"Finished {idx+1}/100")
        # lines[-1] = lines[-1].replace("\n","")
        
        if not os.path.isdir(self.run_path):
            os.makedirs(self.run_path)
        
        # print(f"Run file saved at {self.run_path}/{self.model_name}.run")
        with open(os.path.join(self.run_path, f"{self.model_name}.run"), "w") as f:
            f.writelines(lines)
            
   
    def get_measurements(self, judgments_path:str):
        qrles = ir_measures.read_trec_qrels(judgments_path)
        run = ir_measures.read_trec_run(self.run_path)
        accuracy = ir_measures.calc_aggregate([nDCG@3, Precision@3, Recall@3], qrles, run)
        return accuracy
    
    def search(self, query:str, k=5):
        searcher = LuceneSearcher(index_dir=self.output_index_dir)
        searcher.set_bm25(b=0.4, k1=0.9)
        
        hits = searcher.search(q=query, k=k)
        for hit in hits:
            doc_json = json.loads(hit.raw)
            taskmap_json = doc_json['recipe_document_json']
            taskmap = Parse(json.dumps(taskmap_json), TaskMap())
            # empty_judgment = {
            #     # "doc-id" : taskmap.taskmap_id, 
            #     # "doc-title" : taskmap.title, 
            #     # "doc-url" : taskmap.source_url, 
            #     # "score": round(float(hit.score),3),
            #     # "query-id": query_id,
            #     # "query": query,
            #     # "taskgraph" : taskmap,
            #     "raw-query": query["raw query"],
            #     "html_link": taskmap.source_url,
            #     "relevance": "",
            #     "usability": "",
            #     "quality": "",
            # }
            
            print(f'Judgment: {query} {taskmap.source_url}')
            
    def search_best(self, query:str):
        searcher = LuceneSearcher(index_dir=self.output_index_dir)
        searcher.set_bm25(b=0.4, k1=0.9)
        hits = searcher.search(q=query, k=1)
        doc_json = json.loads(hits[0].raw)
        taskmap_json = doc_json['recipe_document_json']
        taskmap = Parse(json.dumps(taskmap_json), TaskMap())
        return taskmap
            
        
        
        
    