
import sys
import subprocess

from index_builder.abstract_index_builder import AbstractIndexBuilder

from taskmap_pb2 import TaskMap
import subprocess
import stream
import json
import time
import os

import marqo


class MarqoIndexBuilder(AbstractIndexBuilder):
    
    def __init__(self, ):
        self.mq = None
        self.model = "marqo"
    
    # def __parse_tags(self, proto_message):
    #      return " ".join([tag for tag in proto_message.tags])
    
    # def __parse_steps(self, proto_message):
    #     return " ".join([step.response.speech_text for step in proto_message.steps])
    
    # def __parse_requirements(self, proto_message):
    #     return " ".join([requirement.name for requirement in proto_message.requirement_list])
    def __parse_title(self, proto_message):
        """ Extract text contents from proto title and requirements """
        return proto_message.title

    def __parse_title_and_requirements(self, proto_message):
        """ Extract text contents from proto title and requirements """
        contents = ''
        contents += proto_message.title + '. '
        for requirement in proto_message.requirement_list:
            contents += requirement.name + ' '

        return contents
    
    def __parse_all(self, proto_message):
        """ Extract text content from proto. """
        contents = ''
        contents += proto_message.title + '. '
        for requirement in proto_message.requirement_list:
            contents += requirement.name + ' '
        for tag in proto_message.tags:
            contents += tag + ' '
        contents += proto_message.description + ''
        for step in proto_message.steps:
            contents += step.response.speech_text + ' '

        return contents
    

    def __get_protobuf_list_messages(self, path, proto_message):
        """ Retrieve list of protocol buffer messages from binary fire """
        return [d for d in stream.parse(path, proto_message)]

    # def __build_doc(self, taskmap:TaskMap, how='all', dense=False):
    #     """ Build pyserini document from taskmap message. """
    #     # print(type(taskmap))
    #     # print(type(taskmap.SerializeToString()))
    #     return {
    #         "_id": taskmap.taskmap_id,
    #         "Title": taskmap.title,
    #         "Date": taskmap.date,
    #         "Steps": self.__parse_steps(taskmap),
    #         "Tags": self.__parse_tags(taskmap),
    #         "Requirements": self.__parse_requirements(taskmap),
    #         "Domain": taskmap.domain_name,
    #         "Description": taskmap.description,
    #         # "DocumentAsString": str(taskmap.SerializeToString()),
    #     }
    def __build_doc(self, taskmap, how='all', dense=False):
        """ Build pyserini document from taskmap message. """
        if how == 'all':
            contents = self.__parse_all(taskmap)
        elif how == 'title':
            contents = self.__parse_title(taskmap)
        elif how == 'title+ingredients':
            contents = self.__parse_title_and_requirements(taskmap)
        else:
            print('error - not set how correctly')
            contents = self.__parse_all(taskmap)
        return {
                "_id": taskmap.taskmap_id,
                "Contents": contents
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
            docs_list = [self.__build_doc(taskmap, how=how, dense=dense) for taskmap in taskmap_list]
            with open(out_path+".json", 'w') as f:
                # f.write('[\n')
                f.write(json.dumps(docs_list, indent=4))
                # for doc in docs_list:
                #     f.write(json.dumps(doc, indent=4) + ',\n')
                # f.write(']')
                


            # for idx, taskmap in enumerate(taskmap_list):
            #     docs_list.append(self.__build_doc(taskmap, how=how, dense=dense))
            #     if idx % 1000 == 0:
            #         print(f"Taskmap: {idx}/{len(taskmap_list)}")
            #         # Write to file
            #         if idx != 0:
            #             with open(f'{out_path}_{idx//1000}.jsonl', 'w') as f:
            #                 for doc in docs_list:
            #                     if 'text' in doc:
            #                         if len(doc['text']) > 0:
            #                             f.write(json.dumps(doc) + '\n')
            #                     else:
            #                         f.write(json.dumps(doc) + '\n')
            #             docs_list = []

            # with open(out_path+".jsonl", 'w') as f:
            #     for doc in docs_list:
            #         if 'text' in doc:
            #             if len(doc['text']) > 0:
            #                 f.write(json.dumps(doc) + '\n')
            #         else:
            #             f.write(json.dumps(doc) + '\n')

    def __build_marqo_index(self, input_dir, domain):
        
        if not self.mq:
            self.mq = marqo.Client(url='http://localhost:8882')
        
        # if self.model != "marqo":    
        #     settings = {
        #         "index_defaults": {
        #             "treat_urls_and_pointers_as_images": False,
        #             "model": "flax-sentence-embeddings/all_datasets_v4_mpnet-base",
        #             "normalize_embeddings": True,
        #         },
        #     }
        #     self.mq.create_index({domain}-{self.model}, settings_dict=settings)
        # self.mq.index(f"{domain}-{self.model}").delete()
        # self.mq.create_index(domain)
        # input_file = os.path.join(input_dir, "wikihow-taskmaps_108_v2.jsonl")
        for file in os.listdir(input_dir):
            input_file = os.path.join(input_dir, file)
            print(input_file)
            # subprocess.run(["curl", "-XPOST", f"http://localhost:8882/indexes/{domain}-{self.model}/documents?device=cuda&processes=4&batch_size=20",
            #     "-H", "Content-Type: application/json", 
            #     "-T", input_file,
            #     ])    
            # subprocess.run(["curl", "-XPOST", f"http://localhost:8882/indexes/{domain}-{self.model}/documents?device=cuda&processes=4&batch_size=20",
            #     "-H", "Content-Type: application/json", 
            #     "-T", input_file,
            #     "-d", '{"index_defaults": {"treat_urls_and_pointers_as_images": false,"model": "flax-sentence-embeddings/all_datasets_v4_mpnet-base","normalize_embeddings": true,"text_preprocessing": {"split_length": 2,"split_overlap": 0,"split_method": "sentence"},"image_preprocessing": {"patch_method": null}},"number_of_shards": 5}'
            #     ])          
  


        # file_names = [f for f in os.listdir(input_dir) if '.jsonl' in f]

        # for i,file in enumerate(file_names):
        #     print(file)
        #     with open(os.path.join(input_dir, file)) as json_file:
        #         docs_list = [json.loads(doc) for doc in json_file]
        #     self.mq.index(domain).add_documents(
        #         docs_list,
        #         batch_size=20,
        #     )

        #     # print("doc", i, "taskgraph count", len(docs_list))
        #     # print(docs_list[0])
        
        #     # doc_chunk_size = 100
        #     # idx = 0
        #     # while idx * doc_chunk_size < len(docs_list):
        #     #     print("chunk", idx, "size", doc_chunk_size)
        #     #     if (idx + 1)  * doc_chunk_size >= len(docs_list):
        #     #         doc_chunk = docs_list[idx*doc_chunk_size:]
        #     #     else:
        #     #         end_idx = (idx + 1)  * doc_chunk_size 
        #     #         doc_chunk = docs_list[idx*doc_chunk_size:end_idx]
                
        #     #     print(len(doc_chunk))
        #     #     self.mq.index(domain).add_documents(doc_chunk)
        #     #     idx+=1
                
    def build_index(self, input_dir, domain):
        # Build Pyserini index.
        self.__build_marqo_index(input_dir=input_dir,
                                  domain=domain)
        
    
    def query_index(self, domain, q, limit=50, offset=0):
        if not self.mq:
            self.mq = marqo.Client(url='http://localhost:8882')
        return self.mq.index(f'{domain}').search(q, searchable_attributes=['Contents'], limit=50, offset=0)
    
    # def query_index_filter(self, q:str, filter:str):
    #     return self.mq.index("index-name").search(q=q, filter_string=filter)
    
    def get_index_stats(self, domain, limit=50, offset=0):
        if not self.mq:
            self.mq = marqo.Client(url='http://localhost:8882')
        return self.mq.index(f'{domain}').get_stats()
    
    def get_single_document(self, domain, doc_id):
        if not self.mq:
            self.mq = marqo.Client(url='http://localhost:8882')
        return self.mq.index(f'{domain}').get_document(document_id=doc_id, expose_facets=True)
