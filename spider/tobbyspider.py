#!/usr/bin/env python
# -*- coding:utf-8 -*-
# _Author_:Qi Yao
# _Date_:2018/1/5

import requests
from fake_useragent import FakeUserAgent
import re
import json
import time
import logging
import mysql.connector
#########################################################
######################全局配置###########################

#内存存储银行，省份，城市信息
CITY=[]
BANK={}
PROVINCE={}
CITYDIC={}
FINISHED=[]

#logging日志模块配置
logger = logging.getLogger("tobbbyspider")
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S')
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')

#filehandler
filehandler = logging.FileHandler("tobbuspider.log","a",encoding="utf-8")
logging.getLogger('').addHandler(filehandler)

#streamhandler
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

#Mysql全局数据库配置
conn = mysql.connector.connect(host='localhost', database='test', user='root', password='root')
cursor = conn.cursor()

#########################################################
#########################################################

def main(url, bankid, provinceid, cityid, key=''):

    'get请求格式:bank=1&province=1&city=35&key='
    try:
        ua = FakeUserAgent()
        # print(ua.random)
        user_agent = ua.random
        # user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17"
        headers = {"User-Agent": user_agent}
        params = {'bank': bankid, 'province': provinceid, 'city': cityid, 'key': key}
        time.sleep(1)
        resp = requests.get(url=url,params=params,headers=headers,timeout=5)
        text =resp.text
        parse(text,bankid,provinceid,cityid)

        FINISHED.append([bankid,provinceid,cityid])
    except Exception as e:
        print(e)
        with open("finished.txt","w+",encoding="utf-8") as f:
            for item in FINISHED:
                f.write(str(item))
        main(url,bankid,provinceid,cityid,key)


def getbank(context):
    '一次执行，获取银行信息'
    banks_group = re.findall("<select name=\"bank\".*?>(.*?)</select>",context,re.S)
    bank = re.findall("<option value=\"(.*?)\">(.*?)</option>", banks_group[0], re.S)[1:-1]
    with open("./bank.txt.bak", "wb") as f:
        for bank_item in bank:
            f.write(bytes(bank_item[0]+","+bank_item[1]+"\r\n",encoding="utf-8"))
def getprovinces(context):
    '一次执行，获取省份信息'
    provinces_group = re.findall("<select class=\"input-text\" name=\"province\".*?>(.*?)</select>", context, re.S)
    province = re.findall("<option value=\"(.*?)\">(.*?)</option>", provinces_group[0], re.S)[1:]
    with open("./province.txt", "wb") as f:
        for i in province:
            f.write(bytes(i[0] + "," + i[1] + "\r\n", encoding="utf-8"))
def getcitybyprovince(provinceid):
    '获取各省份下的城市信息'
    url="http://www.lianhanghao.com/index.php/Index/Ajax?id="+provinceid
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17"
    headers = {"User-Agent": user_agent}
    try:
        resp = requests.get(url, headers, timeout=5)
        js =json.loads(resp.text.replace("ï»¿",""),encoding="utf-8")
        for i in js:
            provinceid=i["pid"]
            cityid = i["id"]
            cityname = i["name"]
            cityinfo = {"provinceid":provinceid,"cityid":cityid,"cityname":cityname}
            CITY.append(cityinfo)
            print(cityinfo)
        time.sleep(1)

        print("success "+provinceid)
    except Exception as e:
        print(e)
        getcitybyprovince(provinceid)





def parse(context,bankid,provinceid,cityid):
    '解析页面，并将数据存入mysql数据库中'
    tbody = re.findall("<tbody>(.*?)</tbody>",context,re.S)
    print(tbody)
    tr = re.findall("<tr>(.*?)</tr>",tbody[0],re.S)
    if len(tr)==0:
        return
    for item in tr:
        td = re.findall("<td.*?>(.*?)</td>",item,re.S)
        id = td[0]
        name = td[1]
        phone = td[2]
        address = td[3]
        if id=="" or name=="":
            return
        #增量插入，通过联行号判断
        cursor.execute("select accountid from bank where accountid=%s",(id,))
        res = True
        for (res) in cursor:
            if len(res)!=0:
                res=False
        if res:
            cursor.execute("insert into bank(accountid,accountname,phone,address,bankname,province,city) values(%s,%s,%s,%s,%s,%s,%s)",(
                id,name,phone,address,BANK[bankid],PROVINCE[provinceid],CITYDIC[cityid]))
            conn.commit()
    ishasnext(context, bankid, provinceid, cityid)

def ishasnext(context,bankid,provinceid,cityid):
    '判断是否含有下一页'
    nextPage = re.findall("<a class=\"next\" href=\"(.*?)\".*?</a>", context, re.S)
    if len(nextPage)!=0:
        for page in nextPage:
            url="http://www.lianhanghao.com/"+page
            parsenextpage(url,bankid,provinceid,cityid)
    else:
        return


def parsenextpage(pageurl,bankid,provinceid,cityid):
    '对子页请求处理'
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17"
    headers = {"User-Agent": user_agent}
    #time.sleep(2)
    print(pageurl)
    try:
        resp = requests.get(url=pageurl, headers=headers, timeout=5)
        parse(resp.text,bankid,provinceid,cityid)
    except Exception as e:
        e.with_traceback()
        print(e)
        parsenextpage(pageurl,bankid,provinceid,cityid)


def init():
    '初始化加载银行信息，省份信息，城市信息'
    with open("bank.txt","r",encoding="utf-8") as f:
        while True:
            line = f.readline().replace("\n","")
            if line=="":
                break
            bankinfo = line.split(",")
            bankid = bankinfo[0]
            bankname = bankinfo[1]
            BANK[bankid]=bankname
    with open("city.txt","r",encoding="utf-8") as f:
        while True:
            line = f.readline().replace("'","\"")
            if line=="":
                break
            js= json.loads(line,encoding="utf-8")
            for item in js:
                CITY.append(item)
                CITYDIC[item["cityid"]]=item["cityname"]
    with open("province.txt","r",encoding="utf-8") as f:
        while True:
            line = f.readline().replace("\n","")
            if line=="":
                break
            provinceinfo = line.split(",")
            provinceid = provinceinfo[0]
            provincename = provinceinfo[1]
            PROVINCE[provinceid]= provincename

if __name__=="__main__":
    url = "http://www.lianhanghao.com/index.php/Index/index/p/index.php"
    init()
    for bankid in BANK:
        logging.debug("Start Crawl"+BANK[bankid].center(20, "-"))
        for provinceid in PROVINCE:
            logging.debug("\t\tStart Crawl" + PROVINCE[provinceid].center(20, "-"))
            cityofcurrentprovince=[]
            for city in CITY:
                if city["provinceid"]==provinceid:
                    cityofcurrentprovince.append(city)
            for curcity in cityofcurrentprovince:
                logging.debug("\t\t\t\tStart Crawl" + curcity["cityname"].center(20, "-"))
                main(url, bankid, provinceid, curcity["cityid"])
                logging.debug("\t\t\t\tCrawl Current City Finish ".center(20, "-"))
            logging.debug("\t\tCrawl Current Province Finish ".center(20, "-"))
        logging.debug("\t\tCrawl Current Bank Finish ".center(20, "-"))





    # for i in range(34):
    #     if i==0:
    #         continue
    #     else:
    #         getcitybyprovince(str(i))
    # print(CITY)
    #url="http://www.lianhanghao.com/index.php/Index/index/p/1.html"
    #main(url, '8', '4', '58')
    #main(url,'1','1','35')
    #parsenextpage("http://www.lianhanghao.com//index.php/Index/index/p/4/bank/2/province/13/city/150.html",'1','1','35')
    cursor.close()
    conn.close()
    #print("\u77f3\u5bb6\u5e84\u5e02")