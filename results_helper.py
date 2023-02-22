import os
import ir_measures
from ir_measures import *
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def get_filepaths(folder):
  file_names = os.listdir(folder)
  return [os.path.join(folder, filename) for filename in file_names]

def get_accuracy(run_filepath, qrels_filepath, metrics=None):
    run = ir_measures.read_trec_run(run_filepath)
    qrles = ir_measures.read_trec_qrels(qrels_filepath)
    if metrics is None:
        metrics = [nDCG@3, nDCG@5, nDCG@10, Precision@3, Precision@5, Precision@10, Recall@10, Recall@20, Recall@50, Judged@10, Judged@20, Judged@50, MAP]
    accuracy = ir_measures.calc_aggregate(metrics, qrles, run)
    return accuracy

def get_nDGCs_per_run(run_filepath, qrels_filepath):
    metrics = [nDCG@i for i in range(1,11)]
    run = ir_measures.read_trec_run(run_filepath)
    qrles = ir_measures.read_trec_qrels(qrels_filepath)
    accuracy = ir_measures.calc_aggregate(metrics, qrles, run)
    return accuracy

def get_precision_recall(run_filepath, qrles_filepath):
    run = ir_measures.read_trec_run(run_filepath)
    qrles = ir_measures.read_trec_qrels(qrles_filepath)
    precs = [IPrec@round(p,1) for p in np.arange(0,1.1,0.1)]
    iprec = ir_measures.calc_aggregate(precs, qrles, run)
    return iprec

def show_iprecs(results_iprec):
  precison_scores = np.arange(0, 1.1, 0.1)
  fig, ax = plt.subplots(figsize=(7,6))

  for model_name, res in results_iprec.items():
    recall_scores = res
    ax.plot(precison_scores,recall_scores, drawstyle='steps-pre',label=model_name)
  

  ax.set_xticks(np.arange(0, 1.1, step=0.1))
  ax.set_yticks(np.arange(0, 1.1, step=0.1))
  ax.set_xlim(left=0)
  ax.set_title(f"Precision-Recall Curve")
  ax.set_xlabel('Recall')
  ax.set_ylabel('Precision')
  ax.grid(axis='both', linestyle='--')
  ax.legend(loc='upper right')
  

# def get_stats(run_filepath, qrles_filepath):
    # run = ir_measures.read_trec_run(run_filepath)
    # qrles = ir_measures.read_trec_qrels(qrles_filepath)
    # precs = [IPrec(rel=2)@round(p,1) for p in np.arange(0,1.1,0.1)]
    # iprec = ir_measures.calc_aggregate(precs, qrles, run)
    # return iprec

def get_all_metrics(runs_dir, qrels, path, with_t5 = None, metrics = None):  
    if with_t5:
        path += '-t5.csv'
    elif with_t5 == False:
        path += '-base.csv'
    else:
        path += '.csv'

    runs = os.listdir(runs_dir)
    results = {}
    for searcher in sorted(runs):
        run = os.path.join(runs_dir, searcher)
        if not run.endswith(".run"):
            continue
        searcher_name = searcher[:-4].lower()
        if with_t5 == False and "t5" in searcher_name:
            continue
        if with_t5 == True and "t5" not in searcher_name:
            continue
        accuracy = get_accuracy(run, qrels, metrics = metrics)
        results[searcher_name] = accuracy
        
    df = pd.DataFrame(results).transpose()
    df.to_csv(path)
    return df

def get_all_metrics_searcher(runs_dir, qrels, path, s_name = None):  
    if s_name:
        path += f'{s_name}.csv'
    else:
        path += '.csv'

    runs = os.listdir(runs_dir)

    results = {}
    for searcher in sorted(runs):
        run = os.path.join(runs_dir, searcher)
        searcher_name = searcher[:-4].lower()
        print(s_name, searcher_name)
        if s_name and s_name not in searcher_name:
            continue
        accuracy = get_accuracy(run, qrels)
        results[searcher_name] = accuracy
        
    df = pd.DataFrame(results).transpose()
    df.to_csv(path)
    return df

def get_precision_recall_graph(runs_dir, qrles, with_t5 = None):
        
    results_iprec = {}
    precs = [IPrec@round(p,1) for p in np.arange(0,1.1,0.1)]
    
    runs = os.listdir(runs_dir)
    for searcher in sorted(runs):
        run = os.path.join(runs_dir, searcher)
        searcher_name = searcher[:-4].lower()
        if with_t5 == False and "t5" in searcher_name:
            continue
        if with_t5 == True and "t5" not in searcher_name:
            continue
        iprec = get_precision_recall(run, qrles)
        vals = [iprec[prec] for prec in precs]
        results_iprec[searcher_name] = vals
    
    show_iprecs(results_iprec)


def get_run_df(filepapth): 
    judgments = []
    with open(filepapth, "r") as f:
        for j in f:
            judgment = j.strip().split(" ")
            judgment[4] = float(judgment[4])
            judgments.append(judgment)
    cols = ['query_id', 'run', 'doc_id', "rank", "score", "model_name"]
    df = pd.DataFrame(judgments, columns=cols)

    return df

def get_qrles_df(filepath):
    judgments = []
    with open(filepath, "r") as f:
        for j in f:
            judgment = j.strip().split(" ")
            judgment[3] = int(judgment[3])
            judgments.append(judgment)
    df = pd.DataFrame(judgments, columns = ['query_id', 'run', 'doc_id', 'relevance']) 
    return df

def get_metric_per_query(df_qrles, df_run, metric, model_name):
    query_ids = df_run["query_id"].unique()
    accuracies = []
    for q_id in query_ids:
        filtered_df_run = df_run[df_run["query_id"] == q_id]
        filtered_df_qrels = df_qrles[df_qrles["query_id"] == q_id]
        run = get_ir_measures_run(filtered_df_run)
        qrels = get_ir_measures_qrels(filtered_df_qrels)
        accuracy = ir_measures.calc_aggregate(measures=[metric], run=run, qrels=qrels)
        accuracies.append({
            "metric_val" : accuracy[metric],
            "query_id" : q_id,
            "model": model_name
        })
    return accuracies

## search query by query analysis

def get_ir_measures_qrels(qrels):
    return [ir_measures.Qrel(qrel["query_id"], qrel["doc_id"], qrel["relevance"]) for index, qrel in qrels.iterrows()]

def get_ir_measures_run(run):
    return [ir_measures.ScoredDoc(score["query_id"], score["doc_id"], score["score"]) for index, score in run.iterrows()]

def get_metrics(run_folder, qrels_file, metric, t5 = True):
    run_files = get_filepaths(run_folder)
    if t5:
        run_files = [f for f in run_files if "t5" in f]
    else:
        run_files = [f for f in run_files if "t5" not in f]
    
    df_qrles = get_qrles_df(qrels_file)
    scores = []
    for file in run_files:
        model_name = file.split('/')[-1].split(".")[0]
        df_run = get_run_df(file)
        scores += get_metric_per_query(df_qrles, df_run, metric, model_name)
    return pd.DataFrame(scores)

def get_raw_query(x, queries):
    query = queries[queries["id"] == x["query_id"]].iloc[0]
    return query["raw query"]