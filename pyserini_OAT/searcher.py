from pyserini.search.lucene import LuceneSearcher
from google.protobuf.json_format import Parse
import json


index_path = "indexes/system_index"
searcher = LuceneSearcher(index_dir=index_path)

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
    # obj = taskmap_list.candidates.add()
    # Parse(json.dumps(taskmap_json), obj)

print(docs[0])