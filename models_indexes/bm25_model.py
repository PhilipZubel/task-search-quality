import os
import json
import csv
import sys
from google.protobuf.json_format import Parse

from models_datasets.abstract_model_dataset import AbstractModelDataset
from models_indexes.abstract_model import AbstractModel
from index_builder.pyserini_sparse_builder import PyseriniSparseBuilder
from pyserini.search import LuceneSearcher

import ir_measures
from ir_measures import *

from taskmap_pb2 import TaskMap

sys.path.insert(0, './pygaggle')
from pygaggle.rerank.base import Query, Text, hits_to_texts
from pygaggle.rerank.transformer import MonoT5

class BM25Model(AbstractModel):

    def __init__(self, domain:str, rm3:bool=False, t5:bool=False, params=None):
        self.model_name = "bm25"
        if rm3:
            self.model_name += "+rm3"
        if t5:
            self.model_name += "+t5"
        if params:
            for key, value in params.items():
                self.model_name += f"+{key}={value}"

        self.domain = domain
        self.rm3 = rm3
        self.t5 = t5
        self.params = params

        self.dataset_model: AbstractModelDataset = self.get_dataset_model(domain)()
        if self.t5:
            self.reranker = MonoT5()
        else:
            self.reranker = None
        
        self.output_temp_dir = os.path.join(self.dataset_model.get_index_temp_path(), "system_index_sparse")
        self.output_index_dir = os.path.join(self.dataset_model.get_index_path(), "system_index_sparse")
        self.run_path = os.path.join(self.dataset_model.get_measurements_path(), "run_files")
        
    def build_index(self, overwrite=False):
        
        if not os.path.isdir(self.output_index_dir):
            os.makedirs(self.output_index_dir)
            
        if not overwrite and len(os.listdir(self.output_index_dir)) > 0:
            print("Index already built. Call overwrite=True in build_index() to rebuild the index again.")
            return
            
        index_builder = PyseriniSparseBuilder()
        
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


    
    def convert_search_results_to_run(self, pd_queries):
        # Initialize searcher
        searcher = LuceneSearcher(index_dir=self.output_index_dir)
        if self.params:
            searcher.set_bm25(b=self.params["best_b"], k1=self.params["best_k1"])
        else:
            searcher.set_bm25(b=0.4, k1=0.9)
        if self.rm3 == True:
            if self.params and "best_fb_terms" in self.params:
                searcher.set_rm3(fb_terms=self.params["best_fb_terms"], fb_docs=self.params["best_fb_docs"], original_query_weight=self.params["best_original_query_weight"])
            else:  
                searcher.set_rm3(fb_terms=10, fb_docs=10, original_query_weight=0.5)
        
        # retrieve results
        lines = []
        for idx, query in pd_queries.iterrows():
            hits = searcher.search(q=query["target query"], k=50)
            if self.t5:
                # print(type(hits[0].raw))
                # print(hits[0].raw)
                hits = self.reranker.rerank(Query(query["target query"]), hits_to_texts(hits))
            for rank, hit in enumerate(hits):
                if type(hit) == Text:
                    doc_json = json.loads(hit.text)
                else:
                    doc_json = json.loads(hit.raw)
                taskmap_json = doc_json['recipe_document_json']
                taskmap = Parse(json.dumps(taskmap_json), TaskMap())
                doc_id = taskmap.taskmap_id
                line = f'{query["id"]} Q0 {doc_id} {rank+1} {hit.score} {self.model_name}\n'
                lines.append(line)
        lines[-1] = lines[-1].replace("\n","")
        
        if not os.path.isdir(self.run_path):
            os.makedirs(self.run_path)
        
        # print(f"Run file saved at {self.run_path}/{self.model_name}.run")
        with open(os.path.join(self.run_path, f"{self.model_name}.run"), "w") as f:
            print(os.path.join(self.run_path, f"{self.model_name}.run"))
            f.writelines(lines)
            
    def create_empty_judgments(self, pd_queries, k, n):
        # Initialize searcher
        searcher = LuceneSearcher(index_dir=self.output_index_dir)
        searcher.set_bm25(b=0.4, k1=0.9)
        
        if self.rm3 == True:
            searcher.set_rm3(fb_terms=10, fb_docs=10, original_query_weight=0.5)
        
        # retrieve results
        # fieldnames = ["raw query", "html_link", "relevance", "usability", "quality"]
        empty_judgments = []
        for idx, query in pd_queries.iterrows():
            hits = searcher.search(q=query["target query"], k=k)
            if self.t5:
                hits = self.reranker.rerank(Query(query["target query"]), hits_to_texts(hits))
            for hit in hits[:n]:
                if type(hit) == Text:
                    doc_json = json.loads(hit.text)
                else:
                    doc_json = json.loads(hit.raw)
                taskmap_json = doc_json['recipe_document_json']
                taskmap = Parse(json.dumps(taskmap_json), TaskMap())
                empty_judgment = {
                    
                    # "doc-title" : taskmap.title, 
                    # "doc-url" : taskmap.source_url, 
                    # "score": round(float(hit.score),3),
                    "query-id": query['id'],
                    "raw-query": query["raw query"],
                    "html_link": taskmap.source_url,
                    "doc-id" : taskmap.taskmap_id, 
                    "title": taskmap.title,
                    "relevance": "",
                }
                empty_judgments.append(empty_judgment)
        
        annotations_path = os.path.join(self.dataset_model.get_measurements_path(), "empty_annotations")
        
        if not os.path.isdir(annotations_path):
            os.makedirs(annotations_path)
        
        print(f"Empty judgments file saved at {annotations_path}/{self.model_name}judgments.csv")
        keys = ["query-id", "doc-id", "raw-query", "html_link", "title", "relevance"]
        with open(os.path.join(annotations_path, f"{self.model_name}-judgments.csv"), 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(empty_judgments)

    
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
            
        
        
        
    