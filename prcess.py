from  pydantic import BaseModel

# class settings(BaseModel):
#   instrumentType: str
#   region: str
#   universe: str
#   delay: 1
#   decay: 0
#   neutralization: str
#   truncation: 0.08
#   pasteurization: str
#   unitHandling: str
#   nanHandling: str
#   maxTrade: str
#   language: str
#   visualization: True
#   startDate: str = "2013-01-20"
#   endDate: str = "2023-01-20"
class other_data(BaseModel):
  pnl: int = 0
  bookSize: int = 0
  longCount: int = 0
  shortCount: int = 0
  turnover: float = 0
  returns: float = 0
  drawdown: float = 0
  margin: float = 0
  fitness: float = 0
  sharpe: float = 0
class _is(BaseModel):
  pnl: 3640630
  longCount: 2588
  shortCount: 910
  turnover: 0.1461
  returns: 0.3522
  drawdown: 0.5918
  margin: 0.004821
  sharpe: 1.03
  fitness: int = 1.0
  startDate: str = "2013-01-20"
  # riskNeutralized: other_data

# class checks:
#   name: str
#   result: str
#   limit: float
#   value: float
  
# class result:
#   id: str
#   type: str
#   # author: str
#   settings:settings
#   regular: str = ""
#   dateCreated: str
#   # name: null
#   # favorite: false
#   # hidden: false
#   # color: null
#   # category: null
#   # tags: []
#   _is: dict = {
#   "is": other_data,
#   "riskNeutralized": other_data}
#   checks: dict
# other_data()
print(other_data().model_dump())

other_data(pnl=0)
result = {}
[i for i in result["is"] if i in _is.model_dump()]