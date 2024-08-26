# -*- coding: utf-8 -*-
"""
Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gaejuPlM0i8H-WNUDfDtOPWgY7b2N9Xl

COMP9417 Group Project (Topic 2)
Task: CommonLit Readability Prize
This program creates the features by feature engineering and combine with the existing features
Written by WENG XINN CHOW (z5346077)
"""

from google.colab import files

# Upload the dataset train.csv
files.upload()

# Import all required libraries
import pandas as pd
import numpy as np
import seaborn as sns
import textstat
import matplotlib.pyplot as plt
import spacy
from textstat.textstat import textstatistics
from collinearity import SelectNonCollinear
from spacy.tokenizer import Tokenizer
from spacy.util import compile_infix_regex

# Read train.csv file and print the first 5 rows
train_df = pd.read_csv('train.csv')
train_df.head()

# Drop id, url_legal and license columns (not relevant)
train_df = train_df.drop(columns = ['id', 'url_legal', 'license'])
train_df.head()

# Read Aztertest_features.csv file and concatenat the dataframes print the first 5 rows
train_df2 = pd.read_csv('Aztertest_features.csv')
train_df2 = train_df2.drop(columns = ['flesch', 'smog'])
train_df = pd.concat([train_df, train_df2], axis = 1, join = 'outer')
train_df.head()

def spacy_words_tokens(excerpt_arr):
    """
    Tokenize the given excerpt_arr (corpus array into tokens) and return the list of tokens
    """
    
    # Add regex to Spacy infix to preserve intra-word concatenators
    nlp = spacy.load('en_core_web_sm')
    infixes = nlp.Defaults.prefixes + (r'[./]',r"[-]~",r"(.'.)")
    infixes_re = spacy.util.compile_infix_regex(infixes)
    nlp.tokenizer = Tokenizer(nlp.vocab, infix_finditer = infixes_re.finditer)
    
    # Tokenize the whole excerpt array 
    words_list = []
    for ex in excerpt_arr:
        doc = nlp(ex)
        tokens = [token for token in doc if not (token.is_punct or token.is_space)]
        words_list.append(tokens)
    
    return words_list

def readability_features(excerpt, word_count, sentence_count):
    """
    Generate the relevant features related to readability and return all features 
    """

    num_words = word_count.to_numpy()
    num_sentences = sentence_count.to_numpy()
    words_list = spacy_words_tokens(excerpt)
    num_longwords = [sum([len(w.text) > 6 for w in wl]) for wl in words_list]
 
    # Readability Scores (different metrics)
    # Flesch Reading Ease
    flesch = [textstat.flesch_reading_ease(ex) for ex in excerpt]
    # Flesch Kincaid Grade
    kincaid = [textstat.flesch_kincaid_grade(ex) for ex in excerpt]
    # Gunning Fog Index
    gunning = [textstat.gunning_fog(ex) for ex in excerpt]
    # SMOG index
    smog = [textstat.smog_index(ex) for ex in excerpt]
    # Automated Readability Index 
    auto = [textstat.automated_readability_index(ex) for ex in excerpt]
    # Coleman-Liau Index
    coleman = [textstat.coleman_liau_index(ex) for ex in excerpt]
    # Linsear Write Formula
    linsear = [textstat.linsear_write_formula(ex) for ex in excerpt]
    # Dale-Chall Readability Score
    dalechall = [textstat.dale_chall_readability_score(ex) for ex in excerpt]
    # LIX
    lix = num_longwords / num_words
    # RIX
    rix = num_longwords / num_sentences
    
    feature_scores = []
    feature_scores.extend((num_longwords, flesch, kincaid, gunning, smog, 
                           auto, coleman, linsear, dalechall, lix, rix))
    
    return feature_scores

# Run readability_features to create features for datasets
features = readability_features(train_df['excerpt'], train_df['num_words'], train_df['num_sentences'])

# Convert features into a pandas dataframe
features_names = ['num_longwords', 'flesch', 'kincaid', 'gunning', 'smog', 'auto', 'coleman', 'linsear', 'dalechall', 'lix', 'rix']
features_df = pd.DataFrame(np.array(features).T, columns = features_names)
features_df.head()

# Concatenate both original and features dataframes (Use outer for union concatenation)
train_df = pd.concat([train_df, features_df], axis = 1, join = 'outer')
train_df.head()

# Find the correlations between features and target
correlations = train_df.drop(columns=['excerpt', 'standard_error']).corr()
cor_target = abs(correlations['target'])
# Drop the features that have correlations < 0.1
irrelevant = cor_target.index[cor_target < 0.1]
print(irrelevant)

# Drop the irrelevant columns
print('Before: ', train_df.shape)
train_df2 = train_df.drop(columns = irrelevant)
print('After: ', train_df2.shape)

# Find the correlations between features and target
collinearity = train_df2.drop(columns=['excerpt', 'standard_error', 'target']).corr()
collinearity = abs(collinearity)
upper_triangle = collinearity.where(np.triu(np.ones(collinearity.shape),k=1).astype(np.bool))
high_coll = [column for column in upper_triangle.columns if any(upper_triangle[column] > 0.7)]
print(high_coll)

# Drop the columns that have high collinearity
print('Before: ', train_df2.shape)
train_df2 = train_df2.drop(columns = high_coll)
print('After: ', train_df2.shape)

# Find the correlations between features and target (after removing multicollinear features)
cor = abs(train_df2.drop(columns = ['excerpt', 'standard_error']).corr())

# Create a heatmap to show the correlations 
fig, ax = plt.subplots(figsize=(30, 30))
plot = sns.heatmap(cor, annot = True, cmap = plt.cm.Reds)
plot.set_title("Correlations between Features", fontsize = 20)

train_df2.head()

# Convert into a csv file and download the file
train_df2.to_csv('train_features.csv', index = False)
files.download('train_features.csv')