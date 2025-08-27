import requests
import json
from requests.auth import HTTPBasicAuth
import pandas as pd
from time import sleep
from config import cfg, save_status, status
from log import log
from config import yamldata
class quant:
    def __init__(self) -> None:
        self.arr = {}
        self.count = 0
        self.max_post = 2
        self.sess = requests.Session()
        
    def login(self,):
        with open(cfg.path + '../brain.txt') as f:
            self.username, self.password = json.load(f)
        self.sess.auth = HTTPBasicAuth(self.username, self.password)
        response = self.sess.post('https://api.worldquantbrain.com/authentication')
        print(response.status_code)

    def get_result(self, alpha_num, s_time) -> pd.DataFrame:
        '''传入获取的数量和开始的时间参数
        返回df'''
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
                if "regular" not in result["code"]:
                    continue
                # 获取表达式
                result["code"] = alphas_p["regular"]["code"]
                # 检查checks中是否有fail
                result["result"] = False if  [i.get("name") for i in alphas_p["is"]["checks"] if i.get("result") == "FAIL"] else True
                # is中单keys数据类型的值直接保留
                alpha_is:dict[str, dict] = alphas_p["is"]
                result.update({i:alpha_is[i] for i in alpha_is if isinstance(alpha_is[i], (float, str, int))})
                # 保存checks中的详细数据
                no_check = ["LOW_SHARPE", "LOW_FITNESS", "HIGH_TURNOVER", "LOW_TURNOVER"]
                checks = {i["name"]: round(i.get("value") - i.get("limit"), 4) for i in alphas_p["is"]["checks"]\
                        if ("limit" in i and i.get("name") not in no_check) }
                # 暂定2y sharpe保留为原始值
                result["LOW_2Y_SHARPE"] = [i.get("value") for i in alphas_p["is"]["checks"] if i.get("name")=="LOW_2Y_SHARPE"][0]
                result.update(checks)
                
                # 保存其他项的sharpe和fitness
                _fit = {i+"_fitness": alpha_is[i].get("fitness") for i in alpha_is if isinstance(alpha_is[i], dict)}
                _sharpe = {i+"_sharpe": alpha_is[i].get("fitness") for i in alpha_is if isinstance(alpha_is[i], dict)}
                result.update(_fit)
                result.update(_sharpe)
                result.update(alphas_p["settings"])
                result["settings"] = alphas_p["settings"]
                # 删除settings中不需要的字段
                del result["settings"]["startDate"]
                del result["settings"]["endDate"]
                result["dateCreated"] = alphas_p["dateCreated"]
                result["margin"] = result["margin"]*1e4
                arr.append(result)
        return pd.DataFrame(arr)
    def get_results(self, alpha_num, s_time) -> pd.DataFrame:
        '''传入获取的数量和开始的时间参数
        返回df'''
        # 2025-07-04T22:52:30
        arr = []
        print(alpha_num, s_time)
        self.login()
        for i in range(0, alpha_num+100, 100):
            print(i)
            url = "https://api.worldquantbrain.com/users/self/alphas?limit=100&offset=%d"%(i) \
                    + "&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E=" + s_time  \
                    + "-04:00"
            print(url)
            response = self.sess.get(url)
            if response.status_code>205:
                print(response.json())
            alpha_list = response.json()["results"]
            if len(alpha_list)==0:
                return pd.DataFrame(arr)
            for alpha in  alpha_list:
                alpha["result"] =  False if [i for i in alpha if i.get("reult") == "FAIL"] else True
            arr += alpha_list
        return pd.DataFrame(arr)
    def submit_simulations(self, index,  alpha_list, max_post=3):
        if self.count % 80 == 0:
            self.sess.close()
            self.login()
        self.count +=1
        if  alpha_list:
            print(alpha_list[0])
            for _ in range(30):
                sim1 = None
                sim1 = self.sess.post('https://api.worldquantbrain.com/simulations', json=alpha_list,)
                if sim1.status_code <299:
                    location = sim1.headers['Location'].split("/")[-1]
                    self.arr[index] = location
                    save_status(index+1)
                    print(index, location)
                    break
                print(index, sim1.json())
                location = sim1.headers['Location'].split("/")[-1]
                sleep(10)
                if _ == 29:
                    cfg.log(f"post ERROR: {index}")
                    return
        try:
            while len(self.arr) >= max_post:
                for i in self.arr:
                    url = "https://api.worldquantbrain.com/simulations/" + self.arr[i]
                    sim_progress_resp = self.sess.get(url)
                    retry_after_sec = sim_progress_resp.headers.get("Retry-After", 0)
                    if retry_after_sec == 0:  # simulation done!模拟完成!
                        del self.arr[i]
                        print("  ".join(self.arr.keys()))
                        children = sim_progress_resp.json().get("children")  # 获取alpha id
                        status1 = sim_progress_resp.json().get("status")
                        if status1 == "ERROR":
                            cfg.log(f"status ERROR: {i} {self.arr[i]}" )
                        print(i, status1, children) 
                        break
                    sleep(0.25)
        except Exception as e:
            cfg.log(e)
            print(e)
            cfg.log(f"no location [{index}], sleep for 10 seconds and try next alpha.没有位置，睡10秒然后尝试下一个字母。”")
            sleep(10)
    def sims(self, df: pd.DataFrame, start: int=0):
        print(len(df.index)) 
        arr= []
        start = status.current.case
        start+=1
        for i, index in enumerate(df.index[start:], start=start):
            alpha_s =  { 
                "type": yamldata.type,
                "settings": df.loc[index]["settings"]  if "settings" in df.columns else yamldata.settings,
                "regular": df.loc[index]["code"] }
            arr.append(alpha_s)
            if len(arr) == yamldata.one_slot_number or i>=len(df.index)-1:
                log(f"index is: {index}")
                self.submit_simulations(index, arr, max_post=cfg.max_post)
                arr = []
        self.submit_simulations(len(df.index), [], max_post=1)
