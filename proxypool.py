
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
                print('checking', p,'@', t,'get response.status_code', self.response)
                sess.close()
                Q.put((p, self.response.status_code == 200))
            except Exception as err:
                print('checking', p,'@', t, 'Exception happened:', err)
                if sess:
                    sess.close()
                Q.put((p, False))

        cpus = mp.cpu_count()
        print('cpus:', cpus)
        
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
                    print('Q.get():', check)
                    if not check[1]:
                        return False
            else:
                return True
        else:
            for t in proxypool.proxy_test:
                sess = requests.Session()
                valid_proxy = True
                try:
                    self.response = sess.get(t, timeout=30, proxies=p)
                    print('checking', p,'@', t,'get response.status_code', self.response)
                    sess.close()
                        valid_proxy = self.response.status_code == 200
                except Exception as err:
                    print('checking', p,'@', t, 'Exception happened:', err)
                    if sess:
                        sess.close()
                    valid_proxy = False
                
                if not valid_proxy:
                    return False
            else:
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
            self.proxy_set.remove( list(p.values())[0] )
        return p
    
    def random_choice_one_proxy_with_none_freq(self):
        self.none_freq_cnt += 1
        if self.none_freq_cnt % self.none_freq == 0:
            self.none_freq_cnt = 0
            return None
        else:
            return self.random_choice_one_proxy()     


# In[33]:

p1 = proxypool()


# In[34]:

proxypool.proxy_set= {
    '1.236.79.31:80',
 '1.34.126.189:80',
 '101.53.136.123:8080',
 '103.15.187.116:3128',
 '103.15.187.116:8080',
 '103.15.187.116:81',
 '103.226.152.91:9797',
 '103.226.152.92:9797',
 '103.226.152.93:9797',
 '103.227.60.210:8080',
 '103.227.61.42:8080',
 '103.229.146.126:3128',
 '103.27.0.16:3128',
 '103.37.95.110:3128',
 '103.37.95.110:80',
 '104.238.173.60:3128',
 '106.184.2.142:8118',
 '106.187.93.162:3130',
 '108.61.162.183:808',
 '109.190.131.217:8080',
 '109.190.59.182:8080',
 '109.196.253.72:53281',
 '109.254.211.233:3128',
 '109.86.227.250:8080',
 '112.140.184.136:3128',
 '112.155.42.2:80',
 '112.216.16.250:3128',
 '113.252.236.56:8080',
 '113.253.113.90:80',
 '113.254.110.80:8080',
 '113.254.114.24:80',
 '113.254.44.242:80',
 '114.27.136.8:3128',
 '114.27.169.221:53281',
 '114.39.101.250:3128',
 '114.39.51.92:3128',
 '114.40.17.135:3128',
 '115.70.28.209:53281',
 '116.48.136.128:8080',
 '118.189.172.136:80',
 '119.81.197.124:3128',
 '121.137.69.89:80',
 '121.140.126.250:3128',
 '121.150.206.125:808',
 '121.150.206.155:808',
 '121.166.157.33:8080',
 '122.128.193.128:80',
 '122.146.68.17:8080',
 '123.110.185.95:8080',
 '124.255.23.111:80',
 '124.6.10.162:80',
 '125.141.73.82:3128',
 '128.127.90.34:8080',
 '128.199.103.24:8080',
 '128.199.126.183:3128',
 '128.199.142.35:3128',
 '128.199.142.35:8080',
 '128.199.167.199:3128',
 '128.199.167.199:8080',
 '128.199.169.17:80',
 '128.199.189.94:8080',
 '128.199.190.130:8080',
 '128.199.192.236:80',
 '128.199.219.154:8080',
 '128.199.234.64:8080',
 '128.199.245.163:8080',
 '128.199.47.245:80',
 '128.199.77.93:3128',
 '128.199.77.93:80',
 '128.199.77.93:8000',
 '13.126.58.111:80',
 '13.76.168.146:3128',
 '130.180.127.166:65309',
 '133.232.177.121:8080',
 '137.74.168.174:8080',
 '137.74.254.242:3128',
 '138.201.2.122:10048',
 '138.201.2.122:3128',
 '138.68.147.32:8118',
 '139.130.233.254:8080',
 '139.59.107.171:8080',
 '139.59.114.21:8080',
 '139.59.118.118:80',
 '139.59.124.67:8080',
 '139.59.147.164:80',
 '139.59.160.235:8118',
 '139.59.160.94:8118',
 '139.59.161.110:8118',
 '139.59.161.180:8118',
 '139.59.161.97:8118',
 '139.59.165.0:8118',
 '139.59.165.126:8118',
 '139.59.165.187:8118',
 '139.59.165.66:8118',
 '139.59.168.104:8118',
 '139.59.168.99:8118',
 '139.59.169.135:8118',
 '139.59.169.15:8118',
 '139.59.169.232:8118',
 '139.59.169.81:8118',
 '139.59.170.110:8118',
 '139.59.175.229:8118',
 '139.59.2.223:8888',
 '139.59.244.147:8080',
 '139.59.45.164:80',
 '141.54.99.71:9090',
 '142.44.240.106:80',
 '144.217.62.109:3128',
 '144.217.62.109:80',
 '144.217.62.109:8080',
 '144.217.92.2:3128',
 '144.76.81.79:3128',
 '144.76.81.79:8080',
 '145.239.4.43:8080',
 '146.52.130.99:8080',
 '148.251.211.123:80',
 '149.202.180.55:3128',
 '149.202.49.42:80',
 '149.56.193.80:8080',
 '150.254.65.233:80',
 '151.237.210.199:53281',
 '151.80.100.120:3128',
 '151.80.135.147:3128',
 '156.67.219.61:3128',
 '157.65.28.91:3128',
 '158.69.183.75:8080',
 '158.69.31.45:3128',
 '158.69.31.45:80',
 '159.203.1.72:8080',
 '159.224.115.134:8080',
 '159.224.83.100:8080',
 '160.16.241.139:8080',
 '160.202.41.138:8080',
 '160.202.42.106:8080',
 '160.202.42.195:80',
 '160.202.42.195:8080',
 '160.202.42.58:8080',
 '162.243.140.150:80',
 '163.172.211.176:3128',
 '163.172.215.220:80',
 '163.53.32.238:53281',
 '164.132.222.249:80',
 '164.132.229.75:80',
 '166.62.86.208:8080',
 '167.114.250.199:9999',
 '167.114.47.231:80',
 '167.206.174.105:8080',
 '167.98.60.152:8080',
 '173.212.203.209:80',
 '174.95.235.170:8080',
 '175.126.38.224:80',
 '175.208.122.10:80',
 '175.45.134.96:80',
 '176.103.32.3:8080',
 '176.107.252.163:8080',
 '176.115.250.2:3128',
 '176.31.181.213:3128',
 '176.31.50.61:80',
 '176.37.121.85:8080',
 '178.217.33.134:53281',
 '178.252.26.99:8080',
 '178.33.65.164:80',
 '178.60.28.98:9999',
 '178.62.114.153:8118',
 '178.62.49.23:8118',
 '18.220.146.56:80',
 '180.210.201.54:3128',
 '180.210.204.53:3128',
 '180.210.204.54:3129',
 '180.210.205.104:3128',
 '181.199.202.248:8080',
 '183.181.164.180:80',
 '183.181.168.48:80',
 '183.181.54.121:8080',
 '184.75.254.187:3128',
 '185.112.180.249:8080',
 '185.12.22.43:53281',
 '185.6.242.98:53281',
 '185.65.186.192:8080',
 '185.68.195.103:8080',
 '185.82.203.101:3128',
 '185.82.227.68:53281',
 '185.93.3.123:8080',
 '188.137.121.13:53281',
 '188.162.57.70:3128',
 '188.165.240.92:3128',
 '188.166.144.115:8118',
 '188.166.144.170:8118',
 '188.166.144.172:8118',
 '188.166.144.226:8118',
 '188.166.144.97:8118',
 '188.166.149.73:8118',
 '188.166.164.67:3128',
 '188.166.173.215:8118',
 '188.166.222.152:3128',
 '188.166.226.22:8080',
 '188.166.245.234:88',
 '188.166.3.86:8080',
 '188.168.69.186:8080',
 '188.230.19.33:8080',
 '188.231.150.8:8080',
 '192.99.222.207:3128',
 '192.99.222.207:8080',
 '192.99.245.228:3128',
 '192.99.55.120:3128',
 '192.99.56.254:8080',
 '192.99.71.38:8080',
 '193.110.114.26:8080',
 '193.110.168.8:3128',
 '193.111.50.89:8080',
 '193.27.222.87:80',
 '193.37.152.6:3128',
 '193.70.3.144:80',
 '193.93.216.95:8080',
 '194.1.153.147:80',
 '194.106.219.34:3128',
 '194.110.77.186:8080',
 '194.169.206.141:8080',
 '194.243.194.51:8080',
 '194.243.194.60:8080',
 '194.29.144.82:80',
 '194.44.228.94:8118',
 '194.60.248.22:8081',
 '195.138.95.98:8080',
 '195.154.167.110:8080',
 '198.27.115.40:8080',
 '2.136.8.225:8080',
 '2.138.29.124:8080',
 '202.157.182.141:3128',
 '202.166.196.6:52335',
 '202.73.51.102:80',
 '203.141.149.145:8080',
 '203.198.193.3:808',
 '203.58.117.34:80',
 '203.74.4.0:80',
 '203.74.4.1:80',
 '203.74.4.2:80',
 '203.74.4.3:80',
 '203.74.4.4:80',
 '203.74.4.5:80',
 '203.74.4.6:80',
 '203.74.4.7:80',
 '204.11.243.74:3128',
 '204.12.155.204:3128',
 '204.237.12.210:8080',
 '209.52.241.147:53281',
 '210.101.131.229:8080',
 '210.101.131.231:8080',
 '210.128.16.177:3128',
 '210.202.37.54:3128',
 '210.71.198.230:8118',
 '210.94.2.141:8118',
 '211.127.160.240:8080',
 '211.21.120.163:8080',
 '211.245.62.111:80',
 '211.249.62.39:8080',
 '211.41.163.99:3128',
 '211.49.167.5:3128',
 '211.58.248.163:3128',
 '212.110.20.141:88',
 '212.184.12.11:80',
 '212.225.233.154:8080',
 '212.231.65.8:53281',
 '212.237.14.32:3128',
 '212.237.14.32:80',
 '212.237.16.248:8799',
 '212.237.27.44:80',
 '212.237.27.44:8080',
 '212.237.30.176:3128',
 '212.237.30.176:8080',
 '212.237.6.109:80',
 '212.237.6.109:8080',
 '212.237.9.231:8799',
 '213.171.70.52:8090',
 '213.197.249.228:3128',
 '213.217.188.41:8080',
 '213.27.152.15:3128',
 '213.87.101.187:8080',
 '217.102.173.127:80',
 '217.126.5.224:8080',
 '217.29.53.198:3128',
 '217.61.123.55:8080',
 '217.61.166.128:8080',
 '218.158.29.227:808',
 '218.158.29.69:808',
 '218.161.47.231:3128',
 '218.161.87.19:53281',
 '218.254.1.14:80',
 '218.254.1.14:81',
 '218.50.2.102:8080',
 '219.127.253.43:80',
 '219.166.7.50:1024',
 '219.76.4.71:85',
 '219.76.4.7:80',
 '219.76.4.7:81',
 '219.76.4.8:81',
 '219.79.10.191:8080',
 '219.94.245.97:55555',
 '220.143.165.140:3128',
 '220.143.168.86:3128',
 '220.143.174.159:3128',
 '220.143.174.173:3128',
 '220.143.174.175:3128',
 '221.124.18.9:8080',
 '223.16.224.58:8080',
 '223.19.212.30:80',
 '223.19.41.6:8380',
 '223.19.51.247:80',
 '223.255.191.109:3128',
 '23.101.67.107:3128',
 '24.245.101.10:48678',
 '27.113.26.193:80',
 '27.122.12.45:3128',
 '27.92.13.214:8118',
 '31.131.67.76:8080',
 '31.182.52.156:3129',
 '34.203.213.47:1080',
 '36.55.230.154:3128',
 '37.114.59.201:3128',
 '37.117.252.87:8080',
 '37.128.116.41:8080',
 '37.131.166.251:8080',
 '37.152.93.33:8080',
 '37.18.251.228:8081',
 '37.182.212.118:8080',
 '37.187.116.199:80',
 '37.187.119.226:3128',
 '37.187.120.123:80',
 '37.204.255.79:8081',
 '37.57.224.118:25401',
 '37.59.62.38:8080',
 '45.76.188.195:80',
 '45.76.235.118:3128',
 '45.76.83.40:8080',
 '45.77.4.228:3128',
 '45.79.139.146:80',
 '46.0.192.177:8080',
 '46.101.27.234:8118',
 '46.101.30.137:8118',
 '46.101.37.196:8118',
 '46.101.44.44:8118',
 '46.101.49.108:8118',
 '46.101.49.47:8118',
 '46.101.51.214:8118',
 '46.101.58.141:8118',
 '46.101.7.211:8118',
 '46.101.75.147:8118',
 '46.101.78.149:8118',
 '46.101.83.147:8118',
 '46.101.92.212:80',
 '46.101.96.65:80',
 '46.105.51.183:80',
 '46.164.155.5:8080',
 '46.166.176.187:3128',
 '46.182.19.221:8080',
 '46.219.1.167:8080',
 '46.219.14.43:80',
 '46.219.14.43:8080',
 '46.8.243.89:65205',
 '47.52.240.174:3128',
 '47.52.33.216:3128',
 '47.52.62.110:8080',
 '47.74.15.67:3128',
 '47.74.44.92:3128',
 '47.88.84.190:8080',
 '47.89.17.18:8080',
 '47.89.18.70:3128',
 '47.89.41.164:80',
 '47.89.48.178:80',
 '47.90.203.95:3128',
 '5.152.158.4:8080',
 '5.188.218.24:8080',
 '5.189.133.231:80',
 '5.189.153.156:80',
 '5.196.75.208:3128',
 '5.228.28.31:8081',
 '5.39.101.14:8080',
 '5.9.36.16:3128',
 '50.201.51.216:8080',
 '51.140.29.211:80',
 '51.15.86.160:80',
 '51.254.191.239:8080',
 '51.254.252.34:80',
 '51.255.193.197:80',
 '52.220.217.37:3128',
 '52.69.38.114:3128',
 '52.76.214.252:80',
 '52.79.103.235:3128',
 '54.89.183.75:80',
 '58.124.172.52:80',
 '58.153.108.102:8080',
 '58.181.39.182:80',
 '58.3.110.167:8080',
 '59.126.48.8:80',
 '59.126.48.8:8080',
 '61.213.218.217:8080',
 '61.216.1.23:3128',
 '61.231.189.184:80',
 '62.14.191.139:53281',
 '62.15.205.71:53281',
 '62.22.44.226:8080',
 '62.250.84.188:80',
 '62.33.159.116:8080',
 '62.64.111.42:53281',
 '62.80.182.42:53281',
 '62.81.76.18:8080',
 '64.103.38.147:8080',
 '64.137.225.201:8080',
 '64.137.226.23:8080',
 '64.173.188.21:8080',
 '64.34.21.84:80',
 '66.171.128.61:8080',
 '66.70.189.153:3128',
 '69.10.49.10:80',
 '69.10.49.115:80',
 '69.10.49.50:80',
 '69.85.70.37:53281',
 '71.41.27.245:8080',
 '74.83.246.105:8081',
 '75.150.88.59:80',
 '77.138.191.242:3128',
 '77.174.110.126:80',
 '77.222.139.57:8080',
 '77.239.133.146:3128',
 '77.252.139.246:8080',
 '77.55.226.253:3128',
 '77.65.13.26:8080',
 '77.87.75.10:80',
 '77.87.75.12:80',
 '79.1.180.77:8080',
 '79.135.219.78:8080',
 '79.137.42.124:3128',
 '79.137.86.157:3128',
 '79.143.187.93:8888',
 '80.100.205.14:80',
 '80.161.30.153:80',
 '80.161.30.155:80',
 '80.161.30.156:80',
 '80.19.188.124:8080',
 '80.209.226.133:8080',
 '80.211.150.188:3128',
 '80.211.165.76:8080',
 '80.211.166.20:3128',
 '80.211.166.20:80',
 '80.211.166.20:8080',
 '80.211.173.190:3128',
 '80.211.173.190:8080',
 '80.211.232.151:8080',
 '81.36.204.220:8080',
 '81.40.249.166:8080',
 '81.49.137.110:80',
 '82.107.202.30:8080',
 '82.130.246.64:53281',
 '82.130.246.69:51552',
 '82.151.100.18:53281',
 '82.165.151.230:80',
 '82.211.8.180:3128',
 '82.223.246.72:80',
 '83.145.132.77:8080',
 '83.169.202.2:3128',
 '83.169.38.204:80',
 '83.174.206.6:8080',
 '83.197.155.65:80',
 '83.222.207.142:8080',
 '83.234.42.12:3128',
 '83.3.251.178:8080',
 '83.33.122.97:8080',
 '83.48.85.204:9999',
 '83.56.31.9:8080',
 '85.10.240.186:8080',
 '85.11.114.135:3128',
 '85.142.163.1:3128',
 '85.214.243.92:80',
 '85.90.208.4:3128',
 '86.19.247.72:80',
 '87.140.81.14:8080',
 '87.149.113.246:80',
 '87.169.188.137:8080',
 '87.54.50.94:80',
 '87.98.157.128:3128',
 '88.10.220.74:8080',
 '88.159.115.116:80',
 '88.159.138.197:80',
 '88.159.79.186:80',
 '88.170.1.143:8118',
 '88.20.31.15:8080',
 '88.87.72.72:8080',
 '88.99.110.166:8080',
 '88.99.134.46:8080',
 '88.99.149.188:31288',
 '88.99.176.193:8080',
 '88.99.193.53:3128',
 '89.104.108.178:3128',
 '89.140.133.28:8080',
 '89.140.79.175:3128',
 '89.186.1.215:53281',
 '89.191.131.243:8080',
 '89.237.21.151:8080',
 '89.98.94.50:80',
 '90.45.140.23:80',
 '91.121.162.173:80',
 '91.151.106.127:53281',
 '91.197.220.51:3128',
 '91.205.52.234:8081',
 '91.214.62.168:53281',
 '91.215.106.2:8080',
 '91.221.252.18:8080',
 '91.225.190.159:53281',
 '91.226.35.93:53281',
 '91.235.51.238:53281',
 '91.242.163.174:3128',
 '92.222.74.221:80',
 '92.222.83.160:80',
 '92.255.75.198:80',
 '92.50.142.70:8080',
 '93.104.215.234:3128',
 '93.167.224.213:80',
 '93.167.224.220:80',
 '93.174.92.177:37651',
 '93.190.142.214:80',
 '93.190.142.240:80',
 '93.51.247.104:80',
 '94.103.24.145:80',
 '94.130.153.164:3128',
 '94.142.215.147:80',
 '94.153.172.74:80',
 '94.153.172.75:80',
 '94.154.22.193:53281',
 '94.177.163.88:8080',
 '94.177.175.232:80',
 '94.177.175.232:8080',
 '94.177.207.70:3128',
 '94.177.217.137:3128',
 '94.198.4.14:3128',
 '94.28.213.134:8081',
 '95.121.178.11:8080',
 '95.171.198.206:8080',
 '95.182.112.194:8080',
 '95.215.52.150:8080',
 '95.85.50.218:80',
 '96.67.118.233:8080',
 '98.126.106.2:3128',
 '98.126.106.3:3128',
 '98.143.243.5:8080',
 '99.232.234.15:3128'}


# In[35]:

p1.random_choice_one_proxy()


# In[87]:

p1.group_proxy()


# In[103]:

proxypool.proxy_list


# In[54]:

from queue import Queue


# In[56]:

q = Queue()
q.put(True)
q.put(False)
q.put(True)
q.put(True)
q.put(True)
q.put(False)
q.put(False)
q.put(False)
q.put(True)
q.put(False)


# In[60]:

dir(Queue)


# In[68]:

q.empty()


# In[72]:

d = {"aa":True}
list(d.values())[0]


# In[93]:

s = {1,2,3}
s.remove(3)
s


# In[176]:

dir(Queue)


# In[198]:

dir(mp.Queue)


# In[200]:

qqq = mp.Queue()
qqq.put(1)
qqq.put(2)


# In[204]:

qqq > 0


# In[24]:

import random
random.choice(range(5))


# In[25]:

l = [100,300,900]
del l[l.index(300)]


# In[26]:

l


# In[ ]:



