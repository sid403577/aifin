import json

import pymysql

dbinfo = {
    "host": "62.234.20.47",
    "user": "root",
    "password": "123456",
    "port": 3306}
class DbConnect():
    def __init__(self, db_cof, database=""):
        self.db_cof = db_cof
        # 打开数据库连接
        self.db = pymysql.connect(database=database,
                                  cursorclass=pymysql.cursors.DictCursor,
                                  **db_cof)

        # 使用cursor()方法获取操作游标
        self.cursor = self.db.cursor()

    def select(self, sql):
        # SQL 查询语句
        # sql = "SELECT * FROM EMPLOYEE \
        #        WHERE INCOME > %s" % (1000)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        return results

    def execute(self, sql):
        # SQL 删除、提交、修改语句
        # sql = "DELETE FROM EMPLOYEE WHERE AGE > %s" % (20)
        try:
           # 执行SQL语句
           self.cursor.execute(sql)
           self.cursor.executemany()
           # 提交修改
           self.db.commit()
        except:
           # 发生错误时回滚
           self.db.rollback()

    def close(self):
        # 关闭连接
        self.db.close()

def allStockInfo()->list:
    """
    获取所有的表数据
    """
    sql = "select securities_code,securities_name,stock_code,first_industry,second_industry,third_industry,four_industry,industry_cls_code,industry_cls_name from stock_info";
    db = DbConnect(dbinfo, database="aigc")
    result = db.select(sql)
    db.close()
    # 以json格式输出到控制台
    data=None
    if result and len(result)>0:
        data = json.dumps(result, ensure_ascii=False)
    return data

def batchStockInfo(size:int,current:int)->list:
    """
    获取所有的表数据
    """

    startRow = (current - 1) * size
    sql = f"select securities_code,securities_name,stock_code,first_industry,second_industry,third_industry,four_industry,industry_cls_code,industry_cls_name from stock_info limit {startRow},{size}"
    db = DbConnect(dbinfo, database="aigc")
    result = db.select(sql)
    db.close()
    # 以json格式输出到控制台
    data = None
    if result and len(result) > 0:
        data = json.dumps(result, ensure_ascii=False)
    return data

if __name__ == '__main__':
    print(batchStockInfo(10,1))