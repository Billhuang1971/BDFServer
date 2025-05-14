import queue
import threading

import mysql.connector


class MySqlService:

    def __init__(self, hUrl, hPort, tUser, tPwd,dbname):
        self.hUrl =hUrl
        self.hPort =hPort
        self.tUser =tUser
        self.tPwd =tPwd
        self.dbname =dbname
        self.cnxPools=queue.Queue()
        self.conn_msg = threading.Semaphore(value=8)
        for i in range(8):
            self.cnxPools.put(mysql.connector.connect(user=self.tUser, password=self.tPwd,  host=self.hUrl,
               port=self.hPort, database=self.dbname, use_pure=False, auth_plugin='mysql_native_password'))


    def getConn(self):
        self.conn_msg.acquire()
        conn=self.cnxPools.get()
        if conn.is_connected()  is False :
            conn= mysql.connector.connect(user=self.tUser, password=self.tPwd,  host=self.hUrl,
                port=self.hPort, database=self.dbname, use_pure=False, auth_plugin='mysql_native_password')
            print(f"getConn：=={self.hUrl}:{self.hPort}/{self.dbname}====")
        return conn

    def putConn(self, conn):
        self.cnxPools.put(conn)
        self.conn_msg.release()


    def myConnect(self):
        try:
            del self.cnxPools
            self.cnxPools = queue.Queue()
            for i in range(8):
                self.cnxPools.put(mysql.connector.connect(user=self.tUser, password=self.tPwd, host=self.hUrl,
                                                          port=self.hPort, database=self.dbname, use_pure=False,
                                                          auth_plugin='mysql_native_password'))
            return True
        except Exception as e:
            print(f"myConnect：{self.hUrl}:{self.hPort}/{self.dbname}=Exception==={e}")
            return None

    def myClose(self):
        try:
            # if self.cnxPools.empty():
            #     return True
            # for i in range(self.cnxPools.qsize()):
            #    conn=self.cnxPools.get()
            #    conn.close()
            return True
        except Exception as e:
            return None

    def myExecuteSqlwithid(self, parmSql):
        try:
            conn=self.getConn()
            cursor = conn.cursor()
            cursor.execute(parmSql)
            id1 = cursor.lastrowid
            cursor.close()
            conn.commit()
            self.putConn(conn)
            return id1
        except Exception as e:
            self.putConn(conn)
            return e

    def myQuery(self, sql):
        try:
            conn = self.getConn()
            cursor = conn.cursor()
            cursor.execute(sql)
            dataSet = cursor.fetchall()
            cursor.close()
            conn.commit()
            self.putConn(conn)
            return dataSet
        except Exception as e:
            print(f"myQuery:{e}")
            self.putConn(conn)
            return e

    def myQueryExt(self, sql):
        try:
            conn = self.getConn()
            cursor = conn.cursor()
            cursor.execute(sql)
            dataSet = cursor.fetchall()
            cursor.close()
            conn.commit()
            self.putConn(conn)
            return '1',dataSet
        except Exception as e:
            self.putConn(conn)
            return '0',f'{e}'
    def myExecuteSql(self, parmSql):
        try:
            conn=self.getConn()
            cursor = conn.cursor()
            cursor.execute(parmSql)
            cursor.close()
            conn.commit()
            self.putConn(conn)
            return ""
        except Exception as e:
            print(f"myExecuteSql:{e}")
            self.putConn(conn)
            return e

    # TODO:考虑用这个替换myExecuteSql
    def myExecuteSqlNew(self, parmSql, params=None):
        conn = None
        try:
            conn = self.getConn()
            cursor = conn.cursor()

            if params:
                cursor.execute(parmSql, params)
            else:
                cursor.execute(parmSql)

            cursor.close()
            conn.commit()
            self.putConn(conn)
            return ""
        except Exception as e:
            print(f"myExecuteSql: {e}")
            if conn:
                self.putConn(conn)
            return e

    def myExecuteSqlWithParm(self, parmSql, parmValue):
        try:
            conn = self.getConn()
            cursor = conn.cursor()
            cursor.execute(parmSql, parmValue)
            results = cursor.fetchall()
            cursor.close()
            conn.commit()
            self.putConn(conn)
            return results
        except Exception as e:
            print(f"myExecuteSql:{e}")
            self.putConn(conn)
            return e

    # 专用更新方法（返回受影响行数或其他标识）
    def execute_update(self, parmSql, parmValue):
        try:
            conn = self.getConn()
            cursor = conn.cursor()
            cursor.execute(parmSql, parmValue)
            conn.commit()
            self.putConn(conn)
            return cursor.rowcount  # 返回受影响的行数
        except Exception as e:
            print(f"execute_update error: {e}")
            self.putConn(conn)
            return e
    def myExecuteTranSql(self, parmSql):
        conn = self.getConn()
        try:
            cursor = conn.cursor()
            for sql in parmSql:
                cursor.execute(sql)
            cursor.close()
            conn.commit()
            self.putConn(conn)
            return '1',""
        except Exception as e:
            conn.rollback()
            print(f"myExecuteTranSql:{e}")
            self.putConn(conn)
            return '0',f'{e}'

        # 批量插入
    def myExecuteMany(self, sql, data):
        conn = self.getConn()
        try:
            cursor = conn.cursor()
            cursor.executemany(sql, data)
            cursor.close()
            conn.commit()
        except Exception as e:
            print("myExecuteMany 错误:", e)
            conn.rollback()
            raise
        finally:
            self.putConn(conn)
