import requests, logging, os, sys, re
from logging.handlers import RotatingFileHandler
import json
from requests.auth import HTTPBasicAuth
import pandas as pd
from time import sleep
import time
import datetime
import pytz
# 加载凭据文件
import logging
class quant:
    def __init__(self, data_name: str) -> None:
        self.arr = []
        self.count = 0
        self.max_post = 2
        self.path = "/storage/emulated/0/qua/" if sys.platform == "linux"\
            else "C:\\Project\\qua\\"
        self.path += data_name.split("-")[0]+"/"
        os.makedirs(self.path, exist_ok=True)
        self.data_name =self.path+data_name
        self.log_name = self.path+data_name+'-log.txt'
        self.case_name = self.data_name+"-case.json"
        self.case_df = self.data_name+"-df.json"
        self.result_df = self.data_name+"-result.csv"
        self.sess = requests.Session()
        self.save_file: StopIteration = None
        
    def login(self,):
        with open(self.path + '../brain.txt') as f:
            self.username, self.password = json.load(f)
        self.sess.auth = HTTPBasicAuth(self.username, self.password)
        response = self.sess.post('https://api.worldquantbrain.com/authentication')
        print(response)

    def save_result(self, alpha_num, s_time) -> pd.DataFrame:
        # 2025-07-04T22:52:30
        arr = []
        print(alpha_num, s_time)
        for i in range(0, alpha_num+100, 100):
            print(i)
            url = "https://api.worldquantbrain.com/users/self/alphas?limit=100&offset=%d"%(i) \
                    + "&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E=" + s_time  \
                    + "-04:00"
            print(url)
            response = self.sess.get(url)
            print(response)
            alpha_list = response.json()["results"]
            if len(alpha_list)==0:
                return pd.DataFrame(arr)
            for alphas_p in alpha_list:
                result = dict()
                result["id"] = alphas_p["id"]
                result["code"] = alphas_p["regular"]["code"]
                result["result"] = "FAIL" if  [i.get("name") for i in alphas_p["is"]["checks"] if i.get("result") == "FAIL"] else "PASS"
                LOW_SUB_UNIVERSE_SHARPE = [i for i in alphas_p["is"]["checks"] if i["name"] == "LOW_SUB_UNIVERSE_SHARPE"][0]
                result["sub"]=LOW_SUB_UNIVERSE_SHARPE.get("value", -2)-LOW_SUB_UNIVERSE_SHARPE.get("limit", 2)
                CONCENTRATED_WEIGHT: dict = [i for i in alphas_p["is"]["checks"] if i["name"] == "CONCENTRATED_WEIGHT"][0]
                result["weight"] = CONCENTRATED_WEIGHT.get("limit", 0) - CONCENTRATED_WEIGHT.get("value", 0)
                aplha_is:dict = alphas_p["is"]
                delete =  ["startDate", "checks", "bookSize"]
                for ite in delete:
                    del aplha_is[ite] 
                # del 
                result.update(aplha_is)
                result["settings"] = alphas_p["settings"]
                del result["settings"]["startDate"]
                del result["settings"]["endDate"]
                arr.append(result)
        return pd.DataFrame(arr)

    def submit_simulations(self, index,  alpha_list, max_post=3):
        if self.count % 80 == 0:
            self.sess.close()
            self.login()
        self.count +=1
        if  alpha_list:
            print(alpha_list[0])
            for _ in range(30):
                try:
                    sim1 = None
                    sim1 = self.sess.post('https://api.worldquantbrain.com/simulations', json=alpha_list,)
                    location = sim1.headers['Location'].split("/")[-1]
                    break
                except  Exception as e:
                    print(e, index, sim1)
                    sleep(10)
                    if _ == 19:
                        cfg.log(f"post ERROR: {index}")
                        return
            self.arr.append((index, location))
            self.save_status(index+1)
        try:  
            print(self.arr)
            while len(self.arr) >= max_post:
                for index, ip in self.arr:
                    url = "https://api.worldquantbrain.com/simulations/" + ip
                    sim_progress_resp = self.sess.get(url)
                    retry_after_sec = sim_progress_resp.headers.get("Retry-After", 0)
                    if retry_after_sec == 0:  # simulation done!模拟完成!
                        if (index, ip) in self.arr:
                            self.arr.remove((index, ip)) #删除对应的值
                        children = sim_progress_resp.json().get("children")  # 获取alpha id
                        status1 = sim_progress_resp.json().get("status")
                        if status1 == "ERROR":
                            cfg.log(f"status ERROR: {index} {ip}" )
                        print(index, status1, children) 
                        sleep(0.1)
                    else:
                        sleep(0.25)
        except Exception as e:
            cfg.log(e)
            print(e)
            cfg.log(f"no location [{index}], sleep for 10 seconds and try next alpha.没有位置，睡10秒然后尝试下一个字母。”")
            sleep(10)
    def save_status(self, index):
        cfg.current["case"] = index
        cfg.log(str(cfg.status))
        with open(self.case_name, "w") as f:
            f.write(json.dumps(cfg.status))
    def sims(self, df: pd.DataFrame, start: int=0):
        print(len(df.index)) 
        arr= []
        start = cfg.status.get("case",0)
        i = 0
        start+=1
        for i, index in enumerate(df.index[start:], start=start):
            alpha_s =  { 
                "type": "REGULAR",
                "settings": df.loc[index]["settings"],
                "regular": df.loc[index]["code"] }
            arr.append(alpha_s)
            if len(arr) == 10:
                print(arr[0])
                cfg.log(f"index is: {index}")
                cfg.qua.submit_simulations(index, arr, max_post=cfg.max_post)
                arr = []
        cfg.qua.submit_simulations(index, arr, max_post=cfg.max_post)
        cfg.qua.submit_simulations(i, [], max_post=1)

    def deal_data(self, df: pd.DataFrame,sharpe: float=0.9,n: int=1, save_file:str=""):
        # 变更sharpe和fitness，按照原始表达式分组。按照fitness+sharpe排序取前n。
        for a in df.index:
            if df.loc[a]["sharpe"] <0:
                df.iat[a,"code"] = "-"+df.loc[a]["code"]
        df = df[df["longCount"]+df["shortCount"]>4]
        df["total"] = abs(df["fitness"] + df["sharpe"])
        df["exp"] = df["code"].apply(lambda x: x.split("  ")[1] if "  " in x else x)
        df["op"] = df["code"].apply(lambda x: x.split("(")[1] if "(" in x else x)
        df.sort_values(by="total", inplace=True,ascending=False)
        df.to_csv(self.save_file +".csv")
        df = df[(abs(df["sharpe"])>=sharpe) | (abs(df["fitness"]) >= 1)]
        df = df.groupby(["exp", "op"]).head(n)
        df.to_json(self.case_df)
        cfg.status = {}
        return df
#原始序列
def ff(df :pd.DataFrame):
    return df
# ts序列
def ts_first(df: pd.DataFrame, days:list = [5, 22, 66, 252]) ->pd.DataFrame:
    ts_ops = ["ts_rank", "ts_zscore", "ts_delta",  "ts_sum", "ts_delay", 
          "ts_std_dev", "ts_mean",  "ts_arg_min", "ts_arg_max","ts_scale", "ts_quantile"]
    arr = []
    for i in df.index:
        for op in ts_ops:
            for day in days:
                arr.append({"code": f'{op}({df.loc[i]["code"]}, {day})',
                 "settings": df.loc[i]["settings"]})
    return pd.DataFrame(arr)
def group_second(df: pd.DataFrame,):
    groups=["group_rank", "group_zscore", "group_scale", "group_neutralize"]
    gps = ["industry", "subindustry"]
    if df.loc[df.index[0], "settings"]["region"] in ["GLB", "EUR","ASI"]:
        gps += ["group_cartesian_product(country, industry)", 
    "group_cartesian_product(country, subindustry)"]
    arr = []
    for i in df.index:
        for op in groups:
            for gp in gps:
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
            arr.append({"code":f'{op}? {df.loc[i]["code"]}:-1',
                 "settings": df.loc[i]["settings"]})
    return pd.DataFrame(arr)
    
def t_decay(df: pd.DataFrame, s=2,n=11) ->pd.DataFrame:
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
    neus=["SUBINDUSTRY", "INDUSTRY", "RAM","NONE", "STATISTICAL", "CROWDING", "FAST", "SLOW", "MARKET", "SECTOR", "SLOW_AND_FAST",]
    neus = [i for i in neus if i != now]
    for i in  df.index:
        for neu in neus:
            settings = df.loc[i]["settings"].copy()
            settings["neutralization"]=neu
            arrs.append({"settings": settings, "code": df.loc[i]["code"]})
    return arrs
def cases(func, df):
    def get_time():
        now = datetime.datetime.now(pytz.timezone('America/New_York'))
        return now.isoformat().split(".")[0]
    cfg.qua.save_file = cfg.qua.data_name + f"-{func.__name__}.csv"
    arrs = func(df)
    if not cfg.current.get("time"):
        cfg.current["time"] = get_time()
    cfg.current["func"] = func.__name__
    cfg.status[func.__name__] = {}
    print(cfg.status)
    cfg.qua.sims(arrs)
    df: pd.DataFrame = cfg.qua.save_result(len(arrs), cfg.current.get("time"))
    df = cfg.qua.deal_data(df, sharpe=cfg.sharpe,)
    cfg.current["end_time"] = get_time()
    cfg.status[func.__name__] = cfg.current
    cfg.current = {}
    cfg.qua.save_status(index=0)
    return df
def log(name,):
    logger = logging.getLogger(name)
    formater = logging.Formatter( "[%(asctime)s] %(message)s", '%Y-%m-%d %H:%M:%S' )
    logger.setLevel(logging.DEBUG)
    # if not show:
    file_log = logging.FileHandler(name, )
    file_log.setFormatter(formater)
    logger.addHandler(file_log)
    # 是否需要打印在屏幕上
    # else:
    ch = logging.StreamHandler()
    ch.setFormatter(formater)
    logger.addHandler(ch)
    return logger
class cfg:
    qua: quant = None
    status = {}
    current = {}
    log = None
    max_post: int = 5
    sharpe = 0.8
def flow(data_name, settings: dict= {}, region= "USA",universe="TOP3000", delay=0,neu="SUBINDUSTRY",start=0, end=99, sharpe=0.8 ):
    cfg.qua = quant(data_name)
    cfg.log = log(cfg.qua.log_name).info
    if os.path.exists(cfg.qua.case_name):
        with open(cfg.qua.case_name, "r") as f:
            cfg.status = json.load(f)
    if os.path.exists(cfg.qua.case_df):
        df = pd.read_json(cfg.qua.case_df) 
    else:
        df = pd.read_csv(cfg.qua.data_name+".csv")
        df["code"] = "  " + df["code"] + "  "
        
    if "settings" not in df.columns:
        settings = {
                    "instrumentType": "EQUITY",
                    "region": region,
                    "universe": universe,
                    "delay": delay,
                    "decay": 0,
                    "neutralization": neu,
                    "truncation": 0.08,
                    "pasteurization": "ON",
                    "unitHandling": "VERIFY",
                    "nanHandling": "ON",
                    "language": "FASTEXPR",
                    "visualization": False }
        df = df.to_dict() 
        df["settings"] ={i:settings for i in list(df["code"].keys())}
        df = pd.DataFrame(df)
    print("status: ", cfg.status)
    cfg.current = cfg.status.get("current",{})
    cfg.qua.login()
    funcs = [ff, ts_first, group_second, when_third, t_decay][start: end]
    for i, func  in enumerate(funcs):
        # 获取不到，或者获取到为当前值时进入
        if not cfg.current.get("func") or cfg.current.get("func")== func.__name__:
            cfg.sharpe = sharpe+0.15*i
            df = cases(func, df)
    df: pd.DataFrame = None
    for i in os.listdir(cfg.qua.path):
        if data_name +"-df"  in i:
            continue
        if data_name +"-" in i:
            dft = pd.read_csv(cfg.qua.path+i)
            df = pd.concat([df, dft])
    df.to_csv(cfg.qua.data_name+"-all.csv")
     
flow("news18-EUR-0-TOP2500-v", region="EUR", universe="TOP2500",delay=1, neu="FAST")