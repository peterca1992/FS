#import yfinance as yf
import pandas as pd


#%%
def backtest_ma_entanglement(ticker, df_price, df_vol):
    
    # 1. 下載歷史數據
    df_price = df_price[["Date", str(ticker)]]
    df_vol = df_vol[["Date", str(ticker)]]
    
    df = pd.merge(df_price, df_vol, how = "left", on = "Date")
    
    df.columns = ["Date", "close", "volume"]
    
    # 2. 計算均線 (MA5, MA10, MA20, MA60)
    df["MA5"] = df["close"].rolling(window = 5).mean()
    df["MA10"] = df["close"].rolling(window = 10).mean()
    df["MA20"] = df["close"].rolling(window = 20).mean()
    df["MA60"] = df["close"].rolling(window = 60).mean()
    
    # 3. 計算成交量均線 (判斷是否放量)
    df["V_MA5"] = df["volume"].rolling(window=5).mean()

    # 4. 定義糾纏條件：計算四條線的最大值與最小值的差距
    # 差距在 2.5% 以內視為糾纏（但看昨天的 因為今天可能會突破 造成均線不在糾結）
    #ma_list = ['MA5', 'MA10', 'MA20', 'MA60']
    ma_list = ["MA5", "MA10", "MA20"]
    ma_max = df[ma_list].max(axis=1)
    ma_min = df[ma_list].min(axis=1)
    df["MA_Diff"] = (ma_max - ma_min) / ma_min
    
    df["MA_Diff2"] = df["MA_Diff"].shift(1)

    # 5. 判斷進場訊號
    # 條件 A: 均線糾纏 (差距 < 2.5%)
    # 條件 B: 收盤價突破糾纏區的最大值
    # 條件 C: 今日成交量 > 5日均量 1.5 倍
    # 條件 D: 5跟10日線 > 60日線
    
    df["Signal"] = (
        (df["MA_Diff2"] < 0.025) & 
        (df["close"] > ma_max) & 
        (df["volume"] > df['V_MA5'] * 1.5)&
        ((df["MA5"] > df["MA60"]) & (df["MA10"] > df["MA60"]))
    )

    # 篩選出訊號發生的日期
    #signals = df[df['Signal'] == True]
    return df

#%%
year_list = ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]

df_price = pd.DataFrame()
df_ret = pd.DataFrame()
df_vol = pd.DataFrame()
df_mv = pd.DataFrame()


for i in year_list:
    
    df_part1 = pd.read_csv("/Users/peterca/Desktop/python/2026/0101_均線糾結/data/price_" + str(i) + "_01.csv")
    df_part2 = pd.read_csv("/Users/peterca/Desktop/python/2026/0101_均線糾結/data/price_" + str(i) + "_02.csv")
    
    df_part1 = df_part1[df_part1.columns[1:]]
    df_part2 = df_part2[df_part2.columns[1:]]

    #上半年
    df_part1["Date"] = pd.to_datetime(df_part1["日期"], format = "%Y%m%d")
    df_part1 = df_part1[df_part1.apply(lambda x : len(str(x["股票代號"])), axis = 1) == 4].reset_index(drop = True)
    df_part1["股票代號"] = df_part1.apply(lambda x : str(x["股票代號"]), axis = 1)
    df_part1["ret"] = df_part1["收盤價"] / (df_part1["收盤價"] - df_part1["漲跌"]) - 1
    
    df_price_part1 = df_part1.pivot_table(columns = "股票代號", index = "Date", values = "收盤價").reset_index(drop = False)
    df_ret_part1 = df_part1.pivot_table(columns = "股票代號", index = "Date", values = "ret").reset_index(drop = False)
    df_vol_part1 = df_part1.pivot_table(columns = "股票代號", index = "Date", values = "成交金額(千)").reset_index(drop = False)
    df_mv_part1 = df_part1.pivot_table(columns = "股票代號", index = "Date", values = "總市值(億)").reset_index(drop = False)
    
    df_price = pd.concat([df_price, df_price_part1], axis = 0)
    df_ret = pd.concat([df_ret, df_ret_part1], axis = 0)
    df_vol = pd.concat([df_vol, df_vol_part1], axis = 0)
    df_mv = pd.concat([df_mv, df_mv_part1], axis = 0)
    
    #下半年
    df_part2["Date"] = pd.to_datetime(df_part2["日期"], format = "%Y%m%d")
    df_part2 = df_part2[df_part2.apply(lambda x : len(str(x["股票代號"])), axis = 1) == 4].reset_index(drop = True)
    df_part2["股票代號"] = df_part2.apply(lambda x : str(x["股票代號"]), axis = 1)
    df_part2["ret"] = df_part2["收盤價"] / (df_part2["收盤價"] - df_part2["漲跌"]) - 1
    
    df_price_part2 = df_part2.pivot_table(columns = "股票代號", index = "Date", values = "收盤價").reset_index(drop = False)
    df_ret_part2 = df_part2.pivot_table(columns = "股票代號", index = "Date", values = "ret").reset_index(drop = False)
    df_vol_part2 = df_part2.pivot_table(columns = "股票代號", index = "Date", values = "成交金額(千)").reset_index(drop = False)
    df_mv_part2 = df_part2.pivot_table(columns = "股票代號", index = "Date", values = "總市值(億)").reset_index(drop = False)
    
    df_price = pd.concat([df_price, df_price_part2], axis = 0)
    df_ret = pd.concat([df_ret, df_ret_part2], axis = 0)
    df_vol = pd.concat([df_vol, df_vol_part2], axis = 0)
    df_mv = pd.concat([df_mv, df_mv_part2], axis = 0)
    
del df_part1, df_part2, df_price_part1, df_ret_part1, df_vol_part1, df_mv_part1, df_price_part2, df_ret_part2, df_vol_part2, df_mv_part2, i

stock_list = df_price.columns[1:]


#%%

df_signal_output = pd.DataFrame()

for x in stock_list:
    
    ticker = str(x)
    
    df_part = backtest_ma_entanglement(ticker, df_price, df_vol)
    
    df_part["Signal2"] = df_part.apply(lambda x : 0 if x["Signal"] == False else 1, axis = 1)
    df_part = df_part.iloc[60:].reset_index(drop = True)
    
    signal_list = []
    stop_point_list = []
    
    for i in range(0, len(df_part)):
        
        if i == 0:
            
            signal_list.append(df_part["Signal2"].iloc[0])
            stop_point_list.append(0)
    
        else:
            
            #持續沒進場
            if((df_part["Signal2"].iloc[i] == 0) and (signal_list[i-1] == 0)):
                
                signal_list.append(0)
                stop_point_list.append(0)
            
            #判斷是否進場
            if((df_part["Signal2"].iloc[i] == 1) and (signal_list[i-1] == 0)):
                
                signal_list.append(1)
                
                start_point = df_part["close"].iloc[i]
                max_point = start_point
                stop_point = max_point * 0.95 #跌5％就出場
                stop_point_list.append(stop_point)
                
            #判斷是否續抱
            if((signal_list[i-1] == 1)):
                
                #出場
                if(df_part["close"].iloc[i] < stop_point):
                    
                    signal_list.append(0)
                    stop_point_list.append(stop_point)
                
                #續抱
                else:
                    
                    signal_list.append(1)
                    
                    max_point = max(df_part["close"].iloc[i], max_point)
                    stop_point = max_point * 0.95 #更新新的停損點 改用收盤最高點跌破5%
                    stop_point_list.append(stop_point)
                    
    df_part["signal3"] = signal_list
    df_part["stop_point"] = stop_point_list
    
    if(x == stock_list[0]):
        
        df_signal_output = pd.concat([df_signal_output, df_part[["Date", "signal3"]].rename(columns = {"signal3" : x})], axis = 0)

    if(x != stock_list[0]):
        
        df_signal_output = pd.merge(df_signal_output, df_part[["Date", "signal3"]].rename(columns = {"signal3" : x}), on = "Date", how = "left")

#%%
df_signal_output2 = df_signal_output.iloc[:-1].reset_index(drop = True)

df_ret2 = df_ret[df_signal_output.columns]
df_ret2 = df_ret2[df_ret2["Date"] >= df_signal_output2["Date"].iloc[1]].reset_index(drop = True)

df_ret_signal = df_ret2[df_ret2.columns[1:]] * df_signal_output2[df_ret2.columns[1:]]
df_ret_signal["avr"] = df_ret_signal.mean(axis = 1)
df_ret_signal["Date"] = df_ret2["Date"]

df_ret_signal = df_ret_signal[["Date", "avr"]]








        
        
        





























