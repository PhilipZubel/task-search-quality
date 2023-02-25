
import os
import json
import numpy as np
import pandas as pd
import itertools
import ir_measures

np.random.seed(42)

from google.protobuf.json_format import Parse
from taskmap_pb2 import TaskMap

from pyserini.search import LuceneSearcher
from models_datasets.recipe_1m_model import Recipe1MModel
from models_datasets.wikihow_model import WikihowModel

class GridSearchCV():

    def __init__(self, domain:str, queries, params, cv=5):
        self.dataset_model: AbstractModelDataset = self.__get_dataset_model(domain)()
        self.cv = cv
        self.queries = queries
        self.index_dir = os.path.join(self.dataset_model.get_index_path(), "system_index_sparse")
        self.params = params
        self.split_queries = self.__split_queries()
        judgments_df = self.__get_qrles_df(f'/home/ubuntu/task-search-quality/measurements/judgments/{domain.lower()}.qrels')
        self.judgments = self.__get_ir_measures_qrels(judgments_df)

    def predict(self):

        averages = []
        p = []
        for b in self.params['b']:
            run = self.__get_ir_measures_run(b=b)
            scores = self.__get_average_score(run)
            print(f'MAP scores: {scores}')
            p.append(b)
            averages.append(scores)
        self.best_b = self.__get_best_param(averages, p)

        averages = []
        p = []
        for k1 in self.params['k1']:
            run = self.__get_ir_measures_run(b=self.best_b, k1=k1)
            scores = self.__get_average_score(run)
            print(f'MAP scores: {scores}')
            p.append(k1)
            averages.append(scores)
        self.best_k1 = self.__get_best_param(averages, p)

        if "fb_terms" not in self.params:
            return {
                "best_k1" : self.best_k1,
                "best_b" : self.best_b,
            }

        averages = []
        p = []
        for fb_terms in self.params['fb_terms']:
            run = self.__get_ir_measures_run(b=self.best_b, k1=self.best_k1, fb_terms=fb_terms, rm3=True)
            scores = self.__get_average_score(run)
            print(f'MAP scores: {scores}')
            p.append(fb_terms)
            averages.append(scores)
        self.best_fb_terms = self.__get_best_param(averages, p)

        averages = []
        p = []
        for fb_docs in self.params['fb_docs']:
            run = self.__get_ir_measures_run(b=self.best_b, k1=self.best_k1, fb_terms=self.best_fb_terms, fb_docs=fb_docs, rm3=True)
            scores = self.__get_average_score(run)
            print(f'MAP scores: {scores}')
            p.append(fb_docs)
            averages.append(scores)
        self.best_fb_docs = self.__get_best_param(averages, p)
        
        averages = []
        p = []
        for original_query_weight in self.params['original_query_weight']:
            run = self.__get_ir_measures_run(b=self.best_b, k1=self.best_k1, fb_terms=self.best_fb_terms, fb_docs=self.best_fb_docs, original_query_weight=original_query_weight, rm3=True)
            scores = self.__get_average_score(run)
            print(f'MAP scores: {scores}')
            p.append(original_query_weight)
            averages.append(scores)
        self.original_query_weight = self.__get_best_param(averages, p)

        return {
            "best_k1" : self.best_k1,
            "best_b" : self.best_b,
            "best_fb_terms" : self.best_fb_terms,
            "best_fb_docs" : self.best_fb_docs,
            "original_query_weight" : self.original_query_weight,
        }
        
    def __get_best_param(self, averages, p):
        averages = np.array(averages)
        p = np.array(p)
        max_idxs = np.argmax(averages, axis=0)
        p_max_values = p[max_idxs]
        return  round(np.mean(p_max_values), 2)

    def __get_average_score(self, run):
        scores = []
        for i in range(self.cv):
            tested_queries = [self.split_queries[k] for k in range(self.cv) if k != i]
            flatten_queries = itertools.chain(*tested_queries)
            scores_it = [run[query] for query in flatten_queries]
            scores.append(np.average(scores_it))
        return scores

    def __split_queries(self):
        n_rows = len(self.queries)
        rand_ints = np.random.randint(self.cv, size=n_rows)
        df_parts = []
        for i in range(self.cv):
            df_parts.append(self.queries[rand_ints == i]["id"].tolist())
        return df_parts

    def __get_ir_measures_run(self, k1=0.9, b=0.4, fb_terms=10, fb_docs=10, original_query_weight=0.5, rm3=False): 
        scores_per_query = {}
        searcher = LuceneSearcher(index_dir=self.index_dir)
        searcher.set_bm25(k1=k1, b=b)
        if rm3:
            # print(fb_terms,fb_docs,original_query_weight)
            searcher.set_rm3(fb_terms=fb_terms, fb_docs=fb_docs, original_query_weight=original_query_weight)
            print(f"Generating run... k1={k1}, b={b}, fb_terms={fb_terms}, fb_docs={fb_docs}, original_query_weight={original_query_weight}")
        else:
            print(f"Generating run... k1={k1}, b={b}")
        for idx, query in self.queries.iterrows():
            hits = searcher.search(q=query["target query"], k=50)
            run = []
            for rank, hit in enumerate(hits):
                doc_json = json.loads(hit.raw)
                taskmap_json = doc_json['recipe_document_json']
                taskmap = Parse(json.dumps(taskmap_json), TaskMap())
                doc_id = taskmap.taskmap_id
                run.append(ir_measures.ScoredDoc(query["id"], doc_id, hit.score))
            scores_per_query[query["id"]] = self.__get_ir_measures_score(run)[ir_measures.AP] * len(self.queries)
        return scores_per_query
    
    def __get_ir_measures_score(self, run):
        return ir_measures.calc_aggregate(measures=[ir_measures.AP], run=run, qrels=self.judgments)

    def __get_ir_measures_qrels(self, qrels):
        return [ir_measures.Qrel(qrel["query_id"], qrel["doc_id"], qrel["relevance"]) for index, qrel in qrels.iterrows()]

    def __get_qrles_df(self,filepath):
        judgments = []
        with open(filepath, "r") as f:
            for j in f:
                judgment = j.strip().split(" ")
                judgment[3] = int(judgment[3])
                judgments.append(judgment)
        df = pd.DataFrame(judgments, columns = ['query_id', 'run', 'doc_id', 'relevance']) 
        return df

    def __get_dataset_model(self, domain):
        if domain != "DIY" and domain != "COOKING":
            raise Exception(f'Task type must be either DIY or COOKING. Entered: {domain}')
        
        dataset_models = {
            "COOKING" : Recipe1MModel,
            "DIY": WikihowModel,
        }
        return dataset_models[domain]

