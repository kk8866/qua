
import sys, json, yaml
from pydantic import BaseModel
with open('./case.yaml', 'r', encoding='utf-8') as f:
        yldata = yaml.load(f.read(), Loader=yaml.FullLoader)
        cases = {i :cas for i, cas in enumerate(yldata["cases"])}
        yldata["cases"] = cases
class paras:
        type: str
        settings: str
class cases:
        name: str
        config: dict
class yamldata:
        name: str = ""
        type: str = ""
        settings: dict = {}
        cases: dict = yldata["cases"]
        slots_counts: int = 8
        one_slot_number:  int = 10
class current_model(BaseModel):
    index: int = 0
    name: str = ""
    start_time: str = None
    case: int = 0
    total: int = 0 
    end_time: str = None
    finish: bool = False
class statuss(BaseModel):
    current: current_model = current_model()
    status: dict = {}

class currend:
        xxx: 123
        
class cfg:
    data_name: str = yldata.get("name")
    path: str = "/storage/emulated/0/qua/" if sys.platform == "linux"\
            else "C:\\Project\\qua/"
#     status = {}
#     current = {}
    log = None
    max_post: int = 5
    sharpe = 0.8
    path = "/storage/emulated/0/qua/" if sys.platform == "linux"\
            else "D:/rjh/learn/"
    path += data_name.split("-")[0]+"/"
    data_name =path+data_name
    log_name = path+data_name+'-log.txt'
    status = data_name+"-case.json"
    case_json = data_name+"-df.json"
    result_df = data_name+"-result.csv"
    save_file: str = None
def save_status(self, index):
    status.current["case"] = index
    cfg.log(str(status.model_dump()))
    with open(cfg.status, "w") as f:
        f.write(json.dumps(status.model_dump()))
# print(yldata["cases"])

status = statuss()