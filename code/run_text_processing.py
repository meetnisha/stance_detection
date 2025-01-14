#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Text processing of data
"""

import numpy as np
import pandas as pd
import os
import re
import pickle
import nltk
from sklearn import feature_extraction
from score import report_score, LABELS, score_submission
from dataset import DataSet

import codecs
import sys
#reload(sys) # for text processing
#sys.setdefaultencoding('utf8') # for text processing

# ======== Load data =======
base_path = '/Users/Monu/NLP/Stance/code'
#base_path = '/home/jupiter/Manisha/code/'
def read_data(): 
    
    # Extracting data
    dataset = DataSet(path = base_path + '/data')
    stances = dataset.stances
    articles = dataset.articles
    
    # Data to lists
    h, b, y = [],[],[]
    for stance in stances:
        y.append(LABELS.index(stance['Stance']))
        h.append(stance['Headline'])
        b.append(dataset.articles[stance['Body ID']])
    y = np.asarray(y, dtype = np.int64)
    #print(h)
    #print(b)
    #print(y)
    return h, b, y

       
    
# ----- Loading Glove embeddings ----
def loadGloVe(filename):
    #print(filename)
    # Getting embedding dimension
    file0 = open(filename,'r')
    #file0 = codecs.open(filename, 'r', 'utf8', 'ignore')
    line = file0.readline()
    emb_dim = len(line.strip().split(' ')) - 1
    file0.close()

    # First row of embedding matrix is 0 for zero padding
    vocab = ['<pad>'] #By Manisha - Using this
    embd = [[0.0] * emb_dim] #By Manisha - Using this
    #vocab = []
    #embd = []
    #model = {}
    # Reading embedding matrix
    file = open(filename,'r')
    file = codecs.open(filename, 'r', 'utf8', 'ignore')
    for line in file.readlines():
        row = line.strip().split(' ')
        vocab.append(row[0])
        embd.append(row[1:])
        #model[vocab] = embd
        #embd.append(map(float,row[1:]))
    print('Loaded GloVe!')
    file.close()
    
    return vocab,embd


# ------ Clean quote signs ---------
def clean_data(sentences):
    '''
    Delete quote signs
        - Rational: quote signs mix with the parsing
        - Con: quote signs are meaningul --> distanciation from a statement
    '''

    new_sentences = []
    #new_sentences = " ".join(re.findall(r'\w+', sentence, flags=re.UNICODE)).lower()
    for sentence in sentences:
        #print(sentence.replace("'","").replace('"',''))
        #print(re.findall(r'\w+', sentence.lower(), flags=re.UNICODE))
        new_sentences.append(sentence.replace("'","").replace('"','')) #re.findall(r'\w+', sentence.lower(), flags=re.UNICODE))#sentence.replace("'","").replace('"',''))
    return new_sentences

# ---- Build vocab dictionary from embedding matrix -----
def build_vocDict(vocab):
    voc_dict = {}
    for i in range(len(vocab)):
        #print(vocab[i])
        voc_dict[vocab[i]] = i
    return voc_dict

# -------- words to ids only -------

def words2ids(sentences, voc_dict, option = 'simple'):
    '''
    Inputs: 
        - sentences: list of sentences as string
        - embedding_vocab: list of vocab words in the order of the rows of embedding_matrix
    Ouptut: 
        - new_sentences_ids: list of sentences as successive word indexes
    Processing: delete word which do no appear in vocabulary
        - Alternative: replace missing words by the mean
    '''
    new_sentences_ids = []
    j = 0
    for sentence in sentences:
        j+=1
        if j % 5000 == 0:
            print ('sentence',str(j))
        sentence_ids = []
        if option == 'nltk':
            sentence = sentence.decode('utf8', 'ignore')
            # print('sentence', sentence)
            word_list = tokenize(sentence)
            # print('word_list', word_list)
        elif option == 'simple':
            word_list = sentence.split(" ")
        
        for word in word_list:
            word = word.decode("utf-8")
            if word.lower() in voc_dict: # Only add word if in dictionary
                word_index = voc_dict[word.lower()]
                sentence_ids.append(word_index)
                
        new_sentences_ids.append(sentence_ids)
        #print ("added",j)
    return new_sentences_ids

def normalize_word(w):
    _wnl = nltk.WordNetLemmatizer()
    return _wnl.lemmatize(w).lower()

def remove_stopwords(l):
    return [w for w in l if w not in feature_extraction.text.ENGLISH_STOP_WORDS]

# -------- words to ids and vectors -------
def words2ids_vects(sentences, voc_dict, embedding_matrix, option = 'simple'):  
    '''
    Inputs: 
        - sentences: list of sentences as string
        - embedding_vocab: list of vocab words in the order of the rows of embedding_matrix
        - embedding_matrix
    Ouptut: 
        - new_sentences_ids: list of sentences as successive word indexes
        - new_sentences_vects: list of sentences as successive word vectors
    Processing: delete word which do no appear in vocabulary
        - Alternative: replace missing words by the mean
    '''
    #print(voc_dict)
    new_sentences_ids = []
    new_sentences_vects = []
    j = 0
    newsentences = clean_data(sentences)
    for sentence in newsentences:
        j+=1
        if j % 5000 == 0:
            print ('sentence',str(j))
        sentence_ids = []
        sentence_vects = []
        if option == 'nltk':
            #sentence = sentence.decode('utf8', 'ignore')
            # print('sentence', sentence)
            wrdlst = tokenize(sentence)
            word_list = remove_stopwords(wrdlst)
            # print('word_list', word_list)
        elif option == 'simple':
            word_list = sentence.split(" ")
        #print(word_list)
        for word in word_list:
            word = word.decode("utf-8")
            if word.lower() in voc_dict: # Only add word if in dictionary                
                word_index = voc_dict[word.lower()]
                #print(word_index)
                #print(embedding_matrix[word_index])
                sentence_ids.append(word_index)
                sentence_vects.append(embedding_matrix[word_index])
                
        new_sentences_ids.append(sentence_ids)
        #print ("added", j)
        #print(sentence_vects)
        new_sentences_vects.append(sentence_vects)
    #print(new_sentences_vects)
    return new_sentences_ids, new_sentences_vects

def tokenize(sequence):
    #nltk.download('punkt')
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    tokens = [token.replace("``", '"').replace("''", '"') for token in nltk.word_tokenize(sequence)]
    #tokens =  [normalize_word(t).replace("``", '"').replace("''", '"') for t in nltk.word_tokenize(sequence)]
    # return tokens
    return map(lambda x:x.encode('utf8', errors = 'ignore'), tokens)

# ---------- Averaging vectors for headline and truncated body ---------

def avg_trunc(sentences_vects):
    s_vects_np = []
    for sentence in sentences_vects:
        s_vects_np.append(np.array(sentence))
    s_vects_avg = []
    for sentence in s_vects_np:
        s_vects_avg.append(np.mean(sentence,axis=0))
    return s_vects_avg

def concatConvert_np(h_list, b_list):
    '''
    1. Concatenate headlines and bodies
    2. Convert list data to numpy zero padded data
    3. Also outputs sequences lengths as np vector
    '''
    
    # Concatenate
    n_sentences = len(h_list)
    h_b_list = []
    seqlen = []
    for i in range(n_sentences):
        h_b_list.append(h_list[i] + b_list[i])
        seqlen.append(len(h_b_list[i]))
        
    max_len = max(seqlen)
    
    # Convert to numpy with zero padding. No truncating
    h_b_np = np.zeros((n_sentences, max_len))
    for i in range(n_sentences):
        h_b_np[i,:seqlen[i]] = h_b_list[i]
    
    return h_b_list, h_b_np, np.array(seqlen)

def distinctConvert_np(h_list, b_list):
    '''
    1. Convert list data to numpy zero padded data, 2 distinct matrices for headlines and bodies 
    2. Also outputs sequences lengths as np vector
    '''
    # Compute sequences lengths
    n_sentences = len(h_list)
    h_seqlen = []
    b_seqlen = []
    for i in range(n_sentences):
        h_seqlen.append(len(h_list[i]))
        b_seqlen.append(len(b_list[i]))
        
    h_max_len = max(h_seqlen)
    b_max_len = max(b_seqlen)
    
    # Convert to numpy
    h_np = np.zeros((n_sentences, h_max_len))
    b_np = np.zeros((n_sentences, b_max_len))
    for i in range(n_sentences):
        h_np[i,:h_seqlen[i]] = h_list[i]
        b_np[i,:b_seqlen[i]] = b_list[i]
        
    return h_np, np.array(h_seqlen), b_np, np.array(b_seqlen)

#------for nn_test--------#

def get_BOW_data(config, reload = None, save_data = None):
    ## Random seed
    np.random.seed(1)

    # Define path
    cwd = os.getcwd()
    #filename_embeddings = cwd + '/../../glove/glove.6B.50d.txt'
    filename_embeddings = base_path + '/glove/glove.6B.50d.txt'
    # GloVe embeddings
    #word_to_index, index_to_embedding = load_embedding_from_disks(filename_embeddings, with_indexes=True)
    vocab,embd = loadGloVe(filename_embeddings)
    #vocab_size, embedding_dim = index_to_embedding.shape
    #embd = list(np.array(index_to_embedding[idx], dtype=int))
    vocab_size = len(vocab)
    embedding_dim = len(embd[0])
    embedding = np.asarray(embd)

    if reload:
        # Get vocab dict
        voc_dict = build_vocDict(vocab)
        
        # Read and process data
        h, b, y = read_data() #read_data(cwd + '/../../') # headline / bodies/ labels
        # h_ids, _ = words2ids_vects(h, voc_dict, embd)
        # b_ids, _ = words2ids_vects(b, voc_dict, embd)
        h_ids = words2ids(h, voc_dict)
        b_ids = words2ids(b, voc_dict)
        
        # zero padded np matrices for headlines and bodies; seq. lengths as np vector
        h, h_len, b, b_len = distinctConvert_np(h_ids, b_ids)

        # Find and delete empty headings/bodies
        ind_empty = []
        for i in range(np.shape(h)[0]):
            if ((h_len[i] == 0) or (b_len[i] == 0)):
                ind_empty.append(i)
                # print(i)
        #print('Empty sequences: ', ind_empty)
        if (len(ind_empty) > 0):
            y = np.delete(y, ind_empty)
            h = np.delete(h, ind_empty, 0)
            b = np.delete(b, ind_empty, 0)
            h_len = np.delete(h_len, ind_empty)
            b_len = np.delete(b_len, ind_empty)

        if save_data:
            # Attention: Bodies CSV is HUGE (800mb)
            assert(False) ## Do you REALLY want to do this? Consider saving it in a txt file instead.
            # Write
            y_pd = pd.DataFrame(y) 
            h_pd = pd.DataFrame(h) 
            b_pd = pd.DataFrame(b) 
            h_len_pd = pd.DataFrame(h_len) 
            b_len_pd = pd.DataFrame(b_len) 
            y_pd.to_csv('saved_data/y_noempty.csv', index = False, header = False)
            h_pd.to_csv('saved_data/h_noempty.csv', index = False, header = False)
            b_pd.to_csv('saved_data/b_noempty.csv', index = False, header = False)
            h_len_pd.to_csv('saved_data/h_len_noempty.csv', index = False, header = False)
            b_len_pd.to_csv('saved_data/b_len_noempty.csv', index = False, header = False)
            # assert(False)

    if not reload:
        # Load 
        # Attention: Bodies CSV is HUGE (800mb)
        print("Loading Data")
        y = np.asarray(pd.read_csv('saved_data/y_noempty.csv', header = None))
        print("loaded labels")
        h = np.asarray(pd.read_csv('saved_data/h_noempty.csv', header = None))
        print("loaded headings")
        b = np.asarray(pd.read_csv('saved_data/b_noempty.csv', header = None))
        print("loaded headings")
        h_len = np.asarray(pd.read_csv('saved_data/h_len_noempty.csv', header = None))
        b_len = np.asarray(pd.read_csv('saved_data/b_len_noempty.csv', header = None))
        print("loaded lengths")
        # assert(False)

    # Modify the config
    config.embed_size = embedding_dim
    config.pretrained_embeddings = embedding
    config.vocab_size = vocab_size    
    # finish
    return config, y, h, b, h_len, b_len

## Updated BY Manisha
def save_data_pickle(outfilename, 
                    embedding_type = 'twitter.27B.50d',
                    parserOption = 'nltk'):
    cwd = os.getcwd()
    if embedding_type == 'twitter.27B.50d':
        #filename_embeddings = cwd + '/../../glove/glove.twitter.27B.50d.txt'
        filename_embeddings = base_path + '/glove/glove.twitter.27B.50d.txt'
    else: 
        #filename_embeddings = cwd + '/../../glove/glove.6B.50d.txt'
        filename_embeddings = base_path + '/glove/glove.6B.50d.txt'

    # filename_embeddings = cwd + filename_embeddings

    # GloVe embeddings
    vocab, embd = loadGloVe(filename_embeddings)
    #vocab_size = len(vocab)
    #embedding_dim = len(embd[0])
    #embedding = np.asarray(embd)
    #embedding = np.asarray(embd, dtype = object)

    # Get vocab dict
    voc_dict = build_vocDict(vocab)
    
    # Read and process data
    h, b, y = read_data() #read_data(cwd + '/../../') # headline / bodies/ labels
    
    h_ids, h_vects = words2ids_vects(h, voc_dict, embd, parserOption)
    b_ids, b_vects = words2ids_vects(b, voc_dict, embd, parserOption)
    #print(h_vects)
    # Concatenated headline_bodies zero padded np matrices; seq. lengths as np vector
    h_b_ids, h_b_np, seqlen = concatConvert_np(h_ids, b_ids)
    h_np, h_seqlen, b_np, b_seqlen = distinctConvert_np(h_ids, b_ids)

    data_dict = {'h_ids':h_ids, 'b_ids':b_ids, 'y':y}
    with open(outfilename, 'wb') as fp:
        pickle.dump(data_dict, fp) #pickle.dump(your_object, your_file, protocol=2) #portocol added by manisha for GPU python 2.7
    return vocab, embd

## Updated BY Manisha
def get_data(config, 
            filename_embeddings = '/glove/glove.twitter.27B.50d.txt',
            pickle_path = '/glove/twitter50d_h_ids_b_ids_pickle.p',
            concat = True):
    # np.random.seed(41)
    # Base path
    #cwd = os.getcwd()
    load_path = base_path + pickle_path
    #read_data()
    #vocab, embd = save_data_pickle(load_path) #By Manisha - Comment this ones its loaded
    
    # filename_embeddings = cwd + '/../../glove/glove.6B.50d.txt'

    filename_embeddings = base_path + filename_embeddings
    
    # GloVe embeddings
    vocab, embd = loadGloVe(filename_embeddings)
    #print(vocab)
    #print(embd)
    vocab_size = len(vocab)
    embedding_dim = len(embd[0])
    #print(embd.dtype)
    #embedding = np.asarray(embd, dtype = np.float64)
    embedding = np.asarray(embd)
    #print(vocab)
    #print(embd)
    #print(embedding)

    # Get vocab dict
    #voc_dict = build_vocDict(vocab)
    #print(voc_dict)
    # Read and process data
    #h, b, y = read_data() # headline / bodies/ labels
    
    print('Loading Pickle')
    #load_path = pickle_path
    with open (load_path, 'rb') as fp:
        data_dict = pickle.load(fp)
    #print(data_dict)
    h_ids = data_dict['h_ids']
    b_ids = data_dict['b_ids']
    y = data_dict['y']
    #print(h_ids)
    #print(b_ids)
    #print(y)
    print('finished loading Pickle')
    
    # Concatenated headline_bodies zero padded np matrices; seq. lengths as np vector
    # h_b_ids, h_b_np, seqlen = concatConvert_np(h_ids, b_ids)
    # h_np, h_seqlen, b_np, b_seqlen = distinctConvert_np(h_ids, b_ids)

    if concat:
        h_b_ids, h_b_np, seqlen = concatConvert_np(h_ids, b_ids)
        output_dict = {'y':y,
                       'h_b_np':h_b_np, 
                       'seqlen':seqlen}
    else:
        h_np, h_seqlen, b_np, b_seqlen = distinctConvert_np(h_ids, b_ids)
        # Find and delete empty
        ind_empty = []
        for i in range(np.shape(h_np)[0]):
            if ((h_seqlen[i] == 0) or (b_seqlen[i] == 0)):
                ind_empty.append(i)
        #print('Empty sequences: ', ind_empty)
        if (len(ind_empty) > 0):
            y = np.delete(y, ind_empty)
            h_np = np.delete(h_np, ind_empty, 0)
            b_np = np.delete(b_np, ind_empty, 0)
            h_seqlen = np.delete(h_seqlen, ind_empty)
            b_seqlen = np.delete(b_seqlen, ind_empty)
        output_dict = {'y':y,
                       'h_np':h_np, 
                       'b_np':b_np, 
                       'h_seqlen':h_seqlen,
                       'b_seqlen':b_seqlen}
    
    #Have to check this
    config.embed_size = embedding_dim
    config.pretrained_embeddings = embedding
    config.vocab_size = vocab_size
    return config, output_dict

'''if __name__ == '__main__':
     pickle_path = '/glove/twitter50d_h_ids_b_ids_pickle.p'
     load_path = base_path + pickle_path
    # config, data_dict = get_data(1028, 
            #filename_embeddings = '/glove/glove.twitter.27B.50d.txt',
           # pickle_path = '/glove/twitter50d_h_ids_b_ids_pickle.p',
            #concat = False)
     vocab, embd = save_data_pickle(load_path)
     # ========== YOUR OWN EMBEDDING MATRIX PATH HERE =========
     #filename_embeddings = '/Users/spfohl/Documents/CS_224n/project/altfactcheckers/code/stephen_scratch/glove.6B/glove.6B.50d.txt'
     filename_embeddings = '/Users/Monu/NLP/Stance/code/glove/glove.6B.50d.txt'
     # Glove
     vocab,embd = loadGloVe(filename_embeddings)
     vocab_size = len(vocab)
     embedding_dim = len(embd[0])
     embedding = np.asarray(embd)
     #print(vocab_size)
     print(embedding[0:5, :])
     # Dictionary
     voc_dict = build_vocDict(vocab)
    
     # Read and process data
     h, b, y = read_data() # headline / bodies/ labels
     h_ids, h_vects = words2ids_vects(h, voc_dict, embd)
     b_ids, b_vects = words2ids_vects(b, voc_dict, embd)
    
     # Concatenated headline_bodies zero padded np matrices; seq. lengths as np vector
     h_b_ids, h_b_np, seqlen = concatConvert_np(h_ids, b_ids)
    
     # Distinct headline / bodies zero padded np matrices; seq lengths as np vectors
     h_np, h_seqlen, b_np, b_seqlen = distinctConvert_np(h_ids, b_ids)'''