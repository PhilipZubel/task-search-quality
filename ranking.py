import os
import sys

sys.path.insert(0, './compiled_protobufs')

dataset_names = ["recipe1mln"]
dataset_paths = [os.path.join(os.getcwd(), "bin", dataset, "taskmap") for dataset in dataset_names]

from index_builder.pyserini_bm25_builder import PyseriniBM25Builder
output_temp_dir = os.path.join(os.getcwd(), "temp", "food", "system_index_sparse")
output_index_dir = os.path.join(os.getcwd(), "indexes", "food", "system_index_sparse")

PyseriniBM25Builder = PyseriniBM25Builder()
for taskmap_dir, dataset_name in zip(dataset_paths, dataset_names):
    PyseriniBM25Builder.build_json_docs(input_dir=taskmap_dir,
                                    output_dir=output_temp_dir,
                                    dataset_name=dataset_name)
    
print("JSON BUILT")

PyseriniBM25Builder.build_index(input_dir=output_temp_dir,
                                    output_dir=output_index_dir)