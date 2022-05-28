#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 02:50:46 2021

@author: Amirhossein Farzam
"""

import os
import json
import networkx as nx
import operator
import numpy as np
import sys

import matplotlib.pyplot as plt




path = os.getcwd() + "/"



#%% ----------------- classes ----------------------



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
    

#%% ------------------ main helpers -------------

def plot_distributions_byDiscType(bomss, mean_boms, figName):
   
    x_labels = ['Apolitical', 'Divisive political']
    
    fig, ax = plt.subplots(1)
    fig.set_size_inches(8, 6, forward=True)
    
    
    # seaborn violinplot
    import seaborn as sns
    sns.set(style="whitegrid")
    
    
    cm = plt.cm.get_cmap('Greys')
    color_scale = .7 / max(mean_boms)
    colors = [cm(mean_boms[i]*color_scale) for i in [0, 2]]
    
    
    vplot = sns.violinplot(data=[bomss[0], bomss[2]], 
                           inner='box', 
                           cut=False,
                           palette=colors,
                           linewidth=1.8, 
                           saturation=1.0, 
                           ax=ax)
    
    ax.set_ylim(-0.02, 1.03)
    ax.set_ylabel('CAP', fontsize=16)
    ax.set_xticks(ticks=list(range(len(x_labels))))
    
    ax.set_xticklabels(labels=x_labels, 
                        size=16)
    
    ax.tick_params(axis='both', which='major', labelsize=12, length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.grid(which="major", color='gray', linestyle='--', linewidth=1, alpha=0.2)
    
    plt.tight_layout()
    
    
    plt.savefig(figName, dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', format='png',
            transparent=True, bbox_inches='tight', pad_inches=0.1)

    
    print("\nplot(s) saved in " + figName + " !\n")
    
    return 





#%% --------------- Count all tweets ----------------------


dirname = '../data/rt_networks/'
filenames = os.popen("ls " + dirname ).read().split('\n')[:-1]


all_tweets_name = []
for word_ind, word in enumerate(filenames):
    word_fname = "../data/" + word + "/tweets_" + word
    tweets_fname =  os.popen("ls " + word_fname ).read().split('\n')[:-1]
    all_tweets_name += tweets_fname
    
    prog_msg = word + " has " + str(len(tweets_fname)) + " tweets"
    progressBar(word_ind, len(filenames), 
                optional_message=prog_msg)

all_tweets_name = set(all_tweets_name)

print("\n Total number of tweets: " + str(len(all_tweets_name)) + "\n")

# Result:   Total number of tweets: 1081846



#%% --------------- Count tweets and users by topic ----------------------

dirname = '../data/rt_networks/'
filenames = os.popen("ls " + dirname ).read().split('\n')[:-1]


word_tweetCount_userCount = dict()
summary_str = ""
for word_ind, word in enumerate(filenames):
    fname = "../data/all_uid_bomOrNaN_time_tweets/" + word + "_uid_bomOrNaN_time_tweets.json"
    with open(fname, 'r') as fin:
        uid_bom_tts = json.load(fin)
    
    uid_count = len(set([uid for (uid, cap, tts) in uid_bom_tts]))
    tweet_count = sum([len(tts) for (uid, cap, tts) in uid_bom_tts])
    
    word_tweetCount_userCount[word] = {"uid_count": uid_count, "tweet_count": tweet_count}
    
    prog_msg = word + " has " + str(uid_count) + " users  - and "  + str(tweet_count) + " tweets"
    summary_str += prog_msg + "\n"
    progressBar(word_ind, len(filenames), 
                optional_message=prog_msg)


print("\n Number of users and tweets for each topic:\n " + summary_str + "\n")




#%% --------------- Count all nodes and edges ----------------------


dirname = '../data/frnd_and_rt_12topics_with1stCut/rt_networks/'
filenames = os.popen("ls " + dirname ).read().split('\n')[:-1]

nodes_edges_count_rt = dict()
nodes_edges_count_frnd = dict()
for word_ind, word in enumerate(filenames):
    fname_rt = '../data/rt_networks/' + word + "/" + word + "_retweets_nw_dir.graphml"
    rt_nw = nx.read_graphml(fname_rt)
    num_isolated = len([v for v in rt_nw.nodes() if rt_nw.degree(v)==0])
    nodes_edges_count_rt[word] = {'nodes': rt_nw.number_of_nodes(), 
                                  'edges': rt_nw.number_of_edges(),
                                  'isolated_nodes':num_isolated,
                                  'nonisolated_nodes': rt_nw.number_of_nodes() - num_isolated}
    
    fname_frnd = '../data/frnd_networks/' + word + "/" + word + "_frnd_nw_dir.graphml"
    frnd_nw = nx.read_graphml(fname_frnd)
    num_isolated = len([v for v in frnd_nw.nodes() if frnd_nw.degree(v)==0])
    nodes_edges_count_frnd[word] = {'nodes': frnd_nw.number_of_nodes(), 
                                    'edges': frnd_nw.number_of_edges(),
                                    'isolated_nodes': num_isolated,
                                    'nonisolated_nodes': frnd_nw.number_of_nodes() - num_isolated}
    
    
    prog_msg = "nodes and edges for %s counted" % word
    progressBar(word_ind, len(filenames), 
                optional_message=prog_msg)
    
    
for word in nodes_edges_count_rt:
    print("\nRt nw of %s has %d nodes and %d edges, with %d isolated nodes and %d non-isolated nodes" \
          % (word, nodes_edges_count_rt[word]['nodes'], 
             nodes_edges_count_rt[word]['edges'], 
             nodes_edges_count_rt[word]['isolated_nodes'],
             nodes_edges_count_rt[word]['nonisolated_nodes']))
    print("\nFrnd nw of %s has %d nodes and %d edges, with %d isolated nodes and %d non-isolated nodes\n" \
          % (word, nodes_edges_count_frnd[word]['nodes'], 
             nodes_edges_count_frnd[word]['edges'],
             nodes_edges_count_frnd[word]['isolated_nodes'],
             nodes_edges_count_frnd[word]['nonisolated_nodes']))
        
        

#%% -----------------------------------------------------------



## ------------------- CAP distribution by discussion type ---------------------


dirname = '../data/rt_networks/'
filenames = os.popen("ls " + dirname ).read().split('\n')[:-1]

topics_AD = [
         'afsordegi',
         'golab_adine_mehdi_hashemi_mehnoosh_sadeghi',
         'kobe_bryant',
         'valentine'
         ];

topics_NPD = [
         'bahareh_hedayat',
         'namaki_khodkoshi',
         'pahbad'
         ];

topics_DPD = [
         'bluegirl',
         'snapp',
         'trump'
         ];

topics_dict = {
     'afsordegi': 'Depression',
     'bahareh_hedayat': 'Bahareh Hedayat',
     'bluegirl': 'Blue girl',
     'deltangish': 'Flash mob',
     'golab_adine_mehdi_hashemi_mehnoosh_sadeghi': 'Golab Adineh',
     'havapeyma': 'Air plane',
     'kobe_bryant': 'Kobe Bryant',
     'namaki_khodkoshi': 'Suicide',
     'pahbad': 'Drone',
     'snapp': 'Snapp',
     'trump': 'Trump',
     'valentine': 'Valentine'
    };

bomss = []
uidss = []
uidss_noNaN = []
mean_boms = []
for group_ind, words in enumerate([topics_AD, topics_NPD, topics_DPD]):
    boms = []
    uids = []
    uids_noNaN = []
    for word_ind, word in enumerate(words):
        fname = "../data/all_uid_bomOrNaN_time_tweets/" + word + "_uid_bomOrNaN_time_tweets.json"
        
        uid_bom_tts = json.load(open(fname))
        boms += [bom  for (uid, bom, tt) in uid_bom_tts \
                 if (not np.isnan(bom))]
        uids += [uid for (uid, bom, tt) in uid_bom_tts]
        uids_noNaN += [uid for (uid, bom, tt) in uid_bom_tts \
                       if (not np.isnan(bom))]
        
        prog_msg = word + " boms put in the pool "
        
        progressBar(word_ind + group_ind*len(topics_AD) + 1, 
                    len(filenames), optional_message=prog_msg)
    
    mean_boms.append(np.nanmean(boms))
    bomss.append(boms)
    uidss.append(uids)
    uidss_noNaN.append(uids_noNaN)
    
    
#%% ---- plotting --------
    


figName = path + "../paper/figures/additional/boms/bom_dist_by_topicType.png"
plot_distributions_byDiscType(bomss, mean_boms, figName)
    
    
   


#%% -----------------------------------------------------------

# =====================================================================================
## ------------------- CAP distribution for the highest degrees ---------------------


dirname = '../data/rt_networks/'
filenames = os.popen("ls " + dirname ).read().split('\n')[:-1]

topics_AD = [
         'afsordegi',
         'golab_adine_mehdi_hashemi_mehnoosh_sadeghi',
         'kobe_bryant',
         'valentine'
         ];

topics_NPD = [
         'bahareh_hedayat',
         'namaki_khodkoshi',
         'pahbad'
         ];

topics_DPD = [
         'bluegirl',
         'snapp',
         'trump'
         ];

topics_dict = {
     'afsordegi': 'Depression',
     'bahareh_hedayat': 'Bahareh Hedayat',
     'bluegirl': 'Blue girl',
     'golab_adine_mehdi_hashemi_mehnoosh_sadeghi': 'Golab Adineh',
     'havapeyma': 'Air plane',
     'kobe_bryant': 'Kobe Bryant',
     'namaki_khodkoshi': 'Suicide',
     'pahbad': 'Drone',
     'snapp': 'Snapp',
     'trump': 'Trump',
     'valentine': 'Valentine'
    };




bomss = []
notins = []
nanss = []
uidss = []
uidss_noNaN = []
mean_boms = []
for group_ind, words in enumerate([topics_AD, topics_NPD, topics_DPD]):
    boms = []
    notin = []
    nans = []
    uids = []
    uids_noNaN = []
    for word_ind, word in enumerate(words):
        fname = "../data/rt_networks/" + word + "/" + word + "_retweets_nw_dir.graphml"
        
        # ---- get CAPs of users with largest degrees (top decile)
        nw = nx.read_graphml(fname)
        deg_dict = dict(nx.degree(nw))
        nodeid_deg = list(deg_dict.items())
        nodeid_deg.sort(key = operator.itemgetter(1), reverse = True)
        
        nodeid_cap_dict = dict(nx.get_node_attributes(nw, 'cap'))
        
        boms += [nodeid_cap_dict[nodeid] \
                 for (nodeid, deg) in nodeid_deg[:len(nodeid_deg)//10] \
                     if ((nodeid in nodeid_cap_dict) and (not np.isnan(nodeid_cap_dict[nodeid])))]
            
        notin += [nodeid \
                 for (nodeid, deg) in nodeid_deg[:len(nodeid_deg)//10] \
                     if nodeid not in nodeid_cap_dict]
        
        prog_msg = word + " boms put in the pool "
        
        progressBar(word_ind + group_ind*len(topics_AD) + 1, 
                    len(filenames), optional_message=prog_msg)
    
    mean_boms.append(np.nanmean(boms))
    bomss.append(boms)
    notins.append(notin)
    
    

#%%

# remove nans
bomss = [[x for x in boms if not np.isnan(x)] for boms in bomss]


# --------- Kolmogorov-Smirnov two-sample test -------------

from scipy.stats import ks_2samp

ks_statistic, p_value = ks_2samp(bomss[0], bomss[2], mode="auto")




#%% ---- plotting --------

figName = path + "../paper/figures/additional/boms/bom_highDeg_byTopic.png"
plot_distributions_byDiscType(bomss, mean_boms, figName)
    


#%% -----------------------------------------------------------




#%% -----------------------------------------------------------

# =====================================================================================
## ------------------- Deactivate/suspended VS AD/DPD ---------------------


dirname = '../data/rt_networks/'
filenames = os.popen("ls " + dirname ).read().split('\n')[:-1]

topics_AD = [
         'afsordegi', # Unreliable user status for Afsordegi, comment out for more reliable results
         'golab_adine_mehdi_hashemi_mehnoosh_sadeghi',
         'kobe_bryant',
         'valentine'
         ];

topics_NPD = [
         'bahareh_hedayat',
         'namaki_khodkoshi',
         'pahbad'
         ];

topics_DPD = [
         'bluegirl',
         'snapp',
         'trump'
         ];

topics_dict = {
     'afsordegi': 'Depression',
     'bahareh_hedayat': 'Bahareh Hedayat',
     'bluegirl': 'Blue girl',
     'golab_adine_mehdi_hashemi_mehnoosh_sadeghi': 'Golab Adineh',
     'havapeyma': 'Air plane',
     'kobe_bryant': 'Kobe Bryant',
     'namaki_khodkoshi': 'Suicide',
     'pahbad': 'Drone',
     'snapp': 'Snapp',
     'trump': 'Trump',
     'valentine': 'Valentine'
    };


nanss = []
bomss_nonan = []
for group_ind, words in enumerate([topics_AD, topics_NPD, topics_DPD]):
    nans = []
    boms_nonan = []
    for word_ind, word in enumerate(words):
        fname = "../data/all_uid_bomOrNaN_time_tweets/" + word + "_uid_bomOrNaN_time_tweets.json"
        
        with open(fname, 'r') as fin:
            uid_bom_tt = json.load(fin)
            
        nans += [uid \
                 for (uid, bom, tt) in uid_bom_tt \
                     if np.isnan(bom)]
        boms_nonan += [uid \
                       for (uid, bom, tt) in uid_bom_tt \
                           if not np.isnan(bom)]
        
        prog_msg = word + " boms put in the pool "
        
        progressBar(word_ind + group_ind*len(topics_AD) + 1, 
                    len(filenames), optional_message=prog_msg)
    nanss.append(nans)
    bomss_nonan.append(boms_nonan)


#%% ---- Chi-square test --------
    
# --- make contingency table as follows
#            deactive               active    
#    AD    len(nanss[0])     len(bomss_nonan[0])
#   DPD    len(nanss[2])     len(bomss_nonan[2])
contingency_table = np.array([[len(nanss[0]), len(bomss_nonan[0])], 
                              [len(nanss[2]), len(bomss_nonan[2])]])

from scipy.stats import chi2_contingency

chi2, p, dof, ex = chi2_contingency(observed=contingency_table, 
                                    correction=True)

# odds ratio
oddsR = (contingency_table[1][0]/contingency_table[1][1]) / (contingency_table[0][0]/contingency_table[0][1])


print(" oddsR = %f \n p = %.10f \n chi2 = %f" % (oddsR, p, chi2))


#%% -----------------------------------------------------------
    




#%% -----------------------------------------------------------

# ========================================================================================
## ------------------- Deactivate/suspended VS AD/DPD in high degs ---------------------



dirname = '../data/rt_networks/'
filenames = os.popen("ls " + dirname ).read().split('\n')[:-1]

topics_AD = [
         'afsordegi', # Unreliable user status for Afsordegi, comment out for more reliable results
         'golab_adine_mehdi_hashemi_mehnoosh_sadeghi',
         'kobe_bryant',
         'valentine'
         ];

topics_NPD = [
         'bahareh_hedayat',
         'namaki_khodkoshi',
         'pahbad'
         ];

topics_DPD = [
         'bluegirl',
         'snapp',
         'trump'
         ];

topics_dict = {
     'afsordegi': 'Depression',
     'bahareh_hedayat': 'Bahareh Hedayat',
     'bluegirl': 'Blue girl',
     'golab_adine_mehdi_hashemi_mehnoosh_sadeghi': 'Golab Adineh',
     'havapeyma': 'Air plane',
     'kobe_bryant': 'Kobe Bryant',
     'namaki_khodkoshi': 'Suicide',
     'pahbad': 'Drone',
     'snapp': 'Snapp',
     'trump': 'Trump',
     'valentine': 'Valentine'
    };




bomss = []
notins = []
nanss = []
uidss = []
uidss_noNaN = []
mean_boms = []
for group_ind, words in enumerate([topics_AD, topics_NPD, topics_DPD]):
    boms = []
    notin = []
    nans = []
    uids = []
    uids_noNaN = []
    for word_ind, word in enumerate(words):
        fname = "../data/rt_networks/" + word + "/" + word + "_retweets_nw_dir.graphml"
        
        # ---- get CAPs of users with largest degrees (top decile)
        nw = nx.read_graphml(fname)
        deg_dict = dict(nx.degree(nw))
        nodeid_deg = list(deg_dict.items())
        nodeid_deg.sort(key = operator.itemgetter(1), reverse = True)
        
        nodeid_cap_dict = dict(nx.get_node_attributes(nw, 'cap'))
        
        boms += [nodeid_cap_dict[nodeid] \
                 for (nodeid, deg) in nodeid_deg[:len(nodeid_deg)//10] \
                     if ((nodeid in nodeid_cap_dict) and (not np.isnan(nodeid_cap_dict[nodeid])))]
            
        nans += [nodeid \
                 for (nodeid, deg) in nodeid_deg[:len(nodeid_deg)//10] \
                     if ((nodeid in nodeid_cap_dict) and (np.isnan(nodeid_cap_dict[nodeid])))]
            
        notin += [nodeid \
                 for (nodeid, bom) in nodeid_deg[:len(nodeid_deg)//10] \
                     if nodeid not in nodeid_cap_dict]
            
        
        prog_msg = word + " boms put in the pool "
        
        progressBar(word_ind + group_ind*len(topics_AD) + 1, 
                    len(filenames), optional_message=prog_msg)
    
    mean_boms.append(np.nanmean(boms))
    bomss.append(boms)
    nanss.append(nans)
    notins.append(notin)
    
    

#%% ---- Chi-square test --------
    
# --- make contingency table as follows
#            deactive               active    
#    AD    len(nanss[0])     len(bomss[0])
#   DPD    len(nanss[2])     len(bomss[2])
contingency_table = np.array([[len(nanss[0]), len(bomss[0])], 
                              [len(nanss[2]), len(bomss[2])]])

from scipy.stats import chi2_contingency

chi2, p, dof, ex = chi2_contingency(observed=contingency_table, 
                                    correction=True)

# odds ratio
oddsR = (contingency_table[1][0]/contingency_table[1][1]) / (contingency_table[0][0]/contingency_table[0][1]) 


print(" oddsR = %f \n p = %.10f \n chi2 = %f" % (oddsR, p, chi2))


#%% -----------------------------------------------------------
    

