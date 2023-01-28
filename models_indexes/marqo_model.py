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

class MarqoModel(AbstractModel):

    def __init__(self, domain:str, model = ""):
        
        if model:
            self.model_name = model
        else:
            self.model_name = "marqo"
        
        self.dataset_model: AbstractModelDataset = self.get_dataset_model(domain)()

        
        self.output_temp_dir = os.path.join(self.dataset_model.get_index_temp_path(), "system_index_marqo")
        self.output_index_dir = os.path.join(self.dataset_model.get_index_path(), "system_index_marqo")
        self.run_path = os.path.join(self.dataset_model.get_measurements_path(), "run_files")
        
    def build_index(self, overwrite=False):
        
        if not os.path.isdir(self.output_temp_dir):
            os.makedirs(self.output_temp_dir)
            
        # if not overwrite and len(os.listdir(self.output_temp_dir)) > 0:
        #     print("Marqo index already built. Call overwrite=True in build_index() to rebuild the index again.")
        #     return
            
        index_builder = MarqoIndexBuilder(model = self.model_name)
        
        # print("Build documents...")
        # print(f"Saving documents to {self.output_temp_dir}...")
        # taskmap_dir = self.dataset_model.get_taskgraphs_path()
        # dataset_name = self.dataset_model.get_dataset_name()
        # index_builder.build_json_docs(input_dir=taskmap_dir,
        #                                 output_dir=self.output_temp_dir,
        #                                 dataset_name=dataset_name)
        
        print("Generate index...")
        # print(f"Saving documents to {self.output_index_dir}...")
        index_builder.build_index(input_dir=self.output_temp_dir,
                                    domain = self.dataset_model.get_dataset_name())

    
    def convert_search_results_to_run(self, pd_queries, raw=False):
        index_builder = MarqoIndexBuilder() 
        
        # retrieve results
        lines = []
        for idx, query in pd_queries.iterrows():
            if raw:
                q = query["raw query"]
            else:
                 q = query["target query"]
            hits = index_builder.query_index(domain = self.dataset_model.get_dataset_name(), q=q, limit=50, offset=0)
            for rank, hit in enumerate(hits["hits"]):
                line = f'query-{idx} Q0 {hit["_id"]} {rank+1} {hit["_score"]} {self.model_name}\n'
                lines.append(line)
        lines[-1] = lines[-1].replace("\n","")
        
        # if not os.path.isdir(self.run_path):
        #     os.makedirs(self.run_path)
        
        print(f"Run file saved at {self.run_path}/{self.model_name}-target.run")
        with open(os.path.join(self.run_path, f"{self.model_name}-target.run"), "w") as f:
            f.writelines(lines)
            
    def create_empty_judgments(self, pd_queries, k):
        pass
        # # Initialize searcher
        # encoder = AnceQueryEncoder("castorini/ance-msmarco-passage")
        # searcher = FaissSearcher(
        #     index_dir = self.output_index_dir,
        #     query_encoder= encoder,
        # )
        
        # # retrieve results
        # # fieldnames = ["raw query", "html_link", "relevance", "usability", "quality"]
        # empty_judgments = []
        # for idx, query in pd_queries.iterrows():
        #     hits = searcher.search(q=query["target query"], k=k)
        #     for hit in hits:
        #         doc_json = json.loads(hit.raw)
        #         taskmap_json = doc_json['recipe_document_json']
        #         taskmap = Parse(json.dumps(taskmap_json), TaskMap())
        #         empty_judgment = {
        #             # "doc-id" : taskmap.taskmap_id, 
        #             # "doc-title" : taskmap.title, 
        #             # "doc-url" : taskmap.source_url, 
        #             # "score": round(float(hit.score),3),
        #             # "query-id": query_id,
        #             # "query": query,
        #             # "taskgraph" : taskmap,
        #             "raw-query": query["raw query"],
        #             "html_link": taskmap.source_url,
        #             "relevance": "",
        #             "usability": "",
        #             "quality": "",
        #         }
        #         empty_judgments.append(empty_judgment)
        
        # annotations_path = os.path.join(self.dataset_model.get_measurements_path(), "empty_annotations")
        
        # if not os.path.isdir(annotations_path):
        #     os.makedirs(annotations_path)
        
        # print(f"Empty judgments file saved at {annotations_path}/{self.model_name}_empty.csv")
        # keys = ["raw-query", "html_link", "relevance", "usability", "quality"]
        # with open(os.path.join(annotations_path, f"{self.model_name}-judgments.csv"), 'w', newline='') as f:
        #     dict_writer = csv.DictWriter(f, keys)
        #     dict_writer.writeheader()
        #     dict_writer.writerows(empty_judgments)

    
    def get_measurements(self, judgments_path):
        qrles = ir_measures.read_trec_qrels(judgments_path)
        run = ir_measures.read_trec_run(self.run_path)
        accuracy = ir_measures.calc_aggregate([nDCG@3, Precision@3, Recall@3], qrles, run)
        return accuracy
    
    def search(self, query):
        index_builder = MarqoIndexBuilder() 
        return index_builder.query_index(domain = self.dataset_model.get_dataset_name(), q=query, limit=50, offset=0)

    def get_stats(self):
        index_builder = MarqoIndexBuilder() 
        return index_builder.get_index_stats(domain = self.dataset_model.get_dataset_name())

    def get_single_document(self, doc_id):
        index_builder = MarqoIndexBuilder() 
        return index_builder.get_single_document(domain = self.dataset_model.get_dataset_name(), doc_id=doc_id)

    