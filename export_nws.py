#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 10:55:19 2020

@author: Amirhossein Farzam
"""



import os
import sys
import json
import networkx as nx
import warnings
import collections


path = os.getcwd() + "/"



#%% ----------------- classes ----------------------

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
        


#%% ----------------  misc helpers -------------------


#
# Requires: 
#
# Returns: prints a progress bar
#
def progressBar(value, endvalue, optional_message="", bar_length=50):

        percent = float(value) / endvalue
        arrow = '.' * int(round(percent * bar_length)-1) + '>'
        spaces = ' ' * (bar_length - len(arrow))

        sys.stdout.write("\r {0} Percent: [{1}] {2}%         ".format(optional_message, \
                                                             arrow + spaces, \
                                                             int(round(percent * 100))))
        sys.stdout.flush()
        
        
        
#%% --------------- helper functions ----------------------
        

#
# Requires:
#   [[clstr number (int), 
#     uid1 (str),
#     CAP of uid1 (float),
#     [[
#      ]]
#    ],
#    ...]
# Modifies: -
# Returns: the time each node entered the network in the following format:
#       {uid: tstamp,
#        ... }
#
def get_node_t0(clstr_uid_bom_tt, 
                retweet=False,
                save=False, words=[]):
    
    node_ts = collections.defaultdict(list)
    dump = [node_ts[str(uid)].append(time_txt[0]) \
            for (clstr, uid, bom, tt) in clstr_uid_bom_tt \
                for time_txt in tt]
        
    if (retweet): # those retweeted from might never appear in the nodes
        dump = [node_ts[str(uid0)].append(tstamp) \
                for (clstr, uid1, bom1, tt) in clstr_uid_bom_tt \
                    for (tstamp, uid0, txt) in tt]
    del dump
    
    node_t0s = {uid: min(node_ts[uid]) for uid in node_ts}
        
    return node_t0s
        
    
    
#
# Requires:
#   [[clstr number (int), 
#     uid1 (str),
#     CAP of uid1 (float),
#     [[
#      ]]
#    ],
#    ...]
# Modifies: -
# Returns the time of creation of each edge in the following format:
#       {(uid1 (str), uid2 (str)): tstamp, ...}
#       both uid1 and uid2 are str
#       uid2 is the uid of the account that tweeted the original tweet
#       uid1 is the uid of the account that tweeted the original tweet
#
def get_edge_t0(clstr_uid_bom_tt, 
                save=False, words=[]):
    
    if (len(clstr_uid_bom_tt)==0):
        return []
    
    # Note for retweets, clstr_uid_bom_tt[i][3][j] 
    #   should have [timestamp, user id of the person tweeted, tweet text],
    #   while for tweets, it should only have [timestamp, tweet text] 
    if (len(clstr_uid_bom_tt[0][3][0]) < 3): 
        ValueError("\n Edge timestamp only works on retweet network!" \
                   + "\n get_edge_t0 cannot work on [word]_clstr_uid_bom_tweets* files!" \
                       + "\n Please input the content of [word]_clstr_uid_bom_retweets_louv instead!\n")
            
    edges_ts = collections.defaultdict(list)
    dump = [edges_ts[(str(uid1), str(uid2))].append(tstamp) \
            for (clstr, uid1, bom1, tt) in clstr_uid_bom_tt \
                for (tstamp, uid2, txt) in tt]
    del dump
    
    edges_t0s = {e: min(edges_ts[e]) for e in edges_ts}
    
    
    return edges_t0s
    
    
    


#
# Alternative 2-community community detection (first cut of laplacian spectrum)
#   i.e. based on positive or negative sign of entries of leading e-vec of the laplacian
#
def comm_det_1stCut(nw):
    import numpy as np
    from scipy import linalg
    
    G = nw.to_undirected()
    nodelist = list(G.nodes())
    adj = nx.linalg.graphmatrix.adjacency_matrix(G, nodelist=nodelist)
    N = adj.get_shape()[0]
    
    # the function below gets leading eval mu1 and the corresponding evec w1
    mu1, w1 = linalg.eigh(a=adj.todense(), subset_by_index=[N-1, N-1], eigvals_only=False)
    mu1, w1 = mu1[0], w1.flatten()
    
    clstr1 = [nodelist[i] for i in np.where(w1>0)[0]]
    clstr2 = [nodelist[i] for i in np.where(w1<0)[0]]
    
    
    # adding those with value 0 to clstrs randomly
    val0_in_w1 = [nodelist[i] for i in np.where(w1==0)[0]]
    import random as rnd
    rnd.seed(10101)
    rnd.shuffle(val0_in_w1)
    
    clstr1 += val0_in_w1[:int(len(val0_in_w1)//2)]
    clstr2 += val0_in_w1[int(len(val0_in_w1)//2):]
    
    
    nodes_clusters = {v:'+' for v in clstr1}
    nodes_clusters.update({v:'-' for v in clstr2})
    
    
    return nodes_clusters
            

    

#%% --------------- main functions ---------------------- 


#     
# Returns: nw_undir
#          nw_dir (nx.DiGraph()) : has a directed edge from the user who retweets 
#                                   to the user whose tweet is retweeted
#
#       Note: The direction of the edges are : (uid1, uid2)
#               where uid1 (tail) retweeted uid2 (head), i.e. uid1 --> uid2
#               , i.e. the direction is the oposite of the direction of "information flow" or "tweet propogation"
def get_retweet_nw(words, 
                   relabel=False, attribute=False, export_graphml=False, export_pkl=False):
    
    fname = path + "../data/retweets/" + '_'.join(words) \
                 + "/" + '_'.join(words) + "_retweets_network_edgelist.json"
    with open(fname, 'r') as fin:
        edge_list = json.load(fin)
    edges = [(str(v), str(u)) for v in edge_list for u in edge_list[v]]
    
    nw_undir = nx.from_edgelist(edges)
    nw_dir = nx.DiGraph(edges) # makes a directed edge from the user who retweets to the user whose tweet is retweeted
    
    fname = path + "../data/uname_uids.txt"
    with open(fname, 'r') as fin:
        lines = fin.readlines()

    
    if (relabel):
        uid_uname_dict = dict()
        for line in lines:
            uname, uid = line[:-1].split('\t')
            if uid in nw_undir.nodes():
                uid_uname_dict[str(uid)] = uname
        
        uid_uid = {str(uid): str(uid) for uid in uid_uname_dict}
        for nw in [nw_undir, nw_dir]:
            nx.set_node_attributes(nw, values=uid_uid, name='uid') # preserving uid data
            nx.relabel.relabel_nodes(nw_undir, uid_uname_dict, copy=False)
    
    
    if (attribute):
        if (not relabel):
            uid_uname_dict = dict()
            for line in lines:
                uname, uid = line[:-1].split('\t')
                if uid in nw_undir.nodes():
                    uid_uname_dict[str(uid)] = uname
                
        fname = path + "../data/retweets/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_clstr_uid_bom_retweets_louv.json"
        with open(fname, 'r') as fin:
            clstr_uid_bom_retweets = json.load(fin)
            
        clstr_frnd = False
        fname = path + "../data/" + '_'.join(words) \
                         + "/" + '_'.join(words) + "_clstr_uid_bom_tweets_louv.json"
        try:
            with open(fname, 'r') as fin:
                clstr_uid_bom_frnd = json.load(fin)
            clstr_frnd = True
        except:
            warnings.warn("\n " + fname + " could not be loaded ! \n")
            
        import random as rnd
        uid_tweet = {str(uid): rnd.choice([tweet for (tstamp, uid0, tweet) in retweets]) \
                     for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
        uid_tweet.update({str(uid0): uid_tweet[str(uid)] \
                          for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets \
                          for (tstamp, uid0, tweet) in retweets})

        uid_cap = {str(uid): cap \
                   for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
        if (clstr_frnd):
            uid_cap.update({str(uid): cap \
                            for (clstr, uid, cap, tt) in clstr_uid_bom_frnd})

        uid_clstr = {str(uid): clstr \
                     for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
        uid_clstr.update({str(uid0): uid_clstr[str(uid)] \
                          for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets \
                          for (tstamp, uid0, tweet) in retweets})
        if (clstr_frnd):
            uid_clstr_frnd = {str(uid): clstr \
                              for (clstr, uid, cap, tts) in clstr_uid_bom_frnd}
                
        uid_t0 = get_node_t0(clstr_uid_bom_retweets, retweet=True)
        edge_t0 = get_edge_t0(clstr_uid_bom_retweets)
        
        
        for nw in [nw_undir, nw_dir]:
            if (not relabel):
                nx.set_node_attributes(nw, values=uid_uname_dict, name='screen_name')
            nx.set_node_attributes(nw, values=uid_tweet, name='tweet')
            nx.set_node_attributes(nw, values=uid_cap, name='cap')
            nx.set_node_attributes(nw, values=uid_clstr, name='clstr')  
            if (clstr_frnd):
                nx.set_node_attributes(nw, values=uid_clstr_frnd, name='clstr_frnd')
            nx.set_node_attributes(nw, values=uid_t0, name='t0')
            nx.set_edge_attributes(nw, values=edge_t0, name='t0')
            
    
    if (export_graphml):
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_retweets_nw_undir.graphml"
        nx.readwrite.graphml.write_graphml(nw_undir, fname)
        print("\n graphml for undir is saved in " + fname + "\n")
        
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_retweets_nw_dir.graphml"
        nx.readwrite.graphml.write_graphml(nw_dir, fname)
        print("\n graphml for dir is saved in " + fname + "\n")
        
        
    if (export_pkl):
        import pickle
        
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_retweets_nw_undir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_undir, fout, pickle.HIGHEST_PROTOCOL)    
        print("\n pkl for undir is saved in " + fname + "\n")
            
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_retweets_nw_dir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_dir, fout, pickle.HIGHEST_PROTOCOL)
        print("\n pkl for dir is saved in " + fname + "\n")
        
    
    return Namespace(undirected=nw_undir, directed=nw_undir)



    



#%%
    

#     
# Returns: nw_undir:  friendship network
#          nw_dir (nx.DiGraph()) : friendship network
#
def get_frnd_nw(words, 
                   relabel=False, attribute=False, export_graphml=False, export_pkl=False):
    
    import pickle
    word = '_'.join(words)
    fname = path + "../data/" + word + "/nw_dir_" + word + ".pkl"
    with open(fname, 'rb') as fin:
        nw_dir = pickle.load(fin)

    
    fname = path + "../data/uname_uids.txt"
    with open(fname, 'r') as fin:
        lines = fin.readlines()

    
    nws = [nw_dir]#, nw_undir]
    
    for nw in nws:
        nx.relabel.relabel_nodes(nw, {uid:str(uid) for uid in nw.nodes()}, copy=False)
    
    if (relabel):
        uid_uname_dict = dict()
        for line in lines:
            uname, uid = line[:-1].split('\t')
            if uid in nw_dir.nodes():
                uid_uname_dict[str(uid)] = uname
        
        uid_uid = {str(uid): str(uid) for uid in uid_uname_dict}
        for nw in nws:
            nx.set_node_attributes(nw, values=uid_uid, name='uid') # preserving uid data
            nx.relabel.relabel_nodes(nw, uid_uname_dict, copy=False)
    
    
    if (attribute):
        if (not relabel):
            uid_uname_dict = dict()
            for line in lines:
                uname, uid = line[:-1].split('\t')
                if uid in nw_dir.nodes():
                    uid_uname_dict[str(uid)] = uname
                
        fname = path + "../data/retweets/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_clstr_uid_bom_retweets_louv.json"
        with open(fname, 'r') as fin:
            clstr_uid_bom_retweets = json.load(fin)
            
        fname = path + "../data/" + '_'.join(words) \
                         + "/" + '_'.join(words) + "_clstr_uid_bom_tweets_louv.json"
        with open(fname, 'r') as fin:
            clstr_uid_bom_frnd = json.load(fin)
            
        import random as rnd
        uid_tweet = {str(uid): rnd.choice([tweet for (tstamp, tweet) in tts]) \
                     for (clstr, uid, cap, tts) in clstr_uid_bom_frnd}
        
        uid_cap = {str(uid): cap \
                   for (clstr, uid, cap, tts) in clstr_uid_bom_frnd}
        uid_clstr_rt = {str(uid): clstr \
                        for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
        uid_clstr_rt.update({str(uid0): uid_clstr_rt[str(uid)] \
                              for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets \
                              for (tstamp, uid0, tweet) in retweets})
        uid_clstr_frnd = {str(uid): clstr \
                          for (clstr, uid, cap, tts) in clstr_uid_bom_frnd}
        uid_t0 = get_node_t0(clstr_uid_bom_frnd, retweet=False)
        
        for nw in nws:
            nodes_list = list(set(list(nw.nodes())))
            if (not relabel):
                nx.set_node_attributes(nw, values=uid_uname_dict, name='screen_name')
                
            uid_tweet = {uid: uid_tweet[uid] for uid in uid_tweet
                         if uid in nodes_list}
            nx.set_node_attributes(nw, values=uid_tweet, name='tweet')
            
            uid_cap = {uid: uid_cap[uid] for uid in uid_cap
                       if uid in nodes_list}
            nx.set_node_attributes(nw, values=uid_cap, name='cap')
            
            uid_clstr_rt = {uid: uid_clstr_rt[uid] for uid in uid_clstr_rt
                       if uid in nodes_list}
            nx.set_node_attributes(nw, values=uid_clstr_rt, name='clstr_rt') 
            
            uid_clstr_frnd = {uid: uid_clstr_frnd[uid] for uid in uid_clstr_frnd
                       if uid in nodes_list}
            nx.set_node_attributes(nw, values=uid_clstr_frnd, name='clstr_frnd')  
            
            uid_t0 = {uid: uid_t0[uid] for uid in uid_t0
                       if uid in nodes_list}
            nx.set_node_attributes(nw, values=uid_t0, name='t0')
            
            
    #%
    if (export_graphml):
        nw_undir = nw_dir.to_undirected()
        fname = path + "../data/frnd_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_frnd_nw_undir.graphml"
        nx.readwrite.graphml.write_graphml(nw_undir, fname)
        print("\n graphml for undir is saved in " + fname + "\n")
        
        fname = path + "../data/frnd_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_frnd_nw_dir.graphml"
        nx.readwrite.graphml.write_graphml(nw_dir, fname)
        print("\n graphml for dir is saved in " + fname + "\n")
        
        
    if (export_pkl):
        nw_undir = nw_dir.to_undirected()
        import pickle
        fname = path + "../data/frnd_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_frnd_nw_undir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_undir, fout, pickle.HIGHEST_PROTOCOL)    
        print("\n pkl for undir is saved in " + fname + "\n")
            
        fname = path + "../data/frnd_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_frnd_nw_dir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_dir, fout, pickle.HIGHEST_PROTOCOL)
        print("\n pkl for dir is saved in " + fname + "\n")
        
    
    return Namespace(directed=nw_dir)#, undirected=nw_undir)






#%%  ------------- Add missing attributes ----------------------------

# if retweet is false, it is friendship network
def only_add_tstamps(words, 
                     retweet=True,
                     export_graphml=False, export_pkl=False):
    nw_type="_frnd"
    if (retweet):
        nw_type="_retweets"
    
    try:
        import pickle
        
        """
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.pkl"
        with open(fname, 'rb') as fin:
            nw_undir = pickle.load(fin)    
        print("\n pkl for undir is loaded from " + fname + "\n")
        """
            
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.pkl"
        with open(fname, 'rb') as fin:
            nw_dir = pickle.load(fin)
        print("\n pkl for dir is loaded from " + fname + "\n")
        
        
    except:
        try:
            """
            fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.graphml"
            nw_undir = nx.readwrite.graphml.read_graphml(fname)
            print("\n graphml for undir is loaded from " + fname + "\n")
            """
            
            fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                         + "_networks/" + '_'.join(words) \
                         + "/" + '_'.join(words) + nw_type + "_nw_dir.graphml"
            nw_dir = nx.readwrite.graphml.read_graphml(fname)
            print("\n graphml for dir is loaded from " + fname + "\n")
        
        except:
            raise ValueError("\n!!Couldn't load pkl or graphml network!!\n")
            
            
    #%
    if (retweet):
        fname = path + "../data/retweets/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_clstr_uid_bom_retweets_louv.json"
    else:
        fname = path + "../data/" + '_'.join(words) \
                         + "/" + '_'.join(words) + "_clstr_uid_bom_tweets_louv.json"
    with open(fname, 'r') as fin:
        clstr_uid_bom_tt = json.load(fin)
        
    uid_t0 = get_node_t0(clstr_uid_bom_tt, retweet=retweet)
    if (retweet):
        edge_t0 = get_edge_t0(clstr_uid_bom_tt)
    
    
    nw_undir = nw_dir.to_undirected() # get the undirected version
    
    
    for nw in [nw_dir]:
        nx.set_node_attributes(nw, values=uid_t0, name='t0')
        if (retweet):
            nx.set_edge_attributes(nw, values=edge_t0, name='t0')
            
            # set edge attribute for undirected network to minimum of two possible directed versions
            undir_edge_t0 = {e: 0 for e in nw_undir.edges()}
            for (v, u) in nw_undir.edges():
                if (v, u) in edge_t0:
                    undir_edge_t0[(v, u)] = edge_t0[(v, u)]
                if (u, v) in edge_t0:
                    undir_edge_t0[(v, u)] = min(undir_edge_t0[(v, u)], edge_t0[(u, v)])
                    
            nx.set_edge_attributes(nw_undir, values=undir_edge_t0, name='t0')
        
        
        
    if (export_graphml):
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.graphml"
        nx.readwrite.graphml.write_graphml(nw_undir, fname)
        print("\n graphml for undir is saved in " + fname + "\n")
        
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.graphml"
        nx.readwrite.graphml.write_graphml(nw_dir, fname)
        print("\n graphml for dir is saved in " + fname + "\n")
        
        
    if (export_pkl):
        import pickle
        
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_undir, fout, pickle.HIGHEST_PROTOCOL)    
        print("\n pkl for undir is saved in " + fname + "\n")
            
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_dir, fout, pickle.HIGHEST_PROTOCOL)
        print("\n pkl for dir is saved in " + fname + "\n")
        
    
    return Namespace(directed=nw_dir, undirected=nw_undir)






# if retweet is false, it is friendship network
def only_add_missing_retweet_caps(words, 
                                 export_graphml=False, export_pkl=False):
    
    nw_type="_retweets"
    
    try:
        import pickle
        
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.pkl"
        with open(fname, 'rb') as fin:
            nw_undir = pickle.load(fin)    
        print("\n pkl for undir is loaded from " + fname + "\n")
            
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.pkl"
        with open(fname, 'rb') as fin:
            nw_dir = pickle.load(fin)
        print("\n pkl for dir is loaded from " + fname + "\n")
        
        
    except:
        try:
            fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.graphml"
            nw_undir = nx.readwrite.graphml.read_graphml(fname)
            print("\n graphml for undir is loaded from " + fname + "\n")
            
            fname = path + "../data/rt_networks/" + '_'.join(words) \
                         + "/" + '_'.join(words) + nw_type + "_nw_dir.graphml"
            nw_dir = nx.readwrite.graphml.read_graphml(fname)
            print("\n graphml for dir is loaded from " + fname + "\n")
        
        except:
            raise ValueError("\n!!Couldn't load pkl or graphml network!!\n")
            
    
    
    fname = path + "../data/retweets/" + '_'.join(words) \
                 + "/" + '_'.join(words) + "_clstr_uid_bom_retweets_louv.json"
    with open(fname, 'r') as fin:
        clstr_uid_bom_retweets = json.load(fin)
        
    fname = path + "../data/" + '_'.join(words) \
                     + "/" + '_'.join(words) + "_clstr_uid_bom_tweets_louv.json"
                     
    with open(fname, 'r') as fin:
        clstr_uid_bom_frnd = json.load(fin)
        
    uid_cap = {str(uid): cap \
               for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
    uid_cap.update({str(uid): cap \
                    for (clstr, uid, cap, tt) in clstr_uid_bom_frnd})

    for nw in [nw_undir, nw_dir]:
        nx.set_node_attributes(nw, values=uid_cap, name='cap')
    
        
    if (export_graphml):
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.graphml"
        nx.readwrite.graphml.write_graphml(nw_undir, fname)
        print("\n graphml for undir is saved in " + fname + "\n")
        
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.graphml"
        nx.readwrite.graphml.write_graphml(nw_dir, fname)
        print("\n graphml for dir is saved in " + fname + "\n")
        
        
    if (export_pkl):
        import pickle
        
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_undir, fout, pickle.HIGHEST_PROTOCOL)    
        print("\n pkl for undir is saved in " + fname + "\n")
            
        fname = path + "../data/rt_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_dir, fout, pickle.HIGHEST_PROTOCOL)
        print("\n pkl for dir is saved in " + fname + "\n")
        
    
    return Namespace(undirected=nw_undir, directed=nw_dir)






# if retweet is false, it is friendship network
def only_add_1stCut(words, 
                    retweet=True,
                    export_graphml=False, export_pkl=False):
    nw_type="_frnd"
    if (retweet):
        nw_type="_retweets"
    
    try:
        import pickle
        
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.pkl"
        with open(fname, 'rb') as fin:
            nw_dir = pickle.load(fin)
        print("\n pkl for dir is loaded from " + fname + "\n")
        
        
    except:
        try:
            
            fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                         + "_networks/" + '_'.join(words) \
                         + "/" + '_'.join(words) + nw_type + "_nw_dir.graphml"
            nw_dir = nx.readwrite.graphml.read_graphml(fname)
            print("\n graphml for dir is loaded from " + fname + "\n")
        
        except:
            raise ValueError("\n!!Couldn't load pkl or graphml network!!\n")
            
            
    
    nodes_clusters = comm_det_1stCut(nw_dir)
    
    
    nx.set_node_attributes(nw_dir, values=nodes_clusters, name='clstr_1stCut')
    
    nw_undir = nw_dir.to_undirected()
        
    
    if (export_graphml):
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.graphml"
        nx.readwrite.graphml.write_graphml(nw_undir, fname)
        print("\n graphml for undir is saved in " + fname + "\n")
        
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.graphml"
        nx.readwrite.graphml.write_graphml(nw_dir, fname)
        print("\n graphml for dir is saved in " + fname + "\n")
        
        
    if (export_pkl):
        import pickle
        
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_undir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_undir, fout, pickle.HIGHEST_PROTOCOL)    
        print("\n pkl for undir is saved in " + fname + "\n")
            
        fname = path + "../data/" + "rt"*retweet + "frnd"*(1-retweet) \
                     + "_networks/" + '_'.join(words) \
                     + "/" + '_'.join(words) + nw_type + "_nw_dir.pkl"
        with open(fname, 'wb') as fout:
            pickle.dump(nw_dir, fout, pickle.HIGHEST_PROTOCOL)
        print("\n pkl for dir is saved in " + fname + "\n")
        
    
    return Namespace(directed=nw_dir, undirected=nw_undir)





#%%


if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser()
    

    parser.add_argument('-w', '--words', nargs='+', type=str, required=True,
                        help='(str) : Words to analyze')
    parser.add_argument('-p', '--export_pkl', nargs='?', const=1, type=bool, required=False, default=True,
                        help='(bool) : export pkl file - default is True')
    parser.add_argument('-g', '--export_gml', nargs='?', const=1, type=bool, required=False, default=False,
                        help='(bool) : export gml file - default is False')
    parser.add_argument('-l', '--relabel', nargs='?', const=1, type=bool, required=False, default=False,
                        help='(bool) : relabels the nodes with screen_name and adds uid as an attribute - default is False')
    parser.add_argument('-a', '--attribute', nargs='?', const=1, type=bool, required=False, default=False,
                        help='(bool) : adds tweet, screen_name, cap, and clstr attributes - default is False')
    parser.add_argument('-r', '--retweet', nargs='?', const=1, type=bool, required=False, default=False,
                        help='(bool) : exports retweet network - default is False')
    parser.add_argument('-f', '--friends', nargs='?', const=1, type=bool, required=False, default=False,
                        help='(bool) : exports friendsgip network - default is False')
    parser.add_argument('-m', '--missing', nargs='?', const=1, type=bool, required=False, default=False,
                        help='(bool) : just add the missing attributes - default is False')
    
    
    
    
    args = parser.parse_args()
    print("\n\n export retweet network ... " \
           + "\n  for the following arguments:\n   " \
           + str(args) + "\n")
    
    import datetime
    print("\n\n Start time : " + str(datetime.datetime.now()) + " EST \n\n")
    
    if (args.retweet):
        if (args.missing):
            nws = only_add_missing_retweet_caps(words=args.words, 
                                                export_graphml=args.export_gml, 
                                                export_pkl=args.export_pkl)
            nws = only_add_tstamps(words=args.words,
                                   retweet=True,
                                   export_graphml=args.export_gml, 
                                   export_pkl=args.export_pkl)
        else:
            get_retweet_nw(words=args.words, 
                           relabel=args.relabel, 
                           attribute=args.attribute, 
                           export_graphml=args.export_gml, 
                           export_pkl=args.export_pkl)
    if (args.friends):
        if (args.missing):
            nws = only_add_missing_retweet_caps(words=args.words, 
                                                export_graphml=args.export_gml, 
                                                export_pkl=args.export_pkl)
            nws = only_add_tstamps(words=args.words,
                                   retweet=False,
                                   export_graphml=args.export_gml, 
                                   export_pkl=args.export_pkl)
        else:
            get_frnd_nw(words=args.words, 
                       relabel=args.relabel, 
                       attribute=args.attribute, 
                       export_graphml=args.export_gml, 
                       export_pkl=args.export_pkl)
    
        
    