import time, datetime
from math import ceil

from PyQt5.QtGui import QStandardItem


class curUser:
    def __init__(self, _Util, _DbUtil):
        self.appUtil = _Util
        self.dbUtil = _DbUtil
        self.root_path = self.appUtil.root_path
        # 每个用户存放的信息顺序为[uid, account, name, phone, email, administrator, labeler, student, teacher, doctor,
        # researcher, macAddr, defaultConfigID, now, curAuthority]
        self.users = {}
        self.config = self.dbUtil.queryConfigData()
        # 与action序号的的对应关系{'密码修改':2, '用户管理':3, '标注类型':4, '基本配置':5, '配置选择':6,
        #                    '导联配置':7, '切换用户':8, '退出':9, '病人管理': 10, '导入脑电’：12,
        #                    '诊断查询':14, '创建会诊':15, '脑电会诊':16, '创建课堂':17, '诊断学习':18,
        #                    '学习测试’:19,'学习评估':20, '样本统计':21, '任务设置':22, '科研标注': 23, '执行查看':24,
        #                    '构建集合':25,'算法管理‘:27,'模型训练':28,'模型查删':30,
        #                    }
        # F中的数字对应代表该身份不能使用的菜单项编号，登录时初始化用户权限
        self.authority = {
             'adminF': [6, 10, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 27, 28, 29, 30, 31, 32, 33],
            'labelerF': [3, 4, 5, 7, 10, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 27, 28,29, 30, 31, 32, 33],
            'studentF': [3, 4, 5, 6, 7, 10, 12, 14, 15, 16, 17, 21, 22, 23, 24, 25, 27, 28,29, 30, 31, 32, 33],
            'teacherF': [3, 4, 5, 7, 12, 15, 16, 18, 19, 21, 22, 23, 24, 25, 27, 28,29, 30, 31, 32, 33],
            'doctorF': [3, 4, 5, 7, 17, 18, 19, 20, 21, 22, 24, 25, 27, 28,29, 30, 31, 32, 33],
            'researcherF': [3, 4, 5, 7, 12, 15, 17, 18, 19, 20],
            'adminT': ['pwd', 'userManager', 'quit', 'logout', 'labelType', 'basicConfig', 'montage'],
            'labelerT': ['pwd', 'quit', 'logout', 'configOptions', 'reserching'],
            'studentT': ['pwd', 'quit', 'logout', 'diagTest', 'diagTraining', 'testAssess', "EEG"],
            'teacherT': ['pwd', 'quit', 'logout', 'configOptions', 'manualQuery', 'consulting', 'createLesson','testAssess','reserching', 'patientManager', "EEG"],
            'doctorT': ['pwd', 'quit', 'logout', 'patientManager', 'configOptions', 'manual', 'manualQuery',
                        'consulting', 'createCons', 'dataImport','testAssess','reserching', 'EEG'],
            'researcherT': ['pwd', 'quit', 'logout', 'configOptions', 'manualQuery', 'consulting', 'reserching','reserchingQuery', 'setBuild','delSet_info', 'algorithm', 'taskSettings', 'modelTrain', 'classifier', 'sampleState', 'patientManager', 'modelTest', 'detailLook', 'auto', 'clearLabel', 'assessLabel', "EEG"],
        }

    def login(self, userAccount, pwd, macAddr):
        # (88, 'hzx', 'e10adc3949ba59abbe56e057f20f883e', '黄泽鑫', None, None, 0, 1, 0, 0, 1, 1)
        print(f'Login userAccount: {userAccount}, macAddr: {macAddr}')
        print(f'Login users: {self.users}')
        onlineUserInfos = self.users.values()
        for userInfo in onlineUserInfos:
            if userInfo[1].lower() == userAccount.lower():
                if macAddr != userInfo[11]:
                    msg = f'{userAccount} 当前 MAC 地址与初始登录 MAC 地址不符'
                    return 2, msg, ''
                else:
                    msg = f'{userAccount}登录成功'
                    return 1, msg, userInfo
        user_infos = self.dbUtil.getUserInfo('account', userAccount)
        if len(user_infos) == 0:
            user_info = None
            msg = f'{userAccount} 当前用户不存在'
            return 3, msg, ''
        else:
            user_info = user_infos[0]
        print(f'user_info: {user_info}')
        if user_info:
            if pwd == user_info[2]:
                defaultConfigID = 0
                for config in self.config:
                    if config[6] == 1:
                        defaultConfigID = config[0]
                        break
                now = datetime.datetime.now()
                info = list(user_info)
                print(f'info: {info}')
                del info[2]
                info.extend([str(macAddr), defaultConfigID, now])
                self.users.setdefault(user_info[0], info)
                msg = f'{userAccount}登录成功'
                # 设置不能执行的权限
                curAuthority = self.setUserPermission(info[5], info[6], info[7], info[8], info[9], info[10])
                info.append(curAuthority)
                print(f'Login Info: {info}')
                return 1, msg, info
            else:
                msg = f'{userAccount}用户名或密码错误'
                return 0, msg, None
        else:
            msg = f'{userAccount}用户名或密码错误'
            return 0, msg, None

    def logout(self, userID, macAddr):
        userInfo = self.users.get(userID)
        print(f'userInfo: {userInfo}')
        if userInfo:
            if userInfo[11] == str(macAddr):
                del self.users[userID]
                msg = f'{userInfo[1]}退出当前用户'
                return [1, '', msg]
            else:
                msg = f'{userInfo[1]}当前 MAC 地址与初始登录 MAC 地址不符'
                return [2, '', msg]
        return False

    def permission(self, userID, macAddr, cmd):
        print(f'size: {len(self.users)}')
        print(self.users)
        try:
            userInfo = self.users.get(userID)
            if userInfo[11] != str(macAddr):
                msg = f'{userInfo[1]}当前 MAC 地址与初始登录 MAC 地址不符'
                return 0, msg
            judge = []
            # 判断是否为管理员身份
            if userInfo[5]:
                temp = self.authority.get('adminT')
                print(temp)
                for i in temp:
                    if i == cmd:
                        return True
                return False
            # 判断是否为标注员身份
            if userInfo[6]:
                temp = self.authority.get('labelerT')
                judge.extend(temp)
            # 判断是否为学生身份
            if userInfo[7]:
                temp = self.authority.get('studentT')
                judge.extend(temp)
            # 判断是否为老师身份
            if userInfo[8]:
                temp = self.authority.get('teacherT')
                judge.extend(temp)
            # 判断是否为医生身份
            if userInfo[9]:
                temp = self.authority.get('doctorT')
                judge.extend(temp)
            # 判断是否为研究员身份
            if userInfo[10]:
                temp = self.authority.get('researcherT')
                judge.extend(temp)
            print(f'judge: {judge}')
            for i in judge:
                if i == cmd:
                    return True
            return False
        except Exception as e:
            print('permission', e)

    def setUserPermission(self, admin, labeler, student, teacher, doctor, researcher):
        permission_list = [i for i in range(2, 34)]
        print(f'permission_list11: {permission_list}')
        if admin:
            permission_list = set(permission_list) & set(self.authority['adminF'])
            print(f'permission_list222: {permission_list}')
            return permission_list
        if labeler:
            permission_list = set(permission_list) & set(self.authority['labelerF'])
        if student:
            permission_list = set(permission_list) & set(self.authority['studentF'])
        if teacher:
            permission_list = set(permission_list) & set(self.authority['teacherF'])
        if doctor:
            permission_list = set(permission_list) & set(self.authority['doctorF'])
        if researcher:
            permission_list = set(permission_list) & set(self.authority['researcherF'])
        return permission_list

    # 根据传入参数删除数据库信息用户信息
    def delUserInfo(self, REQmsg):
        try:
            onlineUserInfos = self.users.values()
            print(onlineUserInfos)
            userAccount = REQmsg[3][1]
            isSearch = REQmsg[3][4]
            # 判断当前删除账号是否在线,在线则设置无法删除
            for userInfo in onlineUserInfos:
                if userInfo[1] == userAccount:
                    print('online:', userInfo[1], userAccount)
                    msgtip = [REQmsg[1], f"删除{REQmsg[3][1]}用户信息失败,在线的用户不能删除", '', '']
                    ret = ['0', REQmsg[1], REQmsg[3][2], 0]
                    return msgtip, ret
            r, result = self.dbUtil.delUserInfo('account', REQmsg[3][1])
            if r == '1':
                _curPageIndex = REQmsg[3][3]
                if _curPageIndex <= 0:
                    _curPageIndex = 1
                _Pagerows = 12
                if isSearch:
                    key_word = REQmsg[3][5]
                    key_value = REQmsg[3][6]
                    ui_size = self.dbUtil.getUserInfoLen(where_name=key_word, where_like=key_value)
                    ptotal = ceil(ui_size[0][0] / _Pagerows)
                    if ptotal == 0:
                        result = []
                    elif _curPageIndex > ptotal and ptotal > 0:
                        _curPageIndex = ptotal
                        result = self.dbUtil.getSearchUserInfoByPage(where_name=key_word, where_value=key_value,
                                                                     offset=(_curPageIndex - 1) * _Pagerows,
                                                                     psize=_Pagerows)
                    else:
                        result = self.dbUtil.getSearchUserInfoByPage(where_name=key_word, where_value=key_value,
                                                                     offset=(_curPageIndex - 1) * _Pagerows,
                                                                     psize=_Pagerows)
                else:
                    ui_size = self.dbUtil.getUserInfoLen()
                    ptotal = ceil(ui_size[0][0] / _Pagerows)
                    if _curPageIndex > ptotal:
                        _curPageIndex = ptotal
                    if _curPageIndex == 1:
                        result = self.dbUtil.getUserInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows + 1)
                    else:
                        result = self.dbUtil.getUserInfoByPage(offset=((_curPageIndex - 1) * _Pagerows + 1),
                                                               psize=_Pagerows)
                msgtip = [REQmsg[1], f"删除{REQmsg[3][1]}用户信息成功", f'{REQmsg[2]}', '']
                ret = ['1', REQmsg[1], REQmsg[3][2], result, ptotal, _curPageIndex, isSearch]
                return msgtip, ret
            else:
                msgtip = [REQmsg[1], f"删除{REQmsg[3][1]}用户信息失败", f'{result}', '']
                ret = ['0', REQmsg[1], REQmsg[3][2], 1, isSearch]
                return msgtip, ret
        except Exception as e:
            print('delUserInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret

    # 根据传入参数编辑数据库信息用户信息
    def updateUserInfo(self, REQmsg):
        # print('updateUserInfo')
        try:
            onlineUserInfos = self.users.values()
            if REQmsg[3][0] == True:
                userAccount = REQmsg[3][1]
            else:
                userAccount = REQmsg[3][0]
            # 判断当前删除账号是否在线
            for userInfo in onlineUserInfos:
                if userInfo[1] == userAccount:
                    msgtip = [REQmsg[1], f"编辑{REQmsg[3][1]}用户信息失败,在线的用户信息不能编辑", '', '']
                    REQmsg[3].append(0)
                    ret = ['0', REQmsg[1], REQmsg[3]]
                    return msgtip, ret
            if REQmsg[3][0] == True:
                r = self.dbUtil.updateUserInfo(set_name='pwd', set_value=REQmsg[3][2], where_name='account',where_value=REQmsg[3][1])
                if r:
                    msgtip = [REQmsg[2], f"修改{REQmsg[3][1]}密码成功", f'{REQmsg[2]}', '']
                    ret = ['1', REQmsg[1], REQmsg[3]]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"修改{REQmsg[3][1]}密码失败", f'{REQmsg[2]}', '']
                    REQmsg[3].append(1)
                    ret = ['0', REQmsg[1], REQmsg[3]]
                    return msgtip, ret
            else:
                r, result = self.dbUtil.updateUserInfo('account', REQmsg[3][0], userInfo=REQmsg[3])
                if r == '1':
                    msgtip = [REQmsg[1], f"更新{REQmsg[3][0]}用户信息成功", f'{REQmsg[2]}', '']
                    ret = ['1', REQmsg[1], REQmsg[3]]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[1], f"更新{REQmsg[3][0]}用户信息失败", f'{result}', '']
                    ret = ['0', REQmsg[1], REQmsg[3]]
                    return msgtip, ret
        except Exception as e:
            print('updateUserInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret