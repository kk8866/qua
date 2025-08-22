
import os,datetime, json
import pytz
import yaml
import pandas as pd
from .config import cfg, save_status
from .config import yamldata
from .log import log
from .api import quant
from .  import data


def get_time()->str:
        now = datetime.datetime.now(pytz.timezone('America/New_York'))
        return now.isoformat().split(".")[0]
def one_cases(func, df, para=None):

    # 组装生成alphas
    arrs: pd.DataFrame = getattr(data, func)(df, para)
    status.current.total = len(arrs)
    if not status.current.start_time:
        status.current.start_time = get_time()
    status.current.name = func
    log(cfg.status)
    # 执行回测
    qua = quant()
    qua.sims(arrs)
    # 获取结果
    df: pd.DataFrame = qua.get_result(status.current.total, cfg.current.start_time)
    # self.save_file = self.data_name + f"-{func.__name__}.csv"
    df = data.deal_data(df, sharpe=cfg.sharpe,)
    status.current.end_time = get_time()
    status[func] = cfg.current
    status.current.finish = True
    save_status(index=0)
    return df

def init(data, funcs, region= "USA",universe="TOP3000",\
    delay=0,neu="SUBINDUSTRY", start=1, end=5 ,sharpe=0.66,\
    only_case:bool=False):
    df = None
    if isinstance(data, list):
        df = pd.DataFrame(data, columns=["code"])
        data = "temp-1"
    if os.path.exists(cfg.case_status):
        with open(cfg.case_status, "r") as f:
            cfg.status = json.load(f)
    if os.path.exists(cfg.case_df):
        df = pd.read_csv(cfg.case_df)
    elif not df:
        df = pd.read_csv(cfg.data_name+".csv")
        df["code"] = "  " + df["code"] + "  "
    if "settings" not in df.columns:
        settings =  yamldata.config.settings
        # df = df.to_dict() 
        df["settings"] ={i:settings for i in list(df["code"].keys())}
        df = pd.DataFrame(df)
    print("status: ", cfg.status)
    return df
    
def flow(data, funcs, region= "USA",universe="TOP3000",\
    delay=0,neu="SUBINDUSTRY", start=1, end=5 ,sharpe=0.66,\
    only_case:bool=False) -> None :
    
    # 加载状态
        
    
   
    cfg.current = cfg.status.cu
    # funcs = [t_neutralization, ff, ts_first, group_second, when_third, t_decay][start:end]
    for i, func  in enumerate(funcs):
        cfg.current = cfg.current.get("func", func.__name__)
        if cfg.current.get("func") != func.__name__:
            continue
        # 设置开始时间
        if not cfg.current.get("time"):
            now = datetime.datetime.now(pytz.timezone('America/New_York'))
            s_time =  now.isoformat().split(".")[0]
            cfg.current["time"] = s_time
            # 开始组装回测
        cfg.sharpe +=i*0.2
        df = one_cases(func, df, sharpe=sharpe+i, max_post=8)
    for i in cases:
        finish = cases[i]["finish"]
        if  finish:
            continue
        func = cases[i]["name"]
        config = cases[i]["config"]
        
        # 把所有结果拼接到一个表里
    # df: pd.DataFrame = None
    # for i in os.listdir(cfg.qua.path):
    #     if data +"-df"  in i:
    #         continue
    #     if data +"-" in i:
    #         dft = pd.read_csv(cfg.qua.path+i)
    #         df = pd.concat([df, dft])
    #     df.to_csv(cfg.qua.data_name+"-all.csv")
    # os.remove(cfg.cas)
def init():
    name = yldata.get("name")
    cases = yldata.get("cases")
    for i in cases:
        o_case = cases[i]["case_name"]
        para = cases[i]["para"]
class current:
    name: str
    start_time: str = None
    case: int
    total: int
    end_time: str = None
    finish: bool        

class status:
    current: current
cases: dict = {}
