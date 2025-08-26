import pymysql
 
# 打开数据库连接
db = pymysql.connect(host='localhost',
                     user='root',
                     password='root',
                     database='TESTDB')
 
# 使用cursor()方法获取操作游标 
cursor = db.cursor()
 
'''alphaid	code	ctype	result	region	delay	sub	fitness	sharpe	turnover	margin	drawdown	neutralization		weight	longCount	shortCount settings'''
{'instrumentType': 'EQUITY', 'region': 'EUR', 'universe': 'TOP2500', 
 'delay': 0, 'decay': 8, 'neutralization': 'STATISTICAL', 
 'truncation': 0.08, 
 'pasteurization': 'ON', 'unitHandling': 'VERIFY', 
 'nanHandling': 'ON', 'maxTrade': 'OFF', 'language': 'FASTEXPR',
 'visualization': False}

"ALTER TABLE alphas ADD stuId INT(4) FIRST;"
# SQL 插入语句
sql = """INSERT INTO EMPLOYEE(FIRST_NAME,
         LAST_NAME, AGE, SEX, INCOME)
         VALUES ('Mac', 'Mohan', 20, 'M', 2000)"""
try:
   # 执行sql语句
   cursor.execute(sql)
   # 提交到数据库执行
   db.commit()
except:
   # 如果发生错误则回滚
   db.rollback()
 
# 关闭数据库连接
db.close()