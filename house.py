# coding=utf-8
import time            
import re            
import urllib2
import json
import csv
from bs4 import BeautifulSoup
from test import csv_name
try:
    import cPickle as pickle
except ImportError:
    import pickle
from lxml import etree
from selenium import webdriver              
import selenium.webdriver.support.ui as ui        
import httplib  
httplib.HTTPConnection._http_vsn = 10  
httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'        #指定HTTP/1.0而不是HTTP/1.1

#先调用无界面浏览器PhantomJS或Firefox      
driver = webdriver.Firefox()

wait = ui.WebDriverWait(driver,10)



def GetCitys(mainUrl):
    try:
        #**********************************************************************
        # 获得所有城市的名称和对应楼盘网址
        #**********************************************************************
        print u'登陆链家网站...'
        driver.get(mainUrl) 
        time.sleep(2)  #避免页面还没显示，出现下面的Element is not visible错误
        cityButton = driver.find_element_by_xpath("//div[@class='fl']/span")
        cityButton.click()              #点击登陆
        print u'点击成功'
        time.sleep(2)
        #**********************************************************************
        # diriver打开的网页，可以通过driver.find_elements_by_xpath("//div[@class='fc-main clear']//a//@href")
        #来获取页面所有符合条件的网址（element类型），但是无法将网址转化成字符串类型，所以只能先读取整个网页html
        #然后用lxml来解析html
        #注意：diriver中的xpath要匹配多个元素的话，find_element后要加s
        #**********************************************************************
        html_unicode = driver.page_source   #获取网页所有的内容
        SaveHtml(html_unicode)              #保存网页内容,可以用于测试，省的每次打开浏览器测试
        
        html = etree.HTML(html_unicode)     #lxml中etree将读取的unicode类型网页解析成html
        
        city_urls =  []
        city_names = []
          
        city_urls = html.xpath("//div[@class='fc-main clear']//a/@href")     #获取所有a标签中的href值
        print city_urls
        
        for city_name in html.xpath("//div[@class='fc-main clear']//a"):     #获取所有a标签内容
            city_names.append(city_name.text)                                #获取所有a标签中文字
        print str(city_names).replace('u\'','\'').decode("unicode-escape")    #打印中文字符真是烦！！！
        
        if u'北京' in city_names:
            print u'北京在城市列表中！！'

    except Exception,e:      
        print "Error: ",e
    finally:    
        return city_names,city_urls

def SaveHtml(html):
    data = pickle.dumps(html)  #转化为字符串，写文件则不会遇到编码问题
    with open ("lianjia.html","wb") as fw:  
        #   写文件用bytes而不是str，所以要转码    
        fw.write(data) 
        
def ReadHtml():
    with open("lianjia.html",'rb') as fr:
        htmlFile = fr.read()
        data = pickle.loads(htmlFile)
        print u'加载文件成功'        
        html = etree.HTML(data)
    return html

#第一次下载失败，还可以根据num_retries重试几次
def download(url, num_retries=3):
    """Download function that also retries 5XX errors"""
    print 'Downloading:', url
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        html = response.read()
        #查看当前跳转后的url是否和开始url所属城市的相同，不同则有问题;
        current_url = response.geturl()
        if current_url.split('.')[0] != url.split('.')[0] :
            print current_url
            return None
        
    except urllib2.URLError as e:
        print 'Download error:', e.reason
        html = None
        if num_retries > 0:
#             if hasattr(e, 'code') and 500 <= e.code < 600:
#                 # retry 5XX HTTP errors
            print num_retries
            html = download(url, num_retries-1)
    return html

#获得楼盘页数
def GetPageNum(pageHtml,flag):
    if flag == 'hot':
        print flag
        try:
            page_data = pageHtml.xpath("//div[@class='page-box house-lst-page-box']/@page-data")
            #将page_data[0]由类对象编码为字符串，并解析出其中的总页数
            page_num = int(re.findall('totalPage.:(.*?),', page_data[0].encode('utf-8'))[0])
        except Exception,e:
            print "Error: ",e
            page_data = pageHtml.xpath("//div[@class='pagination']/@data-totalpage")
            page_num = int(page_data[0])
    else:
        print flag
        try:
            page_data = pageHtml.xpath("//div[@class='page_box']//a[last()-1]")[0].text
            page_num = int(page_data)
        except Exception,e:      
            print "Error: ",e
            page_num = 1
    return page_num

#处理网页text.判断网页中获取的text是否有&nbsp，有的话要干掉，其不能编码为gbk;
def ProcessText(text):
    code = 'gbk'
    text_utf8 = text.encode('utf-8')
#         print text_utf8+'uu'                  #可以通过打印看到是否含&nbsp
    if ' ' in text_utf8 :                        #去除&nbsp这个恶心的东西，它不是空格，要打印出来并拷贝才能得到
        tag = text_utf8.split(' ')
        try:
            return tag[0].decode('utf-8').encode(code)
        except Exception,e:
            print tag[0]
            print "该字符串无法编码为GBK"
            return 'None'.decode('utf-8').encode(code) 
    else:
        try:
            return text.encode(code)
        except Exception,e:      
            print text
            print "该字符串无法编码为GBK"
            return 'None'.decode('utf-8').encode(code)
    
#获取楼盘信息
def GetHouses(url,page_num,flag,list):
    code = 'gbk'
    page_url = url+'pg'+str(page_num)
    house_page = download(page_url)
        
    if house_page == None :
        print u'页 数'+str(page_num)+u' 无楼盘信息！！'
        return                          
        
    house_html = etree.HTML(house_page)              #两种花样解析网页，此为lxml
    house_bp = BeautifulSoup(house_page,'lxml')      #两种花样解析网页，此为BeautifulSoup
    
    if flag == 'hot':
        #楼盘名称
        for tag1 in house_html.xpath("//div[@class='col-1']//a[@target='_blank']/text()"):
            tag11 = ProcessText(tag1)
            list[0].append(tag11)

        #楼盘位置和面积    
        for tag23 in house_bp.find_all(name='div', attrs={'class':re.compile('col-1')}):
            tag2 = tag23.find(name='div', attrs={'class':re.compile('where')})
            tag22 = tag2.find(name='span', attrs={'class':re.compile('region')})
            tag222 = ProcessText(tag22.get_text())
            list[1].append(tag222)
            
            tag3 = tag23.find(name='div', attrs={'class':re.compile('area')})
            tag33 = tag3.find(name='span')
            if len(tag33) > 0 :
                tag333 = re.findall('(.*\d).*', tag33.get_text().encode('utf-8'))[0]+'平'
                list[2].append(tag333.decode('utf-8').encode(code)) 
            else:
                list[2].append(0)
                print 0
                        
        #楼盘在售状态
        for tag4 in house_html.xpath("//div[@class='col-1']/div[@class='type']/span[1]/text()"):
            tag44 = ProcessText(tag4)
            list[3].append(tag44)
        #楼盘住宅类型
        for tag5 in house_html.xpath("//div[@class='col-1']/div[@class='type']/span[2]/text()"):
            tag55 = ProcessText(tag5)
            list[4].append(tag55)
   
        #楼盘均价或总价、价格待定字段
        ff = True
        for tag6 in house_html.xpath("//div[@class='col-2']//div[@class='average']/text()"):
            #通过ff标志，除去单位‘元/平’,只保留 均价 字段
            if ff :
                tag66 =re.findall(r'.*(均价|总价|价格待定).*',tag6.encode('utf-8'))[0]
                list[5].append(tag66)
                if tag66 == '价格待定':
                    continue
                else:
                    ff = False
            else:
                ff = True
        #楼盘价格,注意，如果上面有价格待定的，则无法获得价格，所以要通过整合，让tag6和tag7对应上
        for tag7 in house_html.xpath("//div[@class='col-2']//div[@class='average']/span/text()"):
            tag77 = ProcessText(tag7)
            list[6].append(tag77)

    else:
        #楼盘名称
        for tag1 in house_html.xpath("//div[@class='lp_m']//a[@target='_blank']/text()"):
            tag11 = ProcessText(tag1)
            list[0].append(tag11)
            
        #楼盘位置和面积    
        for tag23 in house_bp.find_all(name='div', attrs={'class':re.compile('lp_m')}):
            tag2 = tag23.find_all(name='p', attrs={'class':re.compile('dzh')})   
            tag22 = ProcessText(tag2[0].get_text())
            list[1].append(tag22)
         
            if len(tag2) != 1 :
                tag3 = re.findall('(.*\d).*', tag2[1].get_text().encode('utf-8'))[0]+'平'
                list[2].append(tag3.decode('utf-8').encode(code)) 
            else:
                list[2].append(0)
                print 0        

        #楼盘在售状态
        for tag4 in house_html.xpath("//div[@class='lp_m']/div[@class='midbot']/a[1]/text()"):
            tag44 = ProcessText(tag4)
            list[3].append(tag44)
        #楼盘住宅类型
        for tag5 in house_html.xpath("//div[@class='lp_m']/div[@class='midbot']/a[2]/text()"):
            tag55 = ProcessText(tag5)
            list[4].append(tag55)
  
        #楼盘均价或总价、价格待定字段
        ff = True
        for tag6 in house_html.xpath("//div[@class='lp_r']//p[@class='jj']/text()"):
            #通过ff标志，除去单位‘元/平’,只保留 均价 字段
            if ff :
                tag66 =re.findall(r'.*(均价|总价|价格待定).*',tag6.encode('utf-8'))[0]
                list[5].append(tag66)
                if tag66 == '价格待定':
                    continue
                else:
                    ff = False
            else:
                ff = True
        #楼盘价格,注意，如果上面有价格待定的，则无法获得价格，所以要通过整合，让tag6和tag7对应上
        for tag7 in house_html.xpath("//div[@class='lp_r']//p[@class='jj']/a/text()"):
            tag77 = ProcessText(tag7)
            list[6].append(tag77)       
            
#上海s和苏州s的专属函数
def GetHouses_ss(url,page_num,list):
    code = 'gbk'
    page_url = url+'pg'+str(page_num)
    house_page = download(page_url)
        
    if house_page == None :
        print u'页 数'+str(page_num)+u' 无楼盘信息！！'
        return                          
        
    house_html = etree.HTML(house_page)              #两种花样解析网页，此为lxml
    house_bp = BeautifulSoup(house_page,'lxml')      #两种花样解析网页，此为BeautifulSoup
    

    #楼盘名称
    for tag1 in house_html.xpath("//div[@class='col-1']/div[@class='title-box']//a[@target='_blank']/text()"):
        tag11 = ProcessText(tag1)
        list[0].append(tag11)

    #楼盘位置和面积    
    for tag23 in house_bp.find_all(name='div', attrs={'class':re.compile('col-1')}):
        tag2 = tag23.find_all(name='div', attrs={'class':re.compile('row')})
        tag22 = tag2[0].find(name='a', attrs={'class':re.compile('region')})
        tag222 =  re.sub('\s','',tag22.get_text().encode('utf-8'))
        tag2222 = ProcessText(tag222.decode('utf8'))
        list[1].append(tag2222)
            
        tag33 = tag2[1].find(name='a', attrs={'class':re.compile('area')})
        if len(tag33) > 0 :
            if ' ' in tag33.get_text().encode('utf-8') :                 #恶心的&nbsp
                tag333 = tag33.get_text().encode('utf-8').split(' ')
                tag3333 = re.findall('(.+\d)', tag333[1])
            if len(tag3333) > 0 :
                tag3_3 = tag3333[0]+'平'
                list[2].append(tag3_3.decode('utf-8').encode(code)) 
            else:                                                        #有面积标签，但户型未知，无面积参数
                list[2].append(0) 
        else:                                                            #无面积标签
            list[2].append(0)                                           
                        
    #楼盘在售状态
    for tag4 in house_html.xpath("//div[@class='col-1']/div[@class='title-box']/span[2]/text()"):
        tag44 = ProcessText(tag4)
        list[3].append(tag44)
    #楼盘住宅类型
    for tag5 in house_html.xpath("//div[@class='col-1']/div[@class='title-box']/span[1]/text()"):
        tag55 = ProcessText(tag5)
        list[4].append(tag55)
    
    
    #楼盘均价或总价、价格待定字段,以及价格字段
    for tag67 in house_bp.find_all(name='div', attrs={'class':re.compile('col-2')}):
        tag6 = tag67.find(name='div', attrs={'class':re.compile('average')})
        tag7 = tag6.find(name='span')
        try:
            if len(tag7) > 0 :                       #如果求长度有问题，说明没有面积标签，则价格统一为'价格待定'
                tag66 =re.findall(r'.*(均价|总价).*',tag6.get_text().encode('utf-8'))[0]
                list[5].append(tag66)
                tag77 = ProcessText(tag7.get_text())
                list[6].append(tag77)
        except Exception,e:
            tag6_6 = '价格待定'                                               
            list[5].append(tag6_6)
         
            
 
if __name__ == '__main__':     
    netAddress = 'https://bj.lianjia.com/'
    city_names,city_urls = GetCitys(netAddress)
    driver.close()
    time.sleep(2)
    
    for i in range(0,len(city_names)):
        #打开城市的楼盘网页,网址分热门城市和一般城市，两者网页呈现形式不同。东莞和珠海居然还没有新楼盘！！
        #"大理"："http://you.lianjia.com/dl1"，"中山": "https://zs.lianjia.com/"
#         if u'保亭' == city_names[i] or u'北京' == city_names[i] or u'成都' == city_names[i] or u'澄迈' == city_names[i] or u'苏州' == city_names[i] \
#            or u'大连' == city_names[i] or u'长沙' == city_names[i] or u'重庆' == city_names[i] or u'上海' == city_names[i] \
#            or u'定安' == city_names[i] or u'大理' == city_names[i] or u'佛山' == city_names[i] or u'广州' == city_names[i] \
#            or u'杭州' == city_names[i] or u'惠州' == city_names[i] or u'海口' == city_names[i] or u'合肥' == city_names[i] \
#            or u'济南' == city_names[i] or u'昆明' == city_names[i] or u'陵水' == city_names[i] or u'廊坊' == city_names[i] \
#            or u'临高' == city_names[i] or u'乐东' == city_names[i] or u'南京' == city_names[i] or u'青岛' == city_names[i] \
#            or u'琼海' == city_names[i] or u'琼中' == city_names[i] or u'儋州' == city_names[i] :
#             print u"该城市已经爬取过了"
#             continue
        if u'上海' == city_names[i] or u'苏州' == city_names[i] :
            pass
        else:
            print u"该城市已经爬取过了"
            continue 
        
        
        
        flag = 'hot'
        if u'太原' == city_names[i] :
            url = city_urls[i]+'loupan/'      #太原的链接比较特殊
            flag = 'hot'                      #热门城市
#             csv_name = re.findall('.*//(.*?)\.', city_urls[i])[0]     #保存文件的名称
        elif city_urls[i][-1] == '/' :
            urls = city_urls[i].split('.')
            url = urls[0]+'.fang.'+urls[1]+'.'+urls[2]+'loupan/'    #热门城市
            flag = 'hot'
#             csv_name = re.findall('.*//(.*?)\.', city_urls[i])[0]
        else:
            url = city_urls[i]+'/loupan/'     #一般城市
            flag = 'cold'
#             csv_name = city_urls[i].split('/')[-1]
        the_page = download(url)
        
        if the_page == None :
            print json.dumps(city_names[i],ensure_ascii=False,encoding="UTF-8") +u' 无楼盘！！'
            continue                          #城市无楼盘的话就跳过
        
        pageHtml = etree.HTML(the_page)
        page_num = GetPageNum(pageHtml,flag)
       
        print page_num
        print u'开始爬取城市楼盘。。'
        
        list = [[],[],[],[],[],[],[]]
        #开始获取城市的楼盘信息
        while page_num >0 :
            if u'上海' == city_names[i] or u'苏州' == city_names[i] :
                GetHouses_ss(url,page_num,list)         #上海和苏州专属爬取信息的函数
            else:
                GetHouses(url,page_num,flag,list)            
            page_num = page_num-1
            print  len(list[0]),len(list[1]),len(list[2]),len(list[3]),len(list[4]),len(list[5]),len(list[6])
            
        #有些无价格的房子，价格项显示为0
        for m in range(0,len(list[5])):
            if list[5][m] == '价格待定':
                list[6].insert(m,0)
                
        print  len(list[0]),len(list[1]),len(list[2]),len(list[3]),len(list[4]),len(list[5]),len(list[6])        
        
        csv_name = city_names[i]+'.csv'                 #保存文件的名称
        csvfile = file(csv_name,'ab+')
        writer = csv.writer(csvfile)
        writer.writerow(['name','address','area','on-sales','house-type','price-type','price'])
        
        for y in range(0,len(list[6])):
            writer.writerow([list[0][y],list[1][y],list[2][y],list[3][y],list[4][y]\
                             ,list[5][y].decode('utf-8').encode('gbk'),list[6][y]])
        csvfile.close()           
    print u'完了'
      
    
    
    
    
    
    
