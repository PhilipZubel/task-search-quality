from abc import ABC, abstractmethod

from models_datasets.recipe_1m_model import Recipe1MModel
from models_datasets.wikihow_model import WikihowModel
from models_datasets.abstract_model_dataset import AbstractModelDataset

from pyserini.search import LuceneSearcher

import os

class AbstractModel(ABC):
    
    @abstractmethod
    def build_index(self):
        pass
    
    @abstractmethod
    def convert_search_results_to_run(self, queries):
        pass
    
    @abstractmethod
    def get_measurements(self):
        pass
    
    @abstractmethod
    def search(self, query):
        pass
    
    def get_dataset_model(self, domain):
        if domain != "DIY" and domain != "COOKING":
            raise Exception(f'Task type must be either DIY or COOKING. Entered: {domain}')
        
        dataset_models = {
            "COOKING" : Recipe1MModel,
            "DIY": WikihowModel,
        }
        return dataset_models[domain]
    
    def get_lucene_searcher(self, dataset_model: AbstractModelDataset):
        output_index_dir = os.path.join(dataset_model.get_index_path(), "system_index_sparse")
        searcher = LuceneSearcher(index_dir=output_index_dir)
        return searcher
        
        
        


    