#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 13 04:30:53 2020

Description: Participation by group over time + spearman correlation
                Paper version, i.e. not onlyinactives, and by defaults nonans

@author: Amirhossein Farzam
"""


import os
import sys
import numpy as np
import json
import collections
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import copy
import pickle

import prepare_twitter_data as ptd


path = os.getcwd() + "/"



#%% ----------------- constants --------------------

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)




#%% --------------- helper functions ----------------

# Returns: prints a progress bar
def progressBar(value, endvalue, optional_message="", bar_length=50):

        percent = float(value) / endvalue
        arrow = '.' * int(round(percent * bar_length)-1) + '>'
        spaces = ' ' * (bar_length - len(arrow))

        sys.stdout.write("\r {0} Percent: [{1}] {2}%         ".format(optional_message, \
                                                             arrow + spaces, \
                                                             int(round(percent * 100))))
        sys.stdout.flush()


#%% -------------- main functions -------------------

#
# Requires: uid_bom_tstamps (list): [(uid, bom, [timestamp, ...]), ...]
#           bins_in_a_day (float): number of bins (could be less than one)
#                                   for timestamps in each day
# Modifies: -
# Returns: [(uid, bom, tstampBins), ...]
#
def get_tstampBins(uid_bom_tstamps, bins_in_a_day=1):

    tstamps = [t for (uid, bom, ts) in uid_bom_tstamps for t in ts]
    num_bins = int(round(((max(tstamps) - min(tstamps)) / (3600*24.0)) * bins_in_a_day))
    times_bins_freq, times_bins_edges = np.histogram(tstamps, bins=num_bins)

    boms_tstampBins = []
    for i, (uid, bom, tstamps) in enumerate(uid_bom_tstamps):
        tstamp_bins = np.digitize(tstamps, times_bins_edges, right=False)
        boms_tstampBins.append(tuple([uid, bom, tstamp_bins]))


    return boms_tstampBins, num_bins



def get_bomCount_over_time(boms_tstampBins,
                           weighted=False):
    time_boms = collections.defaultdict(list)
    for (uid, bom, tstampBins) in boms_tstampBins:
        if (weighted):
            tstampBins = list(tstampBins)
            for tbin in tstampBins:
                time_boms[tbin].append(bom)
        else:
            tstampBins_set = list(set(tstampBins))
            for tbin in tstampBins_set:
                time_boms[tbin].append(bom)

    return time_boms



def get_participation_by_group(time_boms,
                               borders,
                               save_data=False, plot_mode="", fname_root=""):

    if (save_data and (plot_mode+fname_root=="")):
        raise ValueError("!! If save_data==True, plot_mode and fname_root must be specified!!")


    group_a = [len([bom for bom in time_boms[t] if 1.0 > bom >= borders[1]]) \
               for t in range(len(time_boms))]
    group_b = [len([bom for bom in time_boms[t] if borders[0] <= bom < borders[1]]) \
               for t in range(len(time_boms))]
    group_c = [len([bom for bom in time_boms[t] if  bom < borders[0]]) \
               for t in range(len(time_boms))]
    min_len = min([len(group_a), len(group_b), len(group_c)])
    group_a, group_b, group_c = group_a[:min_len], group_b[:min_len], group_c[:min_len]


    if (save_data):
        fname = fname_root + "_" + plot_mode + ".json"
        with open(fname, 'w') as f:
            json.dump({'group_a':group_a, 'group_b':group_b, 'group_c':group_c}, f)

        print("\n The {group_a, b, c} (long version) is saved in " + fname + "\n")


    return group_a, group_b, group_c




# Returns: index of the first day that it got > trippled
def find_firstDay(time_series):

    jumps = [i+1 for i in range(len(time_series)-1) \
             if 3*time_series[i] < time_series[i+1]]

    if (len(jumps)==0):
        return 0
    else:
        return max(jumps)


# Returns: index of the last day before  it got cut to < a third for the last time
def find_lastDay(time_series):

    drops = [i for i in range(len(time_series)-1) \
             if time_series[i] > 3*time_series[i+1]]

    if (len(drops)==0):
        return len(time_series)-1
    else:
        return max(drops)




#%% ------------ plotting function -----------

def plot_participationByGroup(words,
                              group_a, group_b, group_c,
                              mean_boms,
                              ylabel='Frequency',
                              day_0=0, day_end=-1):
    if (day_end==-1):
        day_end = len(group_a)

    fig, ax = plt.subplots(1)
    fig.set_size_inches(8, 6, forward=True)

    cm = plt.cm.get_cmap('copper_r')

    colors = [cm(((len(mean_boms)-i-1)+.3)/len(mean_boms)) for i in range(len(mean_boms))]

    group_a, group_b, group_c = group_a[day_0:day_end+1], group_b[day_0:day_end+1], group_c[day_0:day_end+1]

    barsXs = 10*6*np.array(list(range(1, len(group_a)+1)))

    ax.xaxis.set_ticks(np.arange(barsXs[0], barsXs[-1], 120))
    ax.set_xticklabels(labels = [xl*2 for xl in list(range(len(np.arange(barsXs[0], barsXs[-1], 120))))],
                       size=11, minor=False)

    lines = [Line2D([0], [0], color=c, linewidth=3, linestyle='-') for c in colors]
    labels = ['A',
              'B', 
              'C'] 

    ax.legend(lines, labels,
              bbox_to_anchor=(1.1, .95),
              fontsize='13', frameon=False)


    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_xlabel('Day', fontsize=16)

    ax.tick_params(axis='both', which='major', labelsize=11, length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.grid(which="major", color='gray', linestyle='--', linewidth=1, alpha=0.2)

    plt.tight_layout()


    return fig, ax





#
# Requires: corrs (2d array for pairwise correlations)
# Modifies: -
# Returns: the heatmap for the correlations
#
def plot_correlations(corrs, rownames, colnames):

    # ----- plotting the pearsonrs
    fig, ax = plt.subplots(1, 1, facecolor='white')
    fig.set_size_inches(len(rownames), len(colnames), forward=True)

    im = ax.imshow(corrs,
                   cmap='RdBu', vmin=-1, vmax=1, interpolation='none')

    ax.set_frame_on(False)

    ax.set_xticks(np.arange(0, len(colnames), 1), minor=True)
    ax.set_yticks(np.arange(0, len(rownames), 1), minor=True)


    # Labels for major ticks
    ax.set_yticklabels([], minor=False)
    ax.set_xticklabels([], minor=False)

    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')

    tick_locs = np.arange(-.5, len(colnames), 1)
    ax.set_xticks(tick_locs, minor=True)
    ax.set_yticks(tick_locs, minor=True)


    ax.xaxis.set(ticks=tick_locs+.5, ticklabels=rownames)
    ax.yaxis.set(ticks=tick_locs+.05*len(rownames)+.35, ticklabels=rownames)

    ax.tick_params(axis='x', pad=-25, direction='out')
    ax.tick_params(axis='y', pad=-3, rotation=90)
    ax.tick_params(labelsize=40*(len(rownames)/4))


    # Gridlines based on minor ticks
    ax.grid(np.arange(0, len(colnames), 1) - 1,
            axis='both', which='minor', color='w', linestyle='-', linewidth=2)

    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    axins1 = inset_axes(ax,
                width="2%",  
                height="95%", 
                loc='upper right',
                borderpad=0)

    cb = fig.colorbar(im, cax=axins1, orientation="vertical")
    cb.outline.set_visible(False)
    cb.set_ticks(ticks=[-1, -.5, 0, .5, 1])
    cb.ax.tick_params(labelsize=20*(len(rownames)/4), size=0)

    """
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size="5%", pad=0.2)
    fig.add_axes(cax)
    fig.colorbar(im, cax=cax)
    """

    return fig, ax



#%%

#%% ------------- main driver ----------------

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()


    parser.add_argument('-w', '--words', nargs='+', type=str, required=True,# default=False,
                        help='(str) : Words to analyze')
    parser.add_argument('-m', '--plot_mode', type=str,
                        choices=['tweets', 'corrs', 'none'],
                        required=True,
                        help='(str) : which plots? ("first" is only first tweets, ' \
                             + '"per" is tweet per user, "corrs" is for correlations (all of them"))')

    parser.add_argument('-d', '--save_data', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : Save the data for plot or not - default is False')
    parser.add_argument('-p', '--save_plot', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : Save the plot or not - default is False')
    parser.add_argument('-o', '--output_for_paper', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : If True, saves the plots in their corresponding directory for paper, not words - default is False')



    args = parser.parse_args()
    print("\n\n Participation by group per day ... " \
           + "\n  for the following arguments:\n   " \
           + str(args) + "\n")

    import datetime
    print("\n\n Start time : " + str(datetime.datetime.now()) + " EST \n\n")


    #%%

    save_data = args.save_data
    words = args.words
    save_plot = args.save_plot
    save_for_paper = args.output_for_paper

    plot_mode = args.plot_mode
    corrs = False
    if (plot_mode=='tweets'):
        weighted = False
    elif (plot_mode=='corrs'):
        corrs = True
        weighted = True
        save_plot_corrs, save_data_corrs = save_plot, save_data
        save_plot, save_data = False, False
    elif (plot_mode=='none'):
        weighted = False

    sub_dir = "" # subdirectory for saving
    if (corrs):
        sub_dir = 'corrs/'

    fname_word = '_'.join(words)
    if (save_for_paper):

        for root in ["../paper/data/output/temporal/" , "../paper/figures/temporal/" ]:
            filenames = os.popen("ls " + root).read().split('\n')[:-1]
            if (fname_word not in filenames):
                os.popen("mkdir " + root + fname_word)

        fname_root = path + "../paper/data/output/temporal/" + fname_word + '/' \
                      + sub_dir + fname_word + "_participationByGroup"
        figName_root = path + "../paper/figures/temporal/" + fname_word + '/' \
                        + sub_dir + fname_word + "_participationByGroup"

    else:
        fname_root = path + "../data/" + fname_word + "/" + fname_word + "_participationByGroup"
        figName_root = path + "../figures/" + fname_word + "/" + fname_word + "_participationByGroup"



    uid_bom_tweets_withNaN = ptd.get_uid_bom_tweets(words)


    #%%

    uid_bom_tweets_withNaN = [(uid, bom, [t_time for (t_time, t_txt) in tt]) \
                              for (uid, bom, tt) in uid_bom_tweets_withNaN]

    uid_bom_tweets = [(uid, bom, ttimes) \
                          for (uid, bom, ttimes) in uid_bom_tweets_withNaN \
                      if (not np.isnan(bom))]
    #%%

    boms_tstampBins, num_bins = get_tstampBins(uid_bom_tweets_withNaN, bins_in_a_day=1)

    caps_arr = np.array([x[1] for x in uid_bom_tweets])

    borders = [0.01, 0.059]

    mean_boms = [np.mean([cap for cap in caps_arr if cap < b]) \
                 for b in borders + [0.999]]

    #%%


    boms_tstampBins_initialCopy = copy.deepcopy(boms_tstampBins)
    used_boms_tstampBins = False
    time_boms_wd = get_bomCount_over_time(boms_tstampBins=boms_tstampBins,
                                          weighted=True)
    used_boms_tstampBins = True



    #%%

    if (save_plot): # first save the mean_boms
        with open(figName_root + '_mean_boms.txt', 'w') as fout:
            fout.write(str({g: mean_boms[i] for i, g in enumerate(['A', 'B', 'C'])}))
        group_a, group_b, group_c  = get_participation_by_group(time_boms_wd,
                                                               borders,
                                                               save_data=save_data,
                                                               plot_mode='tweets',
                                                               fname_root=fname_root)
        days_before_first, days_after_last = 2, 3
        day_0 = max(0,
                    min([find_firstDay(g) for g in [group_a, group_b, group_c]]) - days_before_first)
        day_end = min(len(group_a) - 1,
                      max([find_lastDay(g) for g in [group_a, group_b, group_c]]) + days_after_last)


    group_a_wd, group_b_wd, group_c_wd  = get_participation_by_group(time_boms_wd,
                                                           borders,
                                                           save_data=save_data,
                                                           plot_mode='tweets',
                                                           fname_root=fname_root)
    if (save_plot):
        fig, ax = plot_participationByGroup(words,
                                          group_a_wd, group_b_wd, group_c_wd,
                                          mean_boms,
                                          ylabel='Number of Tweets',
                                          day_0=day_0, day_end=day_end)
        figName = figName_root + "_tweets.png"
        fig.savefig(figName, dpi=300, facecolor='w', edgecolor='w',
                    orientation='portrait', papertype=None, format='png',
                    transparent=False,
                    bbox_inches='tight', pad_inches=0.1,
                    frameon=False)
        print("\n The plot is saved in " + figName + "\n")





    #%% ______________________________________________________________________
    #    ----------------------- The correlations ---------------------------
    #   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


    if (corrs):

        from scipy import stats as st
        def corr_func(x, y):
            return st.spearmanr(np.diff(x), np.diff(y)).correlation

        correlations_groups = {'u': {'a-b':None, 'a-c':None, 'b-c':None},
                               't': {'a-b':None, 'a-c':None, 'b-c':None},
                               'f': {'a-b':None, 'a-c':None, 'b-c':None},
                               'p': {'a-b':None, 'a-c':None, 'b-c':None}}
        correlations_vars = {'a': {'u-t':None, 'u-f':None, 't-f':None},
                             'b': {'u-t':None, 'u-f':None, 't-f':None},
                             'c': {'u-t':None, 'u-f':None, 't-f':None}}


        # ---- correlation between different groups, for number of tweets ----

        corrs_groups = {'u':np.ones((3, 3)), 't':np.ones((3, 3)),
                        'f':np.ones((3, 3)), 'p':np.ones((3, 3))}

        min_len = min([len(g) for g in [group_a_wd, group_b_wd, group_c_wd]])
        correlations_groups['t']['a-b'] = corr_func(group_a_wd[:min_len], group_b_wd[:min_len])
        correlations_groups['t']['a-c'] = corr_func(group_a_wd[:min_len], group_c_wd[:min_len])
        correlations_groups['t']['b-c'] = corr_func(group_b_wd[:min_len], group_c_wd[:min_len])
        corrs_groups['t'][0, 1] = corrs_groups['t'][1, 0] = correlations_groups['t']['a-b']
        corrs_groups['t'][0, 2] = corrs_groups['t'][2, 0] = correlations_groups['t']['a-c']
        corrs_groups['t'][1, 2] = corrs_groups['t'][2, 1] = correlations_groups['t']['b-c']


        if (save_data_corrs):
            fname = fname_root + "_corrs_groups.pkl"
            with open(fname, 'wb') as f:
                pickle.dump(corrs_groups, f, pickle.HIGHEST_PROTOCOL)

            print("\n The correlations between the different groups "\
                  + "for the same variable is saved in " + fname + "\n")



        if (save_plot_corrs):
            rows_cols_names = ['A', 'B', 'C']

            fig, ax = plot_correlations(corrs=corrs_groups['t'],
                                        rownames=rows_cols_names,
                                        colnames=rows_cols_names)

            figName = figName_root + "_corrs_groups_tweets.png"

            fig.savefig(figName, dpi=300, facecolor='w', edgecolor='w',
                        orientation='portrait', papertype=None, format='png',
                        transparent=False,
                        bbox_inches='tight', pad_inches=0.1,
                        frameon=False)
            print("\n The plot is saved in " + figName + "\n")





    #%%













    # =========================================================================
    # ==============================    THE END    ============================
    # =========================================================================
    #%% =======================================================================







