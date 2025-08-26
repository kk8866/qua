# https://api.worldquantbrain.com/alphas/7R56JlQ/check
import requests
import logging
import time, sys
import pandas as pd
import json
class cfg:
        data_path =  "/storage/emulated/0/qua/check/" \
        if sys.platform == "linux"\
        else "C:\\Project\\qua\\check\\"
        with open(data_path + '../brain.txt') as f:
               username, password = json.load(f)
        sess = None
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
def get_check_submission(s:requests.Session, alpha_id):
    while True:
        result = s.get("https://api.worldquantbrain.com/alphas/" + alpha_id + "/check")
        if "retry-after" in result.headers:
            time.sleep(float(result.headers["Retry-After"]))
        else:
            break
    try:
        if result.json().get("is", 0) == 0:
            print("logged out")
            return "sleep"
        checks_df = pd.DataFrame(
                result.json()["is"]["checks"]
        )
        pc = checks_df[checks_df.name == "PROD_CORRELATION"]["value"].values[0]
        print(pc)
        if not any(checks_df["result"] == "FAIL"):
            return pc
        else:
            return "fail"
    except:
        print("catch: %s"%(alpha_id))
        return "error"
cfg.sess = sign_in(cfg.username, cfg.password) 
df = pd.read_csv(cfg.data_path+"20250827-000136-check.csv", index_col=0)
df = df[df["selfcheck"]<0.5]
for i in df.index:
    proc = get_check_submission(cfg.sess, i)
    print(i, proc)