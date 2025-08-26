import pandas as pd
'''
组成aplha的方法
'''
def ff(df :pd.DataFrame):
    return df
# ts序列
def ts_first(df: pd.DataFrame, days:list = [5, 22, 66, 252]) ->pd.DataFrame:
    ts_ops = ["ts_rank", "ts_zscore", "ts_delta",  "ts_sum", "ts_delay", 
          "ts_std_dev", "ts_mean",  "ts_arg_min", "ts_arg_max","ts_scale", "ts_quantile"]
    arr = []
    for i in df.index:
        for day in days:
            for op in ts_ops:
                arr.append({"code": f'{op}({df.loc[i]["code"]}, {day})',
                 "settings": df.loc[i]["settings"]})
    return pd.DataFrame(arr)
def group_second(df: pd.DataFrame,):
    group_ops=["group_rank", "group_zscore", "group_scale", "group_neutralize"]
    group_datas = ["industry", "subindustry", "exchange","market"]
    if df.loc[df.index[0], "settings"]["region"] in ["GLB", "EUR","ASI"]:
        gps += ["group_cartesian_product(country, industry)", 
    "group_cartesian_product(country, subindustry)"]
    group_cartesian_product = [f"group_cartesian_product(country, {i})" for i in group_datas]
    arr = []
    for i in df.index:
        # 判断地区，是欧亚全球时，走国家联合
        current_datas = group_datas + group_cartesian_product if \
            df.loc[i]["settings"]["region"] in ["GLB", "EUR","ASI"] else group_datas
        for op in group_ops:
            for gp in current_datas:
                arr.append({"code": f'{op}({df.loc[i]["code"]}, {gp})',
                 "settings": df.loc[i]["settings"]})
    return pd.DataFrame(arr)

def when_third(df:pd.DataFrame,) ->pd.DataFrame:
    open_events = ['group_rank(ts_std_dev(returns,60),sector)>0.7', 
        'ts_mean(volume,5)>ts_mean(volume,60)', 
        'ts_zscore(returns,60)>2', 
        'ts_std_dev(returns, 5)>ts_std_dev(returns, 20)', 
        'returns<0.09', 
        'ts_corr(close,volume,5)>0', 
        'ts_corr(close,volume,5)<0', 
        'returns>-0.09',
        "abs(returns)<0.10"]
    # open_events=["rank(rp_css_business)>0.8","ts_rank(rp_css_business,22)>0.8",
    # "rank(vec_avg(nws3_scores_posnormscr))>0.8",
    # "ts_rank(vec_avg(nws3_scores_posnormscr),22)>0.8",]
    arr=  []
    for i in df.index:
        for op in open_events:
            arr.append({"code":f'{op}?{df.loc[i]["code"]}:-1',
                 "settings": df.loc[i]["settings"]})
    return pd.DataFrame(arr)
    
def t_decay(df: pd.DataFrame, s=1,n=11) ->pd.DataFrame:
    arr = []
    for i in df.index:
        for decay in range(s, n):
            settings = df.loc[i]["settings"].copy()
            settings["decay"]=decay
            arr.append({"code": df.loc[i]["code"], "settings":  settings})
    return pd.DataFrame(arr)
def t_truncation(df: pd.DataFrame, s=0, e=10) ->pd.DataFrame:
    arr = []
    for i in  df.index:
        for decay in range(s, e):
            settings = df.loc[i]["settings"].copy()
            settings["decay"]=0.061+decay/500
            arr.append({"truncation":settings, "code": df.loc[i]["code"]})
    return pd.DataFrame(arr)
def t_neutralization(df: pd.DataFrame, now:str=None) ->pd.DataFrame:
    arrs = []
    neus=["SUBINDUSTRY", "INDUSTRY", "RAM", "STATISTICAL", "CROWDING", "FAST", "SLOW", "MARKET", "SECTOR", "SLOW_AND_FAST",]
    fast = ["SUBINDUSTRY", "INDUSTRY", "MARKET", "SECTOR"]
    slow = ["STATISTICAL", "CROWDING", "FAST", "SLOW","SLOW_AND_FAST"] 
    neus = [i for i in neus if i != now]
    for i in  df.index:
        for neu in neus:
            settings = df.loc[i]["settings"].copy()
            settings["neutralization"]=neu
            arrs.append({"settings": settings, "code": df.loc[i]["code"]})
    return arrs
def deal_data(df: pd.DataFrame,sharpe: float=0.9,n: int=1, 
    save_file:str="", case_df: str="") ->pd.DataFrame:
    # 变更sharpe和fitness，按照原始表达式分组。按照fitness+sharpe排序取前n。
    def op(x: str):
        # 存在？ 代表三阶
        if "?" in x:
            x = x.split("?")[1:]
        elif x.startswith("group_"):
            return "-".join(x.split("(")[0:1])
        return x.split("(")[0]
    def get_exp(x: str):
        return x.split("  ")[1] if "  " in x else x
    # df["result"] = df["checks"].apply(lambda x:  False if [i for i in x if i.get("reult") == "FAIL"] else True)
    df["total"] = abs(df["fitness"] + df["sharpe"])
    df["exp"] = df["code"].apply(lambda x: get_exp(x))
    df["op"] = df["code"].apply(lambda x: op(x))
    df.sort_values(by="total", inplace=True,ascending=False)
    df.to_csv(save_file)
    # 移除带\n表示网页端测试
    df = df[df["code"].apply(lambda x: "\n" not in x)]
    # long+short<20的不考虑
    df = df[df["longCount"]+df["shortCount"]>20]
    df = df[(abs(df["sharpe"])>=sharpe) | (abs(df["fitness"]) >= 1)]
    df = df.groupby(["exp", "op"]).head(n)
    df.reset_index(drop=True, inplace=True)
    for a in df.index:
        if df.loc[a]["sharpe"] <0:
            df.iat[a,"code"] = " -"+df.loc[a]["code"]
    df.to_json(case_df)
    return df
def Processing_results():
    
    pass