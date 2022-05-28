#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 20:26:58 2020

Description: functions for preparing the data, including network etc.

@author: Amirhossein Farzam
"""





import os
import json
import networkx as nx
import pickle
import collections
import operator
import numpy as np

import sqlite3 as sql

path = os.getcwd() + "/"



#%% ----------------- classes ----------------------

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
        
        
#%% --------------- small functions, loading data ----------------------


def get_uids(words):
    uids = []
    for word in words:
        fname = path + '../data/' + word + '/' + word + 'TweetsUsers.json'
        with open(fname, 'r') as fin:
            uids += json.load(fin)
    
    return uids


def get_bomres(words):
    bomres = dict()
    for word in words:
        fname = path + '../data/bomResults/' + word + '_twitterUsers_bomResults_all.json'
        with open(fname) as handle:
            bomres.update(json.load(handle))
        
    return bomres



def get_uid_bom_tweets(words):
    word = '_'.join(words)
    uid_bom_tweets = dict()
    tweets_bom_fname = path + '../data/' + word + '/' + word + '_uid_bomOrNaN_time_tweets.json'
    with open(tweets_bom_fname, 'r') as handle:
        uid_bom_tweets_in = json.load(handle)
        for (uid, bom, tts) in uid_bom_tweets_in:
            if uid in uid_bom_tweets:
                uid_bom_tweets[uid][1] += tts
            else:
                uid_bom_tweets[uid] = [bom, tts]
    
    uid_bom_tweets = [(uid, uid_bom_tweets[uid][0], uid_bom_tweets[uid][1]) \
                      for uid in uid_bom_tweets]
    
    return uid_bom_tweets



def get_uids_followers(uids):
    
    import csv
    followers_fname = path + '../data/dbs/followerlist.csv'
    with open(followers_fname, 'r') as handle:
        csv_followers = csv.reader(handle, delimiter=',')
        lines_followers = [row for row in csv_followers]
        uid_followers = {int(l[1]):json.loads('[' + l[4].replace('{', '').replace('}', '') + ']') \
                         for l in lines_followers[1:] \
                         if int(l[1]) in uids}
        
    return uid_followers


def get_uids_friends(uids):
    
    import csv
    friends_fname = path + '../data/dbs/friendlist.csv'
    with open(friends_fname, 'r') as handle:
        csv_friends = csv.reader(handle, delimiter=',')
        lines_friends = [row for row in csv_friends]
        uid_friends = {int(l[1]):json.loads('[' + l[4].replace('{', '').replace('}', '') + ']') \
                       for l in lines_friends[1:] \
                       if int(l[1]) in uids}
        
    return uid_friends




def get_inds_uids(words):
    if (words[0]=='snapp'):
        word = words[0]
        dbfile = path + '../data/dbs/' + word + 'db.db'
    
        conn = sql.connect(dbfile)
        mycur = conn.cursor()
        mycur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        
        rows_followers = mycur.execute("select * from 'followers_table'").fetchall()
        rows_friends = mycur.execute("select * from 'friends_table'").fetchall()
        rows_users = mycur.execute("select * from 'users_table'").fetchall()
        
        ind_uid = {row[0]: row[1] for row in rows_users}
        
        edges_followers = [[ind_uid[x[1]], ind_uid[x[2]]] for x in rows_followers]
        edges_friends = [[ind_uid[x[1]], ind_uid[x[2]]] for x in rows_friends]
        
        uid_friends, uid_followers = [], []
        
        
    else:
        uids = get_uids(words)
            
        import csv
        followers_fname = path + '../data/dbs/followerlist.csv'
        with open(followers_fname, 'r') as handle:
            csv_followers = csv.reader(handle, delimiter=',')
            lines_followers = [row for row in csv_followers]
            uid_followers = {int(l[1]):json.loads('[' + l[4].replace('{', '').replace('}', '') + ']') \
                             for l in lines_followers[1:] \
                             if int(l[1]) in uids}
        
        import csv
        friends_fname = path + '../data/dbs/friendlist.csv'
        with open(friends_fname, 'r') as handle:
            csv_friends = csv.reader(handle, delimiter=',')
            lines_friends = [row for row in csv_friends]
            uid_friends = {int(l[1]):json.loads('[' + l[4].replace('{', '').replace('}', '') + ']') \
                           for l in lines_friends[1:] \
                           if int(l[1]) in uids}
        
        isolated_nodes = set(uids).difference(set(uid_friends.keys()).union(set(uid_followers.keys())))
        nonisolated = set(uids).difference(isolated_nodes)
        edges_followers = [(v, uid) for uid in uid_followers \
                           for v in uid_followers[uid] \
                           if v in nonisolated]
        edges_friends = [(v, uid) for uid in uid_friends \
                         for v in uid_friends[uid] \
                         if v in nonisolated]
        
    
    inds_uids = [(int(x[0]), int(x[1])) for x in lines_followers[1:]] 
    inds_uids += [(int(x[0]), int(x[1])) \
                  for x in lines_friends[1:] \
                  if int(x[1]) not in uid_followers]
    inds_uids = list(set(inds_uids))
    
    # catching the remainders that are only in the values, not the keys ...
    max_ind = max([x[0] for x in inds_uids])
    missing_uids = list(set([v for (v, uid) in edges_followers] + [v for (uid, v) in edges_friends]))
    missing_uids = list(set(missing_uids).difference(set([uid for (v, uid) in edges_followers] \
                                                   + [uid for (uid, v) in edges_friends])))
    inds_uids += [(max_ind+ind+1, v) for ind, v in enumerate(missing_uids)]
    inds_uids.sort(key = operator.itemgetter(0), reverse = False)
    
    
    return inds_uids



def get_inds_boms_dict(words):
    bomres =  get_bomres(words)
    
    inds_uids = get_inds_uids()
    
    inds_boms_dict = {ind:bomres[str(uid)]['cap']['universal'] if str(uid) in bomres \
                                 else np.NaN
                                 for (ind, uid) in inds_uids} 

    return inds_boms_dict



#%% -------------- larger functions, processing data ----------------------


#     
# Returns: nw_undir
#          nw_dir (nx.DiGraph()) : has a directed edge from the user who retweets 
#                                   to the user whose tweet is retweeted
#
def get_retweet_nw(words, 
                   relabel=False, attribute=False):
    
    fname = path + "../data/retweets/" + '_'.join(words) \
                 + "/" + '_'.join(words) + "_retweets_network_edgelist.json"
    with open(fname, 'r') as fin:
        edge_list = json.load(fin)
    edges = [(str(v), str(u)) for v in edge_list for u in edge_list[v]]
    
    nw_dir = nx.DiGraph(edges) # makes a directed edge from the user who retweets to the user whose tweet is retweeted
    
    fname = path + "../data/uname_uids.txt"
    with open(fname, 'r') as fin:
        lines = fin.readlines()

    
    if (relabel):
        uid_uname_dict = dict()
        for line in lines:
            uname, uid = line[:-1].split('\t')
            if uid in nw_dir.nodes():
                uid_uname_dict[str(uid)] = uname
        
        uid_uid = {str(uid): str(uid) for uid in uid_uname_dict}
        for nw in [nw_dir]:
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
            
        clstr_frnd = False
        fname = path + "../data/" + '_'.join(words) \
                         + "/" + '_'.join(words) + "_clstr_uid_bom_tweets_louv.json"
        try:
            with open(fname, 'r') as fin:
                clstr_uid_bom_frnd = json.load(fin)
            clstr_frnd = True
        except:
            print("\n " + fname + " could not be loaded ! \n")
            
        import random as rnd
        uid_tweet = {str(uid): rnd.choice([tweet for (tstamp, uid0, tweet) in retweets]) \
                     for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
        uid_tweet.update({str(uid0): uid_tweet[str(uid)] \
                          for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets \
                          for (tstamp, uid0, tweet) in retweets})
        uid_cap = {uid: cap \
                   for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
        uid_clstr = {str(uid): clstr \
                     for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets}
        uid_clstr.update({str(uid0): uid_clstr[str(uid)] \
                          for (clstr, uid, cap, retweets) in clstr_uid_bom_retweets \
                          for (tstamp, uid0, tweet) in retweets})
        if (clstr_frnd):
            uid_clstr_frnd = {str(uid): clstr \
                              for (clstr, uid, cap, tts) in clstr_uid_bom_frnd}
        
        for nw in [nw_dir]:#, nw_undir]
            if (not relabel):
                nx.set_node_attributes(nw, values=uid_uname_dict, name='screen_name')
            nx.set_node_attributes(nw, values=uid_tweet, name='tweet')
            nx.set_node_attributes(nw, value=uid_cap, name='cap')
            nx.set_node_attributes(nw, values=uid_clstr, name='clstr')  
            if (clstr_frnd):
                nx.set_node_attributes(nw, values=uid_clstr_frnd, name='clstr_frnd')  
            
    
    return Namespace(directed=nw_dir)#, undirected=nw_undir)





def make_frnd_nw(words):
    if (words[0]=='snapp'):
        word = words[0]
        dbfile = path + '../data/dbs/' + word + 'db.db'
    
        conn = sql.connect(dbfile)
        mycur = conn.cursor()
        mycur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        
        rows_followers = mycur.execute("select * from 'followers_table'").fetchall()
        rows_friends = mycur.execute("select * from 'friends_table'").fetchall()
        rows_users = mycur.execute("select * from 'users_table'").fetchall()
        
        ind_uid = {row[0]: row[1] for row in rows_users}
        
        edges_followers = [[ind_uid[x[1]], ind_uid[x[2]]] for x in rows_followers]
        edges_friends = [[ind_uid[x[1]], ind_uid[x[2]]] for x in rows_friends]
        
        uid_friends, uid_followers = [], []
        
        
    else:
        uids = get_uids(words)
            
        
        uid_followers = get_uids_followers(uids)
        
        uid_friends = get_uids_friends(uids)
        
        isolated_nodes = set(uids).difference(set(uid_friends.keys()).union(set(uid_followers.keys())))
        nonisolated = set(uids).difference(isolated_nodes)
        edges_followers = [(v, uid) for uid in uid_followers \
                           for v in uid_followers[uid] \
                           if v in nonisolated]
        edges_friends = [(v, uid) for uid in uid_friends \
                         for v in uid_friends[uid] \
                         if v in nonisolated]

    edge_list = collections.defaultdict(list)
    for v, u in edges_followers:
        edge_list[v].append(u)
        
    for v, u in edges_friends:
        edge_list[v].append(u)
        
        
    nw_dir = nx.DiGraph((v, u) for (v, u) in edges_followers)
    nw_dir.add_edges_from([(u, v) for (v, u) in edges_friends])
    
    
    return nw_dir



#     
# Returns: nw_undir:  friendship network
#          nw_dir (nx.DiGraph()) : friendship network
#
def get_friendship_nw(words, 
                      load=False,
                      relabel=False, attribute=False):

        
    if (load):
        word = '_'.join(words)
        fname = path + "../data/" + word + "/nw_dir_" + word + ".pkl"
        with open(fname, 'rb') as fin:
            nw_dir = pickle.load(fin)
        """
        fname = path + "../data/" + word + "/nw_undir_" + word + ".pkl"
        with open(fname, 'rb') as fin:
            nw_undir = pickle.load(fin)
        """
        
        fname = path + "../data/uname_uids.txt"
        with open(fname, 'r') as fin:
            lines = fin.readlines()
    
    else:
        nw_dir = make_frnd_nw(words)
    
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
        
        for nw in nws:
            if (not relabel):
                nx.set_node_attributes(nw, values=uid_uname_dict, name='screen_name')
            nx.set_node_attributes(nw, values=uid_tweet, name='tweet')
            nx.set_node_attributes(nw, value=uid_cap, name='cap')
            nx.set_node_attributes(nw, values=uid_clstr_rt, name='clstr_rt')  
            nx.set_node_attributes(nw, values=uid_clstr_frnd, name='clstr_frnd')  
            
    
    return Namespace(directed=nw_dir)#, undirected=nw_undir)


