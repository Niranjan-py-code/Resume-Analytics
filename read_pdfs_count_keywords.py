# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 16:13:17 2019

@author: Niranjan
"""

#from collections import Counter
#from IPython.display import clear_output
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
#from textblob import TextBlob
import io
#import math
#import numpy as np
import pandas as pd
#import string
import os
#import re
#import PyPDF2

######## REAdS PDF FILES AND RETURNS STRING #######
def read_pdf(path):
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True): 
        interpreter.process_page(page)
    text = retstr.getvalue()
    text = " ".join(text.replace(u"\xa0", " ").strip().split())  
    fp.close()
    device.close()
    retstr.close()
    return text
########## TOKENIZATION ####################
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize

# converting the string message into lowercase and returning a list of strings(tokens).
def split_tokens(message):
  message=message.lower()
  message = str(message) #convert bytes into proper unicode
  word_tokens =word_tokenize(message)
  return word_tokens
############## STOP WORD REMOVAL ###################
from nltk.corpus import stopwords
# nltk has a list of stop words in stopwords library,(e.g- is,was,this,a..) . we are removing those words here.
def stopword_removal(message):
    stop_words = set(stopwords.words('english'))
    filtered_sentence = []
    filtered_sentence = ' '.join([word for word in message if word not in stop_words])
    return filtered_sentence
##########COUNT THE KEYWORDS OF PDFS############
# we are passing pdfs- series value of all pdf lists, series of each category
def count_keywords(pdfs, labels):
    #removing the null values from the category list.
    label = filter_keyword[labels].dropna().to_list()
#     print("Label==",label)
    c=0
    for key in label:
      c+=pdfs.count(key.strip())
    return c
###################################################

# File path where all pdf files present.
path = 'C:\\Users\\Niranjan\\Documents\\CHECK_ml\\resume_shortlist_Proj\\pdf_info'
#path = 'C:\\Users\\Niranjan\\Documents\\CHECK_ml\\SpyderProj\\docs'
# path = 'resumeData'
filter_keyword = pd.read_csv(path+"\\keywords\\techkeyword.csv")
files = []
filename = []
# r=root, d=directories, f = files
# OS.walk() generate the file names in a directory tree by walking the tree either top-down or bottom-up.
# it yeilds three values r=root directory, d=subdirectory and f = files
for r, d, f in os.walk(path):
    for file in f:
        if '.pdf' in file:
            filename.append(file.replace('.pdf', ''))
            files.append(os.path.join(r, file))

pdflist = []
for f in files:
    rawText =  read_pdf(os.path.join(r, f))
#   csvText = " ".join(rawText.split())
    pdflist.append(rawText)
pdfseries = pd.Series(pdflist)
#print(pdfseries)

#pdfseries is a Series, apply method will pass one by one element of the series to the method and returns another series of outputs.
pdfseries_tokens = pdfseries.apply(lambda pdfseries: split_tokens(pdfseries))
# stop word removal
pdfseries = pdfseries_tokens.apply(lambda pdfseries_tokens: stopword_removal(pdfseries_tokens))
# Tokenizing the series.
pdfseries_tokens = pdfseries.apply(lambda pdfseries: split_tokens(pdfseries))
#converting the filter_keyword columns to a list, to pass one by one column to count_keywords()
tech_cols = filter_keyword.columns.to_list()
# Creating an empty dataframe with column names of filter_keyword dataframe.
pdfseries_df = pd.DataFrame(columns = tech_cols)
# Creating list of columns of pdfseries_df dataframe after counting the category frequency.
resumeId = []
for i in tech_cols:
  pdfseries_df[i] =pdfseries_tokens.apply(count_keywords, args=(i,))
# Adding another column to dataframe resume -  assigning pdfseries Series.
print("=========",len(pdfseries))
#resumeId = ["candidate"+str(no+1) for no in range(len(pdfseries))]
pdfseries_df['CandidateName']=filename
#pdfseries_df['resumes']=pdfseries
print(pdfseries_df)
pdfseries_df.to_csv("labelCountPDFresume.csv")

