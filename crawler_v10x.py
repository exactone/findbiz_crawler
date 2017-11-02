
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


# In[2]:

class CmpyinfoCrawlerError(Exception):
    def __init__(self, prefix, sta=0):
        self.sta = sta
        self.end = time.time()
        self.exe = self.end - self.sta
        self.prefix = prefix
            
    def __str__(self):
        def timestr(t):
            d, r = divmod(t, 86400)
            h, r = divmod(r, 3600)
            m, s = divmod(r, 60)
            return "{} days {:02}:{:02}:{:.2f}".format(d, h, m, s)
        
        s = self.prefix + " raised at {} ".format(timestr(self.end-self.sta))
        return s


# In[3]:

import proxypool
#p = proxypool()
#p.na_proxy()
#print(p.proxy_set)
#p.filter_proxy()


# In[4]:

class back_log:
    def __init__(self, flush=False, flush_threshold=1000, first_line='',log_format='', fname =''):
        self.queue = list()
        self.flush = flush
        self.flush_threshold = flush_threshold
        self.first_line = first_line
        self.log_format = log_format
        self.fname = fname
        with open(fname, 'a') as log_file:
            if self.first_line:
                log_file.write(self.first_line + '\n')
        
    def log(self, mode='format', args = tuple(), in_log='', postfix=''):
        if mode == 'format':
            log_str = self.log_format.format(*args) + ' ' + postfix
        elif mode == 'manual':
            log_str = in_log + ' ' + postfix
                
        self.queue.append(log_str)
        
        if len(self.queue) >= self.flush_threshold:
            log_str = '\n'.join(self.queue)
            self.log_flush()
            
    def log_flush(self):
        if self.queue:
            log_str = '\n'.join(self.queue)
            with open(self.fname, 'a') as log_file:
                log_file.write(log_str + '\n')
            
                self.flush = False
            
                del self.queue
                self.queue = list()        


# In[5]:

from collections import defaultdict
from datetime import datetime
import copy
import pandas as pd
import json
import pickle



#d = defaultdict(set)


class cmpyinfo_crawler:
    #proxies = [{'http':'http://proxy.hinet.net:80'}, {'http':'172.103.3.156:53281'}]

    h3_dict = {
        '公司基本資料':'Cmpy',
        '大陸公司許可報備基本資料':'CmpyCnRp', # 53656300 
        '大陸公司許可基本資料':'CmpyCn',# 53026057
        '外國公司報備基本資料':'CmpyFrgnRp', # 16747659
        '外國公司認許基本資料':'CmpyFrgn', # 24812289
        '商業登記基本資料':'Busm',
        '商業登記基本資料(分支機構)':'BrBusm', # 02284257
        '工廠基本資料':'Fact', 
        '分公司資料':'BrCmpy',
        '有限合夥登記基本資料':'Lmtd',
        '有限合夥登記基本資料(分支機構)':'BrLmtd'
    }

    url2_dict = {
        'HC' : 'http://findbiz.nat.gov.tw/fts/query/QueryCmpyDetail/queryCmpyDetail.do',
        'HB' : 'http://findbiz.nat.gov.tw/fts/query/QueryBusmDetail/queryBusmDetail.do',
        'BB' : 'http://findbiz.nat.gov.tw/fts/query/QueryBusmDetail/queryBusmDetail.do',
        'HF' : 'http://findbiz.nat.gov.tw/fts/query/QueryFactDetail/queryFactDetail.do',
        'BC' : 'http://findbiz.nat.gov.tw/fts/query/QueryBrCmpyDetail/queryBrCmpyDetail.do',
        'HL' : 'http://findbiz.nat.gov.tw/fts/query/QueryLmtdDetail/queryLmtdDetail.do',
        'BL' : 'http://findbiz.nat.gov.tw/fts/query/QueryLmtdDetail/queryLmtdDetail.do'
    }
    cmpy_type_dict = {
        'HC' : 'Cmpy',
        'HB' : 'Busm',
        'BB' : 'Busm',
        'HF' : 'Fact',
        'BC' : 'BrCmpy',
        'HL' : 'Lmtd',
        'BL' : 'BrLmtd'
    }
    ua = UserAgent()
    
    #proxy = proxypool()
    
    def __init__(self, qryCond='', qryType='', pageStart=1, pageEnd=1, path_phantomjs = '/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs', logname = 'task.log', sleep_scale='small'):
        self.path_phantomjs = path_phantomjs
        self.session = None
        self.pageStart = pageStart 
        self.pageNow = pageStart
        self.pageEnd = pageEnd
        self.pageItem = 1 
        self.qryCond = qryCond
        self.qryType = qryType
        # self.banKey = None
        # self.objectId = None
        """
        self.task = {'qryCond': self.qryCond, 
                     'qryType': self.qryType, 
                     'pageStart': self.pageStart, 
                     'pageEnd': self.pageEnd, 
                     'pageNow': self.pageNow,
                     'pageItem' : self.pageItem}
        """

        
        
        self.banNo = None
        self.brBanNo = None
        self.banKey = None
        self.estbId = None
        self.objectId = None
        
        self.querytype = None
        #self.cmpy_type = None
        
        self.cookie = None
        self.oncontextmenu = list()
        # to gater h3_text of each 
        self.h3_info = defaultdict(set)
        self.response = None
        self.h3_text = None
        self.h3_query = None
        self.user_agent = None


        #self.proxyip()
        self.sta = time.time()
        self.end = time.time()
        self.this_round_sta = time.time()
        self.this_round_end = time.time()
        self.pooling = time.time()
        #self.tick = 300
        
        #self.proxy_pool = [{'http':'proxy.hinet.net:80'}, None]
        self.proxypool = proxypool.proxypool(path_phantomjs=path_phantomjs)
        self.proxy_ratio = 5 # 5 proxies vs 1 None
        self.proxy_i = 0
        self.proxy = None
        #self.proxy_pool = [None, None]        
        #self.proxy_set = bool(proxy)
        self.proxy_update = True
        self.proxy_tick = 1800
        #self.proxy_tick = 120
        #self.proxy_tick = 300
        #self.new_proxies()
        #self.proxyip(mode = 1, top = 0)
        
        self.totalPage = 1
        self.totalCount = 1
        self.flush_threshold = 1000
        self.total_json_name = "all_json_out"
        
        
        # self.trlog = back_log(flush=False, flush_threshold=1, first_line='',logformat='', fname ='')
        # self.objidlog = back_log(flush=False, flush_threshold=1, first_line='',logformat='', fname ='')
        def tasklog_timestamp():
            d = datetime.now()#.strftime("%Y-%m-%d-%m-%s")
            d.year,d.month,d.day,d.hour,d.minute,d.second
            nowstr = "{0:0>4d}{1:0>2d}{2:0>2d}_{3:0>2d}{4:0>2d}{5:0>2d}".format(d.year,d.month,d.day,d.hour,d.minute,d.second)
            return nowstr   
            
            
        self.timestamp = tasklog_timestamp()
        self.tasklog = back_log(flush=False, 
                                flush_threshold=100, 
                                first_line='{0: >19s}, {1: >19s}, {2: >6s}, {3: >6s}'.format('task execution time', 'this round time', 'page', 'item'), 
                                log_format= '{0: >19s}, {1: >19s}, {2: >6d}, {3: >6d}', 
                                fname = '{}@{: >17s}.task.log'.format(logname, str(self.timestamp)))
        self.parser = {'Cmpy':parser_cmpy_type('Cmpy', self.tasklog), 
                       'CmpyFrgnRp':parser_cmpy_type('CmpyFrgnRp', self.tasklog), 
                       'CmpyFrgn':parser_cmpy_type('CmpyFrgn', self.tasklog), 
                       'CmpyCnRp':parser_cmpy_type('CmpyCnRp', self.tasklog), 
                       'CmpyCn':parser_cmpy_type('CmpyCn', self.tasklog), 
                       'BrCmpy':parser_cmpy_type('BrCmpy', self.tasklog), 
                       'Busm':parser_cmpy_type('Busm', self.tasklog), 
                       'BrBusm':parser_cmpy_type('BrBusm', self.tasklog), 
                       'Fact':parser_cmpy_type('Fact', self.tasklog),
                       'Lmtd':parser_cmpy_type('Lmtd', self.tasklog), 
                       'BrLmtd':parser_cmpy_type('BrLmtd', self.tasklog)}
        
        self.tr = dict()
        self.trlog = dict()
        self.objidlog = dict()
        
        self.results = defaultdict(list)
        #self.flush_threshold = 20;
        
        self.exception_happened = False
        self.sleep_scale = sleep_scale 
        
        
        
        

    def __str__(self):
        #attr = {"session":self.session, "qryCond":self.qryCond, "banNo":self.banNo, "brBanNo":self.brBanNo, "banKey":self.banKey, "estbId":self.estbId, "objectId":self.objectId, "querytype":self.querytype, "cmpy_type":self.cmpy_type, "h3_text":self.h3_text}
        attr = {"session":self.session, "qryCond":self.qryCond, "banNo":self.banNo, "brBanNo":self.brBanNo, "banKey":self.banKey, "estbId":self.estbId, "objectId":self.objectId, "querytype":self.querytype, "h3_text":self.h3_text, "h3_query":self.h3_query}        
        return str(attr) + " " + self.exectime('task execution time: ')

    def timestr(self, t):
        d, r = divmod(t, 86400)
        h, r = divmod(r, 3600)
        m, s = divmod(r, 60)
        return "{: >4d} days {: >2d}:{: >2d}:{: >2d}".format(int(d), int(h), int(m), int(s))
    
    def exectime(self, prefix = ''):
        # task execution time
        self.end = time.time()
        return prefix + self.timestr(self.end - self.sta)
        
    def this_round_time_start(self):
        self.this_round_sta = time.time()
    
    #def this_round_time_end(self):
    #    self.this_round_end = time.time()
    
    def this_round_exectime(self, prefix = ''):
        # page execution time
        self.this_round_end = time.time()
        return prefix + self.timestr(self.this_round_end - self.this_round_sta)

    def get_banKey_objectId(self, attri):
        # 必須透過objectId來決定要如何填入header
        self.objectId = (attri.replace("javascript:qryDetail('","")).replace("', true);return false;","")
        self.querytype = self.objectId[0:2]
        #self.cmpy_type = cmpyinfo_crawler.cmpy_type_dict[self.querytype]
        
        try:
            if self.querytype not in cmpyinfo_crawler.url2_dict:
                raise CmpyinfoCrawlerError('QueryTypeError', self.sta)
        except CmpyinfoCrawlerError as ccerr:
            print(ccerr)
            return       
                  

        # 按照objectId[0:2]來決定如何填入header
        if self.querytype == 'HC': # 公司
            self.banNo = self.objectId.replace('HC', '')
            self.brBanNo = ''
            self.banKey = ''
            self.estbId = ''
        elif self.querytype == 'BC': # 分公司
            self.banNo = ''
            self.brBanNo = self.objectId.replace('BC', '')
            self.banKey = ''
            self.estbId = ''
        elif self.querytype == 'HB': # 商號
            #self.banNo = self.qryCond
            self.banNo = self.objectId[2:2+8]
            self.brBanNo = ''
            #self.banKey = self.objectId[self.objectId.rindex(self.qryCond) + len(self.qryCond):]
            self.banKey = self.objectId[2+8:]
            self.estbId = ''
        elif self.querytype == 'BB': # 商號分公司
            #self.banNo = self.qryCond
            self.banNo = self.objectId[2:2+8]
            self.brBanNo = ''
            #self.banKey = self.objectId[self.objectId.rindex(self.qryCond) + len(self.qryCond):]
            self.banKey = self.objectId[2+8:]
            self.estbId = ''            
        elif self.querytype == 'HF': # 工廠
            self.banNo = ''
            self.brBanNo = ''
            self.banKey = ''
            self.estbId = self.objectId.replace('HF', '')
        elif self.querytype == 'HL': # 有限合夥
            self.banNo = self.objectId.replace('HL', '')
            self.brBanNo = ''
            self.banKey = ''
            self.estbId = ''
        elif self.querytype == 'BL': # 有限合夥分支
            self.banNo = self.objectId.replace('BL', '')
            self.brBanNo = ''
            self.banKey = ''
            self.estbId = ''

    
        #print('banNo:', self.banNo, 'brBanNo:', self.brBanNo, 'banKey:', self.banKey, 'estbId:', self.estbId, 'querytype:', self.querytype)
        
    def first_connection_header0(self):
        self.form_data_url1 = dict()
        self.form_data_url1 = {'qryCond':str(self.qryCond),
                               'infoType':'D',
                               'qryType':'',
                               'cmpyType':'',
                               'brCmpyType':'',
                               'busmType':'',
                               'factType':'',
                               'lmtdType':'',
                               'isAlive':'all',
                               'sugCont':'',
                               'sugEmail':'',
                               'g-recaptcha-response':''
                              }
        #if len(self.qryType) > 1:
        #    self.form_data_url1['isAlive'] = 'all'
        #else:
        #    self.form_data_url1['isAlive'] = 'true'
        
        for qry in self.qryType:
            if qry == 'cmpyType':
                self.form_data_url1['qryType'] = 'cmpyType'
                self.form_data_url1['cmpyType'] = 'true'
            if qry == 'brCmpyType':
                self.form_data_url1['qryType'] = 'brCmpyType'
                self.form_data_url1['brCmpyType'] = 'true'
            if qry == 'busmType':
                self.form_data_url1['qryType'] = 'busmType'
                self.form_data_url1['busmType'] = 'true'
            if qry == 'factType':
                self.form_data_url1['qryType'] = 'factType'
                self.form_data_url1['factType'] = 'true'            
            if qry == 'lmtdType':
                self.form_data_url1['qryType'] = 'lmtdType'
                self.form_data_url1['lmtdType'] = 'true'            

    def first_connection_header1(self, currentPage):
        self.form_data_url1 = dict()
        self.form_data_url1 = {'pagingModel.totalCount':str(self.totalCount),
                               'pagingModel.currentPage':str(currentPage),
                               'pagingModel.totalPage':str(self.totalPage),
                               'model.qryCond':str(self.qryCond),
                               'model.isAlive':'all',
                               'model.cmpyType':'',
                               'model.brCmpyType':'',
                               'model.busmType':'',
                               'model.factType':'',
                               'model.lmtdType':'',
                               'model.infoType':'D',
                               'model.busiItemSub':'',
                               'model.city':''}        
        
        for qry in self.qryType:
            if qry == 'cmpyType':
                self.form_data_url1['model.cmpyType'] = 'true'
            if qry == 'brCmpyType':
                self.form_data_url1['model.brCmpyType'] = 'true'
            if qry == 'busmType':
                self.form_data_url1['model.busmType'] = 'true'
            if qry == 'factType':
                self.form_data_url1['model.factType'] = 'true'            
            if qry == 'lmtdType':
                self.form_data_url1['model.lmtdType'] = 'true'
                
    def set_form_data_url1(self, mode, currentPage=1):
        if mode == 0:
            self.first_connection_header0()
        elif mode == 1:
            self.first_connection_header1(currentPage)
    
    def new_session(self):
        if self.proxy_update:
            if self.session is not None:
                self.session.close()
        
            self.session = requests.Session()
            self.proxy_update = False    
    
    def first_connection(self):
        url1 = 'http://findbiz.nat.gov.tw/fts/query/QueryList/queryList.do'
        
        request_header1 = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            ##'Content-Length':'239',
            'Content-Type':'application/x-www-form-urlencoded',
            ##'Cookie':'qryCond=00114003~type=cmpyType,brCmpyType,busmType,factType,lmtdType,~infoType=D~isAlive=all~; JSESSIONID=6D2FA44A8850268F8A6A9D429D53B548; DWRSESSIONID=*o94X5xiFwhD8b5kRGWQo7XpKTl; JSESSIONID=33352345177332F62F210E99D78BD44A; _ga=GA1.3.315276753.1502943360; _gid=GA1.3.754870603.1502943360; _gat=1',
            'Host':'findbiz.nat.gov.tw',
            'Origin':'http://findbiz.nat.gov.tw',
            'Referer':'http://findbiz.nat.gov.tw/fts/query/QueryBar/queryInit.do',
            'Upgrade-Insecure-Requests':'1',
            #'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'   
        }
        #if get_new_session:
        
        if self.proxy_update:
            # 新的session 會換瀏覽器，並且拿新的session
            request_header1['User-Agent'] = cmpyinfo_crawler.ua.random
            # self.new_session()會將proxy_update設為False，所以要放後面
            self.new_session()
           
        try:
            self.response = self.session.post(url1, headers=request_header1, data=self.form_data_url1, proxies=self.proxy)
            
        except requests.exceptions.ProxyError as err:
            self.tasklog.log(mode='manual', in_log = "Exception requests.ProxyError @ first_connection(), remove proxy")
            self.change_proxy()
            #self.response = self.session.post(url1, headers=request_header1, data=self.form_data_url1, proxies=self.proxy)
            return False            
        except Exception as err:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ first_connection()")
            print(err.__doc__)
            self.tasklog.log(mode='manual', in_log = err.__doc__)
            self.tasklog.log_flush()
            self.change_proxy()
            return False
        
        
        try:
            if self.response.status_code != 200:
                raise CmpyinfoCrawlerError('Response200Error', self.sta)
        except CmpyinfoCrawlerError as ccerr:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ first_connection()")
            print(ccerr)
            self.tasklog.log(mode='manual', in_log = str(ccerr))
            self.tasklog.log_flush()
            self.change_proxy()
            return False
         except Exception as err:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ first_connection()")
            print(err.__doc__)
            self.tasklog.log(mode='manual', in_log = err.__doc__)
            self.tasklog.log_flush()
            self.change_proxy()
            return False

       
        try:
            selector = etree.HTML(self.response.content)
        except Exception as err:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception from etree @ first_connection()")
            print(err.__doc__)
            self.tasklog.log(mode='manual', in_log = err.__doc__)
            self.tasklog.log_flush()
            self.change_proxy()
            return False
       
        # reCaptcha 測試
        try:
            recaptcha = selector.xpath('//div[@class="g-recaptcha"]')
            if recaptcha:
                raise CmpyinfoCrawlerError('reCaptchaError', self.sta)
        except CmpyinfoCrawlerError as ccerr:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ first_connection()")
            print(ccerr)
            self.tasklog.log(mode='manual', in_log = str(ccerr))
            self.tasklog.log_flush()
            self.change_proxy()
            return False
        except Exception as err:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception from recaptcha@ first_connection()")
            print(err.__doc__)
            self.tasklog.log(mode='manual', in_log = err.__doc__)
            self.tasklog.log_flush()
            self.change_proxy()
            return False

        
        # 同一統編可有多個結果
        hrefs = selector.xpath('//*[@id="vParagraph"]/div[@class="panel panel-default"]/div[@class="panel-heading companyName"]/a')
        del self.oncontextmenu
        self.oncontextmenu = list()
        for h in hrefs:
            if h.attrib['oncontextmenu'] not in self.oncontextmenu:
                self.oncontextmenu.append(h.attrib['oncontextmenu'])

        try:
            if not self.oncontextmenu:
                raise CmpyinfoCrawlerError('searchFailError', self.sta)
            else:
                return True
        except CmpyinfoCrawlerError as ccerr:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ first_connection()")
            print(ccerr)
            self.tasklog.log(mode='manual', in_log = str(ccerr))
            self.tasklog.log_flush()
            self.change_proxy()
            return False                
         except Exception as err:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception from oncontextmenu@ first_connection()")
            print(err.__doc__)
            self.tasklog.log(mode='manual', in_log = err.__doc__)
            self.tasklog.log_flush()
            self.change_proxy()
            return False

               
        
    def second_connection(self):
        url2 = cmpyinfo_crawler.url2_dict[self.querytype]
        
        form_data_url2 = {
            'banNo':str(self.banNo),
            'brBanNo':str(self.brBanNo),
            'banKey':str(self.banKey),
            'estbId':str(self.estbId),
            'objectId':str(self.objectId),
            'CPage':'',
            'brCmpyPage':'',
            'eng':'',
        }

        request_header2={
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            ##'Content-Length':'211',
            ##'Content-Type':'application/x-www-form-urlencoded',
            ##'Cookie':'JSESSIONID=3193CF8D61AEC43F3810BF07524701BA; DWRSESSIONID=*o94X5xiFwhD8b5kRGWQo7XpKTl; _gat=1; _ga=GA1.3.315276753.1502943360; _gid=GA1.3.754870603.1502943360',
            'Host':'findbiz.nat.gov.tw',
            'Origin':'http://findbiz.nat.gov.tw',
            'Referer':'http://findbiz.nat.gov.tw/fts/query/QueryList/queryList.do',
            ##'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        ua = UserAgent()
        request_header2['User-Agent'] = cmpyinfo_crawler.ua.random
        #self.response = self.session.post(url2, headers=request_header2,data=form_data_url2, proxies=self.proxy) # first connection有機會重新設定self.proxy, second connection直接用

        try:
            self.response = self.session.post(url2, headers=request_header2,data=form_data_url2, proxies=self.proxy) # first connection有機會重新設定self.proxy, second connection直接用
        except requests.exceptions.ProxyError as err:
            self.tasklog.log(mode='manual', in_log = "Exception requests.ProxyError @ second_connection(), remove proxy")
            self.change_proxy()
            return False
        except Exception as err:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ second_connection()")
            print(err.__doc__)
            self.tasklog.log(mode='manual', in_log = err.__doc__)
            self.tasklog.log_flush()
            self.change_proxy()
            return False
        
        try:
            if self.response.status_code != 200:
                raise CmpyinfoCrawlerError('Response200Error', self.sta)
        except CmpyinfoCrawlerError as ccerr:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ second_connection()")
            print(ccerr)
            self.tasklog.log(mode='manual', in_log = str(ccerr))
            self.tasklog.log_flush()
            self.change_proxy()
            return False
        
        return True
        
    # 由h3解析出來的中文字串才是比較精確的類型
    def get_h3(self):
        selector = etree.HTML(self.response.content)
        h3 = selector.xpath('//div[@id="content"]/div[@class="tab-content"]/div[@class="tab-pane active"]/h3')
        

        try:
            if len(h3) == 0:
                raise CmpyinfoCrawlerError('h3ResolveError', self.sta)
        except CmpyinfoCrawlerError as ccerr:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ get_h3(): can't resolve h3 in xpath")
            print(ccerr)
            self.tasklog.log(mode='manual', in_log = str(ccerr))
            self.tasklog.log_flush()
            return False
        
        self.h3_text = h3[0].text.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
        self.h3_text = re.sub(r'\s', r'', self.h3_text)
        print('self.h3_text resolved: ', self.h3_text)
        #print(self.h3_text)
        if self.h3_text in cmpyinfo_crawler.h3_dict:
            self.h3_query = cmpyinfo_crawler.h3_dict[self.h3_text]
            print('self.h3_query resolved: ', self.h3_query)
        
        try:
            if self.h3_text not in cmpyinfo_crawler.h3_dict:
                raise CmpyinfoCrawlerError('h3ResolveError', self.sta)
        except CmpyinfoCrawlerError as ccerr:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Exception @ get_h3(): new h3 found")
            print(ccerr)
            self.tasklog.log(mode='manual', in_log = str(ccerr))
            self.tasklog.log_flush()
            return False
        
        return True
            


    def proxy_monitor(self):
        if self.proxy_tick < 0:
            return

        self.end = time.time()        
        if self.end - self.pooling > self.proxy_tick:
            self.change_proxy()
            self.pooling = time.time()
    
    def renew_poroxypool(self):
        self.proxypool.reset_proxy()
        # 更新proxypool，先拿亞洲，拿不到就拿全世界
        try:
            self.proxypool.asia_proxy()
            if len(self.proxypool.proxy_set) == 0:
                raise CmpyinfoCrawlerError('ResolveProxyError', self.sta)
        except CmpyinfoCrawlerError as cerr:
            self.exception_happened = True
            self.tasklog.log(mode='manual', in_log = "Can not resolve proxy from proxypool.asia_proxy(), retry proxypool.world_proxy()")
            print(ccerr)
            self.tasklog.log(mode='manual', in_log = str(ccerr))
            self.tasklog.log_flush()
            
            try:
                self.proxypool.world_proxy()
                if len(self.proxypool.proxy_set) == 0:
                    raise CmpyinfoCrawlerError('ResolveProxyError', self.sta)                
            except:
                self.exception_happened = True
                self.tasklog.log(mode='manual', in_log = "Can not resolve proxy from proxypool.world_proxy(), you can only use local ip")
                print(ccerr)
                self.tasklog.log(mode='manual', in_log = str(ccerr))
                self.tasklog.log_flush()
                return False
            
                
        #self.proxypool.filter_proxy()
        proxy_str = 'resolved ' + str(len(self.proxypool.proxy_set)) + ' proxies'
        print(proxy_str)
        self.tasklog.log(mode='manual', in_log = proxy_str)
        return True

    def set_proxy(self, p):
        self.proxy = p
        proxy_str = 'proxy change to ' + str(self.proxy) + ' @ ' + self.exectime('task execution time: ')
        print(proxy_str)
        self.tasklog.log(mode='manual', in_log = proxy_str)
        self.proxy_update = True

        
    
    def change_proxy(self):
        #ratio = 5 # 5 proxies vs 1 None
        #import random
        #self.proxy_list = self.proxypool.proxy_list self.proxy_list[0]
        if not self.proxypool.proxy_set:
            self.renew_poroxypool()
        
        #self.proxy_i += 1
        #if self.proxy_i % self.proxy_ratio == 0:
        #    p = None
        #else:  
        #    p = {'http':self.proxypool.random_choice_one_proxy()}
        p = self.proxypool.random_choice_one_proxy_with_none_freq()
        
        self.set_proxy(p)
        #self.proxy_update = True
        


    def random_sleep(self, scale = 'small'):
        import random

        #            15%   20%     20%     10% 15%   20%   
        sleeptime = [1,1,1,2,2,2,2,3,3,3,3,4,4,5,5,5,6,6,6,6]
        #            15%               35%                  15%               15%            5%    15%   
        magnitude = [0.75, 0.75, 0.75, 1, 1, 1, 1, 1, 1, 1, 1.25, 1.25, 1.25, 1.5, 1.5, 1.5, 1.75, 2, 2, 2]
        #            10%20%   30%      40%
        basetime  = [5, 7.5, 7.5, 10, 12.5, 12.5, 3, 3, 3, 3]
        
        if scale == 'none':
            return

        if scale == 'mixed':
            scale = random.choice(['small']+['midium']+['large'])
        if scale == 'mixed_small':
            scale = random.choice(['small']*14+['midium']*3+['large']*3)
        if scale == 'mixed_medium':
            scale = random.choice(['small']*3+['midium']*14+['large']*3)
        if scale == 'mixed_large':
            scale = random.choice(['small']*3+['midium']*3+['large']*14)



        
        m = random.choice(magnitude)
        b = random.choice(basetime)        
        s = random.choice(sleeptime)
        if scale == 'small':
            s *= 1
            b *= 0.25
            m *= 0.75
        if scale == 'midium':
            s *= 6
            b *= 0.75
            m *= 0.75
        if scale == 'large':
            s *= 12
            b *= 1
            m *= 1 
            
        time.sleep(b+m*s)
            
    def print_html(self):
        print(self.response.content.decode('utf8'))
        
    def resolve_page(self):
        selector = etree.HTML(self.response.content)
        text = selector.xpath('//*[@id="queryListForm"]/div[@class="main"]/div[@class="container padding_top"]/div[@class="row"]/div[@class="col-lg-12"]/div/div/div/text()')
        #for i, t in enumerate(text):
        #    print(i, t.encode('latin_1').decode('utf8'))
        text = text[1].encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
        print(text)
        self.tasklog.log(mode='manual', in_log = 'task resolved: '+ text)
        text = re.sub(r'[\s共筆分頁,]', r'', text)
        print(text)
        self.totalCount, self.totalPage = [int(t) for t in text.split('、')]
    
    def h3_info_collector(self, pageStart, pageEnd):
        item_count = 0
        for self.pageNow in range(pageStart, pageEnd+1):
            self.this_round_time_start()
            if self.pageNow > 1:
                self.set_form_data_url1(mode = 1, currentPage = self.pageNow)
            else:
                self.set_form_data_url1(mode = 0)
            
            self.proxy_monitor()
            self.first_connection()

            for self.pageItem, o in enumerate(self.oncontextmenu, 1):
                self.get_banKey_objectId(o)
                self.second_connection()
                if not self.get_h3():
                    continue
        
                #parser = parser_cmpy_type(self.h3_query)
                parser = self.parser[self.h3_query]
                
                
                if self.h3_text not in self.objidlog:
                    self.objidlog[self.h3_text] = set()
                self.objidlog[self.h3_text].add(self.objectId)
                
                #if len(self.objectId[self.h3_text]) >= 1000:
                #    continue
                
                if self.h3_text not in self.tr:                    
                    trset = parser.retrive_tr(self.response, set(), 
                                              {'banNo':str(self.banNo),
                                               'brBanNo':str(self.brBanNo),
                                               'banKey':str(self.banKey),
                                               'estbId':str(self.estbId),
                                               'objectId':str(self.objectId)},
                                              {'page':str(self.pageNow),
                                               'item':str(self.pageItem)})
                else:
                    trset = parser.retrive_tr(self.response, self.tr[self.h3_text],  
                                              {'banNo':str(self.banNo),
                                               'brBanNo':str(self.brBanNo),
                                               'banKey':str(self.banKey),
                                               'estbId':str(self.estbId),
                                               'objectId':str(self.objectId)},
                                              {'page':str(self.pageNow),
                                               'item':str(self.pageItem)})
                #    self.tr[self.h3_text] = set()
                    
                #trset = parser.retrive_tr(self.response, self.tr[self.h3_text], self.h3_text)
                
                if self.h3_text not in self.tr:
                    self.tr[self.h3_text] = trset
                    
                    if self.h3_text not in self.trlog:
                        self.trlog[self.h3_text] = dict()
                        
                    for s in trset:
                        if s not in self.trlog[self.h3_text]:
                            (self.trlog[self.h3_text])[s] = (self.banNo if self.banNo != '' else( self.brBanNo if  self.brBanNo != '' else self.estbId))
                else:
                    self.tr[self.h3_text] |= trset
                    
                
                #del parser
                
                
                self.random_sleep(scale = self.sleep_scale)
            else:
                item_count += self.pageItem
                #self.this_round_time_end()
                #self.this_round_exectime()
                self.tasklog.log(mode='format', args=(self.exectime(), self.this_round_exectime(), self.pageNow, self.pageItem), postfix = 'page finished, total {: >6d} items'.format(item_count))
                print('==================================================')
                print('page', self.pageNow, 'total', item_count , ' time', self.exectime(), 'round time', self.this_round_exectime())
                print('==================================================')


                if item_count >= self.flush_threshold:
                    #print('end of h3_info_collector', ' total: ', t, ' pages: ', p)
                    print('end of h3_info_collector() pages:{} items:{}'.format(self.pageNow, item_count))
                    self.tasklog.log(mode='manual', in_log = 'end of h3_info_collector() pages:{} items:{}'.format(self.pageNow, item_count))
                    return
       
            
    def second_page_not_found(self):
        selector = etree.HTML(crawler.response.content)
        texts = selector.xpath('//table/tr/td/table/tr/td/descendant::*/text()')
        
        clean_texts = list()
        for t in texts:
            #t = t.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
            t = re.sub(r'\s', r'', t)
            if t:
                clean_texts.append(t)
        else:
            if '很抱歉，您所存取的網頁系統暫時無法回應。' in clean_texts and '回上一頁' in clean_texts and '回首頁' in clean_texts:
                return True
            else:
                return False
       
    def output_files(self, itemStart, itemEnd):
        d = datetime.now()
        timestamp = "{0:0>4d}{1:0>2d}{2:0>2d}_{3:0>2d}{4:0>2d}{5:0>2d}".format(d.year,d.month,d.day,d.hour,d.minute,d.second)
        fname = '{0:　>5s}@{1: >10s}-{2: >17s}'.format(self.qryCond, str(self.qryType[0]),timestamp)        
        #fname = '{0:　>5s}@{1: >10s} [{2: >6d}-{3: >6d}][{4: >6d}-{5: >6d}]-{6: >17s}'.format(self.qryCond, str(self.qryType[0]), self.pageStart, self.pageEnd, itemStart, itemEnd,timestamp)        
        for key in this.results:
            if this.results[key]:
                #j = json.dumps(this.results[key], ensure_ascii=False)
                j = this.results[key]
                #with open(fname+'_'+key+'_json.json', 'w') as jout:
                #    json.dump(j, jout, ensure_ascii=False)
                with open(self.total_json_name+'_json.json', 'a') as tjout:
                    json.dump(j, tjout, ensure_ascii=False)
                    tjout.write(',\n')
                
                #with open(fname+'_'+key+'_json.pkl', 'wb') as jpklout:  
                #    pickle.dump(j, jpklout)
                    
                #df = pd.DataFrame(this.results[key])
                #with open(fname+'_'+key+'df.csv', 'w') as dfcsvout:
                #    df.to_csv(dfcsvout, index=False)
                #with open(fname+'_'+key+'df.pkl', 'wb') as dfpklout:
                #    pickle.dump(j, dfpklout)
                    
                #with open(fname+'_'+key+'content.html', 'w') as contentout:
                #    contentout.write(self.response.content.decode('utf8'))
                #    #pickle.dump(self.response.content.decode('utf8'), contentout)
                    
    def set_pageStart(self, pageStart):
        self.pageStart = pageStart

    def set_pageEnd(self, pageEnd):
        self.pageEnd = pageEnd


        
    def parse_and_gen_schema(self, pageStart=1, pageEnd=1): 
        self.set_pageStart(pageStart)
        self.set_pageEnd(pageEnd)
        
        item_count = 0
        item_last = 0
        item_count_flush = 0
        for self.pageNow in range(self.pageStart, self.pageEnd+1):
            self.this_round_time_start()
            #self.pageNow = p
            if self.pageNow > 1:
                self.set_form_data_url1(mode = 1, currentPage = self.pageNow)
            else:
                self.set_form_data_url1(mode = 0)
              
            # 在first_connection刷完一頁(20筆)，檢查一次是否超過self.proxy_tick，若是就關掉舊的session，並轉到proxy
            self.proxy_monitor()
            
            # self.first_connection() 出問題時重試10次
            retry = 0
            while not self.first_connection():
                if retry > 10:
                    with open('skip_query.log', 'a') as skpf:
                        skpf.write(self.qryCond+str(self.qryType)+'\n')
                    continue
                
                retry += 1
                self.tasklog.log(mode='manual', in_log = 'first_connection() @ page{} failed, retry {} times'.format(self.pageNow, retry))
                time.sleep(10)
                
            for self.pageItem, o in enumerate(self.oncontextmenu, 1):
                #self.pageItem = i
                self.get_banKey_objectId(o)
                
                retry = 0
                # self.second_connection()
                while not self.second_connection():
                    if retry > 10:
                        continue
                    retry += 1
                    self.tasklog.log(mode='manual', in_log = 'second_connection() @ page{}  item {} failed, retry {} times'.format(self.pageNow, self.pageItem, retry))
                    time.sleep(10)


                
                
                if self.second_page_not_found():
                    # 如果第二層商登資料網頁不存在，跳過
                    self.tasklog.log(mode='format', args=(self.exectime(), self.this_round_exectime(), self.pageNow, self.pageItem), postfix = 'second page not found')                    
                    continue
                
                    
                self.get_h3()
                #parser = parser_cmpy_type(self.h3_query)
                parser = self.parser[self.h3_query]
                parser.init_data_schema()
                # 改掉log的方式
                parser.parser(self.response, 
                              {'banNo':str(self.banNo),
                               'brBanNo':str(self.brBanNo),
                               'banKey':str(self.banKey),
                               'estbId':str(self.estbId),
                               'objectId':str(self.objectId)},
                              {'page':str(self.pageNow),
                               'item':str(self.pageItem)})
                
                
            
                #self.end = time.time()
                self.exectime(self.h3_query)
                print(self.h3_query, parser.data_schema)             
                #self.results[self.h3_query].append(parser.data_schema)
                # add some task info

                parser.data_schema['qryCond'] = self.qryCond
                parser.data_schema['h3_query'] = self.h3_query
                parser.data_schema['pageNow'] = self.pageNow
                parser.data_schema['pageItem'] = self.pageItem
                
                self.results[self.h3_query].append( copy.deepcopy(parser.data_schema) )
                #print("----------- self.results")
                #print(self.results)
                #print("----------- self.results")
                self.tasklog.log(mode='format', args=(self.exectime(), self.this_round_exectime(), self.pageNow, self.pageItem), postfix = 'done') 
                self.random_sleep(scale = self.sleep_scale)
                item_count += 1
                item_count_flush += 1
            else:
                #item_count += self.pageItem
                #self.this_round_exectime()
                #self.this_round_time_end()
                
                self.tasklog.log(mode='format', args=(self.exectime(), self.this_round_exectime(), self.pageNow, self.pageItem), postfix = 'page finished, total {: >6d} items'.format(item_count))
                #self.task_log(mode='manual', in_log='page ', self.pageNow, ' total ', t , ' totaltime ', self.exectime(), '\n', self.this_round_exectime())
                print('==================================================')
                print('page', self.pageNow, 'total', item_count , ' time', self.exectime(), 'round time', self.this_round_exectime())
                print('==================================================')
                if item_count_flush >= self.flush_threshold:
                    item_count_flush = 0
                    
                    self.output_files(item_last, item_count)
                    print('flush results to pandas pages:{} items:{}'.format(self.pageNow, item_count))
                    self.tasklog.log(mode='manual', in_log = 'flush results to pandas pages:{} items:{}'.format(self.pageNow, item_count))
                    
                    del self.results
                    self.results = defaultdict(list)
                    item_last = item_count
                    #return
                #self.results.append( (self.querytype, parser.data_schema) )
                self.random_sleep(scale = self.sleep_scale)
        else:
            #self.output_files()
            self.output_files(item_last, item_count)
            print('flush results to pandas pages:{} items:{}'.format(self.pageNow, item_count))
            self.tasklog.log(mode='manual', in_log = 'flush results to pandas pages:{} items:{}'.format(self.pageNow, item_count))

            print('end of parse_and_gen_schema() pages:{} items:{}'.format(self.pageNow, item_count))
            self.tasklog.log(mode='manual', in_log = 'end of parse_and_gen_schema() pages:{} items:{}'.format(self.pageNow, item_count))
            self.tasklog.log_flush()
            
            del self.results
            self.results = defaultdict(list)
            item_last = item_count
            
        return self.results


# In[6]:

import copy

class parser_cmpy_type:

    # 公司基本資料
    col_Cmpy=['統一編號', '公司狀況', '公司名稱', '資本總額(元)', '實收資本額(元)', '代表人姓名', 
              '公司所在地', '登記機關', '核准設立日期', '最後核准變更日期', '停業日期(起)', '停業日期(迄)',
              '所營事業資料' ]
    rule_Cmpy={
        '統一編號':'rule0',
        '公司狀況':'rule0',
        '公司名稱':'rule0',
        '資本總額(元)':'rule0',
        '實收資本額(元)':'rule0',
        '代表人姓名':'rule0',
        '公司所在地':'rule0',
        '登記機關':'rule0',
        '核准設立日期':'rule0',
        '最後核准變更日期':'rule0',
        '停業日期(起)':'rule0',
        '停業日期(迄)':'rule0',
        '所營事業資料':'rule5'
    }
    col_Cmpy_Shareholder=['序號','職稱','姓名','所代表法人','持有股份數']
    col_Cmpy_Mgr=[]
    col_Cmpy_BrCmpy=['序號','統一編號','分公司名稱','公司狀況','分公司核准設立日期','最後核准變更日期']
    
    # 外國公司報備基本資料
    col_CmpyFrgnRp=['統一編號', '公司狀況', '公司名稱', '訴訟及非訴訟代理人姓名', '辦事處所在地', '登記機關',
                    '核准設立日期', '最後核准變更日期', '代表人在中華民國境內所為的法律行為']    
    rule_CmpyFrgnRp={
        '統一編號':'rule0',
        '公司狀況':'rule0',
        '公司名稱':'rule0',
        '訴訟及非訴訟代理人姓名':'rule0',
        '辦事處所在地':'rule0',
        '登記機關':'rule0',
        '核准設立日期':'rule0',# 會有空值 <td></td>
        '最後核准變更日期':'rule0',# 會有空值 <td></td>
        '代表人在中華民國境內所為的法律行為':'rule0'
        #'所營事業資料':'rule5'
    }

    # 外國公司認許基本資料
    col_CmpyFrgn=['統一編號', '公司狀況', '公司名稱', '在中華民國境內營運資金', '訴訟及非訴訟代理人姓名', '分公司所在地',
                  #'公司所在地', 
                  '登記機關', '核准設立日期', '最後核准變更日期', '停業日期(起)', '停業日期(迄)', '所營事業資料']
    rule_CmpyFrgn={
        '統一編號':'rule0',
        '公司狀況':'rule0',# 處理跨<br>串字，<br>後面可能是空字串
        '公司名稱':'rule0',
        '在中華民國境內營運資金':'rule0',
        '訴訟及非訴訟代理人姓名':'rule0',
        '分公司所在地':'rule0',
        #'公司所在地':'rule0',
        '登記機關':'rule0',
        '核准設立日期':'rule0',
        '最後核准變更日期':'rule0', # <td></td>
        '停業日期(起)':'rule0',
        '停業日期(迄)':'rule0',
        '所營事業資料':'rule5'
    }
    col_CmpyFrgn_BrCmpy=['序號','統一編號','分公司名稱','公司狀況','分公司核准設立日期','最後核准變更日期']


    
    # 大陸公司許可報備基本資料
    col_CmpyCnRp=['統一編號', '公司狀況', '股權狀況', '公司名稱', '訴訟及非訴訟代理人姓名', '辦事處所在地',
                  '登記機關', '核准設立日期', '最後核准變更日期', '代表人在台灣地區業務活動範圍']    
    rule_CmpyCnRp={
        '統一編號':'rule0',
        '公司狀況':'rule0',
        '股權狀況':'rule0',
        '公司名稱':'rule0',# 有<br>串起來
        '訴訟及非訴訟代理人姓名':'rule0',
        '辦事處所在地':'rule0',
        '登記機關':'rule0',
        '核准設立日期':'rule0',
        '最後核准變更日期':'rule0',
        '代表人在台灣地區業務活動範圍':'rule0'
        #'所營事業資料':'rule5'
    }
    
    col_CmpyCnRp_BrCmpy=['序號','統一編號','分公司名稱','公司狀況','分公司核准設立日期','最後核准變更日期']



    # 大陸公司許可基本資料
    col_CmpyCn=['統一編號', '公司狀況', '股權狀況', '公司名稱', '在台灣地區營業所用', '訴訟及非訴訟代理人姓名', 
                '分公司所在地', #'公司所在地', 
                '登記機關', '核准設立日期', '最後核准變更日期', 
                #'停業日期(起)', '停業日期(迄)', 
                '所營事業資料']
    rule_CmpyCn={
        '統一編號':'rule0',
        '公司狀況':'rule0',
        '股權狀況':'rule0',
        '公司名稱':'rule0',# 有<br>串起來
        '在台灣地區營業所用':'rule0',
        '訴訟及非訴訟代理人姓名':'rule0',
        '分公司所在地':'rule0',
        #'公司所在地':'null',
        '登記機關':'rule0',
        '核准設立日期':'rule0',
        '最後核准變更日期':'rule0',
        #'停業日期(起)':'null',
        #'停業日期(迄)':'null',
        '所營事業資料':'rule5'
    }
    col_CmpyCn_BrCmpy=['序號','統一編號','分公司名稱','公司狀況','分公司核准設立日期','最後核准變更日期']
    
    # 分公司資料
    col_BrCmpy=['分公司統一編號', '分公司狀況', '分公司名稱', '分公司經理姓名', '分公司所在地', '核准設立日期', 
                #'廢止日期', 
                '最後核准變更日期', '總(本)公司統一編號', '總(本)公司名稱']
    rule_BrCmpy={
        '分公司統一編號':'rule0',
        '分公司狀況':'rule0',
        '分公司名稱':'rule0',
        '分公司經理姓名':'rule0',
        '分公司所在地':'rule0',
        '核准設立日期':'rule0',
        #'廢止日期':'rule0',
        '最後核准變更日期':'rule0',
        '總(本)公司統一編號':'rule1', # <br><a></a></br>
        '總(本)公司名稱':'rule1' # <br><a>"雙"<img>"有限公司"</a></br>要處理未識別字有圖的狀況
    }
    
    # 商業登記基本資料
    col_Busm=['登記機關', '商業統一編號', '核准設立日期', '最近異動日期', '商業名稱', '負責人姓名',
              '負責人姓名-出資額(元)', '現況', '資本額(元)', '組織類型', '地址', '營業項目']
    
    
    """
    <tr>
    <td class="txt_td">負責人姓名</td>
        <td>
            <table style="width:100%">
                <tbody><tr>
                    <td width="50%">蔡培火</td>         rule21
                    <td width="50%">出資額(元):0</td>   rule22
                </tr></tbody></table>
        </td>
    </tr>
    """
    
    rule_Busm={
        '登記機關':'rule0',
        '商業統一編號':'rule0', # 可能只有訂閱鈕
        '核准設立日期':'rule0', 
        '最近異動日期':'rule0',
        '商業名稱':'rule0', # <td><a>"雙"<img>"有限公司"</a></td>要處理未識別字有圖的狀況
        '負責人姓名':'rule2',
        '負責人姓名-出資額(元)':'rule2',# 出資額(元):0 
        '合夥人姓名':'rule2',
        '合夥人姓名-出資額(元)':'rule2',
        '現況':'rule0',
        '資本額(元)':'rule0',
        '組織類型':'rule0',
        '地址':'rule0',
        '營業項目':'rule5' # 各種金紙冥紙等有關祭拜用品零售買賣（炮竹除外）@@
    }
    col_Busm_BrBusm=['分支機構統一編號','分支機構名稱','分支機構地址','分支機構經理人姓名'] 
    
    # 商業登記基本資料(分支機構)
    col_BrBusm=['分支機構登記機關', '分支機構統一編號', '核准設立日期', '最近異動日期', '分支機構名稱', '分支機構經理人姓名', 
                '分支機構現況', '分支機構地址', '總機構統一編號', '總(本)商業名稱']
    rule_BrBusm={'分支機構登記機關':'rule0', 
                 '分支機構統一編號':'rule0', 
                 '核准設立日期':'rule0',
                 '最近異動日期':'rule0',
                 '分支機構名稱':'rule0',
                 '分支機構經理人姓名':'rule0',
                 '分支機構現況':'rule0',
                 '分支機構地址':'rule0', 
                 '總機構統一編號':'rule1',
                 '總(本)商業名稱':'rule1'}
    
    # 工廠基本資料
    col_Fact=['登記機關', '工廠名稱', '工廠登記編號', '工廠登記核准日期', '工廠設立許可案號', '工廠設立核准日期', 
              '工廠地址', '工廠負責人姓名', '公司(營利事業)統一編號', '工廠組織型態', '工廠資本額', '工廠登記狀態',
              '最後核准變更日期', '工廠設立許可廢止核准日期', '工廠登記歇業核准日期', '工廠登記廢止核准日期', '工廠登記公告廢止核准日期', '最近一次校正年度', 
              '最近一次校正結果', '依據行政院主計處『中華民國行業標準分類』100年3月第9次修訂', '產業類別', '主要產品']
    rule_Fact={
        '登記機關':'rule0',
        '工廠名稱':'rule0',
        '工廠登記編號':'rule0',
        '工廠登記核准日期':'rule0',
        '工廠設立許可案號':'rule0',
        '工廠設立核准日期':'rule0',
        '工廠地址':'rule0',
        '工廠負責人姓名':'rule0',
        '公司(營利事業)統一編號':'rule0',
        '工廠組織型態':'rule0',
        '工廠資本額':'rule0',
        '工廠登記狀態':'rule0',
        '最後核准變更日期':'rule0',
        '工廠設立許可廢止核准日期':'rule0',
        '工廠登記歇業核准日期':'rule0',
        '工廠登記廢止核准日期':'rule0',
        '工廠登記公告廢止核准日期':'rule0',
        '最近一次校正年度':'rule0',
        '最近一次校正結果':'rule0',
        '依據行政院主計處『中華民國行業標準分類』100年3月第9次修訂':'rule0', # 這個tr是有<br>的
        #'依據行政院主計處『中華民國行業標準分類』':'null',
        '產業類別':'rule5', # 單一項最後面有<br>
        '主要產品':'rule5'
    }
    # 有限合夥登記基本資料
    col_Lmtd=['登記機關', '統一編號', '有限合夥名稱', '所在地', '實收出資額(元)', '核准設立日期', '現況', 
              '存續期間', '最近一次登記狀況核准日期及文號', '代表人姓名', '代表人姓名-出資額(元)', '普通合夥人姓名-責任類型', '普通合夥人姓名',
              '普通合夥人姓名-出資額(元)', '普通合夥人姓名-責任類型', '有限合夥人', '有限合夥人-出資額(元)', '有限合夥人-責任類型', '經理人姓名',
              '約定解散事由', '所營事業項目']
    rule_Lmtd={
        '登記機關':'rule0',
        '統一編號':'rule0',
        '有限合夥名稱':'rule0',
        '所在地':'rule0',
        '實收出資額(元)':'rule0',
        '核准設立日期':'rule0',
        '現況':'rule0',
        '存續期間':'rule0',
        '最近一次登記狀況核准日期及文號':'rule0',# 標題有用<br>隔開
        '代表人姓名':'rule2',
        '代表人姓名-出資額(元)':'rule2',
        '代表人姓名-責任類型':'rule2',
        '普通合夥人姓名':'rule2',
        '普通合夥人姓名-出資額(元)':'rule2',
        '普通合夥人姓名-責任類型':'rule2',
        '有限合夥人':'rule2',
        '有限合夥人-出資額(元)':'rule2',
        '有限合夥人-責任類型':'rule2',
        '經理人姓名':'rule0',
        '約定解散事由':'rule0',
        '所營事業項目':'rule5'
    }
    col_Lmtd_BrBusm=['分支機構統一編號','分支機構名稱','分支機構地址','分支機構經理人姓名']
    
    # 有限合夥登記基本資料(分支機構)
    col_BrLmtd=['登記機關', '統一編號', '分支機構名稱', '所在地', '在中華民國境內營運資金', '核准設立日期', 
                '登記狀況', '最近一次登記狀況核准日期及文號', '在中華民國境內負責人', '分支機構經理人', '所營事業項目', 
                '本機構統一編號', '本機構名稱']
    rule_BrLmtd={
        '登記機關':'rule0',
        '統一編號':'rule0',
        '分支機構名稱':'rule0',
        '所在地':'rule0',
        '在中華民國境內營運資金':'rule0',
        '核准設立日期':'rule0',
        '登記狀況':'rule0',
        '最近一次登記狀況核准日期及文號':'rule0',# 標題有用<br>隔開
        '在中華民國境內負責人':'rule0',
        '分支機構經理人':'rule0',
        '所營事業項目':'rule5',
        '本機構統一編號':'rule0',
        '本機構名稱':'rule0'
    }
    
    
    col_book = {'Cmpy':col_Cmpy, 
                'CmpyFrgnRp':col_CmpyFrgnRp, 
                'CmpyFrgn':col_CmpyFrgn, 
                'CmpyCnRp':col_CmpyCnRp, 
                'CmpyCn':col_CmpyCn, 
                'BrCmpy':col_BrCmpy, 
                'Busm':col_Busm, 
                'BrBusm':col_BrBusm, 
                'Fact':col_Fact, 
                'Lmtd':col_Lmtd, 
                'BrLmtd':col_BrLmtd}
    
    col_sub_book = {'Cmpy':[col_Cmpy_Shareholder, col_Cmpy_Mgr, col_Cmpy_BrCmpy],
                    'CmpyFrgnRp':[], 
                    'CmpyFrgn':[col_CmpyFrgn_BrCmpy], 
                    'CmpyCnRp':[col_CmpyCnRp_BrCmpy], 
                    'CmpyCn':[col_CmpyCn_BrCmpy], 
                    'BrCmpy':[], 
                    'Busm':[col_Busm_BrBusm], 
                    'BrBusm':[], 
                    'Fact':[], 
                    'Lmtd':[col_Lmtd_BrBusm], 
                    'BrLmtd':col_BrLmtd}
    
    rule_book = {'Cmpy':rule_Cmpy, 
                 'CmpyFrgnRp':rule_CmpyFrgnRp, 
                 'CmpyFrgn':rule_CmpyFrgn, 
                 'CmpyCnRp':rule_CmpyCnRp, 
                 'CmpyCn':rule_CmpyCn, 
                 'BrCmpy':rule_BrCmpy, 
                 'Busm':rule_Busm, 
                 'BrBusm':rule_BrBusm, 
                 'Fact':rule_Fact, 
                 'Lmtd':rule_Lmtd, 
                 'BrLmtd':rule_BrLmtd}
    
    
    def __init__(self, h3_query, tasklog):
        #self.table_to_db = parser_cmpy_type.table_to_db_assign[cmpy_type]
        self.h3_query = h3_query
        self.tr_rule = parser_cmpy_type.rule_book[self.h3_query]        
        self.data_schema = dict()
        self.td_rule_handler = {
            'rule0'   :self.rule0,
            'rule1'   :self.rule1,
            'rule2'   :self.rule2,
            #'rule3'   :self.special_rule3,
            #'rule4'   :self.special_rule4,
            'rule5'   :self.rule5,
        }
        self.tasklog = tasklog
        
    def init_data_schema(self):
        self.data_schema = dict()
        #for key in parser_cmpy_type.col_book[self.h3_query]:
        #    self.data_schema[key] = ''
            
        #print('init_data_schema() = ', self.data_schema)
    """
    def clean_text(self, text, reencode=True):
        import re

        if text is None or not len(text):
            return ""
        
        if reencode:
            text = text.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
        text = re.sub(r'\s', r'', text)
        text = re.sub(r'[「」]', r'', text)
        return text
    """
    
    def clean_text(self, text):
        text = text.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
        text = re.sub(r'\s', r'', text)
        text = re.sub(r'[「」]',r'', text)
        return text
        
    def clean_Minguo_calendar(self, text):
        #if text is None or not text:
        if text is None or not len(text):
            return ""
            
        text_year = text.split('年')[0]
        text_month = text.split('年')[1].split('月')[0]
        text_day = text.split('年')[1].split('月')[1].replace('日','')
        text_year = str(int(text_year) + 1911)
        return "{}-{}-{}".format(text_year, text_month, text_day)
    
    def td_remove_br(self, td):
        """
        preprocess ./tr/td, remove <br> between text()
        """
        if td is None:
            return ""
        
        tds = td.xpath('./td')
        text = list()
        for t in td.xpath('./text()'):
            t = t.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
            t = re.sub(r'\s', r'', t)
            if t:
                text.append(t)
        #print(''.join(text))
        
        return ''.join(text)
                        
    def special_rule1(self, td):
        """
        分公司資料
          - 總(本)公司統一編號
          - 總(本)公司名稱
        <td>
            <a href="#" onclick="javascript:queryCmpy('03557311', false)" oncontextmenu="javascript:queryCmpy('03557311', true);return false;">
                03557311
            </a>
        </td>
        """
        if td is None or not len(td):
            return ""
        
        a = td.xpath('./a[@href="#"]')
        return self.clean_text(a.text)
        
    def special_rule2(self, td):
        """
        商業登記基本資料
          - 負責人姓名
        <td>
            <table style="width:100%">
                <tbody><tr>
                    <td width="50%">黃霈雯</td>
                    <td width="50%">出資額(元):3,000</td>
                </tr></tbody>
            </table>
        </td>
        """
        if td is None or not len(td):
            return ""
        
        tdtds = td.xpath('./table/tr/td')
        return self.clean_text(tdtds[0].text)
        
    def special_rule3(self, td):
        """
        公司基本資料
          - 核准設立日期
          - 最後核准變更日期
        分公司資料
          - 核准設立日期
          - 最後核准變更日期
        商業登記基本資料
          - 核准設立日期
          - 最近異動日期
        工廠基本資料
          - 工廠登記核准日期
          - 最後核准變更日期
        <td>105年07月28日</td>
        """
        if td is None or not len(td):
            return ""

        
        text = self.clean_text(td.text)
        text = re.sub(r'\(.*\)',r'', text)
        return self.clean_Minguo_calendar(text)
        
        
    def special_rule4(self, td):
        """
        公司基本資料
          - 資本總額(元)
        商業登記基本資料
          - 資本額(元)
        <td>
            3,000
        </td>
        """
        if td is None or not len(td):
            return ""
        
        text = self.clean_text(td.text).replace(',', '')
        if not text.isdigit():
            text = ''
        return text
        
    def special_rule5(self, td):
        """
        公司基本資料
          - 所營事業資料
        
        <td>
            "F106010&nbsp;
            五金批發業"
            <br>
            "F113010&nbsp;
            機械批發業"
            <br>
            "F113020&nbsp;
            電器批發業"
            <br>
            ...
            "ZZ99999&nbsp;
            除許可業務外，得經營法令非禁止或限制之業務"
            <br>
        </td> 
        """
        if td is None or not len(td):
            return ""
        
        #tds = td.xpath('./td')
        text = list()
        for t in td.xpath('./text()'):
            
            t = t.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
            t = re.sub(r'\s', r'', t)
            #t = re.sub(r'[0-9A-Z一二三四五六七八九\.０１２３４５６７８９。]', r'',  t)
            if t:
                text.append(t)
            
        return ','.join(text)
        
    def get_td_text(self, td, sp='', rule=0):
        import re
        """
        get td text from type A cell:
        <td class="txt_td">
            "最近一次登記狀況"
            <br>
            "核准日期及文號"
        </td>
        
        get td text from type B cell:
        <td>
            "
                    大陸商中國銀行股份有限公司(在臺灣地區公司名稱)
            "
            <span>Google搜尋</span>
            <br>
            "
                中國銀行股份有限公司　　　(在大陸地區公司名稱)
            "
            <span id="linkMoea">
                <span>
                    "「"
                    <span>廠商英文名稱查詢(限經營出進口或買賣業務者)</span>
                    "」"
                    <div> ... </div>
                </span>
            </span>
        </td>
        
        get td text from type C cell:
        <td>
            "
                084
                食用油脂
            "
            <br>
            "
                089
                其他食品
            "
            <br>
        </td>        
        """

        if td is None:
            return ""
        
        if rule == 0:
            nodes = td.xpath('./text()')
        elif rule == 1:
            nodes = td.xpath('./descendant::text()')
        elif rule == 5:
            nodes = td.xpath('./text()')            
        
        text = list()
        for t in nodes:
            if t:
                t = self.clean_text(t)
                text.append(t)
        else:
            # 有時<br>後會是空字串，濾掉空字串
            return sp.join([t for t in text if t])
        
    def rule0(self, td):
        return self.get_td_text(td, sp = '+', rule=0)
    
    def rule1(self, td):
        return self.get_td_text(td, sp = '', rule=1)
    
    
    def rule2_json_encode(self, obj):
        import json
        return json.dumps(obj, ensure_ascii=False)
    
    def rule2(self, td, key):
        items = list()
        #texts = td.xpath('./table/tr/td/text()')
        trs = td.xpath('./table/tr')
        for i, tr in enumerate(trs):
            texts = tr.xpath('./td/text()')
            item = dict()
            for t in texts:
                t = self.clean_text(t)
                sub_item = t.split(':')
                if len(sub_item) == 1:
                    item[key]=sub_item[0]
                else:
                    k, v = sub_item
                    item[k]=v
            else:
                items.append(item)
                    #items.append({key+'-'+k: v})
        #return copy.deepcopy(items)
        return items
        #return self.rule2_json_encode(items)
        
    def rule5(self, td):
        rule5_str = self.get_td_text(td, sp = '+', rule=5)
        
        return rule5_str
    
    #def ordinary_rule_br(self, td):
    #    return self.clean_text(self.td_remove_br(td))
    def ordinary_rule(self, td):
        #return self.clean_text(td.text)
        return self.clean_text(self.td_remove_br(td), False)
    
    def retrive_tr(self, res, trcheck, info1, info2):
        selector = etree.HTML(res.content)
        divs = selector.xpath('//div[@class="tab-content"]/div')
        div0 = divs[0]
        trs = div0.xpath('./div[@class="table-responsive"]/table[@class="table table-striped"]/tbody/tr')
        #trs = selector.xpath('//div[@class="table-responsive"]/table[@class="table table-striped"]/tbody/tr')
        
        trset = set()
        for tr in trs:
            tds = tr.xpath('./td')
            td0 = tds[0]
            key = self.get_td_text(td0)
            
            if key not in trcheck:
                #self.tasklog.log('new_tr')
                #self.log('new_tr', info1, info2) 
                self.tasklog.log(mode = 'manual', in_log = self.logstr('new_tr', info1, info2))
            
            trset.add(key)        
        return trset
    
    """
    def log(self, mode, info1, info2):
        info1_str = ' '.join([k+' '+v for k, v in list(info1.items())])
        info2_str = ' '.join(['page', info2['page'], 'item', info2['item']])
        
        with open(self.h3_query + '-' + mode + '.log', 'a') as logfile:
            print(mode,'@', info2_str, 'where', info1_str, '\n')
            logstr = ' '.join(['mode', '@', info2_str, 'where', info1_str, '\n'])
            logfile.write(logstr)
    """
    def logstr(self, mode, info1, info2):
        info1_str = ' '.join([k+' '+v for k, v in list(info1.items())])
        info2_str = ' '.join(['page', info2['page'], 'item', info2['item']])
        return ' '.join([mode, '@', info2_str, 'where', info1_str])
        #with open(self.h3_query + '-' + mode + '.log', 'a') as logfile:
        #    print(mode,'@', info2_str, 'where', info1_str, '\n')
        
        #logfile.write(logstr)
    
    def parser(self, res, info1, info2):
        selector = etree.HTML(res.content)
        divs = selector.xpath('//div[@class="tab-content"]/div')
        div0 = divs[0]
        trs = div0.xpath('./div[@class="table-responsive"]/table[@class="table table-striped"]/tbody/tr')

        for tr in trs:
            tds = tr.xpath('./td')

            td0 = tds[0]
            key = self.get_td_text(td0)
            # 解析出來的tr若只有一欄，不需要解譯
            if len(tds) > 1:
                # 先拿第一個td
                td1 = tds[1]
                
                # 如果tr的項目名稱不在預設的欄位，將它擴充(預設rule0)，記得要處理col_book跟rule_book
                if key not in parser_cmpy_type.col_book[self.h3_query]:
                    parser_cmpy_type.col_book[self.h3_query].append(key)
                    td1_first_child = td1.xpath('./child::*')
                    if len(td1_first_child) == 0:
                        (parser_cmpy_type.rule_book[self.h3_query])[key] = 'rule0'
                    elif td1_first_child[0].tag == 'table':
                        (parser_cmpy_type.rule_book[self.h3_query])[key] = 'rule2'
                    elif td1_first_child[0].tag == 'a':
                        (parser_cmpy_type.rule_book[self.h3_query])[key] = 'rule1'
                    else:
                        (parser_cmpy_type.rule_book[self.h3_query])[key] = 'rule0'
                        

                    # 做個log
                    #self.log('new_tr', info1, info2)
                    self.tasklog.log(mode = 'manual', in_log = self.logstr('new_tr', info1, info2))
                
                # 解譯 
                
                rule = self.tr_rule[key]
                if rule == 'rule2':
                    value = self.td_rule_handler[rule](td1, key)
                    self.data_schema[key] = value
                    #for key, value in items:
                    #    self.data_schema[key] = value
                    #    (parser_cmpy_type.rule_book[self.h3_query])[key] = 'rule2'
                              
                else:
                    value = self.td_rule_handler[rule](td1)
                    self.data_schema[key] = value
                    
            # 只有一個tr的做個log
            else:
                # 寫個information
                #self.log('single_col_tr', info1, info2)
                self.tasklog.log(mode = 'manual', in_log = self.logstr('single_col_tr', info1, info2))
                
        else:
            self.data_schema['update_time'] = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())
            



    


# In[7]:

import pickle
import proxypool
# usage:
# cralwer_v10.py 3        /usr/local/bin/phantomjs 60005            3
#                job號碼   phontomjs執行檔位置        查詢流水號，可接關  proxy_tick

tasknum = sys.argv[1]
path_phantomjs = sys.argv[2]


#tasknum = 1
#path_phantomjs = '/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs'



task_dir = './task_ini/'
task = pickle.load(open(task_dir+'instance-g{}_v10.x_job.pkl'.format(tasknum), 'rb'))
taskstart = int(sys.argv[3]) if len(sys.argv) >= 4 else int(task[0][0])
#proxy_tick = int(sys.argv[4]) if len(sys.argv) >= 5 else 1

#taskstart = 0
#proxy_tick = 20

#config['TASK']['1']
#task_proxy = proxypool.proxypool(path_phantomjs = path_phantomjs)
#task_proxy.proxy_set_max = 100
#task_proxy.world_proxy()

crawler = cmpyinfo_crawler(path_phantomjs = path_phantomjs, logname='instance{}_v10.x_job.log'.format(tasknum), sleep_scale='none')
crawler.proxypool.proxy_set_max = 150
crawler.proxypool.world_proxy()
#crawler.proxy_tick = proxy_tick
crawler.proxypool.none_freq = 4

#crawler.qryCond = t[1]
#crawler.qryType = t[2]
#crawler.pageStart = t[3]
#crawler.pageEnd = t[4]

for t in task:
    print("======================================")
    print("task ", t[0], ": ", t[1], "@", t[2])
    print("======================================")
    
    crawler.qryCond = t[1]
    crawler.qryType = t[2]
    crawler.pageStart = t[3]
    crawler.pageEnd = t[4]
    if int(t[0]) < taskstart:
        continue
    
    
    
    crawler.set_form_data_url1(mode = 0, currentPage = 1)
    if not crawler.first_connection():
        crawler.change_proxy()
        if not crawler.first_connection():

            crawler.set_proxy(None)
            continue
    #time.sleep(random.choice([5,5.5,6,7,10,3,5,4,7,7,1]))
    crawler.resolve_page()
    crawler.parse_and_gen_schema(1, crawler.totalPage)
    #if crawler.proxy_tick < 0:
    #    import random
    #    time.sleep(random.randint(50,70))
    #else:
    #    crawler.proxy_monitor()


# In[ ]:



