
# coding: utf-8

# In[1]:

from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
from lxml import etree
import time
import re
from fake_useragent import UserAgent

import sys


import requests
from lxml import etree

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# In[2]:

class proxypool:
    proxy_html = ['http://free-proxy-list.net', 
                  'http://www.gatherproxy.com/proxylist/country/?c=', 
                  'https://www.us-proxy.org/',  
                  'http://www.proxylisty.com/country/Taiwan-ip-list']
    proxy_test = ['http://www.google.com.tw', 'http://www.google.co.jp', 'http://www.yahoo.com', 'http://findbiz.nat.gov.tw/fts/query/QueryBar/queryInit.do']
    country_asia = ['Taiwan', 'Japan', 'Singapore', 'Korea']
    country_eu = ['Ukraine', 'Russia', 'France', 'Germany']
    country_na = ['United%20States', 'Canada']
    country_world = country_asia + country_eu + country_na
    proxy_list = list()
    proxy_set = set()
    proxy_set_max = 15
    #proxy_re = re.compile('[0-9]+(?:\.[0-9]+){3}:\d{2,4}')
    
    def __init__(self, path_phantomjs = '/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs'):
        self.session = None
        self.response = None
        self.path_phantomjs = path_phantomjs
        
    def new_session(self):
        if self.session is not None:
            self.session.close()
        
        self.session = requests.Session()
    def reset_proxy(self):
        proxypool.proxy_set = set()
        
    def proxy_set_to_proxy_list(list):
        proxypool.proxy_list = [{'http':p} for p in proxypool.proxy_set]
    
    def get_proxy1(self):
        self.new_session()
        self.response = self.session.get(proxypool.proxy_html[0])
        selector = etree.HTML(self.response.content)
        trs = selector.xpath('//*[@id="proxylisttable"]/tbody/tr')
        for tr in trs:
            tds = tr.xpath('./td')
            ip = tds[0].text
            port = tds[1].text
            proxypool.proxy_set.add(ip+':'+port)


    def get_proxy2(self, PhantomJs_executable_path='/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs', country ='Taiwan'):
        def clean_text(text):
            import re
            if text is None:
                text = ''
                return text
        
            text = text.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
            text = re.sub(r'[\t\n\r]', r'', text)
            return text
        # step 1. use PhantomJs to get .js rendered content
        browser = webdriver.PhantomJS(executable_path = PhantomJs_executable_path)
        browser.get(proxypool.proxy_html[1]+country)

        # step 2. click "Show Full List" button to generate full proxies list
        element = WebDriverWait(browser, 1).until(
            EC.presence_of_element_located((By.XPATH, '//div[@id="body"]/form/p/input[@type="submit" and @class="button"]')))
        element.click()
        
        # step 3. generate selector
        selector = etree.HTML(browser.page_source)

        # step 4. resolve how many pages
        pages = selector.xpath('//div[@id="body"]/form[@id="psbform"]/div[@class="pagenavi"]/a')

        # setp 5. resolve trs for first page
        trs = selector.xpath('//div[@class="proxy-list"]/table[@id="tblproxy"]/tbody/tr')  
        for tr in trs[2:]:
            tds = tr.xpath('./td')
            ip = "" if not tds[1].xpath('./text()') else tds[1].xpath('./text()')[0]
            port = "" if not tds[2].xpath('./text()') else tds[2].xpath('./text()')[0]
            proxypool.proxy_set.add(ip+':'+port)
        #print('page 0 done')

    
        # step 6. resolve trs for the rest pages
        for i, page in enumerate(pages, 2):
            # step 6-1. click nextpage's link
            element = WebDriverWait(browser, 1).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="body"]/form[@id="psbform"]/div[@class="pagenavi"]/a[@href="#{}"]'.format(i))))
            element.click()
            
            # step 6-2. resolve trs for ith page
            selector = etree.HTML(browser.page_source)
            trs = selector.xpath('//div[@class="proxy-list"]/table[@id="tblproxy"]/tbody/tr')
            for tr in trs[2:]:
                tds = tr.xpath('./td')
                ip = "" if not tds[1].xpath('./text()') else tds[1].xpath('./text()')[0]
                port = "" if not tds[2].xpath('./text()') else tds[2].xpath('./text()')[0]
                proxypool.proxy_set.add(ip+':'+port)
                if len(proxypool.proxy_set) > proxypool.proxy_set_max:
                    return
            time.sleep(5)
            #print('page', i,'done')
    
    def get_proxy3(self):
        self.new_session()
        self.response = self.session.get(proxypool.proxy_html[2])
        selector = etree.HTML(self.response.content)
        trs = selector.xpath('//*[@id="proxylisttable"]/tbody/tr')
        for tr in trs:
            tds = tr.xpath('./td')
            ip = tds[0].text
            port = tds[1].text
            proxypool.proxy_set.add(ip+':'+port)

    
    def get_proxy4(self):
        self.new_session()
        self.response = self.session.get(proxypool.proxy_html[3])
        selector = etree.HTML(self.response.content)
        trs = selector.xpath('//*[@id="content"]/table[1]/tr')
        for tr in trs[2:-2]:
            tds = tr.xpath('./td')
            if tds:
                ip = tds[0].text
                port = tds[1].xpath('./a')[0].text
                #print(ip, port)
                proxypool.proxy_set.add(ip+':'+port)
        
        
        return

    def world_proxy(self):
        self.get_proxy1()
        for c in proxypool.country_world:
            self.get_proxy2(PhantomJs_executable_path=self.path_phantomjs, country = c)
            
        self.get_proxy3()
        self.get_proxy4()
    
    def eu_proxy(self):
        for c in proxypool.country_eu:
            self.get_proxy2(PhantomJs_executable_path=self.path_phantomjs, country = c)

    def na_proxy(self):
        for c in proxypool.country_na:
            self.get_proxy2(PhantomJs_executable_path=self.path_phantomjs, country = c)
        self.get_proxy3()
        
    def taiwan_proxy(self):
        self.reset_proxy()
        self.get_proxy2(PhantomJs_executable_path=self.path_phantomjs, country ='Taiwan')
        self.get_proxy4()
    
    def asia_proxy(self):
        for c in proxypool.country_asia:
            self.get_proxy2(PhantomJs_executable_path=self.path_phantomjs, country = c)
        self.get_proxy4()
        
    def filter_proxy(self):
        bad_proxy_set = set()
        for p in proxypool.proxy_set:
            connection_score = list()
            for t in proxypool.proxy_test:
                self.new_session()
                try:
                    self.response = self.session.get(t, timeout=30, proxies={'http':p})
                    print('checking', p, t, self.response)
                    connection_score.append(1 if self.response.status_code == 200 else 0)

                #except requests.exceptions.ProxyError as err:
                #    print(p, t, err.__doc__)
                #    connection_score.append(0)
                #    break
                except Exception as err:
                    #print(p, t, err.__doc__)
                    connection_score.append(0)
                    break

              
            #print(connection_score)
            if sum(connection_score) < 4:
                bad_proxy_set.add(p)
        else:
            proxypool.proxy_set = proxypool.proxy_set - bad_proxy_set
            self.proxy_set_to_proxy_list()
                
        
    def check_this_proxy(self, p):
        connection_score = list()
        for t in proxypool.proxy_test:
            self.new_session()
            try:
                self.response = self.session.get(t, timeout=30, proxies={'http':p})
                print('checking', p, t, self.response)
                connection_score.append(1 if self.response.status_code == 200 else 0)
            except Exception as err:
                connection_score.append(0)
                break

               
        if sum(connection_score) < 4:
            return False
        else:
            return True
        
    def random_choice_one_proxy(self):
        p = self.proxy_set.pop()
        while not self.check_this_proxy(p):
            p = self.proxy_set.pop()

        return p if p is not None else None


# In[ ]:



