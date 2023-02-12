# mrtydi-v1.1-arabic (trained on MS MARCO)

Faiss flat index for Mr.TyDi v1.1 (Arabic), using mDPR fine-tuned on MS MARCO.

This index was generated on 2022/03/27 at commit [aa1c0e9](https://github.com/castorini/pyserini/commit/aa1c0e9a5bbfab406f8c73d23c91a009307096c6) on `cedar` with the following command:

```bash
lang=arabic

tarfn=mrtydi-v1.1-$lang.tar.gz
corpus=mrtydi-v1.1-$lang/collection/docs.jsonl
index_dir=mrtydi-mdpr-dindex-msmarco/$lang

wget https://git.uwaterloo.ca/jimmylin/mr.tydi/-/raw/master/data/$tarfn
tar –xvf $tarfn
gzip -cvf $corpus.gz > $corpus

shard_num=1
encoder=mdpr-mrtydi-0shot-msmarco-tied-encoder-converted 

for shard_id in $(seq 0 `$shard_num - 1`) ; do
    index_dir=mdpr-dindex/$lang-$shard_id
    mkdir -p $index_dir
    python -m pyserini.encode   input   --corpus $corpus \
                                        --fields title text \
                                        --delimiter "\n\n" \
                                        --shard-id $shard_id \
                                        --shard-num $shard_num \
                                output  --embeddings  $index_dir \
                                        --to-faiss \
                                encoder --encoder $encoder \
                                        --fields title text \
                                        --batch 128 \
                                        --fp16
done
``` 

Note that the delimiter are only supported after [Pyserini #1000](https://github.com/castorini/pyserini/pull/1000/commits/5021e12d1d2e1bc3d4015955bcf77076c5798ce6#diff-45356c3f5e9cd223bb23d7efea3f7ed834abbcd32f604eb7fdd138e364273241L104).

The index can be later reproduced on commit [7b099d5](https://github.com/crystina-z/pyserini/commit/7b099d534901d1f0161982605cd40d039ddb701d) using
```
encoder=castorini/mdpr-tied-pft-msmarco
index_dir=mdpr-dindex/$lang-$shard_id
mkdir -p $index_dir
python -m pyserini.encode   input   --corpus $corpus \
                                    --fields title text \
                                    --delimiter "\n\n" \
                                    --shard-id $shard_id \
                                    --shard-num $shard_num \
                            output  --embeddings  $index_dir \
                                    --to-faiss \
                            encoder --encoder $encoder \
                                    --fields title text \
                                    --batch 128 \
                                    --encoder-class 'auto' \
                                    --fp16
```

Here's a sample retrieval command (on the test set):

```bash
set_name=test
python -m pyserini.dsearch \
  --encoder castorini/mdpr-tied-pft-msmarco \
  --topics mrtydi-v1.1-${lang}-${set_name} \
  --index ${index_dir} \
  --output runs/run.mrtydi-v1.1-$lang.${set_name}.txt \
  --batch-size 36 \
  --threads 12 \
  --encoder-class 'auto'
```
