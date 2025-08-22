import time
import requests


def submit_alpha(s: requests.Session, alpha_id: str):
  submit_url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/submit"

  # 提交
  count = 0
  while count<5:
    res = s.post(submit_url)
    if res.status_code != 201:
      print(count,"POST Status is:",res.status_code)
      break
    count+=1
  # 检查结果
  count = 0
  while count <5:
    res = s.get(submit_url)
    if res.status_code == 200:
      retry = res.headers.get('Retry-After', 0)
      time.sleep(retry)
      if retry == 0:
        print(f"submit alpha: {alpha_id} sucess")
        break
    count+=1
      
if __name__ == '__main__':
  username = "用户名"
  password = "密码"
  s = requests.Session()
  s.auth = (username, password)
  response = s.post('https://api.worldquantbrain.com/authentication')
  
  submittable_alphas = ['1213', '2132143']
  for alpha_id in submittable_alphas:
    submit_alpha(s, alpha_id)