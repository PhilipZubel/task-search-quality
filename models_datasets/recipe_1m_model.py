import json
import os

from .abstract_model_dataset import AbstractModelDataset
from .taskgraph_conversion.recipe_1m_convertor import Recipe1MConvertor


class Recipe1MModel(AbstractModelDataset):
    
    def __init__(self):
        
        raw_tasks_dir = os.path.join(os.getcwd(), 'task_datasets','recipe1mln_tasks')
        self.__raw_tasks_file_path = os.path.join(raw_tasks_dir,'layer1.json')
        self.taskmap_protos_dir = os.path.join(os.getcwd(), 'bin','recipe1mln')
        self.__taskmap_protos_file_path = os.path.join(self.taskmap_protos_dir,'taskmaps.bin')

        if not os.path.isdir(self.taskmap_protos_dir):
            os.makedirs(self.taskmap_protos_dir)
        
    def convert_to_taskgraphs(self, overwrite = False):
        
        if not overwrite and len(os.listdir(self.taskmap_protos_dir)) > 0:
            print("Taskgraphs already converted. Call overwrite=True in convert_to_taskgraphs() to overwrite the preprocessed taskgraphs.")
            return
        
        # load taskgraphs
        print("Loading taskgraphs...")
        with open(self.__raw_tasks_file_path) as f:
            recipe_dataset = json.load(f)
            
        # load convertor and preprocess taskgraphs
        print("Converting Taskgraphs...")
        convertor = Recipe1MConvertor()
        taskmap_protos = []
        for idx, recipe in enumerate(recipe_dataset):
            taskgraph = convertor.document_to_task_graph((recipe, []))
            taskmap_protos.append(taskgraph.to_proto())
            if idx % 10000 == 0:
                print(f'processed taskgraphs: {idx}/{len(recipe_dataset)}')
        
        print("Saving Taskgraphs...")        
        self.write_protobuf_list_to_file(self.__taskmap_protos_file_path, taskmap_protos)
    
    def get_dataset_name(self):
        return "recipe1m+"
    
    def get_taskgraphs_path(self):
        return self.taskmap_protos_dir
    
    def get_index_path(self):
        return os.path.join(os.getcwd(), 'indexes', "cooking")
    
    def get_index_temp_path(self):
        return os.path.join(os.getcwd(), 'indexes', 'temp', "cooking")
    
    def get_measurements_path(self):
        return os.path.join(os.getcwd(), 'measurements', 'cooking')