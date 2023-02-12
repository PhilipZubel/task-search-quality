# msmarco-v2-passage-augmented

Lucene index of the MS MARCO V2 augmented passage corpus.

Note that there are three variants of this index:

+ `msmarco-v2-passage-augmented` (93G uncompressed): the "default" version, which stores term frequencies and the raw text. This supports bag-of-words queries, but no phrase queries and no relevance feedback.
+ `msmarco-v2-passage-augmented-slim` (20G uncompressed): the "slim" version, which stores term frequencies only. This supports bag-of-words queries, but no phrase queries and no relevance feedback. There is no way to fetch the raw text from this index.
+ `msmarco-v2-passage-augmented-full` (157G uncompressed): the "full" version, which stores term frequencies, term positions, document vectors, and the raw text. This supports bag-of-words queries, phrase queries, and relevance feedback.

These indexes were generated on 2022/08/08 at Anserini commit [`fbe35e`](https://github.com/castorini/anserini/commit/4d6d2a5a367424131331df2a8e9e00e6a9c68856) on `damiano` with the following commands:

```bash
nohup target/appassembler/bin/IndexCollection -collection MsMarcoV2PassageCollection \
  -generator DefaultLuceneDocumentGenerator -threads 18 \
  -input /scratch2/collections/msmarco/msmarco_v2_passage_augmented/ \
  -index indexes/lucene-index.msmarco-v2-passage-augmented.20220808.4d6d2a/ \
  -storeRaw -optimize \
  >& logs/log.msmarco-v2-passage-augmented.20220808.4d6d2a.txt &

nohup target/appassembler/bin/IndexCollection -collection MsMarcoV2PassageCollection \
  -generator DefaultLuceneDocumentGenerator -threads 18 \
  -input /scratch2/collections/msmarco/msmarco_v2_passage_augmented/ \
  -index indexes/lucene-index.msmarco-v2-passage-augmented-slim.20220808.4d6d2a/ \
  -optimize \
  >& logs/log.msmarco-v2-passage-augmented-slim.20220808.4d6d2a.txt &

nohup target/appassembler/bin/IndexCollection -collection MsMarcoV2PassageCollection \
  -generator DefaultLuceneDocumentGenerator -threads 18 \
  -input /scratch2/collections/msmarco/msmarco_v2_passage_augmented/ \
  -index indexes/lucene-index.msmarco-v2-passage-augmented-full.20220808.4d6d2a/ \
  -storePositions -storeDocvectors -storeRaw -optimize \
  >& logs/log.msmarco-v2-passage-augmented-full.20220808.4d6d2a.txt &
```
