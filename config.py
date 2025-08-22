
import sys, json, yaml
with open('./case.yaml', 'r', encoding='utf-8') as f:
        yldata = yaml.load(f.read(), Loader=yaml.FullLoader)
        cases = {i :cas for i, cas in enumerate(yldata["cases"])}
        yldata["cases"] = cases
class currend:
        
        
class cfg:
    data_name: str = yldata.get("name")
    path: str = "/storage/emulated/0/qua/" if sys.platform == "linux"\
            else "C:\\Project\\qua\\"
    status = {}
    current = {}
    log = None
    max_post: int = 5
    sharpe = 0.8
    path = "/storage/emulated/0/qua/" if sys.platform == "linux"\
            else "C:\\Project\\qua\\"
    path += data_name.split("-")[0]+"/"
    data_name =path+data_name
    log_name = path+data_name+'-log.txt'
    case_status = data_name+"-case.json"
    case_df = data_name+"-df.json"
    result_df = data_name+"-result.csv"
    save_file: str = None
def save_status(self, index):
    cfg.current["case"] = index
    cfg.log(str(cfg.status))
    with open(cfg.case_name, "w") as f:
        f.write(json.dumps(cfg.status))
# print(yldata["cases"])
class paras:
        type: str
        settings: str
class cases:
        name: str
        config: dict
class yamldata:
        name: str
        para: paras
        cases: dict
