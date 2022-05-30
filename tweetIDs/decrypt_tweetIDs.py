#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 30 00:17:58 2022

Descryption: Decrypting the tweet IDs

@author: Amirhossein Farzam
"""

import os
import sys
import argparse
import datetime
import rsa
from cryptography.fernet import Fernet
import json


path = os.getcwd() + "/"



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
        
    
    
#%% 


#%%


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    
    parser.add_argument('-i', '--input', nargs=1, type=str, required=False, default="encrypted_tweetIDs_byTopic.json",
                        help="(str) : input file including a dictionary of encrypted tweet IDs by topic" \
                             + " --- default is './encrypted_tweetIDs_byTopic.json'")
    parser.add_argument('-o', '--output', nargs=1, type=str, required=False, default="tweetIDs_byTopic.json",
                        help="(str) : output file to store a dictionary of tweet IDs by topic" \
                             + " --- default is './tweetIDs_byTopic.json'")
    parser.add_argument('-t', '--topics', nargs='+', type=str, required=False,
                        help='(str) : topics to decrypt tweet IDs for' \
                             + '--- if not provided, it will decrypt for all topics, i.e. all keys in the input file')
    parser.add_argument('-k', '--key', nargs=1, type=str, required=False, default="./enc_key",
                        help="(str) : the file containing the encrypted symmetric key for decryption"\
                             + " - default is './enc_key'")
    parser.add_argument('-p', '--priv_key', nargs=1, type=str, required=False, default="./enc_key",
                        help="(str) : the file containing the private key for decrypted the encrypted symmetric key" \
                             + " - default is './private_key'")


    args = parser.parse_args()
    print("\n\n Decrypting and saving tweet IDs ... " \
           + "\n  for the following arguments:\n   " \
           + str(args) + "\n")
    
    print("\n\n Start time : " + str(datetime.datetime.now()) + " EST \n\n")
    
    
    
    
#%% --------- reloading the keys for decryption ---------
    
    with open(args.priv_key[0], 'rb+') as fin:
        fcontent = fin.read()
        privateKey = rsa.PrivateKey.load_pkcs1(fcontent)
        print("\nRSA private key loaded from %s\n" % args.priv_key[0])

    
    with open(args.key[0], 'rb+') as fin:
        enc_fernetKey = fin.read()
        print("\nEncrypted fernet key loaded from %s\n" % args.key[0])
        
    fernetKey = rsa.decrypt(enc_fernetKey, privateKey)
    fernet = Fernet(fernetKey)
    
    
    
#%% --------- loading the dictionary, decrypting, and exporting ---------
    
    with open(args.input[0], 'r') as fin:
        enc_tweetIDs = json.load(fin)
        print("\nDictionary of encrypted tweet IDs by topics loaded from %s\n" % args.input[0])
    
    if (args.topics == None):
        topics = list(enc_tweetIDs.keys())
    else:
        topics = args.topics
        
    print("\nDecrypting for topic...\n")
    topics_tweetIDs = dict()
    for topic_ind, topic in enumerate(topics):
        tweet_IDs = enc_tweetIDs[topic]
        topics_tweetIDs[topic] = [fernet.decrypt(tid.encode('utf-8')).decode()
                                  for tid in tweet_IDs]
        
        progressBar(topic_ind+1, len(topics), 
                    optional_message="  " + topic + "  ")
    
    
    #% ---
    
    with open(args.output[0], 'w') as fout:
        json.dump(topics_tweetIDs, fout)
        print("\nDictionary of tweet IDs by topics saved in %s\n" % args.output[0])




#%% ---------













    