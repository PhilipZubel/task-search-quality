
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


# class Bm25ModelGridCV():

#     def __init__(self, domain:str, queries, cv=4):
#         self.dataset_model: AbstractModelDataset = self.__get_dataset_model(domain)()
#         self.cv = cv
#         self.queries = queries
#         self.index_dir = os.path.join(self.dataset_model.get_index_path(), "system_index_sparse")
#         # np.random.seed(42)
#         # self.split_queries = self.__split_queries()

#     def set_k1_range(self, start, end, step):
#         """ Default is between 0.1-5.0 with step 0.2"""
#         self.k1_range = np.arange(start, end, step)
    
#     def set_b_range(self, start, end, step):
#         """ Default is between 0.1-1.0 with step 0.1"""
#         self.b_range = np.arange(start, end, step)
    




#     def fit(self):
#         param_grid = {
#             'k1': self.k1_range,
#             'b': self.b_range,
#         }
#         searcher = SimpleSearcher(self.index_dir)
#         # grid_search = GridSearchCV(searcher, param_grid, cv=self.cv, scoring='neg_mean_squared_error')
#         # grid_search.fit(self.queries["target query"])
#         # print("Best parameters: ", grid_search.best_params_)
#         # print("Best score: ", grid_search.best_score_)



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
        averages = np.array(averages)
        p = np.array(p)
        max_idxs = np.argmax(averages, axis=0)
        return averages, p, max_idxs

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

    def __get_ir_measures_run(self, k1=0.9, b=0.4):
        print(f"Generating run... k1={k1}, b={b}")
        scores_per_query = {}
        searcher = LuceneSearcher(index_dir=self.index_dir)
        searcher.set_bm25(k1=k1, b=b)
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

