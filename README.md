# Search Analysis on Cooking and DIY Tasks

This repository contains the evaluation of state-of-the art ranking models on a handcrafted task-based dataset benchmark. The dataset consists of Cooking and DIY tasks which are based on the WikiHow [link] and Recipe1m+, queries, and annotations. The two task domains are evaluated separately.

## Dataset
The dataset benchmark includes 100 Cooking and 100 DIY topics and includes the following components:
- Queries
- Runs
- Qrels
- Raw judgments

## Queries

100 Cooking and 100 DIY queries are created. These are assessed based on criteria which ensure the queries are complex and diverse. The following is the list of criteria used throughout query creation:

- Knowledge - The topic requires thorough knowledge in order to be successfully understood.
- Complexity - It may be necessary for an adult to conduct thorough research and investigation
for the correct evaluation of the topic.
- Many points of view - The topic elicits a range of perspectives and all of these perspectives are to be considered in order to provide a thorough and well-informed evaluation.
- Multiple key entities - It is desirable for the topic to involve multiple key entities such as time limitations, senses, mood, ingredients/requirements, etc.

These criteria ensure that queries within the cooking collection are dissimilar and trigger retrieval of disjoint subsets of documents.
- Regionality (Cooking) - It is important that the topics come from a diverse range of geographic regions
around the world to cover a variety of cuisines.
- Seasonality (Cooking) - Topics should encompass a range of different seasons and holidays.
- Meal Type (DIY) - Topics need to cover a range of meals (breakfast, lunch, dinner, dessert) and beverages.


## Models
The following popular ranking algorithms are assessed on the dataset benchmark: BM25, BM25 + RM3, ANCE, TCT-ColBERT v2, MiniLM-L6. These ranking are supported by Pyserini[link] and Marqo[link]. Pygaggle's[link] implementation of T5 reranking is applied on top of each ranking model. Additionally, Reciprocal Rank Fusion (RRF) between BM25 + RM3 and TCT-ColBERT v2 is assessed. 

## Runs
Initial retreival of depth 50 is evaluated. Reranking is applied on all retrieved documents. The runs of each evaluated architecture can be found here[link].

## Annotations
A total of 12,141 annotations have been created for the two task domains. 

|  Domain | **Cooking** |  **DIY**  |  **Both**  |
|:-------:|:-----------:|:---------:|:----------:|
| Score 0 |    2,869    |   3,157   |    6,026   |
| Score 1 |    1,731    |   1,004   |    2,735   |
| Score 2 |     2759    |    621    |    3,380   |
|  Total  |  **7,359**  | **4,782** | **12,141** |

## Installation Setup

Clone this repository:
```
git clone https://github.com/PhilipZubel/task-search-quality
```
Install Java JDK 11+

```
sudo apt-get install openjdk-11-jdk`
```

Create a virtual environment and install all packages in `requirements.txt`:

```
cd task-search-quality
pip install -r requirements.txt
```

Clone pygaggle repository from [here](https://github.com/castorini/pygaggle).

Complie protocol buffers:

```
bash compile_protos.sh
```

Marqo requires [Docker](https://docs.docker.com/get-docker/). Use docker to run Marqo
```
# CPU version
docker pull marqoai/marqo:0.0.12;
docker rm -f marqo;
docker run --name marqo -it --privileged -p 8882:8882 --add-host host.docker.internal:host-gateway marqoai/marqo:0.0.12
```
```
# GPU version'
docker pull marqoai/marqo:0.0.12;
docker rm -f marqo;
docker run --name marqo --gpus all --privileged -p 8882:8882 --add-host host.docker.internal:host-gateway marqoai/marqo:0.0.12
```

Run `main.ipynb` to reproduce results. 

## Results

Overall Results on the Cooking dataset:
| Model             | MAP   | P@3   | P@10  | nDCG@3 | nDCG@10 | R@50  | 
|----------------------------|----------------|----------------|----------------|-----------------|------------------|----------------|
| **BM25**              | 0.493          | 0.730          | 0.586          | 0.624           | 0.584            | 0.747          | 
| **BM25 (optimal)**       | *0.510* | *0.730* | *0.599* | *0.629*  | *0.599*   | *0.758* |
| **BM25 + RM3**        | 0.517          | 0.743          | 0.617          | 0.629           | 0.606            | 0.761          |
| **BM25 + RM3 (best)** | 0.532          | 0.757          | **0.617** | 0.643           | 0.612            | **0.774** |
| **ANCE**              | **0.431** | **0.783** | 0.559          | **0.713**  | 0.617            | **0.635** |
| **TCT-ColBERT v2**    | 0.522          | **0.837** | **0.633** | **0.747**  | **0.669**   | 0.726          |
| **MiniLM-L6**         | **0.453** | 0.713          | **0.555** | 0.617           | 0.574            | 0.731          |
| **BM25 + RM3 + T5 (optimal)**  | **0.582** | **0.810** | **0.701** | **0.733**  | **0.707**   | 0.774          |
| **TCT-ColBERT v2 + T5**     | **0.561** | **0.840** | **0.676** | **0.744**  | **0.710**   | 0.726          |
| **Fusion BM25+RM3/TCT-ColBERT v2** | **0.630** | **0.870** | **0.675** | **0.770**  | **0.706**   | **0.857** |
| **Fusion BM25+RM3/TCT-ColBERT v2 + T5** | **0.629**                   | **0.830** | **0.683** | **0.741** | **0.711**  | **0.857**   |                |
| **MiniLM-L6 + T5**          | **0.562** | **0.840** | **0.675** | **0.746**  | **0.707**   | 0.731          |

Overall Results on the DIY dataset:


| **Model**                           | **MAP** | **P@3** | **P@10** | **nDCG@3** | **nDCG@10** | **R@50** |
|----------------------------------------------|------------------|------------------|-------------------|---------------------|----------------------|-------------------|
| **BM25**              | 0.169            | 0.570            | **0.535**    | 0.454               | **0.435**       | 0.296             | 1.000                  |
| **BM25 (best)**       | *0.171*   | *0.590*   | *0.513*    | *0.469*      | *0.425*       | *0.295*    | 0.907                  |
| **BM25 + RM3**        | 0.170            | **0.527**   | 0.531             | 0.449               | 0.440                | 0.285             | 1.000                  |
| **BM25 + RM3 (best)** | **0.178**   | 0.587            | 0.504             | 0.481               | 0.430                | 0.299             | 0.911                  |
| **ANCE**              | **0.244**   | **0.783**   | **0.715**    | **0.685**      | **0.623**       | 0.333             | 1.000                  |
| **TCT-ColBERT v2**    | **0.278**   | **0.790**   | **0.747**    | **0.708**      | **0.657**       | **0.386**    | 1.000                  |
| **MiniLM-L6**         | 0.204            | 0.670            | **0.643**    | **0.562**      | **0.551**       | 0.324             | 1.000                  |
| **BM25 + RM3 + T5**          | **0.214**   | **0.757**   | **0.654**    | **0.649**      | **0.566**       | 0.285             |
| **TCT-Colbert v2 + T5**             | **0.302**   | **0.873**   | **0.817**    | **0.787**      | **0.737**       | **0.386**    |
| **Fusion BM25+RM3/TCT-ColBERT v2**      | **0.296**   | **0.733**   | **0.631**    | **0.652**      | **0.568**       | **0.436**    |
| **Fusion BM25+RM3/TCT-ColBERT v2 + T5** | **0.335**   | **0.857**   | **0.745**    | **0.756**      | **0.674**       | **0.436**    |
| **ANCE + T5**                       | **0.273**   | **0.880**   | **0.816**    | **0.800**      | **0.735**       | 0.334             |
| **MiniLM-L6 + T5**                  | **0.249**   | **0.807**   | **0.777**    | **0.707**      | **0.672**       | 0.324             |






