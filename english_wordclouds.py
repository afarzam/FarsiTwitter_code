#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 01:46:01 2020

Description: Content analysis

@author: Amirhossein Farzam
"""

from __future__ import unicode_literals

import os
import sys
import numpy as np
import json
import matplotlib.pyplot as plt
import collections
import operator

path = os.getcwd() + "/"



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
        


#%% --------------- main helper functions ----------------


# returns False if it has non-English characters
def isEnglish(s):
  return s.isascii()


# copied from https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
def remove_emojis(data):
    import re
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", re.UNICODE)
    return re.sub(emoj, '', data)


#
# Requires: fa_words (list of Farsi words)
#           custom_fa2en (dictrionary): dictionary of manually translated words
#
# Returns: translated English word_list, cleaned up if clean_up==True
#
def translate_toEN(fa_words, 
                   custom_fa2en=[],
                   clean_up=True, 
                   use_stemmer=True, 
                   only_english=True,
                   only_ascii=True,
                   remove_stopwords=True):
    from googletrans import Translator
    translator = Translator()
    
    if (len(custom_fa2en)>0):
        en_words = []
        for w_ind, w in enumerate(fa_words):
            if w in custom_fa2en:
                en_words.append(custom_fa2en[w])
            else:
                en_words.append(translator.translate(w, dest="en", src="fa").text)
    else:
        en_words = [translator.translate(w, dest="en", src="fa").text \
                    for w in fa_words]
    
    if (clean_up):
        if (remove_stopwords or only_english):
            import nltk
            nltk.download('words')
            
        # remove invalid words
        if (only_english):
            from nltk.corpus import words
            en_words = [w if w in words.words()
                        else "!" \
                        for w in en_words]
        
        # remove words with non-asciii characters
        if (only_ascii):
            import re
            en_words = [re.sub(r'[^\w]', ' ', w) if w.isascii()
                        else "!" \
                        for w in en_words]
        
        # map to english stem
        if (use_stemmer):
            from nltk.stem.snowball import SnowballStemmer
            stemmer = SnowballStemmer("english")
            en_words = [stemmer.stem(w) for w in en_words]
        
        # remove english stopwords one more time
        if (remove_stopwords):
            from nltk.corpus import stopwords as nltk_stopwords
            stopwords = nltk_stopwords.words('english')
            en_words = [w if w not in stopwords
                        else "!" \
                        for w in en_words]
        
        # remove words with less than 2 characters
        en_words = [w if len(w)>1
                    else "!" \
                    for w in en_words]
        
    
    return en_words
    


#
# Requires: sents (list of strings)
#           toEnglish (bool): if True, translate words to English
#
# Returns: tokenized and mapped to roots words list (a multiset)
#
def get_words_list(sents, 
                   toEnglish=False,
                   use_stemmer=True):
    import hazm
    from farsi_tools import stop_words, replace_farsi_digits_with_ascii
    normalizer = hazm.Normalizer()
    stemmer = hazm.Stemmer()
    #lemmatizer = hazm.Lemmatizer() # This makes English translations worse
    stopwords_fa = stop_words() + hazm.stopwords_list()
    
    from string import digits
    remove_digits = str.maketrans('', '', digits)
    
    
    
    word_list = []
    for sent_ind, sent in enumerate(sents):
        sent = normalizer.normalize(sent)
        sent_words = hazm.word_tokenize(sent)
        # remove numbers and remove emojis
        sent_words = [replace_farsi_digits_with_ascii(remove_emojis(w)).translate(remove_digits)
                      for w in sent_words]
        # map to the root
        if (use_stemmer):
            sent_words = [stemmer.stem(w).split('\u200c')[0] \
                          for w in sent_words]
        # remove stopwords 
        sent_words = [w for w in sent_words if w not in stopwords_fa]
        # remove words with less than 2 characters
        sent_words = [w for w in sent_words if len(w)>1]
        

        word_list += sent_words
    
        if (sent_ind % 50 == 0):
            progressBar(sent_ind, len(sents),
                        optional_message="Preparing words list...")
    
    if (toEnglish):
        translate_toEN(word_list, clean_up=True)

    return word_list



def plot_wordclouds(strongDiffs, toEnglish=True):
    if (toEnglish):
        from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
    else:
        import arabic_reshaper
        from bidi.algorithm import get_display
        from wordcloud_fa import WordCloudFa
        WordCloud = WordCloudFa
        
    
    aNOTc_freqs = strongDiffs[('a', 'c')]
    cNOTa_freqs = strongDiffs[('c', 'a')]
    
    
    fig, axs = plt.subplots(1, 2)
    
    font_path = "/Library/Fonts/DejaVuSansCondensed.ttf"
    if (len(aNOTc_freqs)>0):
        word_cloud0 = WordCloud(background_color="white", font_path=font_path,
                                max_font_size=50, max_words=100)
        word_cloud0 = word_cloud0.generate_from_frequencies(aNOTc_freqs)
        axs[0].imshow(word_cloud0, interpolation='bilinear')
    
    if (len(cNOTa_freqs)>0):
        word_cloud1 = WordCloud(background_color="white", font_path=font_path,
                                max_font_size=50, max_words=100)
        word_cloud1 = word_cloud1.generate_from_frequencies(cNOTa_freqs)
        axs[1].imshow(word_cloud1, interpolation='bilinear')
    
    
    #axs[0].set_title('In A but not C')
    #axs[1].set_title('In C but not A')
    
    for ax in axs:
        ax.axis("off")
        
    fig.tight_layout()
    
    return fig, axs




#%% ------------- main driver ----------------

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()


    parser.add_argument('-w', '--words', nargs='+', type=str, required=True,# default=False,
                        help='(str) : Words to analyze')
    parser.add_argument('-d', '--save_data', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : Save the processed data - default is False')
    parser.add_argument('-l', '--load_data', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : load the data from pre-processed data - default is False')
    parser.add_argument('-p', '--save_plot', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : Save the plot or not - default is False')
    parser.add_argument('-t', '--translate', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : translate to English or Not - default is True')
    parser.add_argument('-o', '--out_dir', nargs='?', const=True, type=str, required=False, default="../figures/content/strongDiffs/",
                        help='(bool) : output directory - default is "../figures/content/strongDiffs/"')
    parser.add_argument('-c', '--custom_dict', nargs='?', const=True, type=bool, required=False, default=False,
                        help='(bool) : use custom fa2en dictionary - default is False')


    args = parser.parse_args()
    print("\n\n Word clouds " \
           + "\n  for the following arguments:\n   " \
           + str(args) + "\n")

    import datetime
    print("\n\n Start time : " + str(datetime.datetime.now()) + " EST \n\n")


    #%% -------- prepare wordFreq_abc ------------------
    
    load_wordFreq_abc = args.load_data
    save_data = args.save_data
    words = args.words
    minCAP_a = 0.059 
    minCAP_b = 0.01
    
    #%%
    
    for word in words:
        if (load_wordFreq_abc):
            fname_wordFreq = path + "../data/wordcloud_data/" + word + "_wordFreq_abc.json"
            with open(fname_wordFreq, 'r') as fin:
                wordFreq = json.load(fin)
            print("Loaded wordFreq_abc for topic %s from %s" % (word, fname_wordFreq))
            
            fname_strongDiffs_fa = path + "../data/wordcloud_data/" + word + "_strongDiffs_abc_fa.json"
            with open(fname_strongDiffs_fa, 'r') as fin:
                strongDiffs = json.load(fin)
            print("Loaded strongDiffs_fa for topic %s from %s" % (word, fname_strongDiffs_fa))
            strongDiffs[('a', 'c')] = strongDiffs.pop('a_c')
            strongDiffs[('c', 'a')] = strongDiffs.pop('c_a')
            
            if(False):
                fa_strongDiffs = strongDiffs
                fname_strongDiffs = path + "../data/wordcloud_data/" + word + "_strongDiffs_abc_en.json"
                with open(fname_strongDiffs, 'r') as fin:
                    strongDiffs = json.load(fin)
                strongDiffs[('a', 'c')] = strongDiffs.pop('a_c')
                strongDiffs[('c', 'a')] = strongDiffs.pop('c_a')
                print("Loaded strongDiffs_en for topic %s from %s" % (word, fname_strongDiffs))
            
        else: # i.e. make wordFreq
            fname = "../data/all_uid_bomOrNaN_time_tweets/" + word + "_uid_bomOrNaN_time_tweets.json"
            with open(fname, 'r') as fin:
                uid_bom_tts = json.load(fin)
            
            uid_count = len(set([uid for (uid, cap, tts) in uid_bom_tts]))
            tweet_count = sum([len(tts) for (uid, cap, tts) in uid_bom_tts])
            
            
            sents_a = [tweet for (uid, cap, tts) in uid_bom_tts\
                       for (tstamp, tweet) in tts\
                           if (cap > minCAP_a)]
            sents_b = [tweet for (uid, cap, tts) in uid_bom_tts\
                       for (tstamp, tweet) in tts\
                           if ((cap > minCAP_b) and (cap <= minCAP_a))]
            sents_c = [tweet for (uid, cap, tts) in uid_bom_tts\
                       for (tstamp, tweet) in tts\
                           if (cap <= minCAP_b)]
                
            words_a = get_words_list(sents_a, toEnglish=False, use_stemmer=False)
            words_b = get_words_list(sents_b, toEnglish=False, use_stemmer=False)
            words_c = get_words_list(sents_c, toEnglish=False, use_stemmer=False)
            
            wordFreq_abc = {'a': dict(collections.Counter(words_a)), 
                            'b': dict(collections.Counter(words_b)), 
                            'c': dict(collections.Counter(words_c))}
            
            if (save_data):
                fname_wordFreq = path + "../data/wordcloud_data/" + word + "_wordFreq_abc.json"
                with open(fname_wordFreq, 'w') as fout:
                    json.dump(wordFreq_abc,fout)
                print("Saved wordFreq_abc for topic %s in %s" % (word, fname_wordFreq))
            else:
                print("Prepared wordFreq_abc for topic %s" % word)
        
        
        
            #%% -------- prepare top5perc_abc and top10perc_abc ------------------
            
            top5perc_abc = dict()
            top10perc_abc = dict()
            for group in wordFreq_abc:
                group_freq = wordFreq_abc[group]
                group_freq = list(group_freq.items())
                group_freq.sort(key = operator.itemgetter(1), reverse = True)
                
                top5perc_abc[group] =  dict(group_freq[0:int(np.ceil(len(group_freq)*.05))])
                top10perc_abc[group] =  dict(group_freq[0:int(np.ceil(len(group_freq)*.1))])
                
                    
            
            
            #%% -------- prepare strong_diffs ------------------
            
            group_pairs = [('a', 'c'), ('c', 'a')]
            
            strongDiffs = {gp: {w:top5perc_abc[gp[0]][w] \
                                for w in set(top5perc_abc[gp[0]]).difference(set(top10perc_abc[gp[1]]))} \
                           for gp in group_pairs} 
                
            if (save_data):
                strongDiffs['a_c'] = strongDiffs.pop(('a', 'c'))
                strongDiffs['c_a'] = strongDiffs.pop(('c', 'a'))
                fname_strongDiffs_fa = path + "../data/wordcloud_data/" + word + "_strongDiffs_abc_fa.json"
                with open(fname_strongDiffs_fa, 'w') as fout:
                    json.dump(strongDiffs,fout)
                print("Saved Farsi strongDiffs for topic %s in %s" % (word, fname_strongDiffs_fa))
                strongDiffs[('a', 'c')] = strongDiffs.pop('a_c')
                strongDiffs[('c', 'a')] = strongDiffs.pop('c_a')
            else:
                print("Prepared Farsi strongDiffs for topic %s" % word)
                
            
                
        #%% -------- Translate to English ------------------
        toEnglish = args.translate
        if (toEnglish):
            if (args.custom_dict):
                print('\n Using custom dictionary:\n')
                fname = path + "../data/wordcloud_data/custom_fa2en.json"
                with open(fname, 'r') as fin:
                    fa2en = json.load(fin)
                print("\n Custom fa2en dictionary loaded from %s \n" % fname)
            else:
                fa2en = []
                
            fa_strongDiffs = strongDiffs
            
            for gp in fa_strongDiffs: 
                fa_words = list(fa_strongDiffs[gp].keys())
                en_words = translate_toEN(fa_words, 
                                          custom_fa2en=fa2en,
                                          clean_up=True, 
                                          use_stemmer=False, 
                                          only_english=False,
                                          only_ascii=True,
                                          remove_stopwords=False)
                fa2en_dict = {fa_words[w_ind]: en_words[w_ind] \
                              for w_ind in range(len(fa_words))}
                
                strongDiffs[gp] = {fa2en_dict[w]: fa_strongDiffs[gp][w] \
                                   for w in fa_strongDiffs[gp]}
                strongDiffs[gp].pop('!', None) # remove the invalid ones
                
                
            if (save_data):
                strongDiffs['a_c'] = strongDiffs.pop(('a', 'c'))
                strongDiffs['c_a'] = strongDiffs.pop(('c', 'a'))
                fname_strongDiffs = path + "../data/wordcloud_data/" + word + "_strongDiffs_abc_en.json"
                with open(fname_strongDiffs, 'w') as fout:
                    json.dump(strongDiffs,fout)
                print("Saved English strongDiffs for topic %s in %s" % (word, fname_strongDiffs))
                strongDiffs[('a', 'c')] = strongDiffs.pop('a_c')
                strongDiffs[('c', 'a')] = strongDiffs.pop('c_a')
            else:
                print("Prepared English strongDiffs for topic %s" % word)
                    
            
            
            
        #%% --------- Plot ----------
        
        fig, axs = plot_wordclouds(strongDiffs, toEnglish=toEnglish)
        
        
        #%% ---
           
        if (args.save_plot):
            figName = path + args.out_dir
            figName += word + "_English_wordClouds_strongDiffs_AC"
            if (not toEnglish):
                figName += "_fa"
            figName += ".png"
            
            fig.savefig(figName, dpi=500, facecolor='w', edgecolor='w',
                        orientation='portrait', format='png',
                        transparent=True,
                        bbox_inches='tight', pad_inches=0.1)
            
            print("Plot saved in %s" % figName)
        else:
            plt.show()
            
        
        
            
        #%%% ----
 
        
        
        
        
        
        
        
        
        
        
        
