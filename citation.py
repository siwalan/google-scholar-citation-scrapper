#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


# In[2]:


user_agent = 'Your User Agent'


# In[3]:


columns = ['Publication','Writer_Data','Journal_Data','Link', 'Citation_2019','Citation_2018','Citation_2017','Citation_2016','Done']
citations = pd.DataFrame(columns= columns)


# In[4]:


class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class CaptchaError(Error):
    def __init__(self, message):
        self.message = message

class RequestError(Error):
    def __init__(self, message):
        self.message = message

def error_catcher(r, soup):
    if r.status_code != 200:
        raise RequestError("Request Error {}".format(r.status_code))
    is_captcha_on_page = soup.find("input", id="recaptcha-token") is not None
    if (is_captcha_on_page == True):
        raise CaptchaError("Captcha Error")
    return is_captcha_on_page

def scholar_get_publications(start = 0, scholar_id ="s7Qdk00AAAAJ"):
    current = int(start)
    payload = {'cstart':start, 'pagesize':'100','hl':'en', 'user':scholar_id}
    r = requests.post('https://scholar.google.com/citations?', params=payload, headers = {'User-agent': user_agent})
    r_soup =  BeautifulSoup(r.text, 'html.parser')  
    
    error_catcher(r, r_soup)

    pubs_result = (r_soup.find_all('td', class_="gsc_a_t"))
    
    while is_there_more(r_soup, current, scholar_id):
        current = current + 100
        pubs_result = pubs_result + scholar_get_publications(current, scholar_id)
    return pubs_result

def scholar_get_publications_raw (start = 0, scholar_id ="s7Qdk00AAAAJ"):
    payload = {'cstart':start, 'pagesize':'100','hl':'en', 'user':scholar_id}
    r = requests.post('https://scholar.google.com/citations?', params=payload, headers = {'User-agent': user_agent})
    r_soup =  BeautifulSoup(r.text, 'html.parser')
    return r_soup

def is_there_more(r_soup, current = 0, scholar_id ="s7Qdk00AAAAJ"):
    number_of_cit = str(r_soup.find("span", {"id": "gsc_a_nn"}))
    res = number_of_cit.partition("–")[2] 
    number_of_cit = number_of_cit[number_of_cit.find("–"):]
    
    current = int(current)

    if (number_of_cit.find("</span>") > 0):
        number_of_cit = number_of_cit[:number_of_cit.find("</span>")]
        number_of_cit = int(number_of_cit[1:])
    else:
        number_of_cit = 0
        
    if (number_of_cit >= (current+100)):
        return True
    return False

def get_citation_data_from_publications(publications):
    columns = ['Publikasi','Data_Penulis','Data_Jurnal','Link', 'Sitasi_2019','Sitasi_2018','Sitasi_2017','Sitasi_2016','Terproses']
    dataframe = pd.DataFrame(columns= columns)
    for pub in publications:
        # Get the Citation Link
        a_class_attrs = pub.find('a').attrs
        link = a_class_attrs['data-href']
        link = link.split("citation_for_view=",1)[1] 
        Judul = pub.find('a').get_text()
        divs = (pub.find_all('div', class_="gs_gray"))
        iterator_i = 0
        for div in divs:
            # This Line will always iterate maximum two times
            text = div.get_text().splitlines()
            if (iterator_i == 0):
                author = text
            else:
                journal_name = text
            iterator_i = 1
        input_panda = {
            'Publication': Judul,
            'Writer_Data': author,
            'Journal_Data': journal_name,
            'Link': link
        }
        dataframe = dataframe.append(input_panda, ignore_index=True)
    return dataframe

def get_citation_data_year(citation_id='s7Qdk00AAAAJ:u5HHmVD_uO8C'):
    time.sleep(0.01)
    payload = {'citation_for_view':citation_id, 'view_op':"view_citation"}
    r = requests.post('https://scholar.google.com/citations?', params=payload,  headers = {'User-agent': user_agent})
    r_soup =  BeautifulSoup(r.text, 'html.parser')
    
    error_catcher(r, r_soup)
    cite_results = (r_soup.find_all('a', class_="gsc_vcd_g_a"))
    citation_data = {}

    for cite_result in cite_results:
            a_class_attrs = cite_result.attrs
            citation_year = a_class_attrs['href']
            citation_year = citation_year.split("yhi=",1)[1]
            citation_number = cite_result.get_text()
            citation_data.update({citation_year : citation_number})
    return citation_data


# In[8]:


scholars= pd.read_csv("dosen.csv", delimiter=',') # Format File - Nama Dosen dan ID Google Scholar


# In[9]:


for index, row in scholars.iterrows():
    scholar_id = row['Scholar-id']
    citations = citations.append(get_citation_data_from_publications(scholar_get_publications(0,scholar_id)), ignore_index = True)


# In[6]:


citations = citations.append(get_citation_data_from_publications(scholar_get_publications(0,"Cpl5C2UAAAAJ")), ignore_index = True)


# In[ ]:


for index, row in citations.iterrows():
    if (row['Done'] != True):
        print(index)
        row['Citation_2016'] = 0
        row['Citation_2017'] = 0
        row['Citation_2018'] = 0
        row['Citation_2019'] = 0
        citation_data_year = get_citation_data_year(row['Link'])
        if (citation_data_year.get('2019') != None):
            row['Citation_2019'] = citation_data_year.get("2019")
        if (citation_data_year.get('2018') != None):
            row['Citation_2018'] = citation_data_year.get("2018")
        if (citation_data_year.get('2017') != None):
            row['Citation_2017'] = citation_data_year.get("2017")
        if (citation_data_year.get('2016') != None):
            row['Citation_2016'] = citation_data_year.get("2016")
        row['Done'] = True


# In[12]:


citations.to_excel("data.xlsx")

