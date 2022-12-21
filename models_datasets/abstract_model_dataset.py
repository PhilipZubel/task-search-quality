from abc import ABC, abstractmethod
import stream
import os

class AbstractModelDataset(ABC):
    
    @abstractmethod
    def convert_to_taskgraphs(self):
        pass
    
    def write_protobuf_list_to_file(self, path, protobuf_list, buffer_size=1000):
        """ Write list of Documents messages to binary file. """
        stream.dump(path, *protobuf_list, buffer_size=buffer_size)
    
    @abstractmethod
    def get_dataset_name(self):
        pass
    
    @abstractmethod
    def get_taskgraphs_path(self):
        pass
    
    @abstractmethod
    def get_index_path(self):
        pass
    
    @abstractmethod
    def get_index_temp_path(self):
        pass
    
    @abstractmethod
    def get_measurements_path(self):
        pass