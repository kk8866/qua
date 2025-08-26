import json, os
import requests
import pandas as pd
import logging
import time
import requests
from typing import Optional, Tuple
from typing import Tuple, Dict, List
from typing import Union, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import pickle
from collections import defaultdict
import datetime
# from tqdm import tqdm
from pathlib import Path
import sys

    
def sign_in(username, password):
        s = requests.Session()
        s.auth = (username, password)
        try:
                response = s.post('https://api.worldquantbrain.com/authentication')
                response.raise_for_status()
                logging.info("Successfully signed in")
                return s
        except requests.exceptions.RequestException as e:
                logging.error(f"Login failed: {e}")
                return None
def save_obj(obj: object, name: str) -> None:
    filename = os.path.join(cfg.data_path, name+ '.pickle')
    with open(filename, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
def load_obj(name: str) -> pd.DataFrame:
    filename = os.path.join(cfg.data_path, name+'.pickle')
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    return []

def wait_get(url: str, max_retries: int = 10):
        """
        发送带有重试机制的 GET 请求，直到成功或达到最大重试次数。
        此函数会根据服务器返回的 `Retry-After` 头信息进行等待，并在遇到 401 状态码时重新初始化配置。
     
        Args:
                url (str): 目标 URL。
                max_retries (int, optional): 最大重试次数，默认为 10。
     
        Returns:
                Response: 请求的响应对象。
        """
        retries = 0
        while retries < max_retries:
                while True:
                        simulation_progress = cfg.sess.get(url)
                        if simulation_progress.headers.get("Retry-After", 0) == 0:
                                break
                        time.sleep(float(simulation_progress.headers["Retry-After"]))
                if simulation_progress.status_code < 400:
                        break
                else:
                        time.sleep(2 ** retries)
                        retries += 1
        return simulation_progress
def _get_alpha_pnl(alpha_id: str) -> pd.DataFrame:
        """
        获取指定 alpha 的 PnL数据，并返回一个包含日期和 PnL 的 DataFrame。
        此函数通过调用 WorldQuant Brain API 获取指定 alpha 的 PnL 数据，
        并将其转换为 pandas DataFrame 格式，方便后续数据处理。
        Args:
                alpha_id (str): Alpha 的唯一标识符。
        Returns:
                pd.DataFrame: 包含日期和对应 PnL 数据的 DataFrame，列名为 'Date' 和 alpha_id。
        """
        save_path = cfg.data_path+f"pnls/{alpha_id}.pkl"
        if os.path.exists(save_path):
                return pd.read_pickle(save_path)
        print(f"开始下载:{alpha_id}")
        pnl = wait_get("https://api.worldquantbrain.com/alphas/" + alpha_id + "/recordsets/pnl").json()
        df = pd.DataFrame(pnl['records'], columns=[item['name'] for item in pnl['schema']['properties']])
        df = df.rename(columns={'date':'Date', 'pnl':alpha_id})
        df = df[['Date', alpha_id]]
        # 最后一个值为负时，反转pnls值
        if df.loc[df.index[-1]][alpha_id] < 0:
            df[alpha_id] = - df[alpha_id]
        df.to_pickle(save_path)
        return df
def get_alphas_pnl(alpha_ids):
    '''
    传入alpha-ids列表返回，list[df]
    id对应的pnl列
    '''
    fetch_pnl_func = lambda alpha_id: _get_alpha_pnl(alpha_id).set_index('Date')
    with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(fetch_pnl_func, [item['id'] for item in alpha_ids])
    alpha_pnls = pd.concat(list(results), axis=1)
    alpha_pnls.sort_index(inplace=True)
    return alpha_ids, alpha_pnls

def get_alpha_pnls(
        alphas: list[dict],
        alpha_pnls: Optional[pd.DataFrame] = None,
        alpha_ids: Optional[dict[str, list]] = None
) -> Tuple[dict[str, list], pd.DataFrame]:
        """
        获取 alpha 的 PnL 数据，并按区域分类 alpha 的 ID。
        Args:
                alphas (list[dict]): 包含 alpha 信息的列表，每个元素是一个字典，包含 alpha 的 ID 和设置等信息。
                alpha_pnls (Optional[pd.DataFrame], 可选): 已有的 alpha PnL 数据，默认为空的 DataFrame。
                alpha_ids (Optional[dict[str, list]], 可选): 按区域分类的 alpha ID 字典，默认为空字典。
        Returns:
                Tuple[dict[str, list], pd.DataFrame]:
                        - 按区域分类的 alpha ID 字典。
                        - 包含所有 alpha 的 PnL 数据的 DataFrame。
        """
        if alpha_ids is None:
                alpha_ids = defaultdict(list)
        if alpha_pnls is None:
                alpha_pnls = pd.DataFrame()

        new_alphas = [item for item in alphas if item['id'] not in alpha_pnls.columns]
        if not new_alphas:
                return alpha_ids, alpha_pnls

        for item_alpha in new_alphas:
                alpha_ids[item_alpha['settings']['region']].append(item_alpha['id'])
        fetch_pnl_func = lambda alpha_id: _get_alpha_pnl(alpha_id).set_index('Date')
        with ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(fetch_pnl_func, [item['id'] for item in new_alphas])
        alpha_pnls = pd.concat([alpha_pnls] + list(results), axis=1)
        alpha_pnls.sort_index(inplace=True)
        return alpha_ids, alpha_pnls
def get_os_alphas(limit: int = 100, get_first: bool = False) -> List[Dict]:
        """
        获取OS阶段的alpha列表。
        此函数通过调用WorldQuant Brain API获取用户的alpha列表，支持分页获取，并可以选择只获取第一个结果。
        Args:
                limit (int, optional): 每次请求获取的alpha数量限制。默认为100。
                get_first (bool, optional): 是否只获取第一次请求的alpha结果。如果为True，则只请求一次。默认为False。
        Returns:
                List[Dict]: 包含alpha信息的字典列表，每个字典表示一个alpha。
        """
        fetched_alphas = []
        offset = 0
        retries = 0
        total_alphas = 100
        while len(fetched_alphas) < total_alphas:
                print(f"Fetching alphas from offset {offset} to {offset + limit}")
                url = f"https://api.worldquantbrain.com/users/self/alphas?stage=OS&limit={limit}&offset={offset}&order=-dateSubmitted"
                res = wait_get(url).json()
                if offset == 0:
                        total_alphas = res['count']
                alphas = res["results"]
                fetched_alphas.extend(alphas)
                if len(alphas) < limit:
                        break
                offset += limit
                if get_first:
                        break
        return fetched_alphas[:total_alphas]


def get_list(df: pd.DataFrame):
    finally_alphas = []
    def get_llll(df:pd.DataFrame, arr=[], father:list = []):
            if len(arr)<=1:
                finally_alphas.append(father+arr)
                return None
            # 选择第一个
            get_llll(df,[i for i in arr[1:] if df.loc[arr[0]][i]<0.7], father+arr[:1])
            # 不选择第一个
            get_llll(df, arr[1:], father)
    alpha_ids = df.columns.to_list()
    get_llll(df, alpha_ids, [])
    return finally_alphas
def calc_all_corr(alpha_ids, sim_max: int = 0.7)->pd.DataFrame:
        # 加载已os的pnls数据
        os_alpha_ids, os_alpha_rets = load_data()
        # 下载传入alpha_ids数据
        print("开始获取aplha字段信息")
        alpha_results = []
        alpha_res_func = lambda alpha_id: wait_get(f"https://api.worldquantbrain.com/alphas/{alpha_id}").json()
        with ThreadPoolExecutor(max_workers=10) as executor:
            alpha_results = executor.map(alpha_res_func, alpha_ids)
        # for alpha_id in alpha_ids:
        #     print(alpha_id)
        #     alpha_result = wait_get(f"https://api.worldquantbrain.com/alphas/{alpha_id}").json()
        #     alpha_results.append(alpha_result)
        # print("开始读取os is数据")
        alpha_results = list(alpha_results)
        _, is_pnls = get_alpha_pnls(alpha_results)
        # 算出增量，后一行减前一行的值
        is_rets = is_pnls - is_pnls.ffill().shift(1)
        # 保留四年时间的增量pnls
        is_rets = is_rets[pd.to_datetime(is_rets.index)>pd.to_datetime(is_rets.index).max() - pd.DateOffset(years=4)]
        arr = []
        # 求最大相关性，挑选出满足的alpha id
        similar_l = {}
        col = is_rets.columns
        print(col)
        print(is_rets)
        for alpha_id in alpha_ids:
            if alpha_id not in col:
                continue
            # print(alpha_id)
                # print(os_alpha_rets[os_alpha_ids[alpha_results[0]['settings']['region']]].corrwith(is_rets[alpha_id]).sort_values(ascending=False).round(4).head(2))
            self_corr = os_alpha_rets[os_alpha_ids[alpha_results[0]['settings']['region']]]\
                .corrwith(is_rets[alpha_id]).max()
            if self_corr < sim_max:
                    arr.append(alpha_id)
                    similar_l[alpha_id] = self_corr
            print(alpha_id, self_corr)
        # 计算满足条件的is数据的相关性
        if not similar_l:
                return None
        # 按照自相关系数排序
        # # similar_l = sorted(similar_l.items(), key=lambda x: x[1])
        # arr = [i for i in similar_l]
        # arr = 
        
        df = is_rets[arr].corr()
        df["selfcheck"] = list(similar_l.values())
        # 将对角线设置为与os的相关性
        # for i in similar_l:
        #         df.at[i, i] = similar_l[i]
        print(df)
        return df
        
def download_data(flag_increment=True):
        """
        下载数据并保存到指定路径。
        此函数会检查数据是否已经存在，如果不存在，则从 API 下载数据并保存到指定路径。
        Args:
                flag_increment (bool): 是否使用增量下载，默认为 True。
        """
        if flag_increment:
            os_alpha_ids = load_obj( 'os_alpha_ids')
            os_alpha_pnls = load_obj( 'os_alpha_pnls')
            ppac_alpha_ids = load_obj('ppac_alpha_ids')
            exist_alpha = [alpha for ids in os_alpha_ids.values() for alpha in ids]
        else:
            os_alpha_ids = None
            os_alpha_pnls = None
            exist_alpha = []
            ppac_alpha_ids = []
        if os_alpha_ids is None:
            alphas = get_os_alphas(limit=100, get_first=False)
        else:
            alphas = get_os_alphas(limit=10, get_first=True)

        alphas = [item for item in alphas if item['id'] not in exist_alpha]
        ppac_alpha_ids += [item['id'] for item in alphas for item_match in item['classifications'] if item_match['name'] == 'Power Pool Alpha']

        os_alpha_ids, os_alpha_pnls = get_alpha_pnls(alphas, alpha_pnls=os_alpha_pnls, alpha_ids=os_alpha_ids)
        save_obj(os_alpha_ids, 'os_alpha_ids')
        save_obj(os_alpha_pnls,'os_alpha_pnls')
        save_obj(ppac_alpha_ids, 'ppac_alpha_ids')
        print(f'新下载的alpha数量: {len(alphas)}, 目前总共alpha数量: {os_alpha_pnls.shape[1]}')
        return os_alpha_ids, os_alpha_pnls, ppac_alpha_ids
def load_data(tag=None):
        """
        加载数据。
        此函数会检查数据是否已经存在，如果不存在，则从 API 下载数据并保存到指定路径。
        Args:
                tag (str): 数据标记，默认为 None。
        """
        # os_alpha_ids = load_obj('os_alpha_ids')
        # os_alpha_pnls = load_obj('os_alpha_pnls')
        # ppac_alpha_ids = load_obj('ppac_alpha_ids')
        os_alpha_ids, os_alpha_pnls, ppac_alpha_ids =download_data()
        if tag=='PPAC':
                for item in os_alpha_ids:
                        os_alpha_ids[item] = [alpha for alpha in os_alpha_ids[item] if alpha in ppac_alpha_ids]
        elif tag=='SelfCorr':
                for item in os_alpha_ids:
                        os_alpha_ids[item] = [alpha for alpha in os_alpha_ids[item] if alpha not in ppac_alpha_ids]
        else:
            os_alpha_ids = os_alpha_ids
        exist_alpha = [alpha for ids in os_alpha_ids.values() for alpha in ids]
        os_alpha_pnls = os_alpha_pnls[exist_alpha]
        os_alpha_rets = os_alpha_pnls - os_alpha_pnls.ffill().shift(1)
        os_alpha_rets = os_alpha_rets[pd.to_datetime(os_alpha_rets.index)>pd.to_datetime(os_alpha_rets.index).max() - pd.DateOffset(years=4)]
        return os_alpha_ids, os_alpha_rets

class cfg:
        data_path =  "/storage/emulated/0/qua/check/" \
        if sys.platform == "linux"\
        else "C:\\Project\\qua\\check\\"
        with open(data_path + '../brain.txt') as f:
               username, password = json.load(f)
        sess = None
               

# download_data(flag_increment=True)
# RwLlaw0
alphas = ["XAwb8vX","ZvwAgbY","pegxKwX","1Avq0Ym","vo7N8KG","3vww68N","YoLozz6","Ojl8Jgv","GNZRzjO","lYPmrKx","a8wWzEW", "Ro5ON1o","oXPbMrm","6QGLaXJ","Oj6jomv","PbPAamM","jJVOKjQ"]
data_name = "model110-GLB-DIV3000-1-div-group_second.csv.csv"
path = f"C:\\Project\\qua\\{data_name.split('-')[0]}\\"
alphas = pd.read_csv(path+data_name)
# # # alphas = alphas[(alphas["fitness"]<11) & (alphas["fitness"]>=5)]
# alphas = alphas[alphas["fitness"] >= 1]
alphas = alphas[alphas["result"] == "PASS"]
# alphas = alphas[alphas["weight"] >= -0.05]
alphas.sort_values("fitness", ascending=False, inplace=True)
print(alphas.shape)
alphas = alphas["id"].values.tolist()[:100]
# exit()
cfg.sess = sign_in(cfg.username, cfg.password) 
# 
# alphas = ["3vK9gZz"]
df = calc_all_corr(alphas, sim_max=0.7)
now = datetime.datetime.now()
formatted_date = now.strftime("%Y%m%d-%H%M%S")
df.to_csv(cfg.data_path+f"{formatted_date}-check.csv")
# df.drop("selfcheck", axis=1, inplace=True)
