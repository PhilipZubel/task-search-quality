# from models_datasets.abstract_model_dataset import AbstractModelDataset
# from pyserini.search import SimpleSearcher
# from sklearn.model_selection import GridSearchCV

# from models_datasets.recipe_1m_model import Recipe1MModel
# from models_datasets.wikihow_model import WikihowModel

# import os
# import numpy as np
# import pandas as pd

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
    
#     def __get_dataset_model(self, domain):
#         if domain != "DIY" and domain != "COOKING":
#             raise Exception(f'Task type must be either DIY or COOKING. Entered: {domain}')
        
#         dataset_models = {
#             "COOKING" : Recipe1MModel,
#             "DIY": WikihowModel,
#         }
#         return dataset_models[domain]

#     def __split_queries(self):
#         n_rows = len(self.queries)
#         rand_ints = np.random.randint(self.cv, size=n_rows)
#         df_parts = []
#         for i in range(self.cv):
#             df_parts.append(self.queries[rand_ints == i])
#         return df_parts

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


from pyserini.search import SimpleSearcher
from sklearn.base import BaseEstimator
import ir_measures

import numpy as np

class CustomRetrievalModel(BaseEstimator):
    def __init__(self, k1=1.2, b=0.75):
        self.k1 = k1
        self.b = b
        self.searcher = SimpleSearcher('/path/to/index')
        self.searcher.set_bm25(k1, b)

    def fit(self, X, y):
        return self

    def predict(self, X):
        results = {}
        for query in X:
            hits = self.searcher.search(query["target query"], k=50)
            docs = [(hit.docid, hit.score) for hit in hits]
            results[query] = docs
        return results

    def score(self, X, y):
        y_pred = self.predict(X)
        scored_docs = []
        for query in y.keys():
            relevant_docs = y[query]
            retrieved_docs = y_pred[query]
            scored_docs += [ir_measures.ScoredDoc(query["query_id"], docid, score) for docid, score in retrieved_docs]

        return np.mean(scores)


def get_ir_measures_qrels(qrels):
    return [ir_measures.Qrel(qrel["query_id"], qrel["doc_id"], qrel["relevance"]) for index, qrel in qrels.iterrows()]

def get_ir_measures_run(run):
    return 

