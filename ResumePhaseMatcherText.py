# -*- coding: utf-8 -*-
"""
Created on Fri Aug  9 16:12:28 2019

@author: Niranjan
"""

from collections import Counter
from spacy.matcher import PhraseMatcher
import spacy
#import io
#import math
import numpy as np
import pandas as pd
#import string
import os
import re
from io import StringIO
import xlsxwriter
#import PyPDF2
import random
import sys
from chardet import detect


# get file encoding type and returns the encoding type
def get_encoding_type(file):
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']
######## REAdS TEXT FILES AND RETURNS STRING #######
def read_textfile(textfile):
#    print("Text path==", textfile)
    # trying to open a file, which does not exist
#    print(get_encoding_type(textfile))
    try:
        with open(textfile,'r',encoding=get_encoding_type(textfile), errors='ignore') as file:
            text = file.read()
        text = " ".join(text.replace(u"\xa0", " ").strip().split())  #Tabs and line breaks replace with a space
        text = re.sub(r'[^\w\s]',' ',text)
        return text
    except FileNotFoundError:
#        print(str(textfile.split('\\')[-1])+" File does not exist")
        sys.exit(str(textfile.split('\\')[-1]).replace('.txt','')+" File does not exist")
    except Exception as e:
        print("Error Description")
        print(str(textfile.split('\\')[-1]).replace('.txt',''))
        print("-----------------------------------")
        sys.exit(e)
        
############### CREATE A EXCEL FILE OF THE RESULT #####################
# Creating an excel file using "xlsxwriter" package 
# Creates a workbook and adding worksheets to it.
# Enter candidate resume match details.        
def create_excel(data):
    workbook = xlsxwriter.Workbook('PhaseMatchReslut.xlsx') 
    worksheet = workbook.add_worksheet("match result") 
    row = 0
    col = 0
     # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    worksheet.write(row, col, "Candidate Name", bold) 
    worksheet.write(row, col + 1, "Soft Skill Match", bold) 
    worksheet.write(row, col + 2, "Hard Skill Match", bold) 
    worksheet.write(row, col + 3, "Final Skill Match", bold) 
    worksheet.write(row, col + 4, "50% match", bold) 
    row += 1
# Start from the first cell. Rows and 
# columns are zero indexed. 
    
    for name, soft, hard, total, match in (data): 
        worksheet.write(row, col, name) 
        worksheet.write(row, col + 1, soft) 
        worksheet.write(row, col + 2, hard) 
        worksheet.write(row, col + 3, total) 
        worksheet.write(row, col + 4, match) 
        row += 1
    workbook.close() 
        
############## PHASE MATCH USING SPACY ###############
# 
def PhaseMatch(text_file, soft_skills, hard_skills):
    nlp = spacy.blank('en') # If you need a blank language, you can use the new function spacy.blank() or import the class explicitly, e.g. from spacy.lang.en import English.
    nlp.vocab.lex_attr_getters = {}
    soft_skill = [nlp(text) for text in soft_skills] # Converting list of string values to list of nlp texts.
    hard_skill = [nlp(text) for text in hard_skills]
    matcher = PhraseMatcher(nlp.vocab)
    matcher.add('SOFT SKILLS', None, *soft_skill)
    matcher.add('TECH SKILLS', None, *hard_skill)
    match = []
    text_file = text_file.lower()
    text_file = re.sub('\W+',' ', text_file)
    doc = nlp(text_file)#-------------------------------------------------------------Job desc data
    matches = matcher(doc)
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]  # get the unicode ID, i.e. 'COLOR'
        span = doc[start : end]  # get the matched slice of the doc
        match.append((rule_id, span.text))
    match_df = "\n".join(f'{i[0]}-{i[1]} ({j})' for i,j in Counter(match).items())
    return [match,match_df]

############# CREATES A VIEW FOR THE RESPONSE ###################
def findMatches(pdf_file, candidate_name):
    pdf_file = pdf_file.lower()
    candidate_name = candidate_name.title()
    score_data = list()
    score_data.append(candidate_name)
    resmatch, resmatch_df = PhaseMatch(pdf_file, jd_soft_skill_list, jd_hard_skill_list)
    
    jd_df = pd.read_csv(StringIO(jdmatch_df),names = ['Keywords_List'])
    jd_df1 = pd.DataFrame(jd_df.Keywords_List.str.split('-',1).tolist(),columns = ['Subject','Keywords'])
    jd_df2 = pd.DataFrame(jd_df1.Keywords.str.split('(',1).tolist(),columns = ['Keywords', 'JobDescription'])
    jd_df = pd.concat([jd_df1['Subject'],jd_df2['Keywords'], jd_df2['JobDescription']], axis =1)
    jd_df['JobDescription'] = jd_df['JobDescription'].apply(lambda x: x.rstrip(")"))
    #print("----------------", jd_df3)
    
    res_df = pd.read_csv(StringIO(resmatch_df),names = ['Keywords_List'])
    res_df1 = pd.DataFrame(res_df.Keywords_List.str.split('-',1).tolist(),columns = ['re_Subject','Keyword'])
    res_df2 = pd.DataFrame(res_df1.Keyword.str.split('(',1).tolist(),columns = ['Keyword', 'Resume'])
    res_df = pd.concat([res_df1['re_Subject'],res_df2['Keyword'], res_df2['Resume']], axis =1)
    res_df['Resume'] = res_df['Resume'].apply(lambda x: x.rstrip(")"))
    
    ## Merging Job Description and Resume Dataframe into one Dataframe
    #dataf = pd.concat([name3['Candidate Name'],df3['Keyword'], jd_df3['Subject'],jd_df3['Keywords'],df3['Resume'], jd_df3['JobDescription']], axis = 1)
    dataf = pd.merge(left=jd_df, right=res_df, how='outer', left_on='Keywords', right_on='Keyword')
    #print("$$$$$$$$$$$$$$$$$$$$$", dataf)
    dataf.drop(columns=['re_Subject','Keyword'], inplace=True)
    ## Finding Matching Rate for each record
    #tab_data['Match_Rate'] = tab_data['Match_Rate'].where(tab_data['Resume'].astype(float) >= tab_data['JobDescription'].astype(float), 100, (tab_data['Resume'].astype(float)/tab_data['JobDescription'].astype(float))*100) #create new column in df1 for price diff 
    #tab_data['Match_Rate'] = (tab_data['Resume'].astype(float)/tab_data['JobDescription'].astype(float))*100
    dataf['Match Rate']=0
    dataf['Match Rate'].loc[dataf['Resume'].astype(float) > 0] = 100

#    Final_match_rate = sum(dataf['Match Rate'])/len(dataf['Match Rate'])
    
    dataf = dataf.reset_index(drop=True)
    #dataf['Resume'].fillna('No Match', inplace = True)
    dataf.rename(columns={'JobDescription':'Job Description'}, inplace=True)
    #print("##############", dataf)  
    tab_data = dataf.fillna('No Match')
    softskill_df = tab_data.loc[tab_data['Subject'] == 'SOFT SKILLS']
    techskill_df = tab_data.loc[tab_data['Subject'] == 'TECH SKILLS']
    softskill_df.drop(columns=['Subject'], inplace=True)
    techskill_df.drop(columns=['Subject'], inplace=True)

    ####################
    cid = random.randint(100,200)
    softskill_df.index = np.arange(1, len(softskill_df)+1)
    techskill_df.index = np.arange(1, len(techskill_df)+1)
    print("\n")
    print("********************************************************************")
    print("Resume Id - "+str(cid)+" / "+candidate_name)
    print("********************************************************************")
    print()
    print("==================== SOFT SKILLS ===================================\n")
    print(softskill_df if len(softskill_df) > 0 else "NO MATCH")
    print()
    #print("^^^^^^^^^^^^^===========^^^^^^^^^^^^^^^^")
    print("=================TECH SKILLS/ HARD SKILLS===========================\n")
    print(techskill_df if len(techskill_df) > 0 else "NO MATCH")
    print("====================================================================")
    ## DROP "NO MATCH" rows FROM DATA FRAME
    tab_data = dataf.dropna()
    softskilldrop_df = tab_data.loc[tab_data['Subject'] == 'SOFT SKILLS']
    techskilldrop_df = tab_data.loc[tab_data['Subject'] == 'TECH SKILLS']
    softskilldrop_df.drop(columns=['Subject'], inplace=True)
    techskilldrop_df.drop(columns=['Subject'], inplace=True)
    softskilldrop_df.index = np.arange(1, len(softskilldrop_df)+1)
    techskilldrop_df.index = np.arange(1, len(techskilldrop_df)+1)
    print()
    print("==================== SOFT SKILLS (MATCHED) =========================\n")
    print(softskilldrop_df if len(softskilldrop_df) > 0 else "NO MATCH")
    print()
    #print("^^^^^^^^^^^^^===========^^^^^^^^^^^^^^^^")
    print("=================TECH SKILLS/ HARD SKILLS (MATCHED) ================\n")
    print(techskilldrop_df if len(techskilldrop_df) > 0 else "NO MATCH")
    print("====================================================================")
#    print("FINAL MATCH RATE : ", Final_match_rate)
    tab_data.to_csv("Phrasematcher_tokens.csv")
    ######## Calculating weights FOR Soft and HARD skills ###########
    Total_soft_skills = len(softskill_df['Job Description']) if len(softskill_df['Job Description']) > 0 else 1
    resume_count_soft = len(softskill_df.loc[softskill_df['Resume'] != 'No Match'])
    soft_weightage = (25/Total_soft_skills)*resume_count_soft
    
    
    Total_hard_skills = len(techskill_df['Job Description']) if len(techskill_df['Job Description']) > 0 else 1
    resume_count_tech = len(techskill_df.loc[techskill_df['Resume'] != 'No Match'])
    hard_weightage = (75/Total_hard_skills)*resume_count_tech
    
#    weighted_avg = (resume_count_soft*25 + resume_count_tech*75) / 100
    total_weigth = soft_weightage + hard_weightage
    print("\n####################### SKILL WEIGHTAGE ##########################")
    print("\nSOFT SKILL WEIGHTAGE : {0:.2f}%".format(soft_weightage))
    print("\nTECH/HARD SKILL WEIGHTAGE : {0:.2f}%".format(hard_weightage))
    print("\nFINAL SKILL WEIGHTAGE : {0:.2f}%".format(total_weigth))
    print("\n##################################################################\n\n")
    score_data.append(round(soft_weightage,2))
    score_data.append(round(hard_weightage,2))
    score_data.append(round(total_weigth,2))
    if score_data[3] < 50:
        score_data.append("Below 50%")
    else:
        score_data.append("Above 50%")
    return score_data
    #print("WEIGHTED AVERAGE : ", weighted_avg)
##################################################################################
    
    
# File path where all pdf files present.
resumes_path    = 'phraseMatch\\Resumes'
job_desc_path   = 'phraseMatch\\JobDesc\\Job Description.txt'
skills_db_path  = "phraseMatch\\skills\\SkillsDatabase.csv"

##Reading Skill_Database.csv file to read Soft and Hard Skills
filter_keyword = pd.read_csv(skills_db_path, encoding = 'unicode_escape')
## Selecting skills from the database and Crate Series.
soft_skill_series = pd.Series(filter_keyword["Soft Skills"].dropna())
hard_skill_series = pd.Series(filter_keyword["Hard Skills"].dropna())

## Reading all Resume text files from RESUME PATH, creates resumes Dict
# r=root, d=directories, f = files
# OS.walk() generate the file names in a directory tree by walking the tree either top-down or bottom-up.
# it yeilds three values r=root directory, d=subdirectory and f = files
resumes = {}
for r, d, f in os.walk(resumes_path):
    for file in f:
        if '.txt' in file:
            filename = file.replace('.txt', '')
            rawText  =  read_textfile(os.path.join(r, file))
            resumes[filename] = rawText

##Reading JD file from the location
job_desc_file = read_textfile(job_desc_path)
##Get Soft skill and Hard Skill lists
soft_skill_list = [x.lower().strip() for x in list(soft_skill_series)]
hard_skill_list = [x.lower().strip() for x in list(hard_skill_series)]
##Matching the JD with soft skill and hard skill list
jdmatch, jdmatch_df = PhaseMatch(job_desc_file, soft_skill_list, hard_skill_list)
##Creating soft skill list and hard skill list for Resume text.
jd_soft_skill_list = [] 
jd_hard_skill_list = []
for i,j in Counter(jdmatch).items():
    if i[0] == 'SOFT SKILLS':
        jd_soft_skill_list.append(i[1]) 
    else:
        jd_hard_skill_list.append(i[1])

score_report = []
## READ ONE BY ONE RESUME FROM THE resumes DICT
for pdf_file in resumes:
    name = pdf_file
    pdf_file = resumes[name]
    score_data = findMatches(pdf_file, name)
    score_report.append(score_data)
print(score_report)
create_excel(tuple(score_report))