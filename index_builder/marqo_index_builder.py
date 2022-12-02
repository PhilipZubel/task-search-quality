
import sys
sys.path.insert(0, '/shared')
sys.path.insert(0, '/shared/compiled_protobufs')

from index_builder.abstract_index_builder import AbstractIndexBuilder


from google.protobuf.json_format import MessageToDict
from taskmap_pb2 import TaskMap
import subprocess
import stream
import json
import time
import os

import marqo


class MarqoIndexBuilder(AbstractIndexBuilder):
    
    def __parse_tags(self, proto_message):
         return " ".join([tag for tag in proto_message.tags])
    
    def __parse_steps(self, proto_message):
        return " ".join([step.response.speech_text for step in proto_message.steps])
    
    def __parse_requirements(self, proto_message):
        return " ".join([requirement.name for requirement in proto_message.requirement_list])

    def __get_protobuf_list_messages(self, path, proto_message):
        """ Retrieve list of protocol buffer messages from binary fire """
        return [d for d in stream.parse(path, proto_message)]

    def __build_doc(self, taskmap, how='all', dense=False):
        """ Build pyserini document from taskmap message. """
        print(taskmap)
        return {
            "_id": taskmap.taskmap_id,
            "Title": taskmap.title,
            "Date": taskmap.date,
            "Steps": self.__parse_steps(taskmap),
            "Tags": self.__parse_tags(taskmap),
            "Requirements": self.__parse_requirements(taskmap),
            "Domain": taskmap.domain_name,
            "Description": taskmap.description,
            "Difficulty": taskmap.difficulty,
        }
        
    def build_json_docs(self, input_dir, output_dir, dataset_name):
        """ Build index given directory of files containing taskmaps. """
        # Write Pyserini readable documents (i.e. json) to temporary folder.
        self.__write_doc_file_from_lucene_indexing(input_dir=input_dir,
                                                output_dir=output_dir,
                                                dataset_name=dataset_name,
                                                how='all')

    def __write_doc_file_from_lucene_indexing(self, input_dir, output_dir, dataset_name, how='all', dense=False):
        """ Write folder of pyserini json documents that represent taskmaps. """
        # Get list of files from 'in_directory'.
        file_names = [f for f in os.listdir(input_dir) if '.bin' in f]

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for file_name in file_names:
            # Build in and out paths for file processing.
            in_path = os.path.join(input_dir, file_name)
            out_path = os.path.join(output_dir, dataset_name + '-' + file_name[:len(file_name) - 4] + '.jsonl')

            # Build list of pyserini documents.
            taskmap_list = self.__get_protobuf_list_messages(path=in_path, proto_message=TaskMap)
            self.docs_list = [self.__build_doc(taskmap, how=how, dense=dense)
                         for taskmap in taskmap_list]

    def __build_marqo_index(self, input_dir, output_dir):
        self.mq = marqo.Client(url='http://localhost:8882')
        # self.mq.create_index("index-name")
        print(self.docs_list[0])
        settings = {
            "index_defaults": {
                "treat_urls_and_pointers_as_images": False,
                "model": "flax-sentence-embeddings/all_datasets_v4_MiniLM-L6", # good starting point
                # "model" : "flax-sentence-embeddings/all_datasets_v4_mpnet-base" # provides the best relevancy (in general)
                "normalize_embeddings": True,
            },
        }
        self.mq.index("index-name", **settings).add_documents(self.docs_list)

    def build_index(self, input_dir, output_dir):
        # Build Pyserini index.
        self.__build_marqo_index(input_dir=input_dir,
                                  output_dir=output_dir)

    
    def query_index(self, q):
        return self.mq.index("index-name").search(q, searchable_attributes=['Desription', 'Title', "Tags", "Steps", "Requirements"])
    
    def query_index_filter(self, q:str, filter:str):
        return self.mq.index("index-name").search(q=q, filter_string=filter)
    
    def get_index_stats(self):
        return self.mq.index("index-name").get_stats()
    
