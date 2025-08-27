import pymysql
 
# 打开数据库连接
db = pymysql.connect(host='127.0.0.1',
                     user='root',
                     password='root',
                     database='alphas')
 
# 使用cursor()方法获取操作游标 
cursor = db.cursor()
 
def create_table(tablename, fields):
   print("检查创建", tablename)
   sql = f'''CREATE TABLE IF NOT EXISTS {tablename}
      (
      {fields}
      );'''
   return exe_sql(sql)
def exe_sql(sql):
   try:
      # 执行sql语句
      cursor.execute(sql)
      # 提交到数据库执行
      db.commit()
      return True
   except:
      # 如果发生错误则回滚
      db.rollback()
      return False
 
#  插入
def insert_db(name, data: dict):
   keys = ",".join(list(data.keys()))
   values = str(list(data.values()))[1:-1]
   sql = f'''INSERT INTO {name} ({keys})
   SELECT  {values} FROM DUAL 
   WHERE NOT EXISTS (
   SELECT id FROM {name} WHERE id = '{data["id"]}'
   );'''
   return exe_sql(sql)
# 关闭数据库连接
def close():
   db.close()
