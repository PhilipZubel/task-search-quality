import os
import json
import csv
import sys
from google.protobuf.json_format import Parse

from index_builder.marqo_index_builder import MarqoIndexBuilder
from models_datasets.abstract_model_dataset import AbstractModelDataset
from models_indexes.abstract_model import AbstractModel

import ir_measures
from ir_measures import *

from taskmap_pb2 import TaskMap

from pygaggle.rerank.base import Query, Text
from pygaggle.rerank.transformer import MonoT5

class MarqoModel(AbstractModel):

    def __init__(self, domain:str, t5 = False, doc_build = "all"):
        
        self.doc_build = doc_build
        self.model_name = "marqo"
        
        self.t5=t5
        if t5:
            self.model_name += "+t5"
            self.reranker = MonoT5()
        else:
            self.reranker = None
        
        self.dataset_model: AbstractModelDataset = self.get_dataset_model(domain)()
        
        self.output_temp_dir = os.path.join(self.dataset_model.get_index_temp_path(), "system_index_marqo", doc_build)
        self.output_index_dir = os.path.join(self.dataset_model.get_index_path(), "system_index_marqo", doc_build)
        self.run_path = os.path.join(self.dataset_model.get_measurements_path(), "run_files")


    def dense_hits_to_text(self, hits, scores, ids):
        texts = []
        for i in range(0, len(hits)):
            
            doc = json.loads(hits[i].raw())
            # t = hits[i].contents
            t = doc["contents"]
            metadata = {'raw': doc["contents"], 'docid': ids[i]}
            texts.append(Text(t, metadata, scores[i]))
        return texts

    def build_index(self, overwrite=False):
        
        if not os.path.isdir(self.output_temp_dir):
            os.makedirs(self.output_temp_dir)
            
        # if not overwrite and len(os.listdir(self.output_temp_dir)) > 0:
        #     print("Marqo index already built. Call overwrite=True in build_index() to rebuild the index again.")
        #     return
            
        index_builder = MarqoIndexBuilder()
        
        # print("Build documents...")
        # print(f"Saving documents to {self.output_temp_dir}...")
        # taskmap_dir = self.dataset_model.get_taskgraphs_path()
        # dataset_name = self.dataset_model.get_dataset_name()
        # index_builder.build_json_docs(input_dir=taskmap_dir,
        #                                 output_dir=self.output_temp_dir,
        #                                 dataset_name=dataset_name,
        #                                 doc_build = self.doc_build)
        
        print("Generate index...")
        # print(f"Saving documents to {self.output_index_dir}...")
        index_builder.build_index(input_dir=self.output_temp_dir,
                                    domain = self.dataset_model.get_dataset_name(),
                                    how = self.doc_build)

    
    def convert_search_results_to_run(self, pd_queries):
        index_builder = MarqoIndexBuilder() 
        lucene_searcher = self.get_lucene_searcher(self.dataset_model)
        # retrieve results
        lines = []
        for idx, query in pd_queries.iterrows():
            print(f"query {idx}/{100}")
            q = query["raw query"]
            hits = index_builder.query_index(domain = self.dataset_model.get_dataset_name(), q=q, limit=50, offset=0)
            if self.t5:
                scores = [res["_score"] for res in hits["hits"]]
                ids = [hit["_id"] for hit in hits["hits"]]
                print("scores", scores)
                print("ids", ids)
                retrived_hits = [lucene_searcher.doc(hit['_id']) for hit in hits["hits"]]
                hits = self.reranker.rerank(Query(query["target query"]), self.dense_hits_to_text(retrived_hits, scores, ids))
                print(hits)
                for rank, hit in enumerate(hits[:50]):
                    id = hit.metadata["docid"]
                    line = f'{query["id"]} Q0 {id} {rank+1} {hit.score} {self.model_name}\n'
                    lines.append(line)
            else:  
                for rank, hit in enumerate(hits["hits"]):
                    line = f'query-{idx} Q0 {hit["_id"]} {rank+1} {hit["_score"]} {self.model_name}\n'
                    lines.append(line)
        
        # if not os.path.isdir(self.run_path):
        #     os.makedirs(self.run_path)
        
        print(f"Run file saved at {self.run_path}/{self.model_name}-raw.run")
        with open(os.path.join(self.run_path, f"{self.model_name}-raw.run"), "w") as f:
            f.writelines(lines)

    def convert_search_results_to_run_attributes(self, pd_queries, filters):
        index_builder = MarqoIndexBuilder() 
        lucene_searcher = self.get_lucene_searcher(self.dataset_model)
        # retrieve results
        lines = []
        for idx, query in pd_queries.iterrows():
            print(f"query {idx}/{100}")
            q = query["raw query"]
            hits = index_builder.query_index(domain = self.dataset_model.get_dataset_name(), q=q, limit=50, offset=0, filters=filters)
            # if self.t5:
            #     scores = [res["_score"] for res in hits["hits"]]
            #     ids = [hit["_id"] for hit in hits["hits"]]
            #     print("scores", scores)
            #     print("ids", ids)
            #     retrived_hits = [lucene_searcher.doc(hit['_id']) for hit in hits["hits"]]
            #     hits = self.reranker.rerank(Query(query["target query"]), self.dense_hits_to_text(retrived_hits, scores, ids))
            #     print(hits)
            #     for rank, hit in enumerate(hits[:50]):
            #         id = hit.metadata["docid"]
            #         line = f'{query["id"]} Q0 {id} {rank+1} {hit.score} {self.model_name}\n'
            #         lines.append(line)
            # else:  
            for rank, hit in enumerate(hits["hits"]):
                line = f'query-{idx} Q0 {hit["_id"]} {rank+1} {hit["_score"]} {self.model_name}\n'
                lines.append(line)

        filter_name = "-".join(filters)
        
        print(f"Run file saved at {self.run_path}/marqo-filters/{filter_name}.run")
        with open(os.path.join(self.run_path,"marqo-filters", f"{filter_name}.run"), "w") as f:
            f.writelines(lines)
    
    def get_measurements(self, judgments_path):
        qrles = ir_measures.read_trec_qrels(judgments_path)
        run = ir_measures.read_trec_run(self.run_path)
        accuracy = ir_measures.calc_aggregate([nDCG@3, Precision@3, Recall@3], qrles, run)
        return accuracy
    
    def search(self, query, filters=None):
        index_builder = MarqoIndexBuilder() 
        return index_builder.query_index(domain = self.dataset_model.get_dataset_name(), q=query, limit=50, offset=0, filters=filters)

    def get_stats(self):
        index_builder = MarqoIndexBuilder() 
        return index_builder.get_index_stats(domain = self.dataset_model.get_dataset_name(), how=self.doc_build)

    def get_single_document(self, doc_id):
        index_builder = MarqoIndexBuilder() 
        return index_builder.get_single_document(domain = self.dataset_model.get_dataset_name(), doc_id=doc_id)

    