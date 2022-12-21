from abc import ABC, abstractmethod

from models_datasets.recipe_1m_model import Recipe1MModel
from models_datasets.wikihow_model import WikihowModel

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
    def search(self):
        pass
    
    def get_dataset_model(self, domain):
        if domain != "DIY" and domain != "COOKING":
            raise Exception(f'Task type must be either DIY or COOKING. Entered: {domain}')
        
        dataset_models = {
            "COOKING" : Recipe1MModel,
            "DIY": WikihowModel,
        }
        return dataset_models[domain]


    