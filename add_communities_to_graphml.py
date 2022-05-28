#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 15:06:08 2022

@author: Amirhossein farzam
"""




import os
import sys
import matplotlib.pyplot as plt
import operator
import networkx as nx
import igraph as ig


path = os.getcwd() + "/"



#%% ----------------- classes ----------------------

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
#%% ----------------- constants --------------------


#%% --------------- misc helper functions ----------------

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
# Modifies
# Returns: 
#
def igraph_comm_det(nw, inds_boms_dict, 
                    uids_inds_dict,
                    words, 
                    inds_uids_dict=[], 
                    louv=True,
                    load=True,
                    save=True,
                    rt_nw=False):
    
    if (inds_uids_dict==[]):
        inds_uids_dict = {uids_inds_dict[uid]: uid for uid in uids_inds_dict}
    
    import pickle

    try:
        if (not load):
            raise Exception
        word = '_'.join(words)
        fname = path  + "../network_analysis/" + word + "/" \
                + word + "_comms"
        if (rt_nw):
            fname += "_rt.pkl"
        else:
            fname += "_frnd.pkl"
        with open(fname, 'rb') as out:
            comms = pickle.load(out)
        print("\n The communities (igraph object) is loaded from " + fname + "\n")
    except:
        try:
            g = ig.Graph([(v, u) for (v, u) in list(nw.edges())], 
                          directed=False)
        except:
            g = ig.Graph([(uids_inds_dict[v], uids_inds_dict[u]) for (v, u) in list(nw.edges())], 
                          directed=False)
        g = g.simplify()
        if (louv):
            import louvain
            comms = louvain.find_partition(g, louvain.ModularityVertexPartition)
        else:
            fg_comms = g.community_fastgreedy()
            comms = fg_comms.as_clustering()
        if (save):
            word = '_'.join(words)
            
            #if (louv):
            comms = Namespace(membership=comms.membership, 
                              q=comms.q, n=comms.n, modularity=comms.modularity)
            
            try:
                filenames = os.popen("ls " + "../network_analysis/").read().split('\n')[:-1]
                if (word not in filenames):
                    os.popen("mkdir ../network_analysis/" + word)
            except:
                filenames = os.popen("ls " + "../network_analysis/").read().split('\n')[:-1]
                if (word not in filenames):
                    os.popen("mkdir ../network_analysis/" + word)
            
            fname = path  + "../network_analysis/" + word + "/" \
                    + word + "_comms"
            if (rt_nw):
                fname += "_rt.pkl"
            else:
                fname += "_frnd.pkl"
            with open(fname, 'wb') as out:
                pickle.dump(comms, out, pickle.HIGHEST_PROTOCOL)
                
            print("\n The communities (igraph object) is saved in " + fname + "\n")
        
    #if (louv):
    membs = comms.membership 
    #else:
    #    clstrs = comms.as_clustering()
    #    membs = clstrs.membership
    clstr_boms = dict()
    uid_clstrs = dict()
    for ind, clstr in enumerate(membs):
        if ind in inds_boms_dict:
            if (clstr not in clstr_boms):
                clstr_boms[clstr] = [inds_boms_dict[ind]]
            else:
                clstr_boms[clstr].append(inds_boms_dict[ind])
        if ind in inds_uids_dict:
            uid_clstrs[inds_uids_dict[ind]] = clstr
                
    clstr_boms = list(clstr_boms.items())
    
    return clstr_boms, uid_clstrs, comms


# ------


#
# Requires: nw (nx.Graph object)
#           uids_inds_dict (dict) : {uid: ind, ...}
#           louv (bool) : If True, runs Louvain, otherwise, fast greedy
# Modifies: - 
# Returns:
#
def get_clstrs_comms(nw,
                     uids_inds_dict,
                     louv=True):
    inds_uids_dict = {uids_inds_dict[uid]: uid for uid in uids_inds_dict}
    
    try:
        g = ig.Graph([(v, u) for (v, u) in list(nw.edges())], 
                      directed=False)
    except:
        g = ig.Graph([(uids_inds_dict[v], uids_inds_dict[u]) for (v, u) in list(nw.edges())], 
                      directed=False)
    g = g.simplify()
    if (louv):
        import louvain
        comms = louvain.find_partition(g, louvain.ModularityVertexPartition)
    else:
        fg_comms = g.community_fastgreedy()
        comms = fg_comms.as_clustering()
        
    membs = comms.membership 
    uid_clstrs = dict()
    for ind, clstr in enumerate(membs):
        if ind in inds_uids_dict:
            uid_clstrs[inds_uids_dict[ind]] = [clstr]
    
    from clusim.clustering import Clustering
    
    clst = Clustering(uid_clstrs)
    
    return clst, comms, uid_clstrs




#%% ------------------------------
# ------------ script ---------

# ----- import networks -----
words = ["deltangish"]
nw_fname = path + "../data/rt_networks/" + '_'.join(words) + "/" + '_'.join(words) + '_retweets_nw_dir.graphml'
nw_dir = nx.read_graphml(nw_fname)
nw_rt = nw_dir.to_undirected()

words = ["deltangish"]
nw_fname = path + "../data/frnd_networks/" + '_'.join(words) + "/" + '_'.join(words) + '_frnd_nw_dir.graphml'
nw_dir = nx.read_graphml(nw_fname)
nw_frn = nw_dir.to_undirected()


# ----- comm det ------

inds_uids_rt = [(ind, uid) for ind, uid in enumerate(nw_rt.nodes())]
inds_uids_rt.sort(key = operator.itemgetter(0), reverse = False)
uids_inds_dict_rt = {ind_uid[1]: ind_uid[0] for ind_uid in inds_uids_rt}

clst, comms, uid_clstr_rt =  get_clstrs_comms(nw_rt,
                                              uids_inds_dict_rt,
                                              louv=True)


inds_uids_frn = [(ind, uid) for ind, uid in enumerate(nw_frn.nodes())]
inds_uids_frn.sort(key = operator.itemgetter(0), reverse = False)
uids_inds_dict_frn = {ind_uid[1]: ind_uid[0] for ind_uid in inds_uids_frn}

clst, comms, uid_clstr_frn =  get_clstrs_comms(nw_frn,
                                               uids_inds_dict_frn,
                                               louv=True)


# ----- set attributes -----    

# remove those nodes that don't exist 
uid_clstr_frn4rt = {uid: uid_clstr_frn[uid] 
                    for uid in uid_clstr_rt if uid in uid_clstr_frn}
uid_clstr_rt4frn = {uid: uid_clstr_rt[uid] 
                    for uid in uid_clstr_frn if uid in uid_clstr_rt}
 


# add the missing nodes as community -1
for key in uid_clstr_rt:
    uid_clstr_rt[key] = uid_clstr_rt[key][0] # just taking care of format
    if key not in uid_clstr_frn4rt:
        uid_clstr_frn4rt[key] = -1
    else:
        uid_clstr_frn4rt[key] = uid_clstr_frn4rt[key][0]

for key in uid_clstr_frn:
    uid_clstr_frn[key] = uid_clstr_frn[key][0] # just taking care of format
    if key not in uid_clstr_rt4frn:
        uid_clstr_rt4frn[key] = -1 
    else:
        uid_clstr_rt4frn[key] = uid_clstr_rt4frn[key][0]
    
    

nx.set_node_attributes(nw_rt, values=uid_clstr_rt, name='clstr_rt')
nx.set_node_attributes(nw_rt, values=uid_clstr_frn4rt, name='clstr_frn')

nx.set_node_attributes(nw_frn, values=uid_clstr_rt4frn, name='clstr_rt')
nx.set_node_attributes(nw_frn, values=uid_clstr_frn, name='clstr_frn')



#%% ------ export networks -----

fname = path + "../data/rt_networks/" + '_'.join(words) + "/copy2_" + '_'.join(words) + '_rt_nw_undir.graphml'
nx.readwrite.graphml.write_graphml(nw_rt, fname)
print("\n graphml for rt is saved in " + fname + "\n")

fname = path + "../data/frnd_networks/" + '_'.join(words) + "/copy2_" + '_'.join(words) + '_frnd_nw_undir.graphml'
nx.readwrite.graphml.write_graphml(nw_frn, fname)
print("\n graphml for frn is saved in " + fname + "\n")



#%% -------- quick sanity check ---------


frn_clstr_frn  = list(nx.get_node_attributes(nw_frn, 'clstr_frnd').values())
plt.hist(frn_clstr_frn)

#%%
frn_clstr_rt  = list(nx.get_node_attributes(nw_frn, 'clstr_rt').values())
plt.hist(frn_clstr_rt)
#%%
rt_clstr_frn  = list(nx.get_node_attributes(nw_rt, 'clstr_frnd').values())
plt.hist(rt_clstr_frn)
#%%
rt_clstr_rt  = list(nx.get_node_attributes(nw_rt, 'clstr_rt').values())
plt.hist(rt_clstr_rt)
#%%

tweets_rt  = list(nx.get_node_attributes(nw_rt, 'tweet').values())

tweets_frn  = list(nx.get_node_attributes(nw_frn, 'tweet').values())






 