# python -m spacy download en_core_web_sm

import spacy
import pandas as pd
import nltk
from nltk.stem.snowball import SnowballStemmer
from spellchecker import SpellChecker

nlp = spacy.load('en_core_web_sm', disable=['ner'])

def preprocess_queries():
    query_types = ["cooking", "diy"]
    
    for q_type in query_types:
        df = pd.read_csv(f"queries/{q_type}_raw.csv")

        df["target query"] = df["raw query"].apply(lambda x: preprocess_query(x))

        ids = [f'query-{i}' for i in range(0, len(df))]
        df.insert(0, 'id', ids)

        print(f"Saving preprocessed {q_type} dataset")
        
        path_to = f"queries/{q_type}.csv"
        df.to_csv(path_to, index=False)

def __stopword_removal(text):
    my_file = open("query_pipeline/stopwords.txt", "r")
    stopword_list = my_file.read().split("\n")
    my_file.close()
    
    tokens = []
    # tokenization
    doc = nlp(text, disable=["tagger", "parser", "attribute_ruler", "tok2vec", ])
    # stop word removal
    for t in doc:
        if (not t.is_stop or t.like_num) and not t.is_punct and not t.is_space:
            if not str(t) in stopword_list:
                tokens.append(t.lemma_.lower())
    return tokens

def __stemming(tokens):
    stemmer = SnowballStemmer(language='english')
    return [stemmer.stem(token) for token in tokens]

def __spell_check(tokens):
    spell = SpellChecker()
    misspelled = spell.unknown(tokens)
    words = []
    for word in tokens:
        if word in misspelled:
            if not spell.correction(word) is None:
                words.append(spell.correction(word))
            else:
                words.append(word)
        else:
            words.append(word)
    return words

def __key_words(tokens):
    tokens = nlp(" ".join(tokens))
    pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB', 'NUM']
    return [token.text for token in tokens if token.pos_ in pos_tag]

def preprocess_query(query):    
    tokens = __stopword_removal(query)
    tokens = __spell_check(tokens)
    tokens = __key_words(tokens)
    tokens = __stemming(tokens)
    parsed_query = " ".join(tokens)
    # print(query, " - ", parsed_query)
    return parsed_query

