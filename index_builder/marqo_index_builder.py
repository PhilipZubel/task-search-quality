
import sys

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
    
    def __init__(self):
        self.mq = None
    
    def __parse_tags(self, proto_message):
         return " ".join([tag for tag in proto_message.tags])
    
    def __parse_steps(self, proto_message):
        return " ".join([step.response.speech_text for step in proto_message.steps])
    
    def __parse_requirements(self, proto_message):
        return " ".join([requirement.name for requirement in proto_message.requirement_list])

    def __get_protobuf_list_messages(self, path, proto_message):
        """ Retrieve list of protocol buffer messages from binary fire """
        return [d for d in stream.parse(path, proto_message)]

    def __build_doc(self, taskmap:TaskMap, how='all', dense=False):
        """ Build pyserini document from taskmap message. """
        # print(type(taskmap))
        # print(type(taskmap.SerializeToString()))
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
            # "DocumentAsString": str(taskmap.SerializeToString()),
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
        print("Write doc file")
        
        file_names = [f for f in os.listdir(input_dir) if '.bin' in f]

        # if not os.path.exists(output_dir):
        #     os.makedirs(output_dir)

        # for file_name in file_names:
        #     # Build in and out paths for file processing.
        #     in_path = os.path.join(input_dir, file_name)
        #     out_path = os.path.join(output_dir, dataset_name + '-' + file_name[:len(file_name) - 4] + '.jsonl')

        #     # Build list of pyserini documents.
        #     taskmap_list = self.__get_protobuf_list_messages(path=in_path, proto_message=TaskMap)
        #     self.docs_list = [self.__build_doc(taskmap, how=how, dense=dense)
        #                  for taskmap in taskmap_list]
            
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for file_name in file_names:
            # Build in and out paths for file processing.
            in_path = os.path.join(input_dir, file_name)
            out_path = os.path.join(output_dir, dataset_name + '-' + file_name[:len(file_name) - 4] )

            # Build list of documents.
            taskmap_list = self.__get_protobuf_list_messages(path=in_path, proto_message=TaskMap)            
            docs_list = []
            for idx, taskmap in enumerate(taskmap_list):
                docs_list.append(self.__build_doc(taskmap, how=how, dense=dense))
                if idx % 1000 == 0:
                    print(f"Taskmap: {idx}/{len(taskmap_list)}")
                    # Write to file
                    if idx != 0:
                        with open(f'{out_path}_{idx//1000}.jsonl', 'w') as f:
                            for doc in docs_list:
                                if 'text' in doc:
                                    if len(doc['text']) > 0:
                                        f.write(json.dumps(doc) + '\n')
                                else:
                                    f.write(json.dumps(doc) + '\n')
                        docs_list = []

            with open(out_path+".jsonl", 'w') as f:
                for doc in docs_list:
                    if 'text' in doc:
                        if len(doc['text']) > 0:
                            f.write(json.dumps(doc) + '\n')
                    else:
                        f.write(json.dumps(doc) + '\n')

    def __build_marqo_index(self, input_dir, domain):
        self.mq = marqo.Client(url='http://localhost:8882')
        self.mq.index(domain).delete()
        self.mq.create_index(domain)
        file_names = [f for f in os.listdir(input_dir) if '.jsonl' in f]

        for file in file_names:
            with open(os.path.join(input_dir, file)) as json_file:
                docs_list = [json.loads(doc) for doc in json_file]

            print("length", len(docs_list))
            self.mq.index(domain).add_documents(docs_list)

    def build_index(self, input_dir, domain):
        # Build Pyserini index.
        self.__build_marqo_index(input_dir=input_dir,
                                  domain=domain)
    
    def query_index(self, domain, q):
        if not self.mq:
            self.mq = marqo.Client(url='http://localhost:8882')
        return self.mq.index(domain).search(q, searchable_attributes=['Desription', 'Title', "Tags", "Steps", "Requirements"])
    
    def query_index_filter(self, q:str, filter:str):
        return self.mq.index("index-name").search(q=q, filter_string=filter)
    
    def get_index_stats(self, domain):
        if not self.mq:
            self.mq = marqo.Client(url='http://localhost:8882')
        return self.mq.index(domain).get_stats()
    
