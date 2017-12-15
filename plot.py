# coding=utf-8
import json
import re
import csv
import chardet
import pandas
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import mlab
from matplotlib import rcParams
import copy
from lxml import etree
from _codecs import encode
from cProfile import label
try:
    import cPickle as pickle
except ImportError:
    import pickle
    
def GetCityNames():    
    with open("lianjia.html",'rb') as fr:
        data = fr.read()
        doc = pickle.loads(data)
        print u'加载文件成功'        
        html = etree.HTML(doc)
        cityNames =html.xpath("//div[@class='fc-main clear']//a/text()")
#         print json.dumps(cityNames,ensure_ascii=False,encoding='utf-8') 
#         print cityNames[0].encode('utf-8')
    return cityNames

def ReadCSV(csvName,list):
#         df = pandas.read_csv(csvName,encoding='gbk')
#         print df.tail(2)
    csv_file = file(csvName,'rb')
    reader = csv.reader(csv_file)
    ll = 0
    flag = False
    for line in reader:
        if ll == 0:                                             #第一行去掉
            ll =1
            continue
        
        try:
            if int(line[6].decode('gbk').encode('utf-8')) == 0:          #价格化为整型值，为零的去掉
                continue 
        except Exception,e:                                              #出错则是价格区间，如300-600，无法整型化
            temp = line[6].decode('gbk').encode('utf-8').split('-')
            mid =  (int(temp[0])+int(temp[1]))/2
            price = int(int(temp[0])*0.3+mid*0.5+int(temp[1])*0.2) 
            flag = True                                                   #综合一下，最低价占0.3，中间价0.5，最高价0.2
             
        list[0].append(line[0].decode('gbk').encode('utf-8'))
        list[1].append(line[1].decode('gbk').encode('utf-8'))
        list[2].append(line[2].decode('gbk').encode('utf-8'))
        list[3].append(line[3].decode('gbk').encode('utf-8'))
        list[4].append(line[4].decode('gbk').encode('utf-8'))
        list[5].append(line[5].decode('gbk').encode('utf-8'))
        if flag :
            list[6].append(price)
            flag = False
        else:
            list[6].append(int(line[6].decode('gbk').encode('utf-8')))
        
    csv_file.close()  
    
#计算每个城市的各种住宅的数量    
def CountHouseType(list):
    type_list = [0,0.0,0.0]
    for type_house in list[4]:
        if type_house == '别墅' :
            type_list[0] = type_list[0]+1
        elif type_house == '住宅' :
            type_list[1] = type_list[1]+1
        elif type_house == '商住两用' :
            type_list[1] = type_list[1]+0.5
            type_list[2] = type_list[2]+0.5
        else:
            type_list[2] = type_list[2]+1          
    return type_list 

def MeanValue(list):
    s = 0
    N = 0
    for y in range(0,len(list[4])):
        if list[4][y] == '住宅' or list[4][y] == '商住两用':
            if list[5][y] == '均价' :
                s = s+list[6][y]
                N = N+1
    if N>0 :
        mean_price = s/N
        print N
        print mean_price
        return int(mean_price)
    else:
        return 0

  
#求一维数组排序后的坐标、索引 
def IndexOfSort(array,order):  
    if order :                                     #从小到大的索引
        index = np.argsort(array)                  
    else:                                          #从大到小的索引                                 
        for i in range(0,len(array)):
            array[i] = -array[i]                           #取负号之后，最大值就变为最小值了
        index = np.argsort(array)                  
    return index   

#画条形图        
def BarChart(city_names,numberHouseType_T,sortIndex):
    #生成0~60的等差数组，个数20
    index = np.linspace(0,60,num=20,endpoint=False) #条形图X轴的坐标 20个值，取前楼盘数量前20名的城市
    xticks_labels = []
    fig = plt.figure(2)
    for k in range(20):
        plt.bar(left = index[k]-0.8,height = numberHouseType_T[0][sortIndex[k]],width = 0.8, \
                align = 'center',color = 'r',label = u'别墅')                    #别墅数量
        plt.bar(left = index[k],height = numberHouseType_T[1][sortIndex[k]],width = 0.8, \
                align = 'center',color = 'g',label = u'住宅')                    #住宅数量
        plt.bar(left = index[k]+0.8,height = numberHouseType_T[2][sortIndex[k]],width = 0.8, \
                align = 'center',color = 'y',label = u'商用')                    #商铺数量
        xticks_labels.append(city_names[sortIndex[k]]) 
#     label = [u'别墅',u'住宅',u'商用']
    plt.legend()                                                 #加图例
    plt.xticks(index,xticks_labels)                              #X轴标上城市名称
    plt.title(u'全国城市新楼盘数量前20名')    
#     #给柱子顶部显示数值，无效
#     def autolabel(rects):
#         for rect in rects:
#             height = rect.get_height
#             plt.text(rect.get_x+rect.get_width/2.,1.03*height,height)
#     autolabel(rects)
    plt.show()       
        
def PlotPie(array):
    vals = [1]
    fig,ax = plt.subplots()
    labels = [u'别墅',u'住宅',u'商用']
    colors = ['yellowgreen', 'gold', 'lightskyblue']
    explode = [0,0,0.08]      #中间那块凸出    
    plt.pie(array,explode=explode,labels=labels,colors=colors,autopct='%1.1f%%',shadow=True,startangle=90,radius=1.0)
    plt.pie(vals, radius=0.7,colors='w')              #中间再画一个占比100的白色饼，那就有中空的效果
    ax.set(aspect="equal", title=u'全国楼盘类型占比')      #设置标题以及图形的对称
    plt.legend()
    plt.show()

def PlotLine(city_names,meanPriceOfHouseList,sortIndexOfPrice):
    #生成0~60的等差数组，个数20
    index = np.linspace(0,60,num=20,endpoint=False) #折线图X轴的坐标 20个值，取前楼盘数量前20名的城市
    fig = plt.figure()
    ax = fig.add_subplot(111)
    price_list = []
    xticks_labels = []
    for p in range(0,20):
        price_list.append(meanPriceOfHouseList[sortIndexOfPrice[p]])
        xticks_labels.append(city_names[sortIndexOfPrice[p]]) 
    plt.plot(index,price_list,label = u'每平米均价（元）',marker = '*',markersize=10,color='blue',linewidth=1.5)
    plt.xticks(index,xticks_labels)                              #X轴标上城市名称
    plt.grid()
    plt.title(u'全国城市普通住宅房价前20名')  
    plt.legend(loc = 'upper right',frameon = False)        #frameon表示不要外框线
    #给点标数值
    priceLL = [l+300 for l in price_list]                   #把Y轴坐标增加100
    datadot = tuple(zip(index,priceLL))                     #所标数值的坐标，x轴左移0.5，把Y轴坐标增加100，防止与点重合
    for dot in datadot:
        ax.annotate(str(dot[1]-300),xy=dot)

    plt.show()       
                
if __name__ == '__main__':
    city_names = GetCityNames()
    
    sumHouse = []                                  #城市的楼盘总数
    numberHouseType = []                           #城市各住宅类型的数量 
    meanPriceOfHouseList = []
    
    for i in range(0,len(city_names)):
        if u'东莞' == city_names[i] or u'珠海' == city_names[i]:
            sumHouse.append(0)                     #不要忘了这两个没有数据的城市，否则后面排序会对应不上city_names[i]
            numberHouseType.append([0,0,0])
            meanPriceOfHouseList.append(0)
            continue
        
        list = [[],[],[],[],[],[],[]]
        csvName = city_names[i]+'.csv' 
        print city_names[i]
        ReadCSV(csvName,list)                       #读取城市楼盘数据，保存到list中
        sumHouse.append(len(list[0]))               #某个城市的楼盘总数
        typeList = CountHouseType(list)             #计算每个城市的各种住宅的数量
        numberHouseType.append(typeList) 
        meanPriceOfHouseList.append(MeanValue(list)) #普通住宅的平均单价/平
    #求一下转置并取整，方便访问所有城市   同一住宅属性的数量 
    numberHouseType_T = np.around(np.transpose(numberHouseType)) 
    sum_a = copy.deepcopy(sumHouse)              #赋给另一个值，放止更改原来的数组
    sortIndex = IndexOfSort(sum_a,order=False)   #返回城市楼盘总数从大到小排序的索引
    #画条形图
#     BarChart(city_names,numberHouseType_T,sortIndex)
    #雷达图
    #####################################################
    #普通住宅均价图
    mean_a = copy.deepcopy(meanPriceOfHouseList)      #赋给另一个值，放止更改原来的数组
    sortIndexOfPrice = IndexOfSort(mean_a,order=False)
    PlotLine(city_names, meanPriceOfHouseList, sortIndexOfPrice)
    
    
    #各住宅类型总数量占比，饼状图
#     PlotPie(numberHouseType_T.sum(axis=1))          #矩阵行求和
     
    