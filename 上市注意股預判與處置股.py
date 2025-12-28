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

##上市
url = "https://www.twse.com.tw/zh/announcement/notice.html"

chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome()

driver.get(url)

time.sleep(3)

start_date = datetime.datetime.now() - datetime.timedelta(days = 60)
start_month = start_date.month
start_day = start_date.day

if(len(str(start_month)) == 1):
    
    start_month = "0" + str(start_month)

if(len(str(start_day)) == 1):
    
    start_day = "0" + str(start_day)


start_year = "民國 " + str(start_date.year - 1911) + "年"
start_month = str(start_month) + "月"
start_day = str(start_day) + "日 (" + tr_date((start_date.weekday() + 1)) + ")"

start_date_y = driver.find_element(By.XPATH, '//*[@id="label1"]')
start_date_y.send_keys(start_year)

start_date_m = driver.find_element(By.XPATH, '//*[@id="form"]/div/div[1]/div[2]/span[1]/select[2]')
start_date_m.send_keys(start_month)

start_date_d = driver.find_element(By.XPATH, '//*[@id="form"]/div/div[1]/div[2]/span[1]/select[3]')
start_date_d.send_keys(start_day)

#終止日
end_date = datetime.datetime.now()
end_month = end_date.month
end_day = end_date.day

if(len(str(end_month)) == 1):
    
    end_month = "0" + str(end_month)

end_year = "民國 " + str(end_date.year - 1911) + "年"
end_month = str(end_month) + "月"
end_day = str(end_day) + "日 (" + tr_date((end_date.weekday() + 1)) + ")"

end_date_y = driver.find_element(By.XPATH, '//*[@id="datePick1"]')
end_date_y.send_keys(end_year)

end_date_m = driver.find_element(By.XPATH, '//*[@id="form"]/div/div[1]/div[2]/span[2]/select[2]')
end_date_m.send_keys(end_month)

end_date_d = driver.find_element(By.XPATH, '//*[@id="form"]/div/div[1]/div[2]/span[2]/select[3]')
end_date_d.send_keys(end_day)

search_input = driver.find_element(By.XPATH, '//*[@id="form"]/div/div[1]/div[4]/button')
search_input.click()

time.sleep(3)

#抓資料
df = pd.read_html(driver.page_source)
df = df[0]

driver.close()

df = df[df.apply(lambda x : len(str(x["證券代號"])), axis = 1) == 4]

st_list = df.drop_duplicates(subset = ["證券代號"])

df_output = pd.DataFrame()

for i in range(0, len(st_list)):
    
    if(len(df[df["編號"] == st_list["編號"].iloc[i]]) > 1):
        
        df_part = df[df["編號"] == st_list["編號"].iloc[i]]

        for j in range(1, len(df_part)):
            
            df_part["編號"].iloc[j] = df_part["注意交易資訊"].iloc[j]
            df_part["證券代號"].iloc[j] = df_part["日期"].iloc[j]
            df_part["證券名稱"].iloc[j] = df_part["收盤價"].iloc[j]
            df_part["累計次數"].iloc[j] = df_part["本益比"].iloc[j]
            df_part["注意交易資訊"].iloc[j] = df_part["Unnamed: 8"].iloc[j]
            df_part["日期"].iloc[j] = df_part["Unnamed: 9"].iloc[j]
            df_part["收盤價"].iloc[j] = df_part["Unnamed: 10"].iloc[j]
            df_part["本益比"].iloc[j] = df_part["Unnamed: 11"].iloc[j]
            
        
        df_part = df_part[["編號", "證券代號", "證券名稱", "累計次數", "注意交易資訊", "日期", "收盤價", "本益比"]]

        df_output = pd.concat([df_output, df_part], axis = 0)

df_output["date_tr"] = df_output.apply(lambda x : x["日期"].replace(".", "/"), axis = 1 )

#%%
#找出近30個營業日日期
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

del date, dayNum, df_part, diff_days, end_date_d, end_date_m, end_date_y, start_date_d, start_date_m, start_date_y, i, j, end_day, end_month, end_year, start_day, start_month, start_year, url


#找處1~8款

terms_check_list = []
terms_list = ["﹝第一款﹞", "﹝第二款﹞", "﹝第三款﹞", "﹝第四款﹞", "﹝第五款﹞", "﹝第六款﹞", "﹝第七款﹞", "﹝第八款﹞"]

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


del df_output_part, df_output_part2, i, sign_output_part


#%%
#抓出已處置
url = "https://www.twse.com.tw/zh/announcement/punish.html"
driver = webdriver.Chrome()

driver.get(url)

df_punish = pd.read_html(driver.page_source)
df_punish = df_punish[0]

driver.close()

df_punish = df_punish[["公布日期", "證券代號", "證券名稱", "處置條件", "處置起迄時間", "處置措施"]]

#處置分鐘數轉換

def punish_min_tr(x):
    
    if(x == "第一次處置"):
    
        y = "5分鐘"
        
    if(x == "第二次處置"):
    
        y = "20分鐘"

    return str(y)


df_punish["處置時間"] = df_punish.apply(lambda x : punish_min_tr(x["處置措施"]), axis = 1)






























