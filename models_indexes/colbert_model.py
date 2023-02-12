import os
import json
import csv
import sys
from google.protobuf.json_format import Parse

from index_builder.pyserini_colbert_builder import PyseriniColbertBuilder
from models_datasets.abstract_model_dataset import AbstractModelDataset
from models_indexes.abstract_model import AbstractModel

from pyserini.search.faiss import FaissSearcher, TctColBertQueryEncoder

import ir_measures
from ir_measures import *

from taskmap_pb2 import TaskMap
from pygaggle.rerank.base import Query, Text, hits_to_texts
from pygaggle.rerank.transformer import MonoT5

class ColbertModel(AbstractModel):

    def __init__(self, domain:str, t5:bool=False):
        self.model_name = "TCT-ColBERTv2"
        self.t5 = t5
        if t5:
            self.model_name += "+t5"
            
        self.dataset_model: AbstractModelDataset = self.get_dataset_model(domain)()

        
        self.output_temp_dir = os.path.join(self.dataset_model.get_index_temp_path(), "system_index_colbert")
        self.output_index_dir = os.path.join(self.dataset_model.get_index_path(), "system_index_colbert")
        self.run_path = os.path.join(self.dataset_model.get_measurements_path(), "run_files")
        
        if t5:
            self.reranker = MonoT5()
        else:
            self.reranker = None
        
    def build_index(self, overwrite=False):
        
        if not os.path.isdir(self.output_index_dir):
            os.makedirs(self.output_index_dir)
            
        if not overwrite and len(os.listdir(self.output_index_dir)) > 0:
            print("Colbert dense index already built. Call overwrite=True in build_index() to rebuild the index again.")
            return
            
        index_builder = PyseriniColbertBuilder()
        
        print("Build documents...")
        print(f"Saving documents to {self.output_temp_dir}...")
        taskmap_dir = self.dataset_model.get_taskgraphs_path()
        dataset_name = self.dataset_model.get_dataset_name()
        index_builder.build_json_docs(input_dir=taskmap_dir,
                                        output_dir=self.output_temp_dir,
                                        dataset_name=dataset_name)
        
        print("Generate index...")
        print(f"Saving documents to {self.output_index_dir}...")
        index_builder.build_index(input_dir=self.output_temp_dir,
                                    output_dir=self.output_index_dir)

    
    def dense_hits_to_text(self, hits, scores, ids):
        texts = []
        for i in range(0, len(hits)):
            
            doc = json.loads(hits[i].raw())
            # t = hits[i].contents
            t = doc["contents"]
            metadata = {'raw': doc["contents"], 'docid': ids[i]}
            texts.append(Text(t, metadata, scores[i]))
        return texts
    
    def convert_search_results_to_run(self, pd_queries):
        # Initialize searcher
        
        lucene_searcher = self.get_lucene_searcher(self.dataset_model)
        encoder = TctColBertQueryEncoder("castorini/tct_colbert-v2-hnp-msmarco")
        searcher = FaissSearcher(
            index_dir = self.output_index_dir,
            query_encoder= encoder,
        )
        
        # retrieve results
        lines = []
        for idx, query in pd_queries.iterrows():
            print(f"Started {idx+1}/100")
            hits = searcher.search(query_d = query["raw query"], query_s = query["target query"], k=50)
            if self.t5:
                scores = [res.score for res in hits]
                ids = [hit.docid for hit in hits]
                retrived_hits = [lucene_searcher.doc(hit.docid) for hit in hits]
                print("converted to pygaggle")
                hits = self.reranker.rerank(Query(query["target query"]), self.dense_hits_to_text(retrived_hits, scores, ids))
            for rank, hit in enumerate(hits[:50]):
                if type(hit) == Text:
                    id = hit.metadata["docid"]
                    line = f'{query["id"]} Q0 {id} {rank+1} {hit.score} {self.model_name}\n'
                else:
                    line = f'{query["id"]} Q0 {hit.docid} {rank+1} {hit.score} {self.model_name}\n'
                lines.append(line)
            print(f"Finished {idx+1}/100")
        lines[-1] = lines[-1].replace("\n","")
        
        if not os.path.isdir(self.run_path):
            os.makedirs(self.run_path)
        
        print(f"Run file saved at {self.run_path}/{self.model_name}.run")
        with open(os.path.join(self.run_path, f"{self.model_name}-contents.run"), "w") as f:
            f.writelines(lines)
            
    def create_empty_judgments(self, pd_queries, k, n):
        # Initialize searcher
        encoder = TctColBertQueryEncoder("castorini/tct_colbert-v2-hnp-msmarco")
        searcher = FaissSearcher(
            index_dir = self.output_index_dir,
            query_encoder= encoder,
        )
        lucene_searcher = self.get_lucene_searcher(self.dataset_model)
        
        # retrieve results
        # fieldnames = ["raw query", "html_link", "relevance", "usability", "quality"]
        empty_judgments = []
        for idx, query in pd_queries.iterrows():
            hits = searcher.search(query=query["target query"], k=k)
            for hit in hits[:n]:
                raw_taskgraph = lucene_searcher.doc(hit.docid)
                doc_json = json.loads(raw_taskgraph.raw())
                taskmap_json = doc_json['recipe_document_json']
                taskmap = Parse(json.dumps(taskmap_json), TaskMap())
                empty_judgment = {
                    # "doc-id" : taskmap.taskmap_id, 
                    # "doc-title" : taskmap.title, 
                    # "doc-url" : taskmap.source_url, 
                    # "score": round(float(hit.score),3),
                    # "query-id": query_id,
                    # "query": query,
                    # "taskgraph" : taskmap,
                    "raw-query": query["raw query"],
                    "html_link": taskmap.source_url,
                    "relevance": "",
                    "usability": "",
                    "quality": "",
                }
                empty_judgments.append(empty_judgment)
        
        annotations_path = os.path.join(self.dataset_model.get_measurements_path(), "empty_annotations")
        
        if not os.path.isdir(annotations_path):
            os.makedirs(annotations_path)
        
        print(f"Empty judgments file saved at {annotations_path}/{self.model_name}_empty.csv")
        keys = ["raw-query", "html_link", "relevance", "usability", "quality"]
        with open(os.path.join(annotations_path, f"{self.model_name}-judgments.csv"), 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(empty_judgments)

    def get_measurements(self, judgments_path):
        qrles = ir_measures.read_trec_qrels(judgments_path)
        run = ir_measures.read_trec_run(self.run_path)
        accuracy = ir_measures.calc_aggregate([nDCG@3, Precision@3, Recall@3], qrles, run)
        return accuracy
    
    def search(self, query):
        encoder = TctColBertQueryEncoder("castorini/tct_colbert-v2-hnp-msmarco")
        searcher = FaissSearcher(
            index_dir = self.output_index_dir,
            query_encoder= encoder,
        )
        lucene_searcher = self.get_lucene_searcher(self.dataset_model)
        hits = searcher.search(query=query, k=5)
        for hit in hits[0:1]:    
            raw_taskgraph = lucene_searcher.doc(hit.docid)
            doc_json = json.loads(raw_taskgraph.raw())
            taskmap_json = doc_json['recipe_document_json']
            taskmap = Parse(json.dumps(taskmap_json), TaskMap())
            print(taskmap)
            # print(f'{query}, {taskmap.source_url}')
    