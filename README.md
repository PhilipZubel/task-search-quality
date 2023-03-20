# Task Search Quality

## Installation Setup

1. Install Java JDK 11+

`sudo apt-get install openjdk-11-jdk`

2Create a virtual environment and install all packages in `requirements.txt`:

```
pip install -r requirements.txt
```

2. Clone pygaggle repository from [here](https://github.com/castorini/pygaggle).

3. Complie protocol buffers:

```
bash compile_protos.sh
```


4. Marqo requires [Docker](https://docs.docker.com/get-docker/). Use docker to run Marqo:

```
docker pull marqoai/marqo:0.0.11;
docker rm -f marqo;
docker run --name marqo -it --privileged -p 8882:8882 --add-host host.docker.internal:host-gateway marqoai/marqo:0.0.11
```

describe with GPU

5. Either run `python3 main.py` or run the cells inside `main.ipynb`.


