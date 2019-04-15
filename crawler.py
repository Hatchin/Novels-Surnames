import requests
from bs4 import BeautifulSoup as bs
import re
import datetime
import pandas as pd
import time
import copy
from collections import defaultdict

def one_novel_info(url):
    """
    Extract useful data from the webpage of a novel.
    从单本小说首页中抓取该文信息，包括主角，配角，类别，主题，日期时间与积分
    """
    # 获取网页html
    res = requests.get(url)
    html_encode = 'gb2312' # 中文encoding 
    soup = bs(res.content.decode(html_encode,errors='ignore'), "html.parser")
    
    # 截取有用的tag
    meta_info = soup.find('meta', {'name': 'Description'}) 
    # theme = soup.find('span', {'itemprop':'genre'}).text.strip('\r\n').strip(' ')
    theme_info = soup.find('span', {'itemprop':'genre'})

    # 例子：
    # <span class="bluetext">搜索关键字：主角：李维斯，宗铭。 ┃ 配角：于天河，焦磊。唐熠，桑菡。 ┃ 其它：绝世猫痞</span>
    # <span style="color:#000;float:none" itemprop="genre"> 原创-纯爱-近代现代-悬疑 </span>

    # 提取主题信息
    # 为主题缺失的url补上空返回
    if theme_info:
        try:
            theme = theme_info.text.strip('\r\n').strip(' ')
        except: 
            print ('===========theme not formatted=========')
            theme = ''
    else:
        print ('======== No theme found!===============')
        theme = ''

    # 提取meta data
    # 为无法提取的meta data补上空返回
    if meta_info:
        try:
            writer_book_prot, supp, other = meta_info.attrs['content'].split(' ┃ ')
        except:
            print ('========meta data not formatted============')
            return '', '', '', '','','','','', url
    else:
        print ('========= No meta info find! ===========')
        return '', '', '', '','','','','', url

    
    # 正则化取词
    prot_reg = re.compile("主角：(.*)$")
    supp_reg = re.compile("配角：(.*)$")
    topc_reg = re.compile("其它：(.*) 最新更新:")
    time_reg = re.compile("最新更新:(.*) 作品积分：")
    scor_reg = re.compile("作品积分：(.*)$")
    
    protagonist = re.split('、 |，|/',prot_reg.search(writer_book_prot).group(1)) # 主角
    supporting = re.split('、 |，|/',supp_reg.search(supp).group(1)) # 配角
    topic = topc_reg.search(other).group(1).split('，') # 标签
    updating_str = time_reg.search(other).group(1) # 最近更新日期 （string）
    updating = datetime.datetime.strptime(updating_str, '%Y-%m-%d %H:%M:%S') # 最近更新日期 （datetime）
    update_month = updating.month # 最近更新-月份
    update_year = updating.year # 最近更新 - 年份
    scores = int(scor_reg.search(other).group(1)) # 积分
    
    print (protagonist)
    return protagonist, supporting, theme, topic, updating, update_year, update_month, scores, url

def fetch_novels_url(requesting, url):
    """
    从单页小说列表中获取该页所有小说url
    """
    # 获取小说列表url
    res = requesting.get(url)
    res.encoding = 'utf-8'
    soup = bs(res.content, 'html.parser')

    potential_info = soup.find_all('a', {'title':True}) # 截取相应tag
    # 选取小说url
    novels = [i.attrs['href'] for i in potential_info if i.attrs['href'].startswith('onebook.php?novelid')] 
    return novels

def many_novels_url(basic_url, max_page_id, req):
    """
    历遍m页小说列表，获取其小说url
    """
    nv_list = [] # 储存小说url
    i = 1
    bad_connect = defaultdict(int) # 记录每个url连接失败的次数

    while i < max_page_id:
        page_url = basic_url + str(i)
        
        # 获取第i页小说列表
        try:
            new_urls = fetch_novels_url(req, page_url)
            nv_list += new_urls
            print ('.. page %d' % i)
            i += 1

        # 处理请求过多而连接出错    
        except:
            print ()
            print ('!!')
            print ('Sorry, failing... Waiting to restart page %d' % i)
            
            # 只重连失败5次以内的url，如果大于5次，放弃该小说
            if bad_connect[page_url] < 5:
                bad_connect[page_url] += 1 
            else: # 放弃
                print ('============Too many failures!! =============')
                print (page_url)
                i += 1 # 跳过该页
                print ()

            time.sleep(15) # 暂停15秒重新连接
    return nv_list
        
    

def multiple_novels(novels_list, df):
    """
    提供一个包含多部小说url的list，返回一个dataframe，包含每本小说的相应信息
    """
    i = len(df)
    bad_connect = defaultdict(int) # 记录曾连接失败的url的失败次数
    while novels_list:
        print ('%d novels left...' % len(novels_list))
        # 读取一本小说 
        novel = novels_list.pop()
        url_whole = 'http://www.jjwxc.net/'+novel
        print ('Fetching -- ', url_whole)

        # 提取其信息， 存于dataframe中
        try:
            newe_row_data = one_novel_info(url_whole)
            df.loc[i] = newe_row_data
            i += 1
            print ()
        # 处理请求过多而连接出错    
        except:
            print ()
            print ('!!')
            print ('Sorry, failing... Waiting to restart')

            # 只重连失败5次以内的url，如果大于5次，放弃该小说
            if bad_connect[novel] < 5:
                bad_connect[novel] += 1 
                novels_list.insert(0, novel) # 将该小说放回list中以重新读取
                time.sleep(15) # 暂停15秒重新连接
            else: # 放弃
                print ('============Too many failures!! =============')
                print (url_whole)
                print ()

            
    return df

def chunks(l, n):
    """"
    Break a list into chunks of len(n)
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]
            






