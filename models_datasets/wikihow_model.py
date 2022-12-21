import json
import os

from .abstract_model_dataset import AbstractModelDataset
from .taskgraph_conversion.wikihow_convertor import WikihowConvertor

class WikihowModel(AbstractModelDataset):
    
    def __init__(self):
        
        self.name = "wikihow"
        
        self.raw_tasks_dir = os.path.join(os.getcwd(), 'task_datasets','wikihow_tasks','wikihow')
        self.taskmap_protos_dir = os.path.join(os.getcwd(), 'bin','wikihow')
        self.__taskmap_protos_file_path = os.path.join(self.taskmap_protos_dir,'taskmaps.bin')

        if not os.path.isdir(self.taskmap_protos_dir):
            os.makedirs(self.taskmap_protos_dir)
    
    def convert_to_taskgraphs(self, overwrite = False):

        if not overwrite and len(os.listdir(self.taskmap_protos_dir)) > 0:
            print("Taskgraphs already converted. Call overwrite=True in convert_to_taskgraphs() to overwrite the preprocessed taskgraphs.")
            return
        
        convertor = WikihowConvertor()
        taskmap_protos = []
        
        print("Converting Taskgraphs...")
        print(len(os.listdir(self.raw_tasks_dir)))
                 
        # load taskgraphs and preprocess taskgraphs
        """Each taskmap is stored as a separate json file"""
        for filename in os.listdir(self.raw_tasks_dir):
            with open(os.path.join(self.raw_tasks_dir, filename)) as f:
                diy_document = json.load(f)
                taskgraph = convertor.document_to_task_graph(diy_document)
                taskmap_protos.append(taskgraph.to_proto())
        
        print("Saving Taskgraphs...")
        self.write_protobuf_list_to_file(self.__taskmap_protos_file_path, taskmap_protos)
    
    def get_dataset_name(self):
        return "wikihow"
    
    def get_taskgraphs_path(self):
        return self.taskmap_protos_dir
    
    def get_index_path(self):
        return os.path.join(os.getcwd(), 'indexes', "diy")
    
    def get_index_temp_path(self):
        return os.path.join(os.getcwd(), 'indexes', 'temp', "diy")
    
    def get_measurements_path(self):
        return os.path.join(os.getcwd(), 'measurements', 'diy')