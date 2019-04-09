from bs4 import BeautifulSoup as bs
import datetime
import re
import requests
import pandas as pd
from selenium import webdriver
import sys
import time
from collections import defaultdict


from crawler import *

def start():
    print ('..initializing..')
    username = sys.argv[1]
    psw = sys.argv[2]

    # 登录小说网站
    # 游客只能浏览小说列表前十页
    print ('..starting logging in..')
    chromePath = '../../../chromedriver.exe'
    wd = webdriver.Chrome(executable_path= chromePath)
    loginUrl = 'http://my.jjwxc.net/login.php'
    wd.get(loginUrl)
    wd.find_element_by_xpath('//*[@id="loginname"]').send_keys(username)
    wd.find_element_by_xpath('//*[@id="loginpassword"]').send_keys(psw)
    wd.find_element_by_xpath('//*[@id="login_submit_tr"]/input').submit()

    req = requests.Session() 
    cookies = wd.get_cookies() 
    for cookie in cookies:
        req.cookies.set(cookie['name'],cookie['value']) 
    req.headers.clear() 

    # 从小说列表中读取单本小说url
    basic_url = 'http://www.jjwxc.net/bookbase.php?fw0=0&fbsj=0&ycx1=1&xx0=0&mainview0=0&sd0=0&lx0=0&fg0=0&sortType=0&isfinish=0&collectiontypes=ors&searchkeywords=&page='
    max_page_id = 2001 # 读取列表的最大页数
    df = pd.DataFrame(columns=['prot', 'supp', 'theme', 'topc', 'date','year','month', 'scores', 'url'])

    print ('..fetching novel list..')
    nv_list = many_novels_url(basic_url, max_page_id, req) # 历遍小说列表，读取小说url
    print ('==============Get %d novels' % len(nv_list))
    print ('=============================')

    print ('..fetching done..')
    print ()


    print ('..fetching and storing info..')
    multiple_novels(nv_list, df) # 历遍小说url， 提取信息

    df.to_csv('data.csv', encoding='utf_8_sig') # 存至csv文件，中文encoding

start()





