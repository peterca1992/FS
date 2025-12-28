import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
from bs4 import BeautifulSoup
import requests
import numpy as np

#%%
#轉換交易所星期
def tr_date(x):
    
    if(x == 1):
        y = "一"

    if(x == 2):
        y = "二"

    if(x == 3):
        y = "三"

    if(x == 4):
        y = "四"

    if(x == 5):
        y = "五"
    
    if(x == 6):
        y = "六"
        
    if(x == 7):
        y = "日"

    return y 


#休假日
holiday_list = pd.read_csv("/Users/peterca/Desktop/python/2025/1225_處置股預警/2025_2026_休假日.csv", encoding = "utf-8")

#%%
#登入與設定
#參數設定
#起始日

##上櫃
url = "https://www.tpex.org.tw/zh-tw/announce/market/attention.html"

chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome()

driver.get(url)

time.sleep(3)


start_date_y = driver.find_element(By.XPATH, '//*[@id="___auto1"]')
start_date_y.click()
start_date_y = driver.find_element(By.XPATH, '/html/body/div[3]/div[2]/div[1]/table/thead/tr[1]/th[2]/select[1]')
start_date_y.send_keys("113") #不管輸入多少他就是會一直跳上一年

#選日期都點第一個(有可能會是上個月的 但就是表格的第一個)
start_date_y = driver.find_element(By.XPATH, '/html/body/div[3]/div[2]/div[1]/table/tbody/tr[1]/td[1]')
start_date_y.click()



search_input = driver.find_element(By.XPATH, '//*[@id="tables-form"]/div[4]/div/button[1]')
search_input.click()

time.sleep(3)

#抓資料
df = pd.read_html(driver.page_source)
df = df[0]

driver.close()

df_output = pd.DataFrame()

for i in df.drop_duplicates(subset = ["編號"])["編號"]:
    
    df_part = df[df["編號"] == i]
    
    for j in range(0, len(df_part)):
        
        if(len(str(df_part["證券代號"].iloc[j])) != 4):
            
            df_part["證券代號"].iloc[j] = df_part["證券名稱"].iloc[j]
            df_part["證券名稱"].iloc[j] = df_part["注意交易資訊"].iloc[j]
            df_part["注意交易資訊"].iloc[j] = df_part["本益比"].iloc[j]
            df_part["收盤價"].iloc[j] = df_part["Unnamed: 9"].iloc[j]
            df_part["本益比"].iloc[j] = df_part["Unnamed: 10"].iloc[j]
            
    df_part = df_part[["編號", "證券代號", "證券名稱", "累計", "注意交易資訊", "公告日期", "收盤價", "本益比"]]
    df_part["證券代號"] = df_part.apply(lambda x : str(x["證券代號"]), axis = 1)
    df_part = df_part[df_part.apply(lambda x : len(str(x["證券代號"])), axis = 1) == 4].reset_index(drop = True)
    
    df_output = pd.concat([df_output, df_part], axis = 0)



df_output["date_tr"] = df_output["公告日期"]

#%%
#找出近30個營業日日期
start_date = datetime.datetime.now() - datetime.timedelta(days = 60)
end_date = datetime.datetime.now()

diff_days = (end_date - start_date).days + 1

dates_30 = [] 

for dayNum in range(diff_days):
    # 從起始日開始依次
    date = (start_date + datetime.timedelta(days = dayNum))
    
    #過濾掉週六、日
    if date.weekday() < 5:
        dates_30.append(date.strftime('%Y/%m/%d'))
    
dates_30 = list(set(dates_30).difference(set(holiday_list["Date"])))
dates_30.sort()

dates_30 = dates_30[-30:]

for i in range(0, len(dates_30)):
    
    dates_30[i] = str(int(dates_30[i][0:4]) - 1911) + dates_30[i][4:]


df_output = df_output[df_output["date_tr"] >= dates_30[0]]

del date, dayNum, df_part, diff_days, i, j, url, start_date_y

df_output = df_output[["證券代號", "證券名稱", "注意交易資訊", "公告日期", "收盤價", "本益比", "date_tr"]]


#找處1~8款

terms_check_list = []
terms_list = ["(第一款)", "(第二款)", "(第三款)", "(第四款)", "(第五款)", "(第六款)", "(第七款)", "(第八款)"]

for i in range(0, len(df_output)):
    
    check_str = df_output["注意交易資訊"].iloc[i]
    check_str_tr = ""
    
    for j in terms_list:
        
        if(check_str.find(j) >= 0):
            
            check_str_tr = check_str_tr + j
    
    terms_check_list.append(check_str_tr)

df_output["條款轉換"] = terms_check_list
df_output = df_output[df_output["條款轉換"] != ""].reset_index(drop = True)

del terms_check_list, terms_list, i, j, check_str, check_str_tr

#%%
#找出警示
sign_output = pd.DataFrame()

for i in df_output.drop_duplicates(subset = ["證券代號"])["證券代號"]:
    
    df_output_part = df_output[df_output["證券代號"] == i]
    
    sign_output_part = pd.DataFrame()
    
    #連續三次 要考慮是否為連續三次第一款
    if(len(df_output_part) >= 2):
        
        if(sum(df_output_part["date_tr"].isin(dates_30[-2:])) == 2):
            
            df_output_part2 = df_output_part[df_output_part["date_tr"].isin(dates_30[-2:]) == True]
            df_output_part2 = df_output_part2[df_output_part2["條款轉換"] == "第一款"]
            
            if(len(df_output_part2) == 2):
            
                sign_output_part = pd.concat([sign_output_part, pd.DataFrame([df_output_part["證券代號"].iloc[0], df_output_part["證券名稱"].iloc[0], "連續兩次 可能觸及連續三次"]).T], axis = 0)
    
    #連續五次 要考慮是否為連續五次第一款～第八款
    if(len(df_output_part) >= 4):
        
        if(sum(df_output_part["date_tr"].isin(dates_30[-4:])) == 4):
            
            sign_output_part = pd.concat([sign_output_part, pd.DataFrame([df_output_part["證券代號"].iloc[0], df_output_part["證券名稱"].iloc[0], "連續四次 可能觸及連續五次"]).T], axis = 0)
    
    #10個營業日 6天
    if(len(df_output_part) >= 9):
        
         if(sum(df_output_part["date_tr"].isin(dates_30[-10:])) == 5):
            
            sign_output_part = pd.concat([sign_output_part, pd.DataFrame([df_output_part["證券代號"].iloc[0], df_output_part["證券名稱"].iloc[0], "10個營業日有五次 可能觸及六次"]).T], axis = 0)
    
    
    #30個營業日 12天
    if(len(df_output_part) >= 29):
        
        if(sum(df_output_part["date_tr"].isin(dates_30[-30:])) == 11):
            
            sign_output_part = pd.concat([sign_output_part, pd.DataFrame([df_output_part["證券代號"].iloc[0], df_output_part["證券名稱"].iloc[0], "30個營業日有11次 可能觸及12次"]).T], axis = 0)
    
    
    if(len(sign_output_part) > 0):
        
        sign_output = pd.concat([sign_output, sign_output_part], axis = 0)


del df_output_part, i, sign_output_part


#%%
#抓出已處置
url = "https://www.tpex.org.tw/zh-tw/announce/market/disposal.html"
driver = webdriver.Chrome()

driver.get(url)

df_punish = pd.read_html(driver.page_source)
df_punish = df_punish[0]

driver.close()




























