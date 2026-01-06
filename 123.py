import pandas as pd


df_ret = pd.read_csv("D:\\Python_code\\工作內容\\2026\\0106_均線糾結策略\\ret.csv")


df_ret["Date2"] = pd.to_datetime(df_ret["Date"], format = "%Y/%m/%d")
df_ret["Year"] = df_ret.apply(lambda x : x["Date2"].year, axis = 1)

df_sharpe = pd.DataFrame()

for i in df_ret.drop_duplicates(subset = ["Year"])["Year"]:
    
    df_part = df_ret[df_ret["Year"] == i]
    
    df_part1 = pd.DataFrame([i, "avr_d", df_part["avr_d"].mean()*252, df_part["avr_d"].std()*16]).T
    df_part2 = pd.DataFrame([i, "tw_d", df_part["tw_d"].mean()*252, df_part["tw_d"].std()*16]).T
    
    df_part3 = pd.concat([df_part1, df_part2], axis = 0)

    df_sharpe = pd.concat([df_sharpe, df_part3], axis = 0)


df_dd = pd.DataFrame()

for i in df_ret.drop_duplicates(subset = ["Year"])["Year"]:
    
    df_part = df_ret[df_ret["Year"] == i]
    df_part = df_part[["Date2", "avr_d", "tw_d"]]
    
    df_part["avr_t"] = df_part["avr_d"].cumsum()
    df_part["tw_t"] = df_part["tw_d"].cumsum()
    
    avr_dd_day = []
    tw_dd_day = []
    
    #指標
    for j in range(0, len(df_part)):
        
        if(df_part["avr_t"].iloc[j] < 0):
            
            if(len(avr_dd_day) != 0):
                avr_dd_day.append(avr_dd_day[j-1] + 1)
                
            else:
                avr_dd_day.append(1)
            
        else:
            avr_dd_day.append(0)
        
    
    #大盤
    for j in range(0, len(df_part)):
        
        if(df_part["tw_t"].iloc[j] < 0):
            
            if(len(tw_dd_day) != 0):
                tw_dd_day.append(tw_dd_day[j-1] + 1)
                
            else:
                tw_dd_day.append(1)
            
        else:
            tw_dd_day.append(0)
        
    df_part["avr_dd_day"] = avr_dd_day
    df_part["tw_dd_day"] = tw_dd_day
    
    
    #調整最大天數 與 最大跌幅
    for x in ["avr_dd_day", "tw_dd_day"]:
    
        columns_total = []    
    
        for j in range(0, len(df_part)-1):
            
            if(df_part[x].iloc[j+1] != 0):
                columns_total.append(0)
            
            else:
                columns_total.append(df_part[x].iloc[j])
                
        columns_total.append(0)
            
        df_part[x + "2"] = columns_total
            
    
    
    aa = pd.DataFrame([i, "Avr", min(df_part["avr_t"]), max(df_part["avr_dd_day"]), df_part[df_part["avr_dd_day2"] != 0]["avr_dd_day2"].mean()]).T
    bb = pd.DataFrame([i, "Tw", min(df_part["tw_t"]), max(df_part["tw_dd_day"]), df_part[df_part["tw_dd_day2"] != 0]["tw_dd_day2"].mean()]).T
    
    df_dd = pd.concat([df_dd, pd.concat([aa, bb], axis = 0)], axis = 0)
    
    
    
    
    
    
    
    
    
    
    
    
    
    