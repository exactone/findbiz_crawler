
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

import multiprocessing as mp


# In[32]:

class proxypool:
    proxy_html = ['http://free-proxy-list.net', 
                  'http://www.gatherproxy.com/proxylist/country/?c=', 
                  'https://www.us-proxy.org/',  
                  'http://www.proxylisty.com/country/Taiwan-ip-list']
    proxy_test = ['http://www.google.com.tw', 'http://www.google.co.jp', 'http://www.yahoo.com', 'http://findbiz.nat.gov.tw/fts/query/QueryBar/queryInit.do']
    
    country_asia1 = ['Taiwan', 'Japan', 'Singapore', 'Korea','Republic%20of%20Korea', 'Hong%20Kong']
    country_asia2 = ['Israel', 'China', 'India', 'Iran', 'Pakistan']
    country_asia3 = ['Indonesia', 'Thailand', 'Vietnam', 'Philippines', 'Cambodia', 'Malaysia']
    country_asia4 = ['Iraq', 'Nepal', 'Mongolia', 'Bangladesh', 'Kazakhstan']
    asia = [country_asia1, country_asia2, country_asia3, country_asia4]
    
    country_europe1 = ['Russia', 'France', 'Germany', 'United%20Kingdom', 'Netherlands']
    country_europe2 = ['Denmark', 'Poland', 'Ukraine', 'Italy', 'Spain']
    country_europe3 = ['Turkey','Slovak%20Republic', 'Bulgaria', 'Czech%20Republic', 'Czechia', 'Hungary']
    country_europe4 = ['Romania', 'Serbia', 'Albania', 'Republic%20of%20Moldova', 'Bosnia%20and%20Herzegovina']
    europe = [country_europe1, country_europe2, country_europe3, country_europe4]
    
    country_north_america1 = ['United%20States', 'Canada']
    north_america = [country_north_america1]
    
    country_south_america1 = ['Brazil', 'Venezuela', 'Colombia', 'Argentina', 'Mexico', 'Ecuador']
    country_south_america2 = ['Ecuador', 'Chile', 'Peru', 'Paraguay']
    south_america = [country_south_america1, country_south_america2]
    
    country_oceania1 = ['Australia']
    oceania = [country_oceania1]
    
    country_africa1 = ['South%20Africa', 'Nigeria', 'Egypt', 'Kenya']
    africa = [country_africa1]
    
    country_group1 = country_asia1 + country_europe1 + country_europe2 + country_north_america1 + country_oceania1
    country_group2 = country_asia2 + country_europe3 + country_south_america1 + country_africa1
    country_group3 = country_asia3 + country_asia4 + country_europe4
    group = [country_group1, country_group2, country_group3]
    
    country_world = country_group1 + country_group2 + country_group3
    proxy_list = list()
    proxy_set = set()
    proxy_set_max = 15
    #proxy_re = re.compile('[0-9]+(?:\.[0-9]+){3}:\d{2,4}')
    
    def __init__(self, none_freq = 2, path_phantomjs = '/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs'):
        self.session = None
        self.response = None
        self.path_phantomjs = path_phantomjs
        self.none_freq = none_freq
        self.none_freq_cnt = 0
        self.asia_i = -1
        self.europe_i = -1
        self.north_america_i = -1
        self.south_america_i = -1
        self.group_i = -1
        self.oceania_i = -1
        self.africa_i = -1
        
    def new_session(self):
        if self.session is not None:
            self.session.close()
        
        self.session = requests.Session()
        
    def reset_proxy(self):
        del proxypool.proxy_set
        del proxy_list
        proxypool.proxy_set = set()
        proxypool.proxy_list = list()
        
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


    def get_proxy2(self, country ='Taiwan'):
        #PhantomJs_executable_path='/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs'
        def clean_text(text):
            import re
            if text is None:
                text = ''
                return text
        
            text = text.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
            text = re.sub(r'[\t\n\r]', r'', text)
            return text
        # step 1. use PhantomJs to get .js rendered content
        browser = webdriver.PhantomJS(executable_path = self.path_phantomjs)
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
            if len(tds) < 2:
                continue
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
                if len(tds) < 2:
                    continue
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

    def pick_country(self, area = 'asia'):
        if area == 'asia':
            self.asia_i += 1
            return proxypool.asia[self.asia_i % len(proxypool.asia)]
        elif area == 'europe':
            self.europe_i += 1
            return proxypool.europe[self.europe_i % len(proxypool.europe)]
        elif area == 'oceania':
            self.oceania_i += 1
            return proxypool.oceania[self.oceania_i % len(proxypool.oceania)]
        elif area == 'north_america':
            self.north_america_i += 1
            return proxypool.north_america[self.north_america_i % len(proxypool.north_america)]
        elif area == 'south_america':
            self.south_america_i += 1
            return proxypool.south_america[self.south_america_i % len(proxypool.south_america)]
        elif area == 'africa':
            self.africa_i += 1
            return proxypool.africa[self.africa_i % len(proxypool.africa)]
        elif area == 'world':
            return proxypool.country_world
        elif area == 'group':
            self.group_i += 1
            return proxypool.group[self.group_i % len(proxypool.group)]
        else:
            return list()
        
    def get_proxy2_by_pick_country(self, area = 'asia'):
        for c in self.pick_country(area):
            self.get_proxy2(country = c)        
                
    def world_proxy(self):
        self.get_proxy1()
        self.get_proxy2_by_pick_country('world')
        self.get_proxy3()
        self.get_proxy4()
    
    def eu_proxy(self):
        self.get_proxy2_by_pick_country('europe')

    def na_proxy(self):
        self.get_proxy2_by_pick_country('north_america')
        self.get_proxy3()
        
    def taiwan_proxy(self):
        self.reset_proxy()
        self.get_proxy2(country ='Taiwan')
        self.get_proxy4()
    
    def asia_proxy(self):
        self.get_proxy2_by_pick_country('asia')
        self.get_proxy4()

    def group_proxy(self):
        self.get_proxy2_by_pick_country('group')        
        
    def filter_proxy(self):
        bad_proxy_set = set()
        for p in proxypool.proxy_set:
            connection_score = list()
            for t in proxypool.proxy_test:
                self.new_session()
                
                if not check_this_proxy(p):
                    bad_proxy_set.add(p)
        else:
            proxypool.proxy_set = proxypool.proxy_set - bad_proxy_set
            self.proxy_set_to_proxy_list()
                    
    def check_this_proxy(self, p):
        print('checking', p)
        def check_proxy_on_url(p, url):
            sess = requests.Session()
            try:
                self.response = sess.get(t, timeout=30, proxies=p)
                #print('checking', p,'@', t,'get response.status_code', self.response)
                sess.close()
                Q.put((p, self.response.status_code == 200))
            except Exception as err:
                #print('checking', p,'@', t, 'Exception happened:', err)
                if sess:
                    sess.close()
                Q.put((p, False))

        cpus = mp.cpu_count()
        #print('cpus:', cpus)
        
        if cpus > 1:
            rounds = len(proxypool.proxy_test) // cpus
            Q = mp.JoinableQueue()
            for r in range(rounds):
                plist = list()
                for t in proxypool.proxy_test[cpus*r : cpus*(r+1)]:
                    pi = mp.Process(target=check_proxy_on_url, args=(p, t, cpus))
                    plist.append( pi )
                    pi.start()
        
                Q.join()
                for pi in plist:
                    pi.join()
            
                for pi in plist:
                    pi.terminate()
                    del pi
                else:
                    del plist
                
                while not Q.empty():
                    check = Q.get()
                    #print('Q.get():', check)
                    if not check[1]:
                        print('check fail')
                        return False
            else:
                print('check pass')
                return True
        else:
            for t in proxypool.proxy_test:
                sess = requests.Session()
                valid_proxy = True
                try:
                    self.response = sess.get(t, timeout=30, proxies=p)
                    #print('checking', p,'@', t,'get response.status_code', self.response)
                    sess.close()
                    valid_proxy = self.response.status_code == 200
                except Exception as err:
                    #print('checking', p,'@', t, 'Exception happened:', err)
                    if sess:
                        sess.close()
                    valid_proxy = False
                
                if not valid_proxy:
                    print('check fail')
                    return False
            else:
                print('check pass')
                return True
        
    def random_choice_one_proxy(self):
        import random
        self.proxy_set_to_proxy_list()
        p = random.choice(self.proxy_list)
        del self.proxy_list[self.proxy_list.index(p)]
        self.proxy_set.remove( list(p.values())[0] )
        print('while')
        while not self.check_this_proxy(p):
            print('in while')
            if len(proxypool.proxy_set) == 0:
                p = {'http':None}
                break
                
            p = random.choice(self.proxy_list)
            del self.proxy_list[self.proxy_list.index(p)]
            self.proxy_set.remove( list(p.values())[0] )
        return p
    
    def random_choice_one_proxy_with_none_freq(self):
        self.none_freq_cnt += 1
        if self.none_freq_cnt % self.none_freq == 0:
            self.none_freq_cnt = 0
            return None
        else:
            return self.random_choice_one_proxy()     






