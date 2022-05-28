#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 18:07:56 2020

@author: Amirhossein Farzam
"""



import os
import sys
import numpy as np
import json
import operator
import time
import re

path = os.getcwd() + "/"


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
        
#%%

#
# Requires: -
# Modifies: -
# Returns: a list of tuples : [(uid, cap of user, [(tweet times, tweet texts)]),...]
#          note that the tweet texts include only the unicode part of the text
#
def make_uid_bom_tweets_file(words, 
                             save_tweets=True, outdir="../data/"):
    all_words = '_'.join(words)
    
    if (len(words)>1):
        try:
            os.popen("mkdir ../data/" + all_words + "/tweets_" + all_words)
        except:
            pass
        for word in words:  
            try:
                os.popen("for i in ../data/" + word + "/tweets_" + word + "/*.json;" \
                         + " do cp \"$i\" ../data/" + all_words + "/tweets_" + all_words + "/; done")
            except:
                pass
            
    word = all_words
    filenames = os.popen("ls ../data/" + word + "/tweets_" + word + "/").read().split('\n')[:-1]
    
    tweets = dict()
    for i0, filename in enumerate(filenames):
        filename = path + "../data/" + word + "/tweets_" + word + "/" + filename
        with open(filename) as handle:
            tweet = json.load(handle)
            uid = tweet['user']['id']
            try:
                txt = tweet['full_text']
            except:
                txt = tweet['text']
                            
            
            t_create = time.mktime(time.strptime(tweet['created_at'], \
                                                 "%a %b %d %H:%M:%S +0000 %Y"))
            if uid not in tweets:
                tweets[uid] = []
            tweets[uid] += [(t_create, re.sub(r"[\x00-\x7f]+", ' ', txt))] # gets the unicode only
            tweets[uid].sort(key = operator.itemgetter(0), reverse = False)
                
        if (i0%100==0):
            
            progressBar(i0+1, len(filenames), 
                        optional_message=" reading in tweets and making the edge list...")
            
    
    tweets = tweets.items()
    
    if (save_tweets):
        bomres = dict()
        for word in words:
            fname = path + "../data/bomResults/" + word + "_twitterUsers_bomResults_all.json"
            with open(fname) as handle:
                bomres.update(json.load(handle))
        
        tweets = [(uid, bomres[str(uid)]['cap']['universal'], txts) if str(uid) in bomres \
                  else (uid, np.NaN, txts)
                  for (uid, txts) in tweets]
        
        word = '_'.join(words)
        tweets_bom_fname = path + outdir + word + "/" + word + "_uid_bomOrNaN_time_tweets.json"
        with open(tweets_bom_fname, 'w') as tweets_bom_file:
            json.dump(tweets, tweets_bom_file)
        print("\n The tweets in format uid_bom_tts is saved in " + tweets_bom_fname + "\n")
    
    
    return tweets




if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser()
    

    parser.add_argument('-w', '--words', nargs='+', type=str, required=True,
                        help='(str) : The words')
    parser.add_argument('-o', '--outdir', nargs='?', const=1, type=str, required=False, default="../data/",
                        help="(str) : saves in this directory - default is '../data/'")
    parser.add_argument('-s', '--save', nargs='?', type=bool, required=False, default=True,
                        help='(bool) : saves the results - default is False')
    
    
    
    args = parser.parse_args()
    
    if (args.outdir[-1]!='/'):
        args.outdir += '/'
    
    print("\n\n making [(uid, cap, [(tstamp, tweet),...]),...] file  " \
           + "\n  for the following arguments:\n   " \
           + str(args) + "\n")
    
    import datetime
    print("\n\n Start time : " + str(datetime.datetime.now()) + " EST \n\n")
    
    tweets = make_uid_bom_tweets_file(words=args.words, 
                                      save_tweets=args.save, 
                                      outdir=args.outdir)
    
    print("\n\n End time : " + str(datetime.datetime.now()) + " EST \n\n") 
    
    
    