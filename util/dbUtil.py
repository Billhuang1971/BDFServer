import re
from random import sample

import numpy as np

from util.mysqlService import MySqlService


class dbUtil(MySqlService):
    def __init__(self):
        mysqlInfo = self.GetMysqlInfo()
        super().__init__(mysqlInfo['dbUrl'], mysqlInfo['dbPort'], mysqlInfo['dbUser'], mysqlInfo['dbPwd'],
                         mysqlInfo['dbName'])

    def GetMysqlInfo(self):
        f = open('service/server.txt')
        d = f.readline()
        f.close()
        sysd = eval(d)
        return sysd

    def getUserInfo(self, where_name='', where_value='', where_like=''):
        if where_name == '':
            sql = "select * from user_info "
        elif where_like != '':
            sql = f"select * from user_info where {where_name} like '%{where_value}%'"
        else:
            sql = f"select * from user_info where {where_name}='{where_value}'"
        user_info = self.myQuery(sql)
        return user_info

    def getUserInfoLen(self, where_name='', where_like=''):
        if where_name == '':
            sql = "select count(*) from user_info where uid != 1"
        else:
            sql = f"select count(*) from user_info where {where_name} Like '%{where_like}%' and uid != 1"
        len = self.myQuery(sql)
        return len

    def getUserInfoByPage(self, offset='', psize=''):
        sql = f"select * from user_info limit {offset}, {psize}"
        user_info = self.myQuery(sql)
        return user_info

    def getSearchUserInfoByPage(self, where_name, where_value, offset='', psize=''):
        sql = f"select * from user_info where {where_name} like '%{where_value}%' AND account != 'admin' order by uid " \
              f" limit {offset}, {psize} "
        user_info = self.myQuery(sql)
        return user_info

    def updateUserInfo(self, where_name, where_value, userInfo=None, set_name='', set_value=''):
        try:
            if userInfo is None:
                sql = "update user_info set {} = '{}' where {}='{}'".format(set_name, set_value, where_name,
                                                                            where_value)
                self.myExecuteSql(sql)
                return True
            else:
                sql = "update user_info set name = '{}', phone = '{}', email = '{}', labeler = '{}', student = '{}', teacher = '{}', doctor = '{}',researcher = '{}' where {}='{}'".format(
                    userInfo[1], userInfo[2], userInfo[3], userInfo[4], userInfo[5], userInfo[6], userInfo[7],
                    userInfo[8],
                    where_name, where_value)
                tag = self.myExecuteSql(sql)
                if tag == '':
                    return '1', str(tag)
                else:
                    return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def delUserInfo(self, where_name, where_value):
        try:
            sql = "delete from user_info where {} = '{}'".format(where_name, where_value)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(re)
            return '0', str(e)

    def addUserInfo(self, user_info):
        try:
            sql = f"insert into user_info(account,pwd,name,phone,email,administrator,labeler,student,teacher,doctor,researcher) values " \
                  "('{}','{}','{}','{}','{}',{},{},{},{},{},{})".format(
                user_info[0], user_info[1], user_info[2], user_info[3], user_info[4], user_info[5], user_info[6],
                user_info[7], user_info[8], user_info[9], user_info[10])
            tag = self.myExecuteSql(sql)
            if tag == "":
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            return '0', str(e)

    # 密码修改模块
    # 更新用户信息
    def update_userInfo(self, user_msg='', flag='1'):
        try:
            if flag == "1":
                uid = user_msg[0]
                pwd = user_msg[1]
                sql = f"update user_info set pwd = '{pwd}' where uid='{uid}'"
            self.myExecuteSql(sql)
        except Exception as e:
            print("update_userInfo", e)
            return False
        return True

    # 标注类型
    # 获取标注类型信息
    def get_typeInfo(self, where_name='', where_value=''):
        try:
            if where_name == '':
                sql = "select * from type_info"
            else:
                sql = f"select * from type_info where {where_name} like '%{where_value}%'"
            type_info = self.myQuery(sql)
        except Exception as e:
            print("get_typeInfo", e)
            return None
        return type_info

    # 添加标注类型信息
    def add_typeInfo(self, type_info):
        try:
            type_name = type_info[0]
            description = type_info[1]
            category = type_info[2]
            sql = f"insert into type_info(type_name, description, category) values ('{type_name}','{description}', '{category}')"
            flag = self.myExecuteSql(sql)
            if flag == "":
                return True
            else:
                return False
        except Exception as e:
            print('addtypeInfo', e)

    # 删除标注类型信息
    def del_typeInfo(self, where_name, where_value):
        try:
            sql = f"delete from type_info where {where_name} = '{where_value}'"
            self.myExecuteSql(sql)
        except Exception as e:
            print('delTypeInfo', e)
            return False
        return True

    # 修改标注类型信息
    def update_typeInfo(self, set_value, where_name, where_value):
        try:
            sql = f"update type_info set type_name = '{set_value[0]}',description = '{set_value[1]}',category = '{set_value[2]}'where {where_name}='{where_value}' "
            self.myExecuteSql(sql)
        except Exception as e:
            print('updateTypeInfo', e)
            return False
        return True


    # 脑电导入模块
    # 获取病人诊断信息
    def get_patientCheckInfo(self, where_value=''):

        if where_value != '':
            sql = f"SELECT check_id, patient_id, c.pUid, c.cUid, p.name as pname, check_number, c.measure_date,c.description, u.name as pdoctorname, m.name as cdoctorname, state FROM check_info as c NATURAL JOIN patient_info as p LEFT OUTER JOIN user_info as u on (c.pUid = u.uid) LEFT OUTER JOIN user_info as m on (c.cUid = m.uid) WHERE c.state in ('notUploaded', 'uploading') and c.cUid={where_value} order by  patient_id asc"
        # sql = "select patient_id, check_number, measure_date, pUid, cUid from check_info"
        try:
            patientCheck_info = self.myQuery(sql)
        except Exception as e:
            print("get_patientCheckInfo", e)
            return '0', None
        return '1', patientCheck_info

    # 获取病人id和名字
    def get_patientIdName(self, where_name='', where_value='', flag='', start=None, offset=None):

        # 没有条件查询所有的病人信息
        if where_name == '' and flag == '1':
            sql = f"select patient_id, `name`, DATE_FORMAT(birth, '%Y-%m-%d'), sex, card from patient_info limit 0,{offset}"
            sql1 = f"SELECT count(*) from patient_info "
        # 没有条件分页信息
        elif where_name == '' and flag == '2':
            sql = f"select patient_id, `name`, DATE_FORMAT(birth, '%Y-%m-%d'), sex, card from patient_info limit {start},{offset}"
        # 获取搜索满足条件的病人信息
        elif where_name != '' and flag == '1':
            # 当搜索框有信息的时候
            sql = f"select patient_id, `name`, DATE_FORMAT(birth, '%Y-%m-%d'), sex, card from patient_info WHERE {where_name} LIKE '%{where_value}%' limit 0,{offset}"
            sql1 = f"SELECT count(*) from patient_info WHERE {where_name} LIKE '%{where_value}%'"

        # 查询有条件的病人信息翻页
        elif where_name != '' and flag == '2':
            sql = f"select patient_id, `name`, DATE_FORMAT(birth, '%Y-%m-%d'), sex, card from patient_info WHERE {where_name} LIKE '%{where_value}%' limit {start},{offset}"
        else:
            pass

        if flag == '1':
            try:
                patient_info = self.myQuery(sql)
                totalNUm = self.myQuery(sql1)
            except Exception as e:
                print('get_patientIdName', e)
                return '0', None, None
            return '1', patient_info, totalNUm[0][0]
        else:
            try:
                patient_info = self.myQuery(sql)
            except Exception as e:
                print('get_patientIdName', e)
                return '0', None
            return '1', patient_info

    # 获取医生id和名字
    def get_doctorIdName(self, where_name='', where_value='', flag='', start=None, offset=None):
        # 没有条件查询所有的病人信息
        if where_name == '' and flag == '1':
            sql = f"select uid, name, phone, email FROM user_info where doctor = 1 limit 0,{offset}"
            sql1 = f"SELECT count(*) from user_info where doctor = 1 "
        # 没有条件分页信息
        elif where_name == '' and flag == '2':
            sql = f"select uid, name, phone, email FROM user_info where doctor = 1 limit {start},{offset}"
        # 获取搜索满足条件的病人信息
        elif where_name != '' and flag == '1':
            # 当搜索框有信息的时候
            sql = f"select uid, name, phone, email FROM user_info WHERE {where_name} LIKE '%{where_value}%' and doctor=1 limit 0,{offset}"
            sql1 = f"SELECT count(*) from user_info WHERE {where_name} LIKE '%{where_value}%' and doctor=1"

        # 查询有条件的病人信息翻页
        elif where_name != '' and flag == '2':
            sql = f"select uid, name, phone, email FROM user_info WHERE {where_name} LIKE '%{where_value}%' and doctor=1 limit {start},{offset}"
        else:
            pass

        if flag == '1':
            try:
                doctor_info = self.myQuery(sql)
                totalNUm = self.myQuery(sql1)
            except Exception as e:
                print('get_doctorIdName', e)
                return '0', None, None
            return '1', doctor_info, totalNUm[0][0]
        else:
            try:
                doctor_info = self.myQuery(sql)
            except Exception as e:
                print('get_doctorIdName', e)
                return '0', None
            return '1', doctor_info

     # 获取研究员id和名字
    def get_researcherIdName(self, where_name='', where_value='', flag='', start=None, offset=None):
        # 没有条件查询所有的病人信息
        if where_name == '' and flag == '1':
            sql = f"select uid, name, phone, email FROM user_info where researcher = 1 limit 0,{offset}"
            sql1 = f"SELECT count(*) from user_info where researcher = 1 "
        # 没有条件分页信息
        elif where_name == '' and flag == '2':
            sql = f"select uid, name, phone, email FROM user_info where researcher = 1 limit {start},{offset}"
        # 获取搜索满足条件的病人信息
        elif where_name != '' and flag == '1':
            # 当搜索框有信息的时候
            sql = f"select uid, name, phone, email FROM user_info WHERE {where_name} LIKE '%{where_value}%' and researcher=1 limit 0,{offset}"
            sql1 = f"SELECT count(*) from user_info WHERE {where_name} LIKE '%{where_value}%' and researcher=1"

        # 查询有条件的病人信息翻页
        elif where_name != '' and flag == '2':
            sql = f"select uid, name, phone, email FROM user_info WHERE {where_name} LIKE '%{where_value}%' and researcher limit {start},{offset}"
        else:
            pass

        if flag == '1':
            try:
                researcher_info = self.myQuery(sql)
                totalNUm = self.myQuery(sql1)
            except Exception as e:
                print('get_researcherIdName', e)
                return '0', None, None
            return '1', researcher_info, totalNUm[0][0]
        else:
            try:
                researcher_info = self.myQuery(sql)
            except Exception as e:
                print('get_researcherIdName', e)
                return '0', None
            return '1', researcher_info

    # 获取用户id和名字
    def get_userIdName(self, where_name, where_value, flag=''):
        if flag == '1':
            sql = f"select uid,CONCAT_WS('-',uid,name) from user_info where {where_name}='{where_value}'"
        else:
            sql = f"select uid, CONCAT_WS('-',uid,name) from user_info where {where_name}='{where_value}'"
        try:
            user_IdName = self.myQuery(sql)
        except Exception as e:
            print("get_userIdName", e)
            return '0', None
        return '1', user_IdName

    # 获取配置信息
    def query_configData(self, where_name='', where_value=''):

        if where_name == '':
            sql = "select * from config"
        else:
            sql = f"select * from config where `{where_name}`='{where_value}'"
        print(f'queryConfigData SQL: {sql}')
        try:
            config = self.myQuery(sql)
        except Exception as e:
            print('del_detailInfo', e)
            return '0', None
        return '1', config

    # 删除病人诊断信息
    def del_patientCheckInfo(self, where_name, where_value):
        try:
            sql = f"delete from check_info where {where_name} = '{where_value}'"
            self.myExecuteSql(sql)
        except Exception as e:
            print('del_patientCheckInfo', e)
            return False
        return True

    # 添加病人检查信息
    def add_checkInfo(self, check_info):
        try:
            check_num = check_info[0]
            patient_id = check_info[1]
            description = check_info[2]
            pUid = check_info[3]
            measure_date = check_info[4]
            cUid = check_info[5]
            state = 'notUploaded'

            # 先检查检查单号是否存在
            check_sql = f"SELECT COUNT(*) FROM `check_info` WHERE check_number = '{check_num}'"
            check_flag = self.myQuery(check_sql)

            if check_flag[0][0] > 0:
                return ['0', f"添加失败，检查单号重复！！"]

            # cUid可以传'NULL'，在这里写语句时不加‘’，传入就是NULL
            sql = f"INSERT INTO `check_info`(check_number, patient_id, description, pUid, measure_date, state, cUid) VALUES ('{check_num}', '{patient_id}', '{description}', '{pUid}', '{measure_date}', '{state}', {cUid})"
            flag = self.myExecuteSql(sql)

            if flag == "":
                return ['1', "添加病人检查信息成功！！"]
            else:
                return ['0', "添加病人检查信息失败！！"]
        except Exception as e:
            print('add_checkInfo', e)
            return ['0', f"服务端异常！！{e}"]

    # 更新脑电检查信息
    def update_checkInfo(self, check_info, flag=''):
        try:
            # 更新大部分信息
            if flag == '1':
                check_id = check_info[0]
                state = check_info[1]
                try:
                    sql = f"update check_info set state = '{state}' where check_id = '{check_id}' "
                    self.myExecuteSql(sql)
                except Exception as e:
                    print('updatecheckInfo', e)
                    return False
            # 只是更新状态
            # 这个位置原先会 uid = check_info[2] 导致越界，没有更新cUid的理由，在这里删除
            else:
                check_id = check_info[0]
                # state = check_info[1]
                state = check_info[1]
                # uid = check_info[2]
                try:
                    # sql = f"update check_info set state = '{state}', cUid = '{uid}' where check_id = '{check_id}' "
                    sql = f"update check_info set state = '{state}' where check_id = '{check_id}' "
                    self.myExecuteSql(sql)
                except Exception as e:
                    print('updatecheckInfo', e)
                    return False
            return True
        except Exception as e:
            print("update_checkInfo", e)

    # 获取右下角展示的脑电文件数据信息
    def get_fileInfo_detail(self, where_value=''):
        if where_value != '':
            sql = f"select file_info.check_id, file_info.file_id, file_info.state from file_info  LEFT OUTER JOIN check_info on file_info.check_id = check_info.check_id WHERE check_info.cUid={where_value} and check_info.state in ('notUploaded', 'uploading') "
        try:
            file_info = self.myQuery(sql)
        except Exception as e:
            print('get_fileInfo_detail', e)
            return '0', None
        return '1', file_info

    # 04/17 相同的sql查询语句，第二次查询file_info没查到：'select * from file_info where check_id = 118 and file_id = 2'
    # 04/18 sqlservice里一个事务没commit
    # 获取脑电上传时候脑电数据文件相关信息
    def get_fileInfo(self, where_name='', where_value='', wherename='', wherevalue=''):
        if where_name == '':
            sql = "select check_id, file_id, state from file_info "
        elif where_name and wherename:
            sql = f"select * from file_info where {where_name} = {where_value} and {wherename} = {wherevalue}"
        else:
            sql = f"select * from file_info where {where_name} like '%{where_value}%'"
        try:
            file_info = self.myQuery(sql)
        except Exception as e:
            print('get_fileInfo', e)
            return '0', None
        return '1', file_info

    # 根据check_number获取脑电数据文件相关信息
    def get_fileInfoByCheckNumber(self, check_number='', where_name='', where_value='', wherename='', wherevalue=''):
        """
        查询 file_info 表的信息。如果提供 check_number，会先通过 check_info 表查找对应的 check_id。

        :param check_number: 检查编号，用于查找对应的 check_id。
        :param where_name: 第一个条件的字段名。
        :param where_value: 第一个条件的值。
        :param wherename: 第二个条件的字段名。
        :param wherevalue: 第二个条件的值。
        :return: ('状态', file_info, check_id) 状态为 '1' 表示成功，'0' 表示失败。
        """
        try:
            # 如果提供了 check_number，先查询 check_id
            if check_number:
                sql_check_info = f"SELECT check_id FROM check_info WHERE check_number = '{check_number}'"
                check_info = self.myQuery(sql_check_info)
                if not check_info:
                    return '0', None, None
                check_id = check_info[0][0]  # 提取 check_id
            else:
                check_id = None

            # 构造查询 file_info 的 SQL
            if check_id:
                sql = f"SELECT * FROM file_info WHERE check_id = '{check_id}'"
            elif where_name == '':
                sql = "SELECT check_id, file_id, state FROM file_info"
            elif where_name and wherename:
                sql = f"SELECT * FROM file_info WHERE {where_name} = {where_value} AND {wherename} = {wherevalue}"
            else:
                sql = f"SELECT * FROM file_info WHERE {where_name} LIKE '%{where_value}%'"

            # 查询 file_info 表
            file_info = self.myQuery(sql)
            return '1', file_info, check_id
        except Exception as e:
            print('get_fileInfo_by_checkNumber', e)
            return '0', None, None

    # 向数据库中脑电数据表增加记录
    def add_fileInfo(self, filemsg):
        try:
            check_id = filemsg[1]
            file_id = filemsg[2]
            mac = str(filemsg[3])
            config_id = filemsg[4]
            type = str(filemsg[5])
            state = 'notUploaded'
            block_id = 0
            # TODO：后面需要动态添加配置
            # 这里添加有问题
            sql = f"INSERT INTO `file_info` VALUES ({check_id}, {file_id}, '{type}', {config_id}, '{state}', {block_id}, '{mac}')"
            flag = self.myExecuteSql(sql)
            if flag == "":
                return True
            else:
                return False
        except Exception as e:
            print('add_fileInfo', e)

    # 更新数据库中脑电数据表的记录
    def update_fileInfo(self, filemsg, state, block_id):
        try:
            check_id = filemsg[1]
            file_id = filemsg[2]
            state = state
            block_id = block_id
            sql = f"update file_info set state = '{state}',block_id = {block_id} where check_id={check_id}  and file_id={file_id}"
            self.myExecuteSql(sql)
        except Exception as e:
            print('update_fileInfo', e)
            return False
        return True

    #  删除数据库中脑电数据表中某一状态信息
    def del_fileInfo(self, check_id=None, state='', file_id=None, flag=''):
        try:
            if state == '' and flag == '':
                sql = f"delete from file_info where check_id = {check_id} and file_id = {file_id}"
            elif flag == '':
                sql = f"delete from file_info where state = '{state}' and check_id = {check_id} "
            else:
                sql = f"delete from file_info where state = '{state}' and check_id = {check_id} and file_id = {file_id}"
            result = self.myExecuteSql(sql)
        except Exception as e:
            print('del_fileInfo', e)
            return False
        return True

    # 任务设置模块
    # 查询标注主题信息
    def get_themeInfo(self, where_name='', where_value='', flag='', start=None, offset=None):

        # 没有条件查询所有的标注主题信息
        if where_name == '' and flag == '1':
            sql = f"SELECT theme_id, theme.uid, theme.config_id, theme.`name`, user_info.name as user_name, config.config_id, state, description, CONCAT_WS('-',config.config_id,config.sampling_rate,config.notch, config.low_pass, config.high_pass) as config_info FROM theme  LEFT OUTER JOIN user_info on theme.uid = user_info.uid  LEFT OUTER JOIN config on theme.config_id = config.config_id limit 0,{offset}"
            sql1 = f"SELECT count(*) FROM theme  LEFT OUTER JOIN user_info on theme.uid = user_info.uid  LEFT OUTER JOIN config on theme.config_id = config.config_id "

        # 没有条件分页信息
        elif where_name == '' and flag == '2':
            sql = f"SELECT theme_id, theme.uid, theme.config_id, theme.`name`, user_info.name as user_name, config.config_id, state, description, CONCAT_WS('-',config.config_id,config.sampling_rate,config.notch, config.low_pass, config.high_pass) as config_info FROM theme  LEFT OUTER JOIN user_info on theme.uid = user_info.uid  LEFT OUTER JOIN config on theme.config_id = config.config_id limit {start},{offset}"
        # 获取搜索满足条件的标注主题信息
        elif where_name != '' and flag == '1':
            # 当搜索框有信息的时候
            sql = f"SELECT theme_id, theme.uid, theme.config_id, theme.`name`, user_info.name as user_name, config.config_id, state, description,CONCAT_WS('-',config.config_id,config.sampling_rate,config.notch, config.low_pass, config.high_pass) as config_info  FROM theme  LEFT OUTER JOIN user_info on theme.uid = user_info.uid  LEFT OUTER JOIN config on theme.config_id = config.config_id WHERE {where_name} LIKE '%{where_value}%' limit 0,{offset}"
            sql1 = f"SELECT count(*) FROM theme  LEFT OUTER JOIN user_info on theme.uid = user_info.uid  LEFT OUTER JOIN config on theme.config_id = config.config_id WHERE {where_name} LIKE '%{where_value}%'"

        # 查询有条件的病人信息翻页
        elif where_name != '' and flag == '2':
            sql = f"SELECT theme_id, theme.uid, theme.config_id, theme.`name`, user_info.name as user_name, config.config_id, state, description, CONCAT_WS('-',config.config_id,config.sampling_rate,config.notch, config.low_pass, config.high_pass) as config_info FROM theme  LEFT OUTER JOIN user_info on theme.uid = user_info.uid  LEFT OUTER JOIN config on theme.config_id = config.config_id WHERE {where_name} LIKE '%{where_value}%' limit {start},{offset}"
        else:
            pass

        if flag == '1':
            try:
                theme_info = self.myQuery(sql)
                totalNUm = self.myQuery(sql1)
            except Exception as e:
                print('get_themeInfo', e)
                return '0', None, None
            return '1', theme_info, totalNUm[0][0]
        else:
            try:
                theme_info = self.myQuery(sql)
            except Exception as e:
                print('get_themeInfo', e)
                return '0', None
            return '1', theme_info

    # 查询标注任务信息
    def get_taskInfo(self, where_name='', where_value='', flag=''):

        # 查询所有标注任务详细信息
        if where_name == '' and flag == '':
            sql = "SELECT theme.theme_id, theme.name, CONCAT_WS('-',p.name,LPAD(task.check_id,11,'0'),CONCAT(LPAD(task.file_id,3,'0'),'.edf')) as fileinfo, u.name as markname, task.state FROM task  LEFT JOIN theme  on task.theme_id = theme.theme_id  LEFT JOIN check_info as c on task.check_id = c.check_id   LEFT JOIN patient_info as p on c.patient_id = p.patient_id LEFT JOIN user_info as u on u.uid = task.uid"
        # 查询某个标注主题id的标注脑电文件以及对应人员标注情况
        elif where_name != '' and flag == '':
            sql = f"SELECT theme.theme_id, task.check_id, task.file_id, u.uid,c.check_number, p.name as patientname, CONCAT(LPAD(task.file_id,3,'0'),'.edf') as fileinfo, u.name as username, task.state FROM task  LEFT JOIN theme  on task.theme_id = theme.theme_id  LEFT JOIN check_info as c on task.check_id = c.check_id LEFT JOIN patient_info as p on c.patient_id = p.patient_id LEFT JOIN user_info as u on u.uid = task.uid WHERE theme.{where_name} = {where_value} ORDER BY c.check_number, task.file_id"
        # TODO：1.27插入这里
        # 查询某一主题id里面已经选择的脑电文件和标注人员
        elif where_name != '' and flag == '1':
            sql = f"SELECT  CONCAT_WS('-',p.name,LPAD(task.check_id,11,'0'),CONCAT(LPAD(task.file_id,3,'0'),'.edf')) as fileinfo, GROUP_CONCAT(CONCAT_WS('-',u.uid,u.name) ORDER BY u.uid) FROM task  LEFT JOIN theme  on task.theme_id = theme.theme_id  LEFT JOIN check_info as c on task.check_id = c.check_id   LEFT JOIN patient_info as p on c.patient_id = p.patient_id LEFT JOIN user_info as u on u.uid = task.uid WHERE theme.{where_name} = {where_value} GROUP BY fileinfo"
        # 查询某一theme_id的除了theme_id列的其它所有信息
        elif where_name != '' and flag == '2':
            sql = f"SELECT check_id, file_id, uid, state FROM task WHERE {where_name} = {where_value}"
        elif where_name != '' and flag == '3':
            sql = f"SELECT theme.theme_id, task.check_id, task.file_id, u.uid,c.check_number, p.name as patientname, CONCAT(LPAD(task.file_id,3,'0'),'.edf') as fileinfo, u.name as username, task.state FROM task  LEFT JOIN theme  on task.theme_id = theme.theme_id  LEFT JOIN check_info as c on task.check_id = c.check_id LEFT JOIN patient_info as p on c.patient_id = p.patient_id LEFT JOIN user_info as u on u.uid = task.uid WHERE theme.{where_name} = {where_value} ORDER BY c.check_number, task.file_id"
        else:
            pass
        try:
            task_info = self.myQuery(sql)
        except Exception as e:
            print('get_taskInfo', e)
            return '0', None
        return '1', task_info

    # 获取频率设置基本信息
    def get_configInfo(self):

        sql = "SELECT config_id, CONCAT_WS('-',config_id,config_name,sampling_rate, notch, low_pass, high_pass) FROM config"
        try:
            config_info = self.myQuery(sql)
        except Exception as e:
            print('get_configInfo', e)
            return '0', None
        return '1', config_info

    # 添加标注主题信息
    # def add_themeInfo(self, theme_info):
    #     try:
    #         uid = theme_info[0]
    #         theme_name = theme_info[1]
    #         config_id = theme_info[2]
    #         theme_state = theme_info[3]
    #         theme_description = theme_info[4]
    #         sql = f"insert into theme(name, description, uid, config_id, state) values ('{theme_name}','{theme_description}', '{uid}', '{config_id}', '{theme_state}')"
    #         flag = self.myExecuteSql(sql)
    #         if flag == "":
    #             return [True, None]
    #         else:
    #             if str(flag).find('Duplicate') != -1:
    #                 flag = "标注主题名重复，添加标注主题失败！！！！"
    #             else:
    #                 flag = str(flag)
    #             return [False, flag]
    #     except Exception as e:
    #         print('add_themeInfo', e)
    #         return [False, str(e)]

    def add_themeInfo(self, theme_info):
        try:
            uid = theme_info[0]
            theme_name = theme_info[1]
            config_id = theme_info[2]
            theme_state = theme_info[3]
            theme_description = theme_info[4]

            # 使用参数化语句
            sql = "INSERT INTO theme(name, description, uid, config_id, state) VALUES (%s, %s, %s, %s, %s)"
            values = (theme_name, theme_description, uid, config_id, theme_state)

            flag = self.myExecuteSqlNew(sql, values)

            if flag == "":
                return [True, None]
            else:
                if str(flag).find('Duplicate') != -1:
                    flag = "标注主题名重复，添加标注主题失败！！！！"
                else:
                    flag = str(flag)
                return [False, flag]
        except Exception as e:
            print('add_themeInfo', e)
            return [False, str(e)]

    # 添加标注主题的详细信息
    def add_taskInfo(self, theme_id, task_info, result_flag):
        try:
            # TODO:不使用循环一次性插入多条才是最佳方案
            for detail_task in task_info:
                theme_id = theme_id
                check_id = detail_task[0]
                file_id = detail_task[1]
                uid = detail_task[2]
                state = detail_task[3]
                sql = f"insert into task(theme_id, check_id, file_id, uid, state) values ('{theme_id}','{check_id}', '{file_id}', '{uid}', '{state}')"
                try:
                    flag = self.myExecuteSql(sql)
                except Exception as e:
                    return False, result_flag
                else:
                    if str(flag).find('Duplicate entry') != -1:
                        result_flag.append(1)
            return True, result_flag
        except Exception as e:
            print('add_taskInfo', e)

    # 删除标注主题
    def del_themeInfo(self, where_name, where_value):
        try:
            sql = f"delete from theme where {where_name} = '{where_value}'"
            self.myExecuteSql(sql)
        except Exception as e:
            print('del_themeInfo', e)
            return False
        return True


    # 25/06/04 更新标注主题信息，避免主题名称重复造成主键或唯一性冲突
    def update_themeInfo(self, theme_info):
        try:
            theme_name = theme_info[1]
            theme_description = theme_info[2]
            theme_id = theme_info[3]

            # 通过 myQueryOne 检查是否存在同名主题（排除当前 ID）
            check_sql = "SELECT COUNT(*) FROM theme WHERE name = %s AND theme_id != %s"
            count_result = self.myQueryOne(check_sql, (theme_name, theme_id))
            if count_result and count_result[0] > 0:
                flag = f"主题名称 '{theme_name}' 已存在，更新失败。"
                # print(f"主题名称 '{theme_name}' 已存在，更新失败。")
                return [False,flag]

            # 更新主题信息
            update_sql = "UPDATE theme SET name = %s, description = %s WHERE theme_id = %s"
            self.myExecuteSqlNew(update_sql, (theme_name, theme_description, theme_id))

        except Exception as e:
            print("update_themeInfo", e)
            return [False,str(e)]

        return [True,None]

    # 获取病人id和名字
    def get_FileInfo1(self, where_name='', where_value='', flag='', start=None, offset=None, config_id=None):

        # 没有条件查询所有的病人信息
        if where_name == '' and flag == '1':
            sql = f"SELECT DISTINCT check_info.check_id, check_info.check_number, patient_info.`name`, DATE_FORMAT(check_info.measure_date,'%Y-%m-%d') as date, user_info.`name` as cUname FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' limit 0,{offset}"

            sql1 = f"SELECT count(DISTINCT check_info.check_id) FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' "
            # 查询检查单对应的文件信息
            sql2 = f"SELECT  check_info.check_id, GROUP_CONCAT(file_info.file_id) FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' GROUP BY check_info.check_id"
        # 没有条件分页信息
        elif where_name == '' and flag == '2':
            sql = f"SELECT DISTINCT check_info.check_id, check_info.check_number, patient_info.`name`, DATE_FORMAT(check_info.measure_date,'%Y-%m-%d') as date, user_info.`name` as cUname FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' limit {start},{offset}"
        # 获取搜索满足条件的病人信息
        elif where_name != '' and flag == '1':
            # 当搜索框有信息的时候
            sql = f"SELECT DISTINCT check_info.check_id, check_info.check_number, patient_info.`name`, DATE_FORMAT(check_info.measure_date,'%Y-%m-%d') as date, user_info.`name` as cUname FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' and patient_info.{where_name} LIKE '%{where_value}%' limit 0,{offset}"

            sql1 = f"SELECT count(DISTINCT check_info.check_id) FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' and patient_info.{where_name} LIKE '%{where_value}%' "

            # 查询检查单对应的文件信息
            sql2 = f"SELECT  check_info.check_id, GROUP_CONCAT(file_info.file_id) FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' and patient_info.{where_name} LIKE '%{where_value}%' GROUP BY check_info.check_id"

        # 查询有条件的病人信息翻页
        elif where_name != '' and flag == '2':
            sql = f"SELECT DISTINCT check_info.check_id, check_info.check_number, patient_info.`name`, DATE_FORMAT(check_info.measure_date,'%Y-%m-%d') as date, user_info.`name` as cUname FROM check_info INNER JOIN patient_info on patient_info.patient_id = check_info.patient_id INNER JOIN user_info ON check_info.cUid = user_info.uid INNER JOIN file_info ON file_info.check_id = check_info.check_id WHERE file_info.config_id ={config_id} and check_info.state in ('uploaded','diagnosing','consulting','diagnosed')  and file_info.state='uploaded' and patient_info.{where_name} LIKE '%{where_value}%' limit {start},{offset}"

        else:
            pass

        if flag == '1':
            try:
                patient_info = self.myQuery(sql)
                totalNUm = self.myQuery(sql1)
                file_info = self.myQuery(sql2)
            except Exception as e:
                print('get_FileInfo1', e)
                return '0', None, None, None
            return '1', patient_info, totalNUm[0][0], file_info
        else:
            try:
                patient_info = self.myQuery(sql)
            except Exception as e:
                print('get_FileInfo1', e)
                return '0', None
            return '1', patient_info

    # 删除标注任务
    def del_taskInfo(self, task_info, flag=''):
        try:
            # 删除某一theme_id下所有任务
            if flag == '':
                sql = f"delete from task where theme_id = '{task_info}'"
            # 删除满足条件的某一个task_info
            elif flag == '1':
                theme_id = task_info[0]
                check_id = task_info[1]
                file_id = task_info[2]
                uid = task_info[3]
                sql = f"delete from task where theme_id = '{theme_id}' and check_id = '{check_id}' and file_id = '{file_id}' and uid = '{uid}'"
            else:
                pass
            self.myExecuteSql(sql)
        except Exception as e:
            print('del_taskInfo', e)
            return False
        return True

    # 更新标注主题状态信息
    def update_ThemeState(self, theme_id, set_State):
        try:
            sql = f"update theme set state = '{set_State}' where theme_id ='{theme_id}' "
            self.myExecuteSql(sql)
        except Exception as e:
            print('update_ThemeState', e)
            return False
        return True

    # 获取标注员信息
    def get_markerIdName(self, where_name='', where_value='', flag='', start=None, offset=None):
        # 没有条件查询所有的病人信息
        if where_name == '' and flag == '1':
            sql = f"select uid, name, phone, email FROM user_info where (doctor = 1 or labeler=1 or researcher=1)  limit 0,{offset}"
            sql1 = f"SELECT count(*) from user_info where (doctor = 1 or labeler=1 or researcher=1)  "
        # 没有条件分页信息
        elif where_name == '' and flag == '2':
            sql = f"select uid, name, phone, email FROM user_info where (doctor = 1 or labeler=1 or researcher=1)  limit {start},{offset}"
        # 获取搜索满足条件的病人信息
        elif where_name != '' and flag == '1':
            # 当搜索框有信息的时候
            sql = f"select uid, name, phone, email FROM user_info WHERE {where_name} LIKE '%{where_value}%' and (doctor = 1 or labeler=1 or researcher=1)  limit 0,{offset}"
            sql1 = f"SELECT count(*) from user_info WHERE {where_name} LIKE '%{where_value}%' and (doctor = 1 or labeler=1 or researcher=1) "

        # 查询有条件的病人信息翻页
        elif where_name != '' and flag == '2':
            sql = f"select uid, name, phone, email FROM user_info WHERE {where_name} LIKE '%{where_value}%' and (doctor = 1 or labeler=1 or researcher=1)  limit {start},{offset}"
        else:
            pass

        if flag == '1':
            try:
                marker_info = self.myQuery(sql)
                totalNUm = self.myQuery(sql1)
            except Exception as e:
                print('get_markerIdName', e)
                return '0', None, None
            return '1', marker_info, totalNUm[0][0]
        else:
            try:
                marker_info = self.myQuery(sql)
            except Exception as e:
                print('get_markerIdName', e)
                return '0', None
            return '1', marker_info

    # 删除标注详细信息
    def del_detailInfo(self, detail_info, flag=''):
        try:
            if flag == '':
                theme_id = detail_info[0]
                checke_id = detail_info[1]
                file_id = detail_info[2]
                uid = detail_info[3]
                begin = detail_info[4]
                channel = detail_info[5]
                sql = f"delete from reslab where theme_id  = '{theme_id}' and check_id = '{checke_id}' and file_id = '{file_id}' and uid = '{uid}' and begin = '{begin}' and channel = '{channel}'"
            elif flag == '1':
                theme_id = detail_info[0]
                checke_id = detail_info[1]
                file_id = detail_info[2]
                uid = detail_info[3]
                sql = f"delete from reslab where theme_id  = '{theme_id}' and check_id = '{checke_id}' and file_id = '{file_id}' and uid = '{uid}'"
            elif flag == '2':
                theme_id = detail_info
                sql = f"delete from reslab where theme_id  = '{theme_id}' "
            self.myExecuteSql(sql)
        except Exception as e:
            print('del_detailInfo', e)
            return False
        return True









    def queryConfigData(self, where_name='', where_value=''):
        try:
            if where_name == '':
                sql = "select * from config"
            else:
                sql = f"select * from config where `{where_name}`='{where_value}'"
            print(f'queryConfigData SQL: {sql}')
            config = self.myQuery(sql)
            print(config)
            return config
        except Exception as e:
            print('del_detailInfo', e)
            return False

    def addBasicConfig(self, config):
        try:
            sql = f"insert into config(config_name,sampling_rate,notch,low_pass,high_pass,`default`) values " \
                  "('{}',{},{},{},{},{})".format(config[0], config[1], config[2], config[3], config[4], config[5])
            flag = self.myExecuteSql(sql)
            print(f'addBasicConfig: {sql}')
            if flag == "":
                return True
            else:
                return False
        except Exception as e:
            return False

    def delBasicConfig(self, where_name, where_value):
        try:
            sql = "delete from config where {} = '{}'".format(where_name, where_value)
            re = self.myExecuteSql(sql)
            print(f'delBasicConfig sql: {sql}, re: {re}')
            if re == "":
                return True
            else:
                return False
        except Exception as re:
            return False

    def updateBasicConfig(self, where_name, where_value, config=None, set_name='', set_value=''):
        try:
            if config is None:
                sql = "update config set {} = '{}' where {}='{}'".format(set_name, set_value, where_name, where_value)
            else:
                sql = "update config set config_name = '{}', sampling_rate = '{}', notch = '{}', low_pass = '{}', high_pass = '{}', `default` = '{}' where {}='{}'".format(
                    config[1], config[2], config[3], config[4], config[5], config[6], where_name, where_value)
            print(f'updateBasicConfig SQL: {sql}')
            self.myExecuteSql(sql)
            return True
        except Exception as e:
            print(e)
            return False

    def checkConfigisUsed(self, value):
        selectTable = ['class', 'classifier', 'file_info', 'set_info', 'theme']
        flag = False
        for table in selectTable:
            sql = f"SELECT COUNT(*) AS usage_count FROM {table} WHERE config_id = {value};"
            re = self.myQuery(sql)
            if re[0][0] != 0:
                print(f'{table}')
                flag = True
                break
        return flag

    def getDoctorInfo(self, column='*', where_name='', where_like=''):
        try:
            if where_name == '':
                sql = f"select {column} from user_info where doctor='1' or researcher='1'"
            else:
                sql = f"select {column} from user_info where (doctor='1' or researcher='1') and {where_name} like '%{where_like}%'"
            print(f'getDoctorInfo sql: {sql}')
            user_info = self.myQuery(sql)
            return user_info
        except Exception as e:
            print('getDoctorInfo', e)
            return False

    def getAllConsInfo(self, where_name='', where_like='', date1='', date2='', userID=''):
        try:
            sql1 = """
            SELECT c.check_number, p.name AS patient_name,c.measure_date, u1.name AS pUid_name, u2.name AS cUid_name, c.state, 'NONE' AS create_name,'NONE' AS sign_date, c.description, c.check_id
            FROM check_info c
            JOIN patient_info p ON c.patient_id = p.patient_id
            JOIN user_info u1 ON c.pUid = u1.uid
            JOIN user_info u2 ON c.cUid = u2.uid
            WHERE c.state = 'uploaded'
            """
            sql2 = """
            SELECT
                    ci.check_number,pi.name AS patient_name,ci.measure_date,
                    u1.name AS pUid_name, u2.name AS cUid_name, di.state, ui.name AS create_name, di.sign_date, ci.description, ci.check_id
            FROM check_info AS ci 
            JOIN diag AS di ON ci.check_id = di.check_id
            JOIN patient_info AS pi ON ci.patient_id = pi.patient_id
            JOIN user_info AS ui ON di.uid = ui.uid
            JOIN user_info u1 ON ci.pUid = u1.uid
            JOIN user_info u2 ON ci.cUid = u2.uid
            """

            if where_name == 'check_number':
                sql1 = sql1 + f" and c.{where_name} like '%{where_like}%'"
                sql2 = sql2 + f" where ci.{where_name} like '%{where_like}%'"
            elif where_name == 'name':
                sql1 = sql1 + f" and p.{where_name} like '%{where_like}%'"
                sql2 = sql2 + f" where pi.{where_name} like '%{where_like}%'"

            if userID != '':
                sql1 = sql1 + f" and u2.uid = {userID}"
                sql2 = sql2 + f" and u2.uid = {userID}"

            if date1 != '' and date2 != '':
                sql1 = sql1 + f" and c.measure_date BETWEEN '{date1}' AND '{date2}'"
                sql2 = sql2 + f" and ci.measure_date BETWEEN '{date1}' AND '{date2}'"

            sql1 = sql1 + " ORDER BY c.measure_date DESC"
            sql2 = sql2 + " ORDER BY ci.measure_date DESC"

            print(f'getAllConsInfo SQL1: {sql1}')
            print(f'getAllConsInfo SQL2: {sql2}')
            check_info1 = self.myQuery(sql1)
            check_info2 = self.myQuery(sql2)
            return check_info1 + check_info2
        except Exception as e:
            print('getAllConsInfo', e)

    def updateCons(self, set_name='', set_value='', where_name='', where_value=''):
        try:
            sql = f"UPDATE diag SET {set_name} = '{set_value}' WHERE {where_name} = {where_value};"
            self.myExecuteSql(sql)
            return True
        except Exception as e:
            print('updateCons', e)

    def getCpltCheckInfo(self, where_name='', where_value=''):
        try:
            sql = """
            SELECT c.*, p.name AS patient_name, u1.name AS pUid_name, u2.name AS cUid_name
            FROM check_info c
            JOIN patient_info p ON c.patient_id = p.patient_id
            JOIN user_info u1 ON c.pUid = u1.uid
            JOIN user_info u2 ON c.cUid = u2.uid
            WHERE c.state = 'uploaded'
            """
            if where_name != '':
                sql = sql + f'and c.{where_name} = {where_value};'
            else:
                sql = sql + ";"
            print(f'getCpltCheckInfo SQL: {sql}')
            check_info = self.myQuery(sql)
            return check_info
        except Exception as e:
            print('getCheckInfo', e)

    def getHistoryCons(self):
        try:
            # sql = "SELECT check_id, GROUP_CONCAT(uid) AS uids FROM diag GROUP BY check_id;"
            sql = """
                SELECT
                    ci.check_number,pi.name AS patient_name,ci.measure_date,
                    ui.name AS user_name,di.state,di.sign_date,pi.patient_id,di.uid AS user_id
                FROM check_info AS ci 
                JOIN diag AS di ON ci.check_id = di.check_id
                JOIN patient_info AS pi ON ci.patient_id = pi.patient_id
                JOIN user_info AS ui ON di.uid = ui.uid;
                """
            print(f'getHistoryCons SQL: {sql}')
            cons_info = self.myQuery(sql)
            return cons_info
        except Exception as e:
            print('getHistoryCons', e)

    def getDiagInfo(self, column='*', where_name='', where_value=''):
        try:
            if where_name == '':
                sql = f"select {column} from diag"
            else:
                sql = f"select {column} from diag where {where_name}='{where_value}'"
            diagInfo = self.myQuery(sql)
            return diagInfo
        except Exception as e:
            print('getDiagInfo', e)

    def updateCheckInfo(self, set_name='', set_value='', where_name='', where_value=''):
        try:
            sql = f"UPDATE check_info SET {set_name} = '{set_value}' WHERE {where_name} = {where_value};"
            self.myExecuteSql(sql)
            return True
        except Exception as e:
            print('updateCheckInfo', e)

    def createCons(self, diagInfo):
        try:
            for diag in diagInfo:
                sql = f"INSERT INTO diag (check_id, uid, sign_date) VALUES ({diag[0]}, {diag[1]}, '{diag[2]}')"
                print(f'createCons sql: {sql}')
                flag = self.myExecuteSql(sql)
                if flag == "":
                    continue
                else:
                    return False
        except Exception as e:
            print('createCons', e)

    def getPatientInfo(self, where_name='', where_value='', where_like='', count=''):
        try:
            if count == True:
                sql = "select count(*) from patient_info"
            elif where_name == '':
                sql = "select * from patient_info"
            elif where_like != '':
                sql = f"select * from patient_info where {where_name} like '%{where_like}%'"
            else:
                sql = f"select * from patient_info where {where_name} = {where_value}"
            patient_info = self.myQuery(sql)
            print(f'getPatientInfo sql: {sql}')
            return patient_info
        except Exception as e:
            print('getPatientInfo', e)

    def getPatientInfoByPage(self, offset='', psize=''):
        sql = f"select * from patient_info limit {offset}, {psize}"
        patient_info = self.myQuery(sql)
        return patient_info

    def addPatientInfo(self, patient_info):
        try:
            sql = f"insert into patient_info(name,birth,sex,card,tel,nat_place,cur_place) values " \
                  "('{}','{}','{}','{}','{}','{}','{}')".format(
                patient_info[0], patient_info[1], patient_info[2], patient_info[3], patient_info[4], patient_info[5],
                patient_info[6])
            tag = self.myExecuteSql(sql)
            print(f'addPatientInfo: {sql}')
            if tag == "":
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print('addPatientInfo', e)
            return '0', str(e)

    def delPatientInfo(self, where_name, where_value):
        try:
            sql = "delete from patient_info where {} = '{}'".format(where_name, where_value)
            tag = self.myExecuteSql(sql)
            if tag == "":
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def updatePatientInfo(self, where_name, where_value, patienInfo):
        try:
            sql = "update patient_info set name = '{}', birth = '{}',sex = '{}',card = '{}',tel = '{}'," \
                  "nat_place = '{}',cur_place = '{}' where {} = {}".format(patienInfo[0], patienInfo[1],
                                                                           patienInfo[2], patienInfo[3],
                                                                           patienInfo[4], patienInfo[5],
                                                                           patienInfo[6], where_name, where_value)
            tag = self.myExecuteSql(sql)
            if tag == "":
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(tag)

    ### dsj ==[===

    def get_userNameByUids(self, uids=''):
        try:
            if uids == '':
                sql = "select uid,name from user_info"
            else:
                sql = f"select uid,name from user_info where uid in ({uids})"
            user_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', user_info

    def get_patientNameByPids(self, pids=''):
        try:
            if pids == '':
                sql = "select patient_id,name from patient_info"
            else:
                sql = f"select patient_id,name from patient_info where patient_id in ({pids})"
            patientInfo = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', patientInfo

    # zh 根据用户id,测量日期获取文件名
    def get_fileNameByIdDate(self, check_id):
        try:
            sql = f"select check_id,file_id from file_info where state='uploaded' and check_id={check_id}"
            file_name = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', file_name

    def get_patientInfo(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select * from patient_info"
        else:
            sql = "select * from patient_info where {}='{}'".format(where_name, where_value)
        patientInfo = self.myQuery(sql)
        return patientInfo

    # zh 获取样本列表
    def get_sampleListInfo(self, check_id, file_id, channels, type_names, user_names, status_show):
        try:
            if status_show == True:
                sql = "select channel,begin,end,sample_info.uid,sample_info.type_id,type_name from sample_info," \
                      "type_info,user_info where check_id={} and file_id={} and " \
                      " (channel in {} or channel='all') and sample_info.type_id=type_info.type_id and type_info.type_name in " \
                      " {} and sample_info.uid=user_info.uid and user_info.name in {} order by begin".format(
                    check_id, file_id, channels, type_names, user_names)
            else:
                sql = "select channel,begin,end,sample_info.uid,sample_info.type_id,type_name from sample_info," \
                      "type_info,user_info  where check_id={} and  file_id={} and channel " \
                      "in {} and sample_info.type_id=type_info.type_id and type_info.type_name in {}  and sample_info.uid=" \
                      "user_info.uid and user_info.name in {} order by begin".format(
                    check_id, file_id, channels, type_names, user_names)
            sample_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', sample_info

    # zh 获取样本列表中的状态样本
    def get_statusInfo(self, check_id, file_id, where_name='', where_value=''):
        try:
            if where_name == '':
                sql = "select channel,begin,end,uid,sample_info.type_id,type_name from sample_info,type_info  where " \
                      "check_id={} and file_id={} and channel='all' and type_info.type_id=" \
                      "sample_info.type_id order by begin".format(
                    check_id, file_id)
            else:
                sql = "select channel,begin,end,uid,sample_info.type_id,type_name from sample_info,type_info  where " \
                      "check_id={} and file_id={} and channel='all'  and {}={} and " \
                      "type_info.type_id=sample_info.type_id order by begin".format(
                    check_id, file_id, where_name, where_value)
            state_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', state_info

    # zh 更新样本列表
    def update_sampleInfo(self, check_id, file_id, begin, channel, end, uid, type_id):
        try:
            self.myExecuteSql(
                "update sample_info set end='{}',type_id ={} where check_id={} and "
                " file_id={} and begin='{}'and channel='{}' and uid={}".format(
                    end, type_id, check_id, file_id, begin, channel, uid))
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    def insert_sampleInfo_batch(self, sample_info):
        """
        批量插入 sample_info 记录
        :param sample_info: [[check_id, file_id, begin, channel, end, uid, type_id], ...]
        """
        try:
            sql = (
                "INSERT INTO sample_info (check_id, file_id, begin, channel, end, uid, type_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            self.myExecuteMany(sql, sample_info)
            return True
        except Exception as e:
            print("insert_sampleInfo_batch 错误:", e)
            return False

    # zh 添加样本
    def add_sampleInfo(self, check_id, file_id, begin, channel, end, uid, type_id):
        try:
            self.myExecuteSql(
                "insert into sample_info(check_id, file_id, begin, channel, end, uid, type_id) "
                "values ({},{},'{}','{}','{}',{},{})".format(check_id, file_id, begin, channel, end, uid, type_id))
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    # zh 删除样本
    def del_sampleInfo(self, check_id, file_id, begin, channel, end, uid, type_id):
        try:
            self.myExecuteSql(
                "delete from sample_info where check_id={} and  file_id={} and "
                "begin='{}' and channel='{}' and end='{}' and uid={} and type_id ={}".format(
                    check_id, file_id, begin, channel, end, uid, type_id))
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    # zh 获取标注集??
    def get_labelListInfo(self, patient_id, measure_date, file_name, model, channels, type_names, user_names,
                          status_show):
        try:
            if status_show == True:
                sql = "select channel,begin,end,mid,label_info.mtype_id,label_info.uid,utype_id from label_info,type_info,user_info " \
                      "where patient_id='{}'and measure_date='{}'and file_name='{}' and mid='{}'and (channel in {} or channel='all')" \
                      "and ((label_info.utype_id is null and label_info.mtype_id=type_info.type_id) or (label_info.utype_id is not null " \
                      "and label_info.utype_id=type_info.type_id)) and type_info.type_name in {} " \
                      "and user_info.uid=label_info.uid  and user_info.name in {} order by begin".format(
                    patient_id, measure_date, file_name, model, channels, type_names, user_names)
            else:
                sql = \
                    "select channel,begin,end,mid,label_info.mtype_id,label_info.uid,utype_id from label_info,type_info,user_info " \
                    "where patient_id='{}'and measure_date='{}'and file_name='{}' and mid='{}'and channel in {} " \
                    "and ((label_info.utype_id is null and label_info.mtype_id=type_info.type_id) or (label_info.utype_id" \
                    " is not null and label_info.utype_id=type_info.type_id)) and type_info.type_name in {} " \
                    "and user_info.uid=label_info.uid  and user_info.name in {} order by begin".format(
                        patient_id, measure_date, file_name, model, channels, type_names, user_names)
            label_info = self.myQuery(sql)
        except Exception as ex:
            return '0', f"{ex}"
        # return "1", None
        return label_info

    # zh 获取标注集中的状态??
    def get_labelStatusInfo(self, patient_id, measure_date, file_name, model, where_name='', where_value=''):
        if where_name == '':
            sql = "select channel,begin,end,mid,label_info.mtype_id,uid,utype_id from label_info,type_info  where " \
                  " patient_id='{}'and measure_date='{}'and file_name='{}' and channel='all' and mid='{}' and " \
                  "type_info.type_id=label_info.mtype_id order by begin".format(
                patient_id, measure_date, file_name, model)
        else:
            sql = "select channel,begin,end,mid,label_info.mtype_id,uid,utype_id from label_info,type_info  where " \
                  " patient_id='{}'and measure_date='{}'and file_name='{}' and channel='all' and mid='{}' and " \
                  "{}='{}' and type_info.type_id=label_info.mtype_id order by begin".format(
                patient_id, measure_date, file_name, model, where_name, where_value)
        state_info = self.myQuery(sql)
        return state_info

    def sys_log(self, cmdId, values):
        try:
            sql = "insert into t_syslog values(null,{},current_timestamp(),'{}','{}','{}','{}')".format(
                cmdId, values[0], values[1], values[2], values[3])
            self.myExecuteSql(sql)
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    def diag_add(self, diagInfo):
        sql = f"insert into diag values({diagInfo[0]},'{diagInfo[1]}',{diagInfo[2]},'notDiagnosed',None," \
              f"'{diagInfo[4]}','{diagInfo[5]}','{diagInfo[6]}','{diagInfo[7]}','{diagInfo[8]}','{diagInfo[9]}'," \
              f"'{diagInfo[10]}','{diagInfo[11]}','{diagInfo[12]}','{diagInfo[13]}')"
        try:
            self.myExecuteSql(sql)
        except Exception as re:
            return '0', str(re)
        return '1', True

    def diag_update(self, diagInfo, state=''):
        if state == '':
            sql = f" UPDATE diag SET alpha='{diagInfo[4]}',slow='{diagInfo[5]}',fast='{diagInfo[6]}'," \
                  f"amplitude='{diagInfo[7]}',eyes='{diagInfo[8]}',hyperventilation='{diagInfo[9]}'," \
                  f"sleep='{diagInfo[10]}',abnormal_wave='{diagInfo[11]}',attack_stage='{diagInfo[12]}',summary='{diagInfo[13]}'" \
                  f" where check_id={diagInfo[0]}  and uid={diagInfo[2]}"
        elif state == 'diagnosed':
            sql = f" UPDATE diag SET  sign_date=current_timestamp(),state='{state}',  alpha='{diagInfo[4]}',slow='{diagInfo[5]}',fast='{diagInfo[6]}'," \
                  f"amplitude='{diagInfo[7]}',eyes='{diagInfo[8]}',hyperventilation='{diagInfo[9]}'," \
                  f"sleep='{diagInfo[10]}',abnormal_wave='{diagInfo[11]}',attack_stage='{diagInfo[12]}',summary='{diagInfo[13]}'" \
                  f" where check_id={diagInfo[0]}  and uid={diagInfo[2]}"
        elif state == 'refused':
            sql = f" UPDATE diag SET  sign_date=current_timestamp(),state='{state}' where check_id={diagInfo[0]}  and uid={diagInfo[1]}"
        else:
            sql = f" UPDATE diag SET  state='{state}',  alpha='{diagInfo[4]}',slow='{diagInfo[5]}',fast='{diagInfo[6]}'," \
                  f"amplitude='{diagInfo[7]}',eyes='{diagInfo[8]}',hyperventilation='{diagInfo[9]}'," \
                  f"sleep='{diagInfo[10]}',abnormal_wave='{diagInfo[11]}',attack_stage='{diagInfo[12]}',summary='{diagInfo[13]}'" \
                  f" where check_id={diagInfo[0]}  and uid={diagInfo[2]}"
        try:
            self.myExecuteSql(sql)
        except Exception as re:
            return '0', str(re)
        return '1', True

    def diag_refused(self, check_id, uid):
        sql1 = f" UPDATE diag SET sign_date=current_timestamp(),state='refused'" \
               f" where check_id={check_id}  and uid={uid}"
        sql2 = f" UPDATE check_info SET  state = 'diagnosed' WHERE check_id ={check_id}"
        sql = [sql1, sql2]
        try:
            self.myExecuteTranSql(sql)
        except Exception as re:
            return '0', str(re)
        return '1', True

    def diag_commit(self, diagInfo):
        sql1 = f" UPDATE diag SET sign_date=current_timestamp(),state='diagnosed',alpha='{diagInfo[4]}',slow='{diagInfo[5]}',fast='{diagInfo[6]}'," \
               f"amplitude='{diagInfo[7]}',eyes='{diagInfo[8]}',hyperventilation='{diagInfo[9]}'," \
               f"sleep='{diagInfo[10]}',abnormal_wave='{diagInfo[11]}',attack_stage='{diagInfo[12]}',summary='{diagInfo[13]}'" \
               f" where check_id={diagInfo[0]}  and uid={diagInfo[2]}"
        sql2 = f" UPDATE check_info SET  state = 'diagnosed' WHERE check_id ={diagInfo[0]}"
        sql = [sql1, sql2]
        try:
            self.myExecuteTranSql(sql)
        except Exception as re:
            return '0', str(re)
        return '1', True

    def get_userPhoneEmailByCheckid(self, check_id=''):
        sql = "SELECT uid, name, phone, email FROM  user_info  where uid in (select pUid from check_info where " \
              f"check_id ={check_id} )"
        try:
            resultData = self.myQuery(sql)
            return '1', resultData
        except Exception as re:
            return '0', str(re)

    def diag_getByPage(self, check_id='', pname='', uid='', diag_state='', other_where='', offset=0, psize=0):
        sql = " where diag.check_id = check_info.check_id "
        if check_id != '':
            sql += " and diag.check_id= " + str(check_id)
        if uid != '':
            sql += " and diag.uid= " + str(uid)
        if diag_state != '':
            sql += " and diag.state = '" + diag_state + "'"
        if other_where != '':
            sql += " and  " + str(other_where)
        if pname != '':
            sql += f" and  patient_id in (select patient_id FROM patient_info where name like '%{pname}%') "
        if offset >= 0 and psize > 0:
            sql += f" limit  {offset}, {psize}"
        sql = "select patient_id,measure_date, diag.uid, diag.state,diag.sign_date, alpha,slow,fast,amplitude,eyes," \
              "hyperventilation,sleep,abnormal_wave,attack_stage,summary,diag.check_id,check_info.pUid, " \
              "check_info.check_number,check_info.cUid " \
              " from diag,check_info " + sql
        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    # 统计记录数
    def diag_getRecords(self, uid='', diag_state='', other_where=''):
        sql = ""
        if uid != '':
            if sql == "":
                sql = " where uid = " + str(uid)
            else:
                sql += " and  uid= " + str(uid)
        if diag_state != '':
            if sql == "":
                sql = " where state = '" + diag_state + "'"
            else:
                sql += " and state = '" + diag_state + "'"
        if other_where != '':
            if sql == "":
                sql = " where " + str(other_where)
            else:
                sql += " and  " + str(other_where)

        sql = "select count(*) from diag " + sql
        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet[0]

    # author:dsj  state enum('notDiagnosed','diagnosed','refused')
    # 通过patient_id,measure_date,uid,提取diag信息
    def diag_get(self, check_id='', uid='', diag_state='', other_where=''):
        sql = " where diag.check_id = check_info.check_id "
        if check_id != '':
            sql += " and diag.check_id = " + str(check_id)
        if uid != '':
            sql += " and diag.uid = " + str(uid)
        if diag_state != '':
            sql += " and diag.state = '" + diag_state + "'"
        if other_where != '':
            sql += " and  " + str(other_where)
        sql = "select patient_id,measure_date, diag.uid, diag.state,diag.sign_date, alpha,slow,fast,amplitude,eyes," \
              "hyperventilation,sleep,abnormal_wave,attack_stage,summary,diag.check_id,check_info.pUid, " \
              "check_info.check_number,check_info.cUid " \
              " from diag,check_info " + sql
        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    # author:dsj  state enum('notDiagnosed','diagnosed','refused')
    # 通过patient_id,measure_date,uid,提取diag信息
    def diag_get_forConsulting(self, uid=''):
        sql = " where diag.check_id = check_info.check_id and check_info.state in ('diagnosing','consulting') "
        if uid != '':
            sql += " and diag.check_id in (select check_id from  diag where state='notDiagnosed' and uid = " + str(
                uid) + ")"
        sql = "select patient_id,measure_date, diag.uid, diag.state,diag.sign_date, alpha,slow,fast,amplitude,eyes," \
              "hyperventilation,sleep,abnormal_wave,attack_stage,summary,diag.check_id,check_info.pUid, " \
              "check_info.check_number,check_info.cUid " \
              " from diag,check_info " + sql + " order by diag.check_id "
        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet
    def diag_get_refused_state(self,tempt):
        if not tempt:
            return []

            # 构建 SQL 查询
        queries = []
        for check_id, uid in tempt:
            queries.append(
                f"SELECT {check_id} AS check_id, {uid} AS uid, EXISTS (SELECT 1 FROM sample_info WHERE check_id = {check_id} AND uid = {uid}) AS `exists`")

        sql = " UNION ALL ".join(queries)
        results =self.myQuery(sql)
        # results = data.fetchall()
        exist_results = [row[2] for row in results]
        return exist_results
    # 诊断学习/提取学习的诊断信息
    def study_get(self, class_id='', uid=''):
        sql = ''
        if class_id != '':
            sql = " where class_id = " + str(class_id)
        if uid != '':
            if sql == '':
                sql = "  where uid = " + str(uid)
            else:
                sql += " and  uid = " + str(uid)
        sql = "select * from study " + sql + " order by start "
        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    # 诊断学习，提取学习的诊断信息
    def dl_get_contents(self, where_class=None, where_student=None):
        sql = " SELECT class.class_id,class.name,class.description,class.start,class.end,class.time," \
              "content.check_id,check_info.check_number,check_info.patient_id,check_info.measure_date," \
              "content.file_id,content.uid FROM content,class,check_info where " \
              "content.class_id=class.class_id and content.check_id=check_info.check_id  "
        if where_class is not None and where_class != '':
            sql += f" and  {where_class}"
        if where_student is None or where_student == '':
            sql += " and content.class_id in (select class_id from student )"
        else:
            sql += f" and content.class_id in (select class_id from student where {where_student})"

        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    # 诊断学习，开始学习的诊断信息
    def dl_study_start(self, class_id, uid, start_time):
        sql = f"INSERT INTO study(class_id,uid,start,end) VALUES ({class_id},{uid}, '{start_time}','{start_time}')"
        try:
            dataSet = self.myExecuteSql(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    # 诊断学习，结束本次诊断信息学习

    def dl_study_end(self, class_id, uid, start_time, end_time):
        sql = f"insert into study (class_id, uid, start,end) VALUES ({class_id}, {uid}, '{start_time}', '{end_time}')"
        try:
            dataSet = self.myExecuteSql(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    def dl_student_get(self, class_id=None, uid=None, other_where=None, userInfo=False):
        sql = ""
        if class_id is not None:
            sql = f" where student.class_id={class_id}"
        if uid is not None:
            if sql == "":
                sql = f" where student.uid={uid}"
            else:
                sql += f" and student.uid={uid}"
        if other_where is not None:
            if sql == "":
                sql = f" where {other_where}"
            else:
                sql += f" and {other_where}"
        if userInfo:
            sql = f"select student.class_id,student.uid,student.state,student.grade,account,name,phone,email " \
                  f"from student left join user_info  on student.uid=user_info.uid {sql}"
        else:
            sql = f"select * from student {sql}"

        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    def dl_student_update(self, class_id=None, uid=None, setSQL=''):
        sql = ""
        if class_id is not None:
            sql = f" where class_id={class_id}"
        if uid is not None:
            if sql == "":
                sql = f" where uid={uid}"
            else:
                sql += f" and uid={uid}"

        sql = f" update student set {setSQL} {sql}"

        try:
            dataSet = self.myExecuteSql(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    def user_info_get(self, where_value=''):
        if where_value == '':
            sql = "select * from user_info"
        else:
            sql = f"select * from user_info where {where_value}"
        user_info = self.myQuery(sql)
        return user_info

    # 根据classID提取取样本信息
    def dl_get_sampleInfoByClassID(self, class_id, did=None):
        try:
            sql = f"SELECT  check_id, file_id, uid, begin, channel, end, type_id  FROM  sample_info where " \
                  f"(check_id,file_id,uid) in (select check_id, file_id, uid from content where purpose='test' and " \
                  f"class_id={class_id}) "
            sample_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', sample_info
    # 根据uID提取取样本信息
    def da_get_sampleInfoByUID(self, check_id, file_id, uid,isShow=False):
        try:
            if isShow:
                sql = f"select channel,begin,end,uid,sample_info.type_id,type_info.type_name from " \
                      f" sample_info  left join type_info on sample_info.type_id=type_info.type_id where " \
                      f" sample_info.check_id={check_id} and  sample_info.file_id={file_id} and sample_info.uid={uid} " \
                      f" order by begin"
            else:
              sql = f"SELECT  check_id, file_id, uid, begin, channel, end, type_id  FROM  sample_info where " \
                  f" check_id={check_id} and file_id={file_id} and uid= {uid} order by begin"
            sample_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', sample_info

    # 提取测试结果信息
    def result_get(self, class_id, check_id, file_id, uid,sUid):
        try:
            sql = f"select channel,begin,end,result.uid,result.type_id,type_name,result.sUid from " \
                  f" result  left join type_info on result.type_id=type_info.type_id where " \
                  f" result.class_id={class_id} and result.uid={uid} and result.sUid={sUid} " \
                  f" and result.check_id={check_id} and  file_id={file_id} order by begin"
            result_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', result_info

        # 添加样本

    def result_add(self, class_id, check_id, file_id, begin, channel, end, uid,sUid, type_id):
        try:
            self.myExecuteSql(f"insert into result(class_id,uid,sUid,check_id,file_id,begin,channel,end,type_id) values "
                              f"({class_id},{uid},{sUid},{check_id},{file_id},'{begin}','{channel}','{end}',{type_id})")
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    # 修改样本
    def result_update(self, class_id, check_id, file_id, begin, channel, end, uid,sUid, type_id):
        try:
            self.myExecuteSql(f"update result set end='{end}',type_id ={type_id} where class_id={class_id} and "
                              f" check_id={check_id} and  file_id={file_id} and  uid={uid} and  sUid={sUid} "
                              f" and begin='{begin}' and channel='{channel}'")
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    # 删除样本
    def result_del(self, class_id, check_id, file_id, begin, channel, end, uid,sUid, type_id):
        try:
            self.myExecuteSql(
                f"delete from result where class_id={class_id} and  uid={uid} and  sUid={sUid} and check_id={check_id} and  file_id={file_id} "
                f"and begin='{begin}' and channel='{channel}' and end='{end}' and type_id ={type_id}")
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    #
    def resultList_get(self, class_id, check_id, file_id, channels, type_names, user_names, status_show, suid):
        try:
            if status_show == True:
                sql = "select channel,begin,end,result.uid,result.type_id,type_name,sUid from result left join  " \
                      " type_info on  result.type_id=type_info.type_id  where class_id={} and check_id={} and file_id={} and sUid={} and " \
                      " (channel in {} or channel='all') and (isnull( result.type_id) or type_info.type_name in " \
                      " {}) and result.uid in (select uid from user_info where name in {}) order by begin".format(
                    class_id,
                    check_id,
                    file_id, suid,
                    channels,
                    type_names,
                    user_names)
            else:
                sql = "select channel,begin,end,result.uid,result.type_id,type_name,sUid from result left join  " \
                      " type_info on  result.type_id=type_info.type_id  where class_id={} and check_id={} and file_id={} and sUid={} and " \
                      " channel in {} and (isnull( result.type_id) or type_info.type_name in " \
                      " {}) and result.uid in (select uid from user_info where name in {}) order by begin".format(
                    class_id,
                    check_id,
                    file_id, suid,
                    channels,
                    type_names,
                    user_names)

            resultList = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', resultList

    # 诊断学习/提取样本
    def dl_get_sampleListInfo(self, check_id, file_id, uid):
        try:
            sql = "select channel,begin,end,sample_info.uid,sample_info.type_id,type_name from sample_info," \
                  "type_info,user_info where check_id={} and sample_info.uid={} and file_id={} and " \
                  " sample_info.type_id=type_info.type_id and  sample_info.uid=user_info.uid order by begin".format(
                check_id, uid, file_id)

            sample_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', sample_info

    # 学习评估/课堂学生答题数成绩
    def da_get_resultNumByClass(self, class_id, uids):
        try:
            sql1 = f"select sUid,count(*) from result where class_id={class_id} and sUid in ({uids}) group by sUid"
            qsum = self.myQuery(sql1)
        except Exception as re:
            return '0', str(re)
        return '1', qsum

    # 学习评估/课堂学生答题正确情况成绩
    def da_get_resultAnswerTrueNumByClass(self, class_id, uids):
        try:
            sql2 = f"select result.sUid,count(*) from result right join sample_info on  result.check_id=sample_info.check_id and  result.file_id=sample_info.file_id and " \
                   f" result.uid=sample_info.uid and result.channel=sample_info.channel and result.begin=sample_info.begin and result.end=sample_info.end and result.type_id=sample_info.type_id " \
                   f" where result.class_id={class_id} and result.sUid in ({uids})  group by result.sUid"
            asum = self.myQuery(sql2)
        except Exception as re:
            return '0', str(re)
        return '1', asum

    # 科研标注/提取标注信息
    def reslabList_get(self, theme_id, check_id, file_id, channels, type_names, user_uids, status_show):
        try:
            if status_show == True:
                sql = "select channel,begin,end,reslab.uid,reslab.type_id,type_name from reslab," \
                      "type_info,user_info where theme_id={} and check_id={} and file_id={} and " \
                      " (channel in {} or channel='all') and reslab.type_id=type_info.type_id and type_info.type_name in " \
                      " {} and reslab.uid=user_info.uid and user_info.uid in {} order by begin".format(theme_id,
                                                                                                       check_id,
                                                                                                       file_id,
                                                                                                       channels,
                                                                                                       type_names,
                                                                                                       user_uids)
            else:
                sql = "select channel,begin,end,reslab.uid,reslab.type_id,type_name from reslab," \
                      "type_info,user_info  where theme_id={} and check_id={} and  file_id={} and channel " \
                      "in {}  and reslab.type_id=type_info.type_id and type_info.type_name in {}  and reslab.uid=" \
                      "user_info.uid and user_info.uid in {} order by begin".format(theme_id,
                                                                                    check_id, file_id, channels,
                                                                                    type_names, user_uids)
            resultList = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', resultList

    def getUserInfoByDiag(self, check_id=''):
        if check_id == '':
            sql = "select * from user_info"
        else:
            sql = f"select * from user_info where uid in (select uid from diag  where check_id={check_id})"
        user_info = self.myQuery(sql)
        return user_info

    # 科研标注，提取标注信息
    def rg_get_labels(self, where_theme=None, where_task=None):
        sql = " SELECT theme.theme_id,theme.name,theme.description,task.state,theme.state,theme.config_id,theme.uid," \
              "task.check_id,check_info.check_number,check_info.patient_id,check_info.measure_date," \
              "task.file_id,task.uid FROM task ,theme,check_info where " \
              "theme.theme_id=task.theme_id and task.check_id=check_info.check_id "
        if where_theme is not None and where_theme != '':
            sql += f" and  {where_theme}"
        if where_task is not None and where_task != '':
            sql += f" and  {where_task}"
        sql += f" order by theme.theme_id,task.uid "
        try:
            dataSet = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', dataSet

    # 科研标注，修改任务状态信息
    def task_update(self, theme_id, check_id, file_id, uid, state):
        if state not in ('notStarted', 'labelling', 'labelled', 'qualified', 'notqualified'):
            return '2', f"state err:{state}"
        sql = f" UPDATE task SET state = '{state}' WHERE theme_id = {theme_id} and check_id = {check_id} and " \
              f"file_id ={file_id} and uid = {uid}"
        try:
            r = self.myExecuteSql(sql)
            if r == '':
                return '1', True
            else:
                return '0', str(r)
        except Exception as re:
            return '0', str(re)

    # 科研标注，修改任务状态信息
    def task_get(self, theme_id=None, check_id=None, file_id=None, uid=None, other_sql=None):
        sql = "";
        if theme_id is not None and theme_id != '':
            sql = f" where theme_id={theme_id} "
        if check_id is not None and check_id != '':
            if sql == "":
                sql = f" where check_id={check_id} "
            else:
                sql += f" and check_id={check_id} "
        if file_id is not None and file_id != '':
            if sql == "":
                sql = f" where file_id={file_id} "
            else:
                sql += f" and file_id={file_id} "
        if uid is not None and uid != '':
            if sql == "":
                sql = f" where uid={uid} "
            else:
                sql += f" and uid={uid} "
        if other_sql is not None and other_sql != '':
            if sql == "":
                sql = f" where {other_sql} "
            else:
                sql += f" and {other_sql} "
        sql0 = f" select * from task {sql}"
        try:
            r, d = self.myQueryExt(sql0)
            return r, d
        except Exception as re:
            return '0', str(re)

    # 科研标注，添加标注信息
    def reslab_add(self, check_id, file_id, begin, channel, end, uid, type_id, theme_id):
        sql = f"INSERT INTO reslab VALUES({theme_id},{check_id},{file_id},{uid},{begin},'{channel}',{end},{type_id})"
        try:
            r = self.myExecuteSql(sql)
            if r == '':
                return '1', True
            else:
                return '0', str(r)
        except Exception as re:
            return '0', str(re)

    # 科研标注，修改标注信息
    def reslab_update(self, check_id, file_id, begin, channel, end, uid, type_id, theme_id):
        try:
            self.myExecuteSql(
                "update reslab set end='{}',type_id ={} where theme_id={} and  check_id={} and "
                " file_id={} and begin='{}' and channel='{}' and uid={}".format(
                    end, type_id, theme_id, check_id, file_id, begin, channel, uid))
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    # 科研标注，删除样本
    def reslab_del(self, check_id, file_id, begin, channel, end, uid, type_id, theme_id):
        try:
            self.myExecuteSql(
                "delete from reslab where theme_id={} and check_id={} and  file_id={} and "
                "begin='{}' and channel='{}' and end='{}' and uid={} and type_id ={}".format(
                    theme_id, check_id, file_id, begin, channel, end, uid, type_id))
        except Exception as ex:
            return '0', f"{ex}"
        return "1", None

    ### dsj ==]===

    def getLessonInfo(self, where_name='', where_value='', where_like=''):
        if where_name == '':
            sql = "select * from class"
        elif where_like != '':
            if where_name == 'uid':
                sql = f"select * from class where class.uid in (select uid from user_info where teacher = '1' and name like '%{where_like}%')"
            else:
                sql = f"select * from class where {where_name} like '%{where_like}%'"
        else:
            sql = f"select * from class where {where_name}='{where_value}'"
        lesson_info = self.myQuery(sql)
        return lesson_info

    def getDiagCheckID(self, where_name='', where_value='', offset='', psize=''):
        if where_name == '':
            sql = "select * from check_info"
        elif offset != '':
            sql = f"select * from check_info where {where_name}='{where_value}' order by check_id limit {offset}, {psize}"
        else:
            sql = f"select * from check_info where {where_name}='{where_value}'"
        lesson_info = self.myQuery(sql)
        return lesson_info

    def getFileName(self, check_id, config_id):
        try:
            sql = f"select check_id,file_id from file_info where state='uploaded' and check_id={check_id} " \
                  f"and config_id = {config_id}"
            file_name = self.myQuery(sql)
        except Exception as e:
            return '0', str(e)
        return '1', file_name

    def addLesson(self, lesson_info=''):
        try:
            # 查询是否已存在相同的课堂
            check_sql = f"SELECT COUNT(*) FROM class WHERE name = '{lesson_info[2]}'"
            existing_class = self.myQuery(check_sql)  # 查询数据库

            if existing_class[0][0] > 0:  # 如果查询到数据，说明课堂已存在
                return '2', '课堂已存在'
            sql = f"insert into class(uid,config_id,name,time,start,end,description) values" "('{}','{}','{}','{}','{}','{}','{}')".format(
                lesson_info[0], lesson_info[1], lesson_info[2], lesson_info[3], lesson_info[4], lesson_info[5],
                lesson_info[6])
            result = self.myExecuteSqlwithid(sql)
            if isinstance(result, int):
                return '1', result
            else:
                return '0', result
        except Exception as e:
            return '0', str(e)

    def addLessonContent(self, class_id='', file_id='', user_id='', check_id='', purpose=''):
        try:
            for j in range(len(file_id)):
                for i in range(len(user_id)):
                    sql = f"insert into content values('{class_id}','{check_id}',{file_id[j]},'{user_id[i]}','{purpose}')"
                    result = self.myExecuteSql(sql)
                    if result != '':
                        return '0', result
            return '1', 'result'
        except Exception as e:
            return '0', str(e)

    def addLessonStudent(self, class_id='', student_id=''):
        try:
            for i in range(len(student_id)):
                sql = f"insert into student values('{class_id}','{student_id[i]}','beforeStudy','{0}')"
                result = self.myExecuteSql(sql)
                if result != '':
                    return '0', result
            return '1', ''
        except Exception as e:
            return '0', str(e)

    def delLesson(self, where_name, where_value):
        try:
            sql = "delete from class where {} = '{}'".format(where_name, where_value)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def delLessonStudent(self, where_name, where_value, flag=None):
        try:
            if flag == None:
                sql = "delete from student where {} = '{}'".format(where_name, where_value)
                tag = self.myExecuteSql(sql)
                if tag == '':
                    return '1', str(tag)
                else:
                    return '0', str(tag)
            else:
                for i in range(len(where_value)):
                    sql = "delete from student where class_id = '{}' AND uid = {}".format(where_name, where_value[i])
                    tag = self.myExecuteSql(sql)
                    if tag != '':
                        return '0', str(tag)
                return '1', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def delLessonContent(self, where_name='', where_value='', flag=None):
        try:
            if flag == 1:
                for info in where_value:
                    sql = "delete from content where class_id = '{}' AND check_id = '{}' AND " \
                          "file_id = '{}' AND uid = '{}' AND purpose = '{}'". \
                        format(info[0], info[1], info[3][0], info[2], info[4])
                    tag = self.myExecuteSql(sql)
                    if tag != '':
                        return '0', str(tag)
                return '1', ''
            else:
                sql = "delete from content where {} = '{}'".format(where_name, where_value)
                tag = self.myExecuteSql(sql)
                if tag == '':
                    return '1', str(tag)
                else:
                    return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def updateLesson(self, class_id, user_id, config_id, lessonInfo):
        try:
            sql = "update class set name = '{}', description = '{}',start = '{}',end = '{}',time = '{}' where class_id = '{}' AND uid = '{}' AND config_id = '{}'".format(
                lessonInfo[1], lessonInfo[5],
                lessonInfo[3], lessonInfo[4], lessonInfo[2], class_id, user_id, config_id)
            tag = self.myExecuteSql(sql)
            if tag == "":
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def getStudentInfo(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select * from student"
        else:
            sql = f"select * from student where {where_name}='{where_value}'"
        student_info = self.myQuery(sql)
        return student_info

    def getContentInfo(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select * from content"
        else:
            sql = f"select * from content where {where_name}='{where_value}'"
        content_info = self.myQuery(sql)
        print(content_info)
        return content_info

    def getClassContentTestInfo(self, class_id):
        sql = f"SELECT check_id, file_id, uid FROM content WHERE class_id = {class_id} AND purpose = 'test'"

        content_info = self.myQuery(sql)  # 执行查询
        print(content_info)



        return content_info

    def getContentPurpose(self, where_name='', where_value=''):
        sql = f"select class_id, purpose from content where {where_name}='{where_value}'"
        content_info = self.myQuery(sql)
        print(content_info)
        return content_info

    def getCheckUserID(self, check_id=''):
        sql = f"select check_id, uid from diag where check_id ='{check_id}' "
        user_info = self.myQuery(sql)
        return user_info

    def getCheckID(self, where_name='', where_value=''):
        sql = f"select * from check_info where {where_name} ='{where_value}' "
        user_info = self.myQuery(sql)
        return user_info

    def getCheckNumberbyID(self, where_name='', where_value=''):
        sql = f"select check_number from check_info where {where_name} ='{where_value}' "
        check_number = self.myQuery(sql)
        return check_number

    def getStudentInfobyPage(self, where_value='', offset='', psize='', where_name='', where_like=''):
        if where_name != '':
            sql = f"select * from user_info where student = '1' and {where_name} like '%{where_like}%' and user_info.uid not in (select uid from student where class_id = " \
                  f"{where_value}) order by uid limit {offset}, {psize}"
        else:
            sql = f"select * from user_info where student = '1' and  user_info.uid not in (select uid from student where class_id = " \
                  f"{where_value}) order by uid limit {offset}, {psize}"
        student_info = self.myQuery(sql)
        return student_info

    def getEegInfobyPage(self, offset='', psize='', where_name='', where_like=''):
        if where_name == 'check_number':
            sql = f"select * from check_info where state = 'diagnosed' and {where_name} like '%{where_like}%' " \
                  f"order by check_id limit {offset}, {psize}"
        elif where_name == 'patient_id':
            sql = f"select * from check_info where state = 'diagnosed' and check_info.patient_id in (select patient_id from patient_info where name like '%{where_like}%') " \
                  f"order by check_id limit {offset}, {psize}"
        elif where_name == 'pUid':
            sql = f"select * from check_info where state = 'diagnosed' and check_info.pUid in (select uid from user_info where name like '%{where_like}%') " \
                  f"order by check_id limit {offset}, {psize}"
        else:
            sql = f"select * from check_info where state = 'diagnosed' order by check_id limit {offset},{psize}"
        eeg_info = self.myQuery(sql)
        return eeg_info

    def getCheckLen(self, where_name='', where_like=''):
        if where_name == '':
            sql = f"select count(*) from check_info where state = 'diagnosed'"
        elif where_name == 'patient_id':
            sql = f"select count(*) from check_info where state = 'diagnosed' and check_info.patient_id in (select patient_id from patient_info where name like '%{where_like}%') "
        elif where_name == 'pUid':
            sql = f"select count(*) from check_info where state = 'diagnosed' and check_info.pUid in (select uid from user_info where name like '%{where_like}%') "
        else:
            sql = f"select count(*) from check_info where state = 'diagnosed' and {where_name} like '%{where_like}%'"
        len = self.myQuery(sql)
        return len

    def getStudentLen(self, where_value='', where_name='', where_like=''):
        if where_value != '':
            sql = f"select count(*) from student where class_id = {where_value}"
        elif where_name != '':
            sql = f"select count(*) from user_info where student = '1' and {where_name} like '%{where_like}%'"
        else:
            sql = f"select count(*) from user_info where student = '1'"
        len = self.myQuery(sql)
        return len

    def getSpecificInfo(self, condition=''):
        try:
            sql = f"select distinct type_id, type_name from type_info {condition}"
            print(f'getSpecificInfo sql: {sql}')
            specificInfo = self.myQuery(sql)
            return specificInfo
        except Exception as e:
            print('getSpecificInfo', e)

    def getSpecificNum(self, table, where_value, is_Evaluate=False):
        try:
            if table == 'sample_info':
                sql = "select  e.type_name ,count(*) from {} as a left join type_info " \
                      "as e on a.type_id = e.type_id where {} group by a.type_id".format(table, where_value)
            elif table == 'resLab':
                sql = "select  e.type_name ,count(*) from {} as a left join type_info " \
                      "as e on a.type_id = e.type_id where {} group by a.type_id".format(table, where_value)
            elif table == 'label_info':
                if is_Evaluate is False:
                    sql = "select  e.type_name ,count(*) from {} as a left join type_info " \
                          "as e on a.mtype_id = e.type_id where {} group by a.mtype_id".format(table, where_value)
                else:
                    sql = "select  e.type_name ,count(*) from {} as a left join type_info " \
                          "as e on a.utype_id = e.type_id where utype_id != '' and {} " \
                          "group by a.utype_id".format(table, where_value)
            print(f'getSpecificInfo sql: {sql}')
            specificInfo = self.myQuery(sql)
            return specificInfo
        except Exception as e:
            print('getSpecificInfo', e)

    def getFilterItemByTypeInfo(self, select_name='', from_name='', left_s='', on_s='', type_name='',
                                other_restrict='', is_union=False):
        filter_info = list()
        sql = "select distinct {} from {} as a {} left join type_info as c on {} where c.type_name = '{}' ".format(
            select_name, from_name, left_s, on_s, type_name) + other_restrict
        if is_union:
            sql = sql + ' union ' + sql.replace('sample_info', 'label_info').replace('b.type_id', 'mtype_id')
        print(f'getFilterItemByTypeInfo sql: {sql}')
        specificInfo = self.myQuery(sql)

        if len(specificInfo) == 0:
            return []

        if len(specificInfo[0]) == 2:
            info = {}
            for item in specificInfo:
                if item[0] in info:
                    # 如果键存在，将新值添加到对应的列表中
                    info[item[0]].append(item[1])
                else:
                    # 如果键不存在，添加新的键值对，其中值是包含新值的列表
                    info[item[0]] = [item[1]]
            return info
        else:
            for i in specificInfo:
                filter_info.append(i[0])
            return filter_info

    def getFilterItemByTypeInfoeeg(self, source, type_name, maxSample=1, minSample=0, themeInfo=[],file_type=''):
        msg = {}
        if '诊断标注' in source:
            if msg.get('user') is not None:
                msg['user'] += " union "
                msg['patientName'] += " union "
                msg['measureDate'] += " union "
                msg['fileName'] += " union "
            else:
                msg['user'] = ""
                msg['patientName'] = ""
                msg['measureDate'] = ""
                msg['fileName'] = ""
            # 找到属于type_name 的活动 且活动持续时间在  minSample到 maxSample 单位时间内的用户的 uid 和 account 信息
            msg['user'] += f"select distinct a.uid, a.account from user_info as a " \
                           f"left join sample_info as b on a.uid = b.uid " \
                           f"left join type_info as c on b.type_id = c.type_id " \
                           f"LEFT JOIN file_info AS e ON b.check_id = e.check_id " \
                           f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                           f"and c.type_name = '{type_name}'" \
                           f"AND e.type = '{file_type}'"
            #同样通过内连接（patient_info表和check_info中表的patient_id关联,sample_info和check_info的check_id关联）,找到条件内病人id和名字
            msg['patientName'] += f"select distinct a.patient_id, a.name from patient_info as a " \
                                  f"Join check_info AS ci ON a.patient_id = ci.patient_id " \
                                  f"Join sample_info as b on ci.check_id = b.check_id " \
                                  f"left join type_info as c on b.type_id = c.type_id " \
                                  f"JOIN file_info AS e ON b.check_id = e.check_id " \
                                  f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                                  f"and c.type_name = '{type_name}' " \
                                  f"AND e.type = '{file_type}'"

            msg[
                'fileName'] += f"select distinct d.`name`, CONCAT(a.check_number, '-', b.file_id), a.check_id, b.file_id from check_info as a " \
                               f"JOIN sample_info as b on b.check_id = a.check_id " \
                               f"left join patient_info as d on d.patient_id = a.patient_id " \
                               f"left join file_info as e on e.check_id = a.check_id " \
                               f"left join type_info as c on b.type_id = c.type_id " \
                               f"LEFT JOIN file_info AS f ON b.check_id = e.check_id " \
                               f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                               f"and c.type_name = '{type_name}' " \
                               f"AND e.type = '{file_type}'"

            msg['measureDate'] += f"select distinct a.measure_date from check_info as a " \
                                  f"JOIN sample_info as b on b.check_id = a.check_id " \
                                  f"left join type_info as c on b.type_id = c.type_id " \
                                  f"LEFT JOIN file_info AS e ON b.check_id = e.check_id " \
                                  f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                                  f"and c.type_name = '{type_name}' " \
                                  f"AND e.type = '{file_type}'"

        if '科研标注' in source:
            theme_str = ', '.join(f"{theme}" for theme in themeInfo)

            if msg.get('user') is not None:
                msg['user'] += " union "
                msg['patientName'] += " union "
                msg['measureDate'] += " union "
                msg['fileName'] += " union "
            else:
                msg['user'] = ""
                msg['patientName'] = ""
                msg['measureDate'] = ""
                msg['fileName'] = ""
            msg['user'] += f"select distinct a.uid, a.account from user_info as a " \
                           f"left join reslab as b on a.uid = b.uid " \
                           f"left join type_info as c on b.type_id = c.type_id " \
                           f"LEFT JOIN file_info AS e ON b.check_id = e.check_id " \
                           f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                           f"and c.type_name = '{type_name}'" \
                           f"AND b.theme_id IN ({theme_str}) " \
                           f"AND e.type = '{file_type}'"
            msg['patientName'] += f"select distinct a.patient_id, a.name from patient_info as a " \
                                  f"Join check_info AS ci ON a.patient_id = ci.patient_id " \
                                  f"left join task as t on t.check_id = ci.check_id " \
                                  f"Join reslab as b on t.theme_id = b.theme_id " \
                                  f"left join type_info as c on b.type_id = c.type_id " \
                                  f"LEFT JOIN file_info AS e ON b.check_id = e.check_id " \
                                  f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                                  f"and c.type_name = '{type_name}'" \
                                  f"AND b.theme_id IN ({theme_str}) " \
                                  f"AND e.type = '{file_type}'"

            msg[
                'fileName'] += f"select distinct d.`name`, CONCAT(a.check_number, '-', t.file_id), a.check_id, t.file_id from check_info as a " \
                               f"left join task as t on t.check_id = a.check_id " \
                               f"JOIN reslab as b on b.theme_id = t.theme_id " \
                               f"left join patient_info as d on d.patient_id = a.patient_id " \
                               f"left join file_info as e on e.check_id = a.check_id " \
                               f"left join type_info as c on b.type_id = c.type_id " \
                               f"LEFT JOIN file_info AS f ON b.check_id = e.check_id " \
                               f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                               f"and c.type_name = '{type_name}'" \
                               f"AND b.theme_id IN ({theme_str}) " \
                               f"AND f.type = '{file_type}'"

            msg['measureDate'] += f"select distinct a.measure_date from check_info as a " \
                                  f"left join task as t on t.check_id = a.check_id " \
                                  f"JOIN reslab as b on b.theme_id = t.theme_id  " \
                                  f"left join type_info as c on b.type_id = c.type_id " \
                                  f"LEFT JOIN file_info AS e ON b.check_id = e.check_id " \
                                  f"where (b.end - b.begin) >= {minSample} and (b.end - b.begin) <= {maxSample} " \
                                  f"and c.type_name = '{type_name}'" \
                                  f"AND b.theme_id IN ({theme_str}) " \
                                  f"AND e.type = '{file_type}'"

        if '自动标注' in source:
            if msg.get('user') is not None:
                msg['user'] += " union "
                msg['patientName'] += " union "
                msg['measureDate'] += " union "
                msg['fileName'] += " union "
            else:
                msg['user'] = ""
                msg['patientName'] = ""
                msg['measureDate'] = ""
                msg['fileName'] = ""

        result = {}
        for key, sql in msg.items():
            print(f'getFilterItemByTypeInfoeeg sql: {sql}')
            filter_info = self.myQuery(sql)
            print(f'key: {key}, attr: {filter_info}')

            if len(filter_info) == 0:
                return []

            if key == 'fileName':
                info = {}
                for item in filter_info:
                    if item[0] in info:
                        # 如果键存在，将新值添加到对应的列表中
                        info[item[0]].append((item[1], (item[2], item[3])))
                    else:
                        # 如果键不存在，添加新的键值对，其中值是包含新值的列表
                        info[item[0]] = [(item[1], (item[2], item[3]))]
                result[key] = info
            else:
                result[key] = filter_info
        return result

    def getPosIndexList(self, check_id, file_id, sample, minSample, channels, flt_list, type, theme_id):
        try:
            if len(theme_id) == 0 or theme_id == None:
                if type == 'wave':
                    tempChannels = channels
                else:
                    tempChannels = ['all']
                channels_placeholders = ', '.join(['%s'] * len(tempChannels))
                flt_placeholders = ', '.join(['(%s, %s)'] * len(flt_list))
                sql = f"""
                    SELECT begin, end, channel, type_id
                    FROM sample_info
                    WHERE (check_id, file_id) = (%s, %s)
                      AND channel IN ({channels_placeholders})
                      AND (uid, type_id) IN ({flt_placeholders})
                      AND (end - begin) BETWEEN %s AND %s
                    """
                # channels_str = ', '.join(f"'{channel}'" for channel in tempChannels)
                # flt_list_str = ', '.join(f"({uid}, {type_id})" for uid, type_id in flt_list)
                # sql = f"""
                # SELECT begin, end, channel, type_id
                # FROM sample_info
                # WHERE (check_id, file_id) = ({check_id}, {file_id})
                #   AND channel IN ({channels_str})
                #   AND (uid, type_id) IN ({flt_list_str})
                #   AND (end - begin) BETWEEN {minSample} AND {sample}
                # """
            else:
                if type == 'wave':
                    tempChannels = channels
                else:
                    tempChannels = ['all']
                check_file_placeholders = '(%s, %s)'
                channels_placeholders = ', '.join(['%s'] * len(tempChannels))
                flt_placeholders = ', '.join(['(%s, %s)'] * len(flt_list))
                sql = f"""
                    SELECT begin, end, channel, type_id
                    FROM reslab AS a
                    LEFT JOIN task AS b ON a.theme_id = b.theme_id
                    WHERE (b.check_id, b.file_id) = ({check_file_placeholders})
                      AND channel IN ({channels_placeholders})
                      AND (a.uid, type_id) IN ({flt_placeholders})
                      AND (end - begin) BETWEEN %s AND %s
                    """
                # channels_str = ', '.join(f"'{channel}'" for channel in tempChannels)
                # flt_list_str = ', '.join(f"({uid}, {type_id})" for uid, type_id in flt_list)
                # sql = f"""
                # SELECT begin, end, channel, type_id
                # FROM reslab as a left join task as b on a.theme_id = b.theme_id
                # WHERE (b.check_id, b.file_id) = ({check_id}, {file_id})
                #   AND channel IN ({channels_str})
                #   AND (a.uid, type_id) IN ({flt_list_str})
                #   AND (end - begin) BETWEEN {minSample} AND {sample}
                # """
            params = (
                check_id, file_id,  # (b.check_id, b.file_id)
                *tempChannels,  # channel IN
                *sum(flt_list, ()),  # (a.uid, type_id) IN 展开
                minSample, sample  # (end - begin) BETWEEN
            )
            setInfo = self.myExecuteSqlWithParm(sql, params)
            print(f'getPosIndexList sql: {sql}')
            # setInfo = self.myQuery(sql)
            return setInfo
        except Exception as e:
            print('getPosIndexList', e)

    def getSampleNumWithFlts(self, type_name, search_col, search_value, search_table, isFromEvaluate=False,
                             base_search_scope='', base_join_scope=''):
        search_list = ''
        value_list = ''
        sql = ''
        left_join_centence = ''
        if search_table == 'sample_info':
            sql = "select {} from check_info as a JOIN {} as si on si.check_id = a.check_id left join type_info as d on si.type_id = d.type_id "
        elif search_table == 'resLab':
            sql = "select {} from check_info as a JOIN {} as si on si.check_id = a.check_id left join type_info as d on si.type_id = d.type_id "
        elif search_table == 'label_info':
            if isFromEvaluate is False:
                sql = "select {} from check_info as a JOIN {} as si on si.check_id = a.check_id left join type_info as d on si.mtype_id = d.type_id "
            else:
                sql = "select {} from check_info as a JOIN {} as si on si.check_id = a.check_id left join type_info as d on si.mtype_id = d.type_id "

        j = 0
        for i in search_col:
            if i == 'patient_id':
                search_list = 'b.name'
                if len(search_value[0]) > 1:
                    value_list = 'a.patient_id in {}'.format(tuple(search_value[0]))
                else:
                    value_list = 'a.patient_id = {}'.format(search_value[0][0])
                if j != len(search_col) - 1:
                    left_join_centence += 'left join patient_info as b on a.patient_id = b.patient_id '
                else:
                    left_join_centence += 'left join patient_info as b on a.patient_id = b.patient_id'

                # sql += left_join_centence
                j += 1
                continue
            elif i == 'account':
                if j == 0:
                    search_list = 'c.account'
                    if len(search_value[j]) > 1:
                        value_list = "c.account in {}".format(tuple(search_value[j]))
                    else:
                        value_list = "c.account = '{}'".format(search_value[j][0])
                else:
                    search_list += ', c.account'
                    if len(search_value[j]) > 1:
                        value_list += " and c.account in {}".format(tuple(search_value[j]))
                    else:
                        value_list += " and c.account = '{}'".format(search_value[j][0])
                if j != len(search_col) - 1:
                    left_join_centence += 'left join user_info as c on a.cUid = c.uid '
                else:
                    left_join_centence += 'left join user_info as c on a.cUid = c.uid'

                # sql += left_join_centence
                j += 1
                continue
            elif i == 'mid':
                if j == 0:
                    search_list = 'e.classifier_name'
                    if len(search_value[j]) > 1:
                        value_list = "e.classifier_id in {}".format(tuple(search_value[j]))
                    else:
                        value_list = "e.classifier_id = '{}'".format(search_value[j][0])
                else:
                    search_list += ', e.classifier_name'
                    if len(search_value[j]) > 1:
                        value_list += " and e.classifier_id in {}".format(tuple(search_value[j]))
                    else:
                        value_list += " and e.classifier_id = '{}'".format(search_value[j][0])
                if j != len(search_col) - 1:
                    left_join_centence += 'left join classifier_info as e on a.mid = e.classifier_id '
                else:
                    left_join_centence += 'left join classifier_info as e on a.mid = e.classifier_id'

                # sql += left_join_centence
                j += 1
                continue
            elif i == 'type_name':
                if j == 0:
                    search_list = 'f.type_name'
                    if len(search_value[j]) > 1:
                        value_list = "f.type_name in {}".format(tuple(search_value[j]))
                    else:
                        value_list = "f.type_name = '{}'".format(search_value[j][0])
                else:
                    search_list += ', f.type_name'
                    if len(search_value[j]) > 1:
                        value_list += " and f.type_name in {}".format(tuple(search_value[j]))
                    else:
                        value_list += " and f.type_name = '{}'".format(search_value[j][0])
                if j != len(search_col) - 1:
                    left_join_centence += 'left join type_info as f on a.mtype_id = f.type_id '
                else:
                    left_join_centence += 'left join type_info as f on a.mtype_id = f.type_id'

                # sql += left_join_centence
                j += 1
                continue
            elif i == 'tag':
                print(search_value[j])
                if j == 0:
                    if search_value[j] == '符合':
                        value_list += "a.mtype_id = a.utype_id"
                    elif search_value[j] == '不符合':
                        value_list += "a.mtype_id != a.utype_id"
                else:
                    if search_value[j] == '符合':
                        value_list += " and a.mtype_id = a.utype_id"
                    elif search_value[j] == '不符合':
                        value_list += " and a.mtype_id != a.utype_id"
                j += 1
                continue
            if j == 0:
                search_list = i
                if len(search_value[j]) > 1:
                    value_list = "{} in {}".format(i, tuple(search_value[j]))
                else:
                    value_list = "{} = '{}'".format(i, search_value[j][0])
            else:
                search_list += ", " + i
                if len(search_value[j]) > 1:
                    value_list += ' and {} in {}'.format(i, tuple(search_value[j]))
                else:
                    value_list += " and {} = '{}'".format(i, search_value[j][0])
            j += 1
        # print(left_join_centence)
        # print(base_join_scope)
        final_left = ''
        if base_join_scope != '':
            base_join_list = base_join_scope.split('left join')
            left_join_list = left_join_centence.split('left join')
            left_set = set()
            for i in base_join_list:
                left_set.add(i.strip())
            for i in left_join_list:
                left_set.add(i.strip())
            left_set.remove('')
            # print(left_set)
            j = 0
            for i in left_set:
                if j == 0:
                    final_left += 'left join ' + i
                else:
                    final_left += ' left join ' + i
                j += 1
        else:
            final_left = left_join_centence
        # print(final_left)
        # print(search_list)
        if len(search_list) != 0:
            sql = sql.format(search_list + ', count(*) ', search_table) + final_left
            if base_search_scope != '':
                sql += " where d.type_name = '{}' and ".format(type_name) + base_search_scope + ' and ' + value_list
            else:
                sql += " where d.type_name = '{}' and ".format(type_name) + value_list

            sql += ' group by ' + search_list
        else:
            sql = sql.format('count(*) ', search_table) + final_left
            if base_search_scope != '':
                sql += " where d.type_name = '{}' and ".format(type_name) + base_search_scope + ' and ' + value_list
            else:
                sql += " where d.type_name = '{}' and ".format(type_name) + value_list
        # print(value_list)

        print('sql:')
        print(sql)
        sampleDetail = self.myQuery(sql)
        print('sampleDetail:')
        print(sampleDetail)
        return sampleDetail

    def getSetBuildInfo(self, selColumn='*', after=''):
        try:
            sql = f"select {selColumn} from {after}"
            print(f'getSetInfo sql: {sql}')
            setInfo = self.myQuery(sql)
            return setInfo
        except Exception as e:
            print('getSpecificInfo', e)

    def getSetExportInitData(self, selColumn='*', where_name='', where_value=''):
        try:
            if where_name == '':
                sql = f"select {selColumn} from set_info"
            else:
                sql = f"select {selColumn} from set_info where {where_name}={where_value}"
            content_info = self.myQuery(sql)
            print(content_info)
            return content_info
        except Exception as e:
            print('getSetExportInitData', e)

    def delSet(self, where_value):
        try:
            sql = f'DELETE FROM set_info WHERE set_id = {where_value};'
            print(f'delSet sql: {sql}')
            tag = self.myExecuteSql(sql)
            if tag == "":
                return True
            else:
                return False
        except Exception as e:
            print('delSet', e)
            return False

    def addSet(self, setInfo):
        try:
            # sql = f"insert into " \
            #       f"set_info(set_name, config_id, description, filename_trainingset, filename_testset) " \
            #       f"values ('{setInfo[1]}', {setInfo[2]}, '{setInfo[3]}', '{setInfo[4]}', '{setInfo[5]}')"
            sql = """
                    INSERT INTO set_info 
                    (set_name, config_id, description, filename_trainingset, filename_testset) 
                    VALUES (%s, %s, %s, %s, %s)
                    """
            # 参数按顺序传递（确保与占位符顺序一致）
            params = (
                setInfo[1],  # set_name
                setInfo[2],  # config_id
                setInfo[3],  # description（自动处理单引号转义）
                setInfo[4],  # filename_trainingset
                setInfo[5]  # filename_testset
            )
            print(f'addSet sql: {sql}')
            result = self.execute_update(sql, params)
            # result = self.myExecuteSql(sql)
            if result != '':
                return '0', result
            else:
                return '1', ''
        except Exception as e:
            print('addSet', e)
            return '0', result

    def get_sample(self, sql_list):
        try:
            temp = ''
            if len(sql_list) == 1:
                temp = sql_list[0] + ' order by file_name'
            else:
                i = 0
                for sql in sql_list:
                    if i != len(sql_list) - 1:
                        temp += sql + ' union all '
                    else:
                        temp += sql + ' order by file_name'
                    i += 1
            sample = self.myQuery(temp)
            print(f'get_sample sql: {temp}')
            return sample
        except Exception as e:
            print('get_sample', e)

    def ReverseSample_check(self, check_list):
        print(f'ReverseSample_check check_list: {check_list}')
        try:
            checkNumber = check_list[0].split('-')[0]
            fileID = check_list[0].split('-')[1]
            # file_name = check_list[0]
            begin = check_list[1]
            end = check_list[2]
            montage = check_list[3]
            search_table = ['sample_info', 'label_info', 'resLab']
            sample_sql1 = "select CONCAT(e.check_number, '-', file_id) as file_name, begin, end, channel, type_name, a.type_id, 'sample_info' as tableFrom from {} as a " \
                          "left join check_info as e on e.check_id = a.check_id " \
                          "left join type_info as b on a.type_id = b.type_id " \
                          "left join user_info as c on a.uid = c.uid " \
                          "where check_number = {} and file_id = {} and channel = '{}' " \
                          "and ((begin <= {} and end>={} and end <={}) " \
                          "or (end >= {} and begin >={} and begin <={}) " \
                          "or (begin >= {} and end <={}))".format(search_table[0], checkNumber, fileID, montage
                                                                  , begin, begin, end, end, begin, end, begin, end)
            print(sample_sql1)
            sample1 = self.myQuery(sample_sql1)
            sample_sql2 = "select CONCAT(e.check_number, '-', file_id) as file_name, begin, end, channel, type_name, a.mtype_id, 'label_info' as tableFrom from {} as a " \
                          "left join check_info as e on e.check_id = a.check_id " \
                          "left join type_info as b on a.mtype_id = b.type_id " \
                          "left join user_info as c on a.uid = c.uid " \
                          "where check_number = {} and file_id = {} and channel = '{}' " \
                          "and ((begin <= {} and end>= {} and end <= {}) " \
                          "or (end >= {} and begin >= {} and begin <= {}) " \
                          "or (begin >= {} and end <= {}))".format(search_table[1], checkNumber, fileID, montage
                                                                   , begin, begin, end, end, begin, end, begin, end)
            sample2 = self.myQuery(sample_sql2)
            print(sample_sql2)

            sample_sql3 = "select CONCAT(f.check_number, '-', e.file_id) as file_name, begin, end, channel, type_name, a.type_id, 'resLab' as tableFrom from {} as a " \
                          "left join task as e on e.theme_id = a.theme_id " \
                          "left join check_info as f on f.check_id = e.check_id " \
                          "left join type_info as b on a.type_id = b.type_id " \
                          "left join user_info as c on a.uid = c.uid " \
                          "where check_number = {} and file_id = {} and channel = '{}' " \
                          "and ((begin <= {} and end>= {} and end <= {}) " \
                          "or (end >= {} and begin >= {} and begin <= {}) " \
                          "or (begin >= {} and end <= {}))".format(search_table[2], checkNumber,
                                                                   fileID, montage, begin, begin, end, end, begin, end,
                                                                   begin, end)
            sample3 = self.myQuery(sample_sql3)
            print(sample_sql3)
            sample1.extend(sample3)
            print(f'sample1: {sample1}')
            return sample1
        except Exception as e:
            print('get_sample', e)

    def getNegativeScheme(self, column='*', where_name='', where_value=''):
        try:
            if where_name == '':
                sql = f"select {column} from classifier"
            else:
                sql = f"select {column} from classifier where `{where_name}`='{where_value}'"
            print(f'getNegativeScheme sql: {sql}')
            setInfo = self.myQuery(sql)
            return setInfo
        except Exception as e:
            print('getNegativeScheme', e)

    # 算法管理

    def getAlgorithmInfo(self, where_name='', where_value='', where_like='', where_state='', state=''):
        if where_name == '':
            sql = "select * from algorithm"
        elif where_like != '':
            sql = f"select * from algorithm where {where_name} like '%{where_like}%'"
        elif where_state != '':
            sql = f"select * from algorithm where {where_name}='{where_value}'and {where_state}!='{state}'"
        else:
            sql = f"select * from algorithm where {where_name}='{where_value}'"
        algorithm_info = self.myQuery(sql)
        return algorithm_info

    def getAlgorithmInfoByPage(self, offset='', psize=''):
        sql = f"select * from algorithm limit {offset}, {psize}"
        algorithm_info = self.myQuery(sql)
        return algorithm_info

    def getAlgorithmInfoLen(self, where_name='', where_like=''):
        if where_name == 'alg_name':
            sql = f"select count(*) from algorithm where {where_name} Like '%{where_like}%'"
        elif where_name == 'type':
            sql = f"select count(*) from algorithm where {where_name} = '{where_like}' "
        else:
            sql = " select count(*) from algorithm "
        len = self.myQuery(sql)
        return len

    def getSearchAlgorithmInfoByPage(self, where_name, where_value, offset='', psize=''):
        if where_name == 'alg_name':
            sql = f"select * from algorithm where {where_name} like '%{where_value}%' order by alg_id " \
                  f" limit {offset}, {psize} "
        else:
            sql = f"select * from algorithm where {where_name} = '{where_value}' order by alg_id " \
                  f" limit {offset}, {psize} "
        algorithm_info = self.myQuery(sql)
        return algorithm_info

    def delAlgorithmInfo(self, where_name, where_value):
        try:
            sql = "delete from algorithm where {} = '{}'".format(where_name, where_value)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def addAlgorithmInfo(self, alg_info=''):
        try:
            sql = f"insert into algorithm (alg_name,training_para,test_para,predict_para, type)" \
                  f" values" "('{}','{}','{}','{}', '{}')".format(alg_info['alg_name'], alg_info['training_para'],
                                                                  alg_info['test_para'], alg_info['predict_para'],
                                                                  alg_info['alg_type'])
            result = self.myExecuteSqlwithid(sql)
            if isinstance(result, int):
                return '1', result
            else:
                return '0', result
        except Exception as e:
            return '0', str(e)

    def updateAlgorithmInfo(self, alg_info, alg_id, state='', mac='', flag=None):
        try:
            if state == 'start' and flag == 1:
                sql = "update algorithm set training_state = '{}',training_block_id = '{}',training_mac = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_info[1], mac, alg_id)
            elif state == 'start' and flag == 2:
                sql = "update algorithm set test_state = '{}',test_block_id = '{}',test_mac = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_info[1], mac, alg_id)
            elif state == 'start' and flag == 3:
                sql = "update algorithm set predict_state = '{}',predict_block_id = '{}',predict_mac = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_info[1], mac, alg_id)
            elif state == 'uploaded' and flag == 1:
                sql = "update algorithm set training_state = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_id)
            elif state == 'uploaded' and flag == 2:
                sql = "update algorithm set test_state = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_id)
            elif state == 'uploaded' and flag == 3:
                sql = "update algorithm set predict_state = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_id)
            elif state == '' and flag == 1:
                sql = "update algorithm set training_state = '{}',training_block_id = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_info[1], alg_id)
            elif state == '' and flag == 2:
                sql = "update algorithm set test_state = '{}',test_block_id = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_info[1], alg_id)
            elif state == '' and flag == 3:
                sql = "update algorithm set predict_state = '{}',predict_block_id = '{}'" \
                      " where alg_id = '{}'".format(alg_info[0], alg_info[1], alg_id)
            else:
                sql = "update algorithm set training_filename = '{}', training_state = '{}',test_filename = '{}'," \
                      "test_state = '{}',predict_filename = '{}',predict_state = '{}' where alg_id = '{}'".format(
                    alg_info[0], alg_info[1], alg_info[2], alg_info[3], alg_info[4], alg_info[5], alg_id)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def recoverAlgorithmInfo(self, alg_id, state):
        try:
            if state == 'training':
                sql = "update algorithm set training_state = '{}',training_block_id = '{}'" \
                      " where alg_id = '{}'".format('ready', 0, alg_id)
            if state == 'test':
                sql = "update algorithm set test_state = '{}',test_block_id = '{}'" \
                      " where alg_id = '{}'".format('ready', 0, alg_id)
            if state == 'predict':
                sql = "update algorithm set predict_state = '{}',predict_block_id = '{}'" \
                      " where alg_id = '{}'".format('ready', 0, alg_id)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def getAlgorithmFileName(self, alg_id='', training_state='', test_state='', predict_state=''):
        if training_state != '':
            sql = f"select * from algorithm where alg_id ='{alg_id}' AND training_state = '{training_state}'"
        elif test_state != '':
            sql = f"select * from algorithm where alg_id ='{alg_id}' AND test_state = '{test_state}'"
        elif predict_state != '':
            sql = f"select * from algorithm where alg_id ='{alg_id}' AND predict_state = '{predict_state}'"
        algorithm_info = self.myQuery(sql)
        return algorithm_info

    # 模型训练

    def getsetLen(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select count(*) from set_info"
        else:
            sql = f"select count(*) from set_info where {where_name} like '%{where_value}%'"
        set_info = self.myQuery(sql)
        return set_info

    def get_set_info_by_page(self, offset='', psize=''):
        sql = f"select * from set_info limit {offset}, {psize}"
        set_info = self.myQuery(sql)
        return set_info

    def getSearchSetInfoByPage(self, where_name, where_value, offset='', psize=''):
        sql = f"select * from set_info where {where_name} like '%{where_value}%' order by set_id limit {offset}, {psize}"
        set_info = self.myQuery(sql)
        return set_info

    def get_set_info(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select * from set_info"
        else:
            sql = f"select * from set_info where {where_name}='{where_value}'"
        set_info = self.myQuery(sql)
        return set_info

    def getclassifierInfo_1(self, where_name='', where_value='', flag=None):
        if where_name == '':
            sql = "select * from classifier"
        elif flag == 1:
            sql = f"select * from classifier where alg_id={where_name[0]} AND set_id={where_name[1]} AND config_id={where_name[2]}"
        else:
            sql = f"select * from classifier where {where_name}='{where_value}'"
        classifier_info = self.myQuery(sql)
        return classifier_info

    def getclassifierInfoby_algid_setid(self, alg_id, set_id):
        sql = f"select * from classifier where alg_id = '{alg_id}', set_id = '{set_id}'"
        classifier_info = self.myQuery(sql)
        return classifier_info

    def addClassifierInfo(self, classifier_name, alg_id, set_id, filename, state, train_performance,
                          test_performance,
                          epoch_length, config_id, classifierUnit, channels):
        try:
            sql = "insert into classifier(classifier_name, alg_id, set_id, filename, state, train_performance, " \
                  "test_performance, epoch_length, config_id, classifierUnit, channels) values ('{}','{}',{},'{}','{}', '{}','{}','{}','{}', '{}', '{}')".format(
                classifier_name, alg_id, set_id, filename, state, train_performance, test_performance,
                int(epoch_length)
                , config_id, classifierUnit, channels)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def updateClassifierInfo(self, set_name, set_value, where_name, where_value):
        try:
            sql = "update classifier set {} = '{}' where {}='{}'".format(set_name, set_value, where_name,
                                                                         where_value)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)
    # 模型管理
    def get_classifier_alg_set_name(self, where_name='', where_value='',state_value='', fuzzy_search=False, count=''):
        if count == True:
            sql = "select count(*) from classifier"  # 返回行数
        elif where_name == '':
            sql = "select classifier_name, alg_name, set_name,epoch_length, classifierUnit,type, channels,train_performance, test_performance from classifier" \
                      " left join algorithm on classifier.alg_id = algorithm.alg_id left join set_info on " \
                      "classifier.set_id = set_info.set_id"
        else:
            if fuzzy_search:
                if where_value!='':
                    sql = "select classifier_name, alg_name, set_name,epoch_length, classifierUnit,type, channels,train_performance, test_performance from classifier" \
                            " left join algorithm on classifier.alg_id = algorithm.alg_id left join set_info on " \
                            "classifier.set_id = set_info.set_id where {} like '%{}%' and state ='{}'".format(where_name, where_value,state_value)
                else:
                    sql = "select classifier_name, alg_name, set_name,epoch_length, classifierUnit,type, channels,train_performance, test_performance from classifier" \
                          " left join algorithm on classifier.alg_id = algorithm.alg_id left join set_info on " \
                          "classifier.set_id = set_info.set_id where state ='{}'".format(state_value)
            else:
                sql = "select classifier_name, alg_name, set_name,train_performance, test_performance from classifier" \
                          " left join algorithm on classifier.alg_id = algorithm.alg_id left join set_info on " \
                          "classifier.set_id = set_info.set_id where {} = '{}'".format(where_name, where_value)
        cls_info = self.myQuery(sql)
        return cls_info
    def getClsInfoByPage(self, offset='', psize=''):
        sql = f"select classifier_name, alg_name, set_name,epoch_length, classifierUnit,type, channels,train_performance, test_performance from classifier " \
                  " left join algorithm on classifier.alg_id = algorithm.alg_id left join set_info on " \
                  "classifier.set_id = set_info.set_id limit {}, {}".format(offset, psize)
        cls_info = self.myQuery(sql)
        return cls_info
    def getalgorithmInfoByPage(self, where_name='', where_value='', offset='', psize=''):
        try:
            sql = f"select * from algorithm where {where_name}='{where_value}' limit {offset}, {psize}"
            algorithm_info = self.myQuery(sql)
            return algorithm_info
        except Exception as e:
            print(e)
    def get_classiferInfo_by_setId_and_algId(self, set_id, alg_id):
        sql = "select * from classifier where set_id = {} and alg_id = {}".format(set_id, alg_id)
        cls_info = self.myQuery(sql)
        return cls_info
    def delClassifierInfo(self, where_name, where_value):
        try:
            sql = "delete from classifier where {} = '{}'".format(where_name, where_value)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)
    def getMySetInfo(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select * from set_info"
        else:
            sql = f"select * from set_info where {where_name}='{where_value}'"
        set_info = self.myQuery(sql)
        return set_info
    def getclassifierInfo(self, where_name='', where_value='', flag=None):
        if where_name == '':
            sql = "select * from classifier"
        elif flag == 1:
            sql = f"select * from classifier where alg_id={where_name[0]} AND set_id={where_name[1]} AND config_id={where_name[2]}"
        else:
            sql = f"select * from classifier where {where_name}='{where_value}'"
        classifier_info = self.myQuery(sql)
        return classifier_info
    def add_init_ClassifierInfo(self, classifier_name='', alg_id='', set_id='', filename='', state='', train_performance='',
                                    test_performance='',
                                    epoch_length='', config_id='', channels='',mac='',classifierUnit=''):
        try:
            if filename=='':
                sql = "insert into classifier(classifier_name, alg_id, set_id, filename, mac, state, train_performance, " \
                        "test_performance, epoch_length, config_id,classifierUnit,channels) values ('{}',{},{},'{}','{}','{}', '{}','{}',{},{},'{}','{}')".format(
                        classifier_name, alg_id, set_id, filename, mac,state, train_performance, test_performance,
                        int(epoch_length), config_id, classifierUnit,channels)
            else:
                sql = "update classifier SET filename = '{}' where classifier_name ='{}'".format( filename,classifier_name)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)
    def getClsRecord(self, where_name='', where_value='', where_state='', state=''):
        try:
            sql = f"select * from classifier where {where_name}='{where_value}'and {where_state}='{state}'"
            classifier_info = self.myQuery(sql)
            return classifier_info
        except Exception as e:
            print(e)
    def update_trans_ClassifierInfo(self, set_name, set_value, where_name, where_value):
        try:
            sql = "update classifier set {} = '{}' where {}='{}'".format(set_name, set_value, where_name,
                                                                             where_value)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)
    def Inqcls_and_type(self, where_name='', where_like='', where_state='', state=''):
        try:
            sql = f"select * from algorithm where {where_name} like '%{where_like}%' and {where_state}='{state}'"
            algorithm_info = self.myQuery(sql)
            return algorithm_info
        except Exception as e:
            print(e)
    def Inqcls_set(self,where_type='',offset='',psize=''):
        try:
            if offset!='':
                sql = f"select * from set_info where JSON_EXTRACT(description, '$.type') = '{where_type}'limit {offset}, {psize} "
            else:
                sql = f"select * from set_info where JSON_EXTRACT(description, '$.type') = '{where_type}'"
            algorithm_info = self.myQuery(sql)
            return algorithm_info
        except Exception as e:
            print(e)
    def Inquiryset(self, where_name='', where_like='', where_type=''):
        try:
            sql = f"select * from set_info where {where_name} like '%{where_like}%' and JSON_EXTRACT(description, '$.type') = '{where_type}'"
            algorithm_info = self.myQuery(sql)
            return algorithm_info
        except Exception as e:
            print(e)
    def getsetInfoByPage(self, where_type='', offset='', psize=''):
        try:
            sql = f"select * from set_info where JSON_EXTRACT(description, '$.type') = '{where_type}' limit {offset}, {psize}"
            algorithm_info = self.myQuery(sql)
            return algorithm_info
        except Exception as e:
            print(e)
    def get_al_setInfo(self,where_table,where_name,where_value):
        try:
            sql = f"select * from {where_table} where {where_name}='{where_value}'"
            algorithm_info=self.myQuery(sql)
            return algorithm_info
        except Exception as e:
            print(e)

    # 模型测试
    def getClassifierCount(self, classifier_name):
        try:
            if classifier_name is None:
                sql = "SELECT COUNT(*) from classifier WHERE state IN (\'built\', \'uploaded\')"
            else:
                sql = "SELECT COUNT(*) from classifier WHERE classifier_name LIKE \'%{}%\' AND state IN (\'built\', \'uploaded\')".format(
                    classifier_name)
            return self.myQuery(sql)[0][0]
        except Exception as e:
            print("getClassifierCount", e)

    def getClassifierInfo(self, pageSize, page, classifier_name):
        try:
            if classifier_name is None:
                sql = "SELECT classifier.classifier_id, classifier.classifier_name, set_info.set_name, algorithm.alg_name, algorithm.test_para, algorithm.test_state, classifier.test_performance FROM classifier LEFT JOIN algorithm ON classifier.alg_id = algorithm.alg_id LEFT JOIN set_info ON classifier.set_id = set_info.set_id WHERE state IN (\'built\', \'uploaded\') LIMIT {}, {}".format(
                    (page - 1) * pageSize, pageSize)
            else:
                sql = "SELECT classifier.classifier_id, classifier.classifier_name, set_info.set_name, algorithm.alg_name, algorithm.test_para, algorithm.test_state, classifier.test_performance FROM classifier LEFT JOIN algorithm ON classifier.alg_id = algorithm.alg_id LEFT JOIN set_info ON classifier.set_id = set_info.set_id WHERE classifier.classifier_name LIKE \'%{}%\' AND state IN (\'built\', \'uploaded\') LIMIT {}, {}".format(
                    classifier_name, (page - 1) * pageSize, pageSize)
            return self.myQuery(sql)
        except Exception as e:
            print("getClassifierInfo", e)

    def getClassifierById(self, classifier_id):
        try:
            sql = 'select * from classifier where classifier_id = {}'.format(classifier_id)
            return self.myQuery(sql)[0]
        except Exception as e:
            print('getClassifierById', e)

    def getAlgorithmById(self, algorithm_id):
        try:
            sql = 'select * from algorithm where alg_id = {}'.format(algorithm_id)
            return self.myQuery(sql)[0]
        except Exception as e:
            print('getAlgorithmById', e)

    # 脑电扫描
    def get_patientNameId(self):
        sql = " select patient_id,name from patient_info "
        patient_info = self.myQuery(sql)
        return patient_info

    def getClassifierInfoLen(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select count(*) from classifier"
        else:
            sql = f"select count(*) from classifier where {where_name} like '%{where_value}%'"
        set_info = self.myQuery(sql)
        return set_info

    def getClassifierInfoByPage(self, offset='', psize=''):
        sql = f"select * from classifier limit {offset}, {psize}"
        classifier_info = self.myQuery(sql)
        ans = []
        for c in classifier_info:
            sql = f"select type from algorithm where alg_id = {c[2]}"
            type = self.myQuery(sql)[0][0]
            c = list(c)
            c.append(type)
            ans.append(c)
        return ans

    def getSearchClassifierInfoByPage(self, where_name, where_value, offset='', psize=''):
        sql = f"select * from classifier where {where_name} like '%{where_value}%' order by classifier_id limit {offset}, {psize}"
        classifier_info = self.myQuery(sql)
        ans = []
        for c in classifier_info:
            sql = f"select type from algorithm where alg_id = {c[2]}"
            type = self.myQuery(sql)[0][0]
            c = list(c)
            c.append(type)
            ans.append(c)
        return ans
        return set_info


    def get_measure_day(self, patient_id):
        sql = " select check_number, measure_date, check_id from check_info where patient_id = {}".format(patient_id)
        patient_info = self.myQuery(sql)
        return patient_info

    def get_patient_file(self, check_id):
        sql = " select file_id from file_info where check_id = {}".format(check_id)
        patient_info = self.myQuery(sql)
        return patient_info

    def getAlgorithmInfoByClassifierName(self, classifier_id):
        sql = f"select * from algorithm left join classifier on algorithm.alg_id = classifier.alg_id where classifier_id = {classifier_id} "
        patient_info = self.myQuery(sql)
        return patient_info

    # 清理标注

    def get_fileByModelLen(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select count(distinct mid) from label_info"
        else:
            sql = f"select count(distinct mid) from label_info where label_info.mid in (select classifier_id from classifier where {where_name} like '%{where_value}%')"
        set_info = self.myQuery(sql)
        return set_info

    def get_fileByModel(self, where_name='', where_value='', offset='', psize=''):
        if where_name == '':
            sql = f"select distinct mid from label_info limit {offset}, {psize}"
        else:
            sql = "select distinct mid from label_info where label_info.mid in (select classifier_id from classifier where {} like '%{}%') limit {}, {} ".format(where_name, where_value, offset, psize)
        file_name = self.myQuery(sql)
        return file_name

    def get_fileNameByModel(self, where_name='', where_value=''):
        if where_name == '':
            sql = "select distinct mid, check_id, file_id from label_info"
        else:
            sql = "select distinct mid, check_id, file_id from label_info where {}='{}'".format(where_name, where_value)
        file_name = self.myQuery(sql)
        return file_name

    def get_model_label_number(self, where_name, where_value, check_id=None, file_id=None):
        if check_id == None:
            sql = f"select count(*) from label_info where {where_name} = {where_value}"
        else:
            sql = f"select count(*) from label_info where {where_name} = {where_value} " \
                  f"and check_id = {check_id} and file_id = {file_id}"
        Len = self.myQuery(sql)
        return Len

    def get_model_label_assess(self, where_name, where_value, assess, check_id=None, file_id=None):
        if assess == 1:
            if not check_id == None:
                sql = f"select count(*) from label_info where {where_name} = '{where_value}' and check_id = '{check_id}'" \
                      f" and file_id = '{file_id}' and utype_id is not NULL"
            else:
                sql = f"select count(*) from label_info where {where_name} = '{where_value}' and utype_id is not NULL"
        elif assess == 0:
            if not check_id == None:
                sql = f"select count(*) from label_info where {where_name} = '{where_value}' and check_id = '{check_id}' " \
                      f"and file_id = '{file_id}' and utype_id is NULL"
            else:
                sql = f"select count(*) from label_info where {where_name} = '{where_value}' and utype_id is NULL"
        Len = self.myQuery(sql)
        return Len

    def getclassifierId(self, model_name):
        sql = f"select classifier_id from classifier where classifier_name = '{model_name}'"
        model_id = self.myQuery(sql)
        return model_id

    def getScanFileInfo(self, model_id, check_id, file_id):
        sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
               "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
               " and check_id='{}' and file_id = '{}'order by begin".format(model_id, check_id, file_id)
        label_info = self.myQuery(sql)
        return label_info

    def getSearchScanFileInfo(self, model_id, check_id, file_id, where_name, where_value):
        if where_name == 'channel':
            sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
               "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
               " and check_id='{}' and file_id = '{}' and {} like '%{}%' order by begin".format(model_id, check_id, file_id, where_name, where_value)
        elif where_name == 'begin' or where_name == 'end':
            sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
                  "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
                  " and check_id='{}' and file_id = '{}' and {} = '{}' order by begin".format(model_id, check_id,
                                                                                                   file_id, where_name,
                                                                                                   where_value)
        elif where_name == 'mtype_id':
            sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
                  "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
                  " and check_id='{}' and file_id = '{}' and label_info.mtype_id in(select type_id from type_info where type_name like '%{}%')" \
                  " order by begin".format(model_id, check_id, file_id, where_value)
        elif where_name == 'utype_id':
            sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
                  "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
                  " and check_id='{}' and file_id = '{}' and label_info.utype_id in (select type_id from type_info where type_name like '%{}%')" \
                  " order by begin".format(model_id, check_id, file_id, where_value)
        elif where_name == 'uid':
            sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
                  "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
                  " and check_id='{}' and file_id = '{}' and label_info.uid in (select uid from user_info where name like '%{}%')" \
                  " order by begin".format(model_id, check_id, file_id, where_value)

        label_info = self.myQuery(sql)
        return label_info

    def get_my_typeInfo(self, where_name, where_value):
        sql = f"select * from type_info where {where_name} = '{where_value}'"
        label_info = self.myQuery(sql)
        return label_info

    def getSample_rate(self, where_name, where_value):
        sql = f"select sampling_rate from config where {where_name} = '{where_value}'"
        label_info = self.myQuery(sql)
        return label_info

    def get_patientNameByCheckId(self, check_id):
        sql = f"select name from patient_info left join check_info on patient_info.patient_id = check_info.patient_id where check_id = '{check_id}'"
        patient_info = self.myQuery(sql)
        return patient_info

    def get_patientIdByCheckId(self, check_id):
        sql = f"select patient_info.patient_id from patient_info left join check_info on patient_info.patient_id = check_info.patient_id where check_id = '{check_id}'"
        patient_info = self.myQuery(sql)
        return patient_info

    def delLabelListInfo(self, del_info):
        try:
            parmSql = []
            for i in del_info:
                sql = "delete from label_info where mid = '{}' and check_id = '{}' and file_id = '{}' " \
                      "and begin = '{}' and channel = '{}'".format(i[0], i[1], i[2], i[3], i[4])
                parmSql.append(sql)
            tag1, tag2 = self.myExecuteTranSql(parmSql)
            if tag1 == '1':
                return '1', str(tag2)
            else:
                return '0', str(tag2)
        except Exception as e:
            print(e)
            return '0', str(e)

    def delLabelByModelFile(self, model_id, check_id, file_id):
        try:
            sql = "delete from label_info where mid = '{}' and check_id = '{}' and file_id = '{}'"\
                .format(model_id, check_id, file_id)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as e:
            print(e)
            return '0', str(e)

    def getLabelInfoByAssess(self, model_id, check_id, file_id, flag):
        if flag == 1:
            sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
               "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
               " and check_id='{}' and file_id = '{}' and utype_id is Null order by begin".format(model_id, check_id, file_id)
        else:
            sql = "select channel,begin,end,type_name,user_info.name,utype_id from label_info,user_info,type_info " \
                  "where label_info.uid=user_info.uid and label_info.mtype_id=type_info.type_id and label_info.mid='{}'" \
                  " and check_id='{}' and file_id = '{}' and utype_id is not Null order by begin".format(model_id, check_id, file_id)
        label_info = self.myQuery(sql)
        return label_info

    def get_measure_day_by_checkId(self, check_id):
        sql = " select check_number, measure_date from check_info where check_id = {}".format(check_id)
        patient_info = self.myQuery(sql)
        return patient_info

    def get_label_ListInfo(self, check_id, file_id, model_id, channels, type_names, user_names, status_show):
        try:
            if status_show == True:
                sql = f"select channel,begin,end,mid,label_info.mtype_id,label_info.uid,utype_id from label_info," \
                       f"type_info,user_info where check_id = '{check_id}' and file_id = '{file_id}' " \
                       f"and mid = '{model_id}' and (channel in {channels} or channel='all') " \
                       f"and ((label_info.utype_id is null and label_info.mtype_id=type_info.type_id) " \
                       f"or (label_info.utype_id is not null and label_info.utype_id=type_info.type_id))" \
                       f" and type_info.type_name in {type_names} and user_info.uid=label_info.uid  " \
                       f"and user_info.name in {user_names} order by begin "

            else:
                sql = f"select channel,begin,end,mid,label_info.mtype_id,label_info.uid,utype_id from label_info," \
                      f"type_info,user_info where check_id = '{check_id}' and file_id = '{file_id}' " \
                      f"and mid = '{model_id}' and channel in {channels} " \
                      f"and ((label_info.utype_id is null and label_info.mtype_id=type_info.type_id) " \
                      f"or (label_info.utype_id is not null and label_info.utype_id=type_info.type_id))" \
                      f" and type_info.type_name in {type_names} and user_info.uid=label_info.uid  " \
                      f"and user_info.name in {user_names} order by begin "
            label_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', label_info

    # 获取标注集中的状态
    def get_lable_statusInfo(self, check_id, file_id, model_id, where_name='', where_value=''):
        try:
            if where_name == '':
                sql = "select channel, begin, end, mid, label_info.mtype_id,uid, utype_id from label_info, type_info" \
                      "  where check_id='{}'and file_id='{}' and channel='all' and mid='{}'""and" \
                      " type_info.type_id=label_info.mtype_id order by begin".format(check_id, file_id, model_id)
            else:
                sql = "select channel, begin, end, mid, label_info.mtype_id,uid, utype_id from label_info, type_info" \
                    "  where check_id='{}'and file_id='{}' and channel='all' and mid='{}'""and {} = '{}' and" \
                    " type_info.type_id=label_info.mtype_id order by begin".format(check_id, file_id, model_id, where_name, where_value)
            state_info = self.myQuery(sql)
        except Exception as re:
            return '0', str(re)
        return '1', state_info

    def update_labelListInfo(self, mid, check_id, file_id, begin, channel, end, mtype_id, uid, utype_id):
        try:
            sql = "update label_info set uid='{}', utype_id ='{}' where mid='{}' and check_id='{}'and file_id='{}'" \
                  "and begin='{}'and channel='{}'and end='{}' and mtype_id='{}'".format(uid, utype_id, mid, check_id, file_id, begin, channel, end, mtype_id)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as re:
            print(re)
            return '0', str(re)

    def del_labelListInfo(self, mid, check_id, file_id, begin, channel, end, mtype_id):
        try:
            sql = "delete from label_info where mid='{}' and check_id='{}'and file_id='{}'" \
                  "and begin='{}'and channel='{}'and end='{}' and mtype_id='{}'".format(mid, check_id, file_id, begin, channel, end, mtype_id)
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as re:
            print(re)
            return '0', str(re)

    def add_labelInfo_by_auto(self, mid, check_id, file_id, begin, channel, end, mtype_id, uid):
        try:
            sql = f"insert into label_info (mid, check_id, file_id, begin, channel, end, mtype_id, uid) values ('{mid}'" \
                  f",'{check_id}', '{file_id}', '{begin}', '{channel}', '{end}', '{mtype_id}', '{uid}')"
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1', str(tag)
            else:
                return '0', str(tag)
        except Exception as re:
            print(re)
            return '0', str(re)

    def getWinSampleInfo(self, table_name, check_id, file_id, begin, end, user_id, nSample, fKey):
        try:
            if fKey is None:
                sql = f"select channel, begin, end, type_id from {table_name} where check_id={check_id} and file_id={file_id} and uid = {user_id} order by begin"
            elif table_name == 'result':
                sql = f"select channel, begin, end, type_id from {table_name} where check_id={check_id} and file_id={file_id} and uid = {user_id} and class_id = {fKey} order by begin"
            elif table_name == 'reslab':
                sql = f"select channel, begin, end, type_id from {table_name} where check_id={check_id} and file_id={file_id} and uid = {user_id} and theme_id = {fKey} order by begin"
            elif table_name == 'label_info':
                sql = f"select channel, begin, end, mtype_id from {table_name} where check_id={check_id} and file_id={file_id} and mid = {fKey} order by begin"
            else:
                return []
            samples = self.myQuery(sql)
            labels = []
            for sample in samples:
                sample = list(sample)
                if sample[1] >= begin and sample[1] < end:
                    sample[1] = sample[1] // nSample
                    sample[2] = sample[2] // nSample
                    labels.append(sample)
            return labels
        except Exception as re:
            print(re)
            return []

    def labFirst(self, table_name, check_id, file_id, end, user_id, nDotWin, lenFile, nSample, fKey):
        try:
            if fKey is None:
                sql = f"select channel, begin, end, type_id from {table_name} where check_id={check_id} and file_id={file_id} and uid = {user_id} order by begin"
            elif table_name == 'result':
                sql = f"select channel, begin, end, type_id from {table_name} where check_id={check_id} and file_id={file_id} and uid = {user_id} and class_id = {fKey} order by begin"
            elif table_name == 'reslab':
                sql = f"select channel, begin, end, type_id from {table_name} where check_id={check_id} and file_id={file_id} and uid = {user_id} and theme_id = {fKey} order by begin"
            elif table_name == 'label_info':
                sql = f"select channel, begin, end, mtype_id from {table_name} where check_id={check_id} and file_id={file_id} and mid = {fKey} order by begin"
            else:
                return [], []
            samples = self.myQuery(sql)
            labels = []
            labelBit = np.zeros(nDotWin + 1, dtype=bool)
            for sample in samples:
                sample = list(sample)
                l, r = sample[1] * nDotWin // lenFile, sample[2] * nDotWin // lenFile
                labelBit[l: r + 1] = True
                if sample[1] < end:
                    sample[1] = sample[1] // nSample
                    sample[2] = sample[2] // nSample
                    labels.append(sample)
            return labels, labelBit
        except Exception as err:
            print(err)
            return [], []

    def insertSample(self, label, tableName, fKey):
        try:
            if fKey is None:
                sql = f'insert into {tableName} (channel, begin, end, type_id, check_id, file_id, uid) values ("{label[0]}", {label[1]}, {label[2]}, {label[3]}, {label[4]}, {label[5]}, {label[6]})'
            else:
                sql = f'insert into {tableName} (channel, begin, end, type_id, check_id, file_id, uid, theme_id) values ("{label[0]}", {label[1]}, {label[2]}, {label[3]}, {label[4]}, {label[5]}, {label[6]}, {fKey})'
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1'
            else:
                return '0'
        except Exception as re:
            print(re)
            return '0'

    def updateSample(self, label, tableName, fKey):
        try:
            if fKey is None:
                sql = f'update {tableName} set type_id = {label[3]} where channel = "{label[0]}" and begin = {label[1]} and end = {label[2]} and check_id = {label[4]} and file_id = {label[5]} and uid = {label[6]}'
            elif tableName == 'result':
                sql = f'update {tableName} set type_id = {label[3]} where channel = "{label[0]}" and begin = {label[1]} and end = {label[2]} and check_id = {label[4]} and file_id = {label[5]} and uid = {label[6]} and class_id = {fKey}'
            else:
                sql = f'update {tableName} set type_id = {label[3]} where channel = "{label[0]}" and begin = {label[1]} and end = {label[2]} and check_id = {label[4]} and file_id = {label[5]} and uid = {label[6]} and theme_id = {fKey}'
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1'
            else:
                return '0'
        except Exception as re:
            print(re)
            return '0'

    def deleteSample(self, label, tableName):
        try:
            sql = f'delete from {tableName} where channel = "{label[0]}" and begin = {label[1]} and end = {label[2]} and check_id = {label[4]} and file_id = {label[5]} and uid = {label[6]}'
            tag = self.myExecuteSql(sql)
            if tag == '':
                return '1'
            else:
                return '0'
        except Exception as re:
            print(re)
            return '0'

    def getLabelBit(self, table_name, check_id, file_id, user_id, nDotWin, lenFile):
        sql = f"select channel, begin, end, type_id from {table_name} where check_id={check_id} and file_id={file_id} and uid = {user_id} order by begin"
        samples = self.myQuery(sql)
        labelBit = np.zeros(nDotWin + 1, dtype=bool)
        for sample in samples:
            l, r = sample[1] * nDotWin // lenFile, sample[2] * nDotWin // lenFile
            labelBit[l: r + 1] = True
        return labelBit

    def getState(self, class_id, uid):
        sql = f'select state from student where class_id = {class_id} and uid = {uid}'
        state = self.myQuery(sql)[0][0]
        return state

    def updateState(self, class_id, uid, state, grade=None):
        if grade is None:
            sql = f'update student set state="{state}" where class_id = {class_id} and uid = {uid}'
        else:
            sql = f'update student set state="{state}", grade={grade} where class_id = {class_id} and uid = {uid}'
        self.myExecuteSql(sql)

    def getAllSampleByFile(self, check_id, file_id, Puid):
        sql = f'select channel, begin, end, type_id from sample_info where check_id = {check_id} and file_id = {file_id} and uid = {Puid}'
        samples = self.myQuery(sql)
        return samples

    def addResult(self, class_id, check_id, file_id, uid, channel, begin, end):
        sql = f'insert into result (class_id, check_id, file_id, uid, channel, begin, end) values ({class_id}, {check_id}, {file_id}, {uid}, "{channel}", {begin}, {end})'
        self.myExecuteSql(sql)

    def getSamplesFromResult(self, check_id, file_id, uid, class_id):
        sql = f'select channel, begin, end, type_id from result where check_id = {check_id} and file_id = {file_id} and uid = {uid} and class_id = {class_id}'
        samples = self.myQuery(sql)
        return samples

    def getClassifierChannelsById(self, id):
        sql = f"select channels from classifier where classifier_id = {id}"
        channels = self.myQuery(sql)[0][0]
        return channels

if __name__ == '__main__':
    dbUtil = dbUtil()
    dbUtil.ramdom_add()
