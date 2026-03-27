import pandas as pd
import sys
sys.path.append('C:\\Users\\J1070116\\Desktop')
from WCFAdox import PCAX
import datetime 
import numpy as np
from sklearn.linear_model import LinearRegression

#設定連線主機IP並產生物件
PX=PCAX("172.24.26.40")

#%%

def date_60d_tr(x, before_day):
    
    yy = int(x.split("/")[0])
    mm = int(x.split("/")[1])
    dd = int(x.split("/")[2])
    
    bdate = datetime.date(yy,mm,dd)
    bdate_60 = bdate - datetime.timedelta(before_day)
    
    yy_n = str(bdate_60.year)  
    mm_n = str(bdate_60.month)  
    dd_n = str(bdate_60.day)
    
    
    if(len(mm_n) != 2):
        
        mm_n = "0" + mm_n

    if(len(dd_n) != 2):
        
        dd_n = "0" + dd_n
        
    output_date = yy_n + mm_n + dd_n
    
    return output_date

def date_tr(x):
    
    yy = x.split("/")[0]
    mm = x.split("/")[1]
    dd = x.split("/")[2]
    
    if(len(mm) != 2):
        
        mm = "0" + mm

    if(len(dd) != 2):
        
        dd = "0" + dd
        
    output_date = yy + mm + dd
    
    return output_date


#%%
#input的東西
df_stock_list = pd.read_csv("D:\\Python_code\\工作內容\\2026\\0225_QPB_參數調整\\st_list.csv")
df_stock_list = df_stock_list.rename(columns = {"Bdate": "bdate"})

df_date_list = df_stock_list.drop_duplicates(subset = ["bdate"])[["年季", "bdate", "EDate"]].reset_index(drop = True)
df_date_list = df_date_list.sort_values(by = "bdate")

df_tw_2330 = pd.read_html("http://172.24.26.42/Cht_Strgy_IndexRet.php", encoding = "utf8")[0]
df_tw_2330["Date"] = df_tw_2330.apply(lambda x : x["日期"].split("-")[0] + x["日期"].split("-")[1] + x["日期"].split("-")[2], axis = 1)
df_tw_2330.to_csv("D:\\Python_code\\工作內容\\2026\\0225_QPB_參數調整\\df_tw2330.csv")


df_tw =  "select 日期, 股票代號, 股票名稱, 收盤價, 漲跌 from  [dbo].[日收盤表排行] where 股票代號 = 'TWA00' and 日期 >= '20190101'" 
sqltables = "日收盤表排行"
df_tw = PX.Sql_data(df_tw, sqltables)
df_tw["tw"] = df_tw.apply(lambda x : float(x["收盤價"]), axis = 1)




for i in range(0, len(df_date_list)):
    
    ### 撈資料 ###
    bdate = df_date_list["bdate"].iloc[i] #原始版的bdate
    
    bdate_60_str = date_60d_tr(df_date_list["bdate"].iloc[i], 90) #bdate 往前90天 因為60個交易日 約90天 30:22 = 90:66
    bdate_str = date_tr(df_date_list["bdate"].iloc[i]) #格式化後的bdate
    edate_str = date_tr(df_date_list["EDate"].iloc[i]) #格式化後的edate

    df_stock_list_season = df_stock_list[df_stock_list["bdate"] == bdate]
    
    df_stock_list_season_str = "("
    
    for j in range(0, len(df_stock_list_season)):
        
        df_stock_list_season_str = df_stock_list_season_str + "'" + str(df_stock_list_season["股票代號"].iloc[j]) + "',"

    df_stock_list_season_str = df_stock_list_season_str[:-1] + ")" 

    df_price_part =  "select 日期, 股票代號, 股票名稱, 收盤價, 漲跌 from  [dbo].[日收盤表排行] where (股票代號 in " +  df_stock_list_season_str + ") and (日期 between '" + bdate_60_str + "' and '" + edate_str + "')" 
    
    sqltables = "日收盤表排行"
    
    df_price_part = PX.Sql_data(df_price_part, sqltables)
    
    
    ### 算股票Ret ###
    #收盤價
    df_close = df_price_part.pivot(index = "日期", columns = "股票代號", values = "收盤價")
    
    for k in df_close.columns:
        
        df_close[k] = df_close[k].fillna(method = "ffill")
        df_close[k] = df_close.apply(lambda x : float(x[k]), axis = 1)
    
    df_close = df_close.reset_index(drop = False)
    
    df_close = pd.merge(df_close, df_tw[["日期", "tw"]], how = "left", on = "日期")
    df_close["tw"] = df_close.apply(lambda x : float(x["tw"]), axis = 1)
    
    df_rs_part = pd.DataFrame(df_close["日期"])
    
    #做了rs
    for m in df_close[df_close.columns[1:]]:
        
        if(m != "tw"):
            
            df_rs_part = pd.concat([df_rs_part, pd.DataFrame([df_close[m] / df_close["tw"]]).T.rename(columns = {0 : m})], axis = 1)
 
    df_rs_ratio_part = pd.DataFrame(df_close["日期"])
    
    #目前跑到這裡
    
    #做標準差
    for n in df_rs_part[df_rs_part.columns[1:]]:
        
        if(n != "tw"):
            
            
    
    
    
    
    
    
    
    
    
    
    
    
    
    #漲跌
    df_rise = df_price_part.pivot(index = "日期", columns = "股票代號", values = "漲跌")
    
    for m in df_close.columns:
        
        df_rise[m] = df_rise[m].fillna(0)
        df_rise[m] = df_rise.apply(lambda x : float(x[m]), axis = 1)
    
    #Ret
    df_ret = df_close / (df_close - df_rise) - 1
    df_ret = df_ret.reset_index(drop = False)
    df_ret = df_ret.rename(columns = {"日期" : "Date"})
    
    ### 算Beta ###
    for n in df_ret.columns[1:]:
        
        df_beta = df_ret[["Date", n]]
        df_beta = df_beta[df_beta["Date"] < bdate_str]
        
        df_beta = pd.merge(df_beta, df_tw_2330[["Date", "大盤不含台積電"]])
        df_beta = df_beta.dropna()
        
        x_train = np.array(df_beta['大盤不含台積電']).reshape(-1, 1)
        y_train = np.array(df_beta[n]).reshape(-1, 1)
        
        lm = LinearRegression()
        df_m = lm.fit(x_train, y_train)
        
        df_beta_list_part = pd.DataFrame([df_date_list[df_date_list["bdate"] == bdate]["年季"].iloc[0], n, df_m.coef_[0][0]]).T
        df_beta_list_part.columns = ["season", "st_id", "beta"]
        
        df_beta_list = pd.concat([df_beta_list, df_beta_list_part], axis = 0)
    
    
    ### 算策略調整損益 ###
    df_ret_method_1_output_part = pd.DataFrame(df_ret[df_ret["Date"] >= bdate_str]["Date"])
    df_ret_method_2_output_part = pd.DataFrame(df_ret[df_ret["Date"] >= bdate_str]["Date"])
    
    for o in df_ret.columns[1:]:
        
        df_method_ret_part = df_ret[["Date", o]][df_ret[["Date", o]]["Date"] >= bdate_str]
        df_method_ret_part = pd.merge(df_method_ret_part, df_tw_2330[["Date", "大盤不含台積電"]])
        
        df_stock_beta = df_beta_list[df_beta_list["season"] == df_date_list[df_date_list["bdate"] == bdate]["年季"].iloc[0]]
        df_stock_beta = df_stock_beta[df_stock_beta["st_id"] == o]["beta"].iloc[0]

        #避險調整後Ret
        df_method_ret_part["調整前"] = df_method_ret_part[o] + df_method_ret_part["大盤不含台積電"] * -1  
        df_method_ret_part["調整後"] = df_method_ret_part[o] + df_method_ret_part["大盤不含台積電"] * -1 * df_stock_beta
        
        df_ret_method_1_output_part = pd.merge(df_ret_method_1_output_part, df_method_ret_part[["Date", "調整前"]].rename(columns = {"調整前" : o}), how = "left", on = "Date")
        df_ret_method_2_output_part = pd.merge(df_ret_method_2_output_part, df_method_ret_part[["Date", "調整後"]].rename(columns = {"調整後" : o}), how = "left", on = "Date")

    df_ret_method_1_output_part["avr_ret"] = df_ret_method_1_output_part[df_ret_method_1_output_part.columns[1:]].mean(axis = 1)
    df_ret_method_2_output_part["avr_ret"] = df_ret_method_2_output_part[df_ret_method_2_output_part.columns[1:]].mean(axis = 1)

    df_ret_method_1_output_part = df_ret_method_1_output_part[["Date", "avr_ret"]]
    df_ret_method_2_output_part = df_ret_method_2_output_part[["Date", "avr_ret"]]

    df_ret_method_1_output = pd.concat([df_ret_method_1_output, df_ret_method_1_output_part], axis = 0)
    df_ret_method_2_output = pd.concat([df_ret_method_2_output, df_ret_method_2_output_part], axis = 0)

del bdate, bdate_60_str, bdate_str, df_beta, df_beta_list_part, df_m, df_method_ret_part, df_price_part, df_ret_method_1_output_part, df_ret_method_2_output_part, df_stock_beta, df_stock_list_season_str, edate_str, lm, x_train, y_train



























