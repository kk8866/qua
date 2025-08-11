import os, json
import pandas as pd
from . import simulate
from .simulate import cfg, quant, log
# simulate.flow()
cfg.sharpe=0.8
# class cfg:
    # qua: quant = None
    # status = {}
    # current = {}
    # log = None
    # max_post: int = 5
    # sharpe = 0.8

def flow(data_name, settings: dict= {}, region= "USA",universe="TOP3000", 
    delay=0,neu="SUBINDUSTRY",start=0, end=99, sharpe=0.8 ):
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
    funcs = [simulate.ff, simulate.ts_first, simulate.group_second, simulate.when_third, simulate.t_decay][start: end]
    for i, func  in enumerate(funcs):
        # 获取不到，或者获取到为当前值时进入
        if not cfg.current.get("func") or cfg.current.get("func")== func.__name__:
            cfg.sharpe = sharpe+0.15*i
            df = simulate.cases(func, df)
    df: pd.DataFrame = None
    for i in os.listdir(cfg.qua.path):
        if data_name +"-df"  in i:
            continue
        if data_name +"-" in i:
            dft = pd.read_csv(cfg.qua.path+i)
            df = pd.concat([df, dft])
    df.to_csv(cfg.qua.data_name+"-all.csv")
# flow("news18-EUR-0-TOP2500-v", region="EUR", universe="TOP2500",delay=1, neu="FAST")