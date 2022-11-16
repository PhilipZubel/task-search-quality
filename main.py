
import os
import sys

sys.path.insert(0, './compiled_protobufs')

from index_builder.pyserini_index_builder import PyseriniIndexBuilder
from index_builder.abstract_index_builder import AbstractIndexBuilder


dataset_names = ["seriouseats", "wikihow"]
dataset_paths = [os.path.join(os.getcwd(), "bin", dataset,"taskmap") for dataset in dataset_names]

IndexBuilder = PyseriniIndexBuilder()
output_temp_dir = os.path.join(os.getcwd(), "temp", "system_index")
output_temp_dir_dense = os.path.join(os.getcwd(), "temp", "system_index_dense")
output_index_dir = os.path.join(os.getcwd(), "indexes", "system_index")
output_index_dir_dense = os.path.join(os.getcwd(), "indexes", "system_index_dense")

for taskmap_dir, dataset_name in zip(dataset_paths, dataset_names):
    IndexBuilder.build_json_docs(input_dir=taskmap_dir,
                                    output_dir=output_temp_dir,
                                    dataset_name=dataset_name)

    IndexBuilder.build_json_docs_dense(input_dir=taskmap_dir,
                                        output_dir=output_temp_dir_dense,
                                        dataset_name=dataset_name)
        
# Generate index.
IndexBuilder.build_index(input_dir=output_temp_dir,
                                    output_dir=output_index_dir)
# Generate Dense index.
IndexBuilder.build_index_dense(input_dir=output_temp_dir_dense,
                                output_dir=output_index_dir_dense)
    
    
from pyserini.search.lucene import LuceneSearcher    
import json    
    
searcher = LuceneSearcher(index_dir=output_index_dir)

last_utterance = "I want pasta."
top_k = 5

hits = searcher.search(q=last_utterance, k=top_k)

docs = []
for hit in hits:
    doc = searcher.doc(docid=hit.docid)
    docs.append(doc.raw())

for doc_string in docs:
    doc_json = json.loads(doc_string)
    taskmap_json = doc_json['recipe_document_json']

print(docs[0])