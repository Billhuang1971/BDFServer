#!/usr/bin/python
# author bluenor
# -*- coding: utf-8 -*-
import datetime
import os
import pickle
import threading
from distutils.command.check import check
from functools import partial
from math import ceil
from os import makedirs, path, remove
import json

import mne
from PyQt5.QtCore import QProcess, QEventLoop, QTimer
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QApplication

from service.socketServer import socketServer
# from classifier.setBuild.EEGDeepState import EEGDeepState
from classifier.setBuild.randomState import randomState
from classifier.setBuild.randomWave import randomWave
from util.EEGUpload import EEGUpload
from util.algobject import trainAlg, testAlg, predictAlg


class server(socketServer):
    def __init__(self, s_ip, s_port, dbUtilH, appUtilH, curUserH):
        super().__init__(s_ip, s_port)
        self.tabV_model = QStandardItemModel(0, 5)
        self.dbUtil = dbUtilH
        self.appUtil = appUtilH
        self.curUser = curUserH
        self.model_path = appUtilH.model_path
        self.training_mutex = threading.Lock()
        self.testing_mutex = threading.Lock()
        self.diag_mutex = threading.Lock()
        self.filename_mutex = threading.Lock()
        self.permission_mutex = threading.Lock()
        self.EEGUploadService = EEGUpload(self.dbUtil, self.appUtil)
    def appMain(self, clientAddr, REQmsg):
        userID = REQmsg[2]
        macAddr = REQmsg[3][0]
        REQmsg[3] = REQmsg[3][1:]
        if userID == 0:
            # 登录
            userAccount = REQmsg[3][0]
            pwd = REQmsg[3][1]
            tipmsg, ret = self.login(userAccount, pwd, macAddr)
            REQmsg[3] = ret
            self.myTip(REQmsg[1], tipmsg)
            print(f'REQmsg: {REQmsg}')
            return REQmsg
        else:
            cmd = REQmsg[0]
            cmdID = REQmsg[1]
            self.permission_mutex.acquire()
            pret=self.curUser.permission(userID, macAddr, cmd)
            self.permission_mutex.release()
            if not pret:
                REQmsg[3] = ['0', REQmsg[1], f'权限不足']
                tipmsg = [REQmsg[2], f"应答{REQmsg[0]} ", f'权限不足', '']
                self.myTip(REQmsg[1], tipmsg)
                return REQmsg

            if cmd == "quit" and cmdID == 1:
                # 系统退出时注销用户
                tipmsg, ret = self.logout(REQmsg, macAddr)
                REQmsg[3] = ret
            elif cmd == "logout" and cmdID == 1:
                # 切换用户时注销用户
                tipmsg, ret = self.logout(REQmsg, macAddr)
                REQmsg[3] = ret
            # 修改密码
            elif cmd == "pwd" and cmdID == 1:
                tipmsg, ret = self.changePwd(REQmsg)
                REQmsg[3] = ret

            # 获取用户信息
            elif cmd == 'userManager' and cmdID == 1:
                tipmsg, ret = self.getUserInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            # 新增用户信息
            elif cmd == 'userManager' and cmdID == 2:
                tipmsg, ret = self.addUserInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            # 删除用户信息
            elif cmd == 'userManager' and cmdID == 3:
                tipmsg, ret = self.delUserInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            # 编辑用户信息
            elif cmd == 'userManager' and cmdID == 4:
                tipmsg, ret = self.updateUserInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'userManager' and cmdID == 5:
                tipmsg, ret = self.userPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'userManager' and cmdID == 6:
                tipmsg, ret = self.inquiryUserInfo(macAddr, REQmsg)
                REQmsg[3] = ret


            # 获取导联配置信息
            elif cmd == 'montage' and cmdID == 1:
                tipmsg, ret = self.getMontage(macAddr, REQmsg)
                REQmsg[3] = ret
            # 添加导联方案
            elif cmd == 'montage' and cmdID == 2:
                tipmsg, ret = self.addMontageScheme(macAddr, REQmsg)
                REQmsg[3] = ret
            # 编辑导联方案
            elif cmd == 'montage' and cmdID == 3:
                tipmsg, ret = self.editMontageScheme(macAddr, REQmsg)
                REQmsg[3] = ret
            # 编辑导联方案
            elif cmd == 'montage' and cmdID == 4:
                tipmsg, ret = self.delMontageScheme(macAddr, REQmsg)
                REQmsg[3] = ret
            # 保存导联方案通道
            elif cmd == 'montage' and cmdID == 5:
                tipmsg, ret = self.saveMontageChannel(macAddr, REQmsg)
                REQmsg[3] = ret


            # 标注类型
            # 获取标注类型信息
            elif cmd == 'labelType' and cmdID == 1:
                tipmsg, ret = self.getTypeInfo(REQmsg)
                REQmsg[3] = ret

            # 增加标注类型信息
            elif cmd == 'labelType' and cmdID == 2:
                tipmsg, ret = self.addTypeInfo(REQmsg)
                REQmsg[3] = ret

            # 删除标注类型信息
            elif cmd == 'labelType' and cmdID == 3:
                tipmsg, ret = self.delTypeInfo(REQmsg)
                REQmsg[3] = ret

            # 更新标注类型信息
            elif cmd == 'labelType' and cmdID == 4:
                tipmsg, ret = self.updateTypeInfo(REQmsg)
                REQmsg[3] = ret

            # 脑电导入模块
            # 获取病人诊断信息
            elif cmd == 'dataImport' and cmdID == 1:
                tipmsg, ret = self.getPatientCheckInfo(REQmsg)
                REQmsg[3] = ret
            # 删除病人诊断信息
            elif cmd == 'dataImport' and cmdID == 2:
                tipmsg, ret = self.delPatientCheckInfo(REQmsg)
                REQmsg[3] = ret
            # 添加病人检查信息
            elif cmd == 'dataImport' and cmdID == 3:
                tipmsg, ret = self.addCheckInfo(REQmsg)
                REQmsg[3] = ret
            # 检查脑电文件配置
            elif cmd == 'dataImport' and cmdID == 4:
                tipmsg, ret = self.checkConfig(REQmsg)
                REQmsg[3] = ret
            # 生成文件名请求
            elif cmd == 'dataImport' and cmdID == 10:
                print("这里生成文件名的REQmsg是：", REQmsg)
                tipmsg, ret = self.makeFileName(REQmsg)
                REQmsg[3] = ret
            # 写脑电请求
            elif cmd == 'dataImport' and cmdID == 5:
                print("这里的REQmsg是：", REQmsg)
                tipmsg, ret = self.writeEEG(REQmsg)
                REQmsg[3] = ret
            # 更新脑电检查信息请求
            elif cmd == 'dataImport' and cmdID == 6:
                tipmsg, ret = self.updateCheckInfo(REQmsg)
                REQmsg[3] = ret
            # 获取脑电检查信息
            elif cmd == 'dataImport' and cmdID == 7:
                tipmsg, ret = self.getFileInfo(REQmsg)
                REQmsg[3] = ret
            # 删除脑电检查文件
            elif cmd == 'dataImport' and cmdID == 11:
                tipmsg, ret = self.delFileInfo(REQmsg)
                REQmsg[3] = ret
            # 获取病人详细信息
            elif cmd == 'dataImport' and cmdID == 8:
                tipmsg, ret = self.getChoosePatientInfo(REQmsg)
                REQmsg[3] = ret
            # 获取医生详细信息
            elif cmd == 'dataImport' and cmdID == 9:
                tipmsg, ret = self.getChooseDoctorInfo(REQmsg)
                REQmsg[3] = ret

            # 任务设置模块
            # 获取标注主题信息
            elif cmd == 'taskSettings' and cmdID == 1:
                tipmsg, ret = self.getThemeInfo(REQmsg)
                REQmsg[3] = ret
            # 添加标注主题信息
            elif cmd == 'taskSettings' and cmdID == 2:
                tipmsg, ret = self.addThemeInfo(REQmsg)
                REQmsg[3] = ret
            # 删除标注主题信息
            elif cmd == 'taskSettings' and cmdID == 3:
                tipmsg, ret = self.delThemeInfo(REQmsg)
                REQmsg[3] = ret
            # 更新标注主题信息
            elif cmd == 'taskSettings' and cmdID == 4:
                tipmsg, ret = self.updateThemeInfo(REQmsg)
                REQmsg[3] = ret
            # 获取标注任务信息
            elif cmd == 'taskSettings' and cmdID == 5:
                tipmsg, ret = self.getTaskInfo(REQmsg)
                REQmsg[3] = ret
            # 添加标注任务信息
            elif cmd == 'taskSettings' and cmdID == 6:
                tipmsg, ret = self.addTaskInfo(REQmsg)
                REQmsg[3] = ret
            # 删除标注任务信息
            elif cmd == 'taskSettings' and cmdID == 7:
                tipmsg, ret = self.delTaskInfo(REQmsg)
                REQmsg[3] = ret
            # 更新标注任务信息
            elif cmd == 'taskSettings' and cmdID == 8:
                tipmsg, ret = self.updateTaskInfo(REQmsg)
                REQmsg[3] = ret
            # 获取病人检查单信息
            elif cmd == 'taskSettings' and cmdID == 9:
                tipmsg, ret = self.getChooseDetailInfo(REQmsg)
                REQmsg[3] = ret
            # 启动标注主题
            elif cmd == 'taskSettings' and cmdID == 10:
                tipmsg, ret = self.startTheme(REQmsg)
                REQmsg[3] = ret
            # 获取标注员信息
            elif cmd == 'taskSettings' and cmdID == 11:
                tipmsg, ret = self.getChooseMarkerInfo(REQmsg)
                REQmsg[3] = ret







            # 获取基本配置数据
            elif cmd == 'basicConfig' and cmdID == 1:
                tipmsg, ret = self.getConfigData(cmdID)
                REQmsg[3] = ret
            elif cmd == 'basicConfig' and cmdID == 2:
                tipmsg, ret = self.addBasicConfig(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'basicConfig' and cmdID == 3:
                tipmsg, ret = self.delBasicConfig(cmdID, REQmsg[3][0])
                REQmsg[3] = ret
            elif cmd == 'basicConfig' and cmdID == 4:
                tipmsg, ret = self.updateBasicConfig(cmdID, REQmsg[3])
                REQmsg[3] = ret


            elif cmd == 'configOptions' and cmdID == 1:
                tipmsg, ret = self.getCurConfigData(cmdID, userID)
                REQmsg[3] = ret
            elif cmd == 'configOptions' and cmdID == 2:
                tipmsg, ret = self.getAllConfigData(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'configOptions' and cmdID == 3:
                tipmsg, ret = self.chgCurUserConfigData(cmdID, userID, REQmsg[3])
                REQmsg[3] = ret

            ##===dsj  [====
            # 执行查看/提取未标注信息
            elif cmd == 'reserchingQuery' and cmdID == 1:
                tipmsg, ret = self.rgQ_get_labels(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/类型、用户信息
            elif cmd == 'reserchingQuery' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/打开脑电文件
            elif cmd == 'reserchingQuery' and cmdID == 8:
                tipmsg, ret = self.rg_openEEGFile(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/读取脑电文件数据块
            elif cmd == 'reserchingQuery' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 执行查看/添加样本
            elif cmd == 'reserchingQuery' and (cmdID == 11 or cmdID == 12):
                tipmsg, ret = self.rg_update_reslab12(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/删除样本
            elif cmd == 'reserchingQuery' and cmdID == 13:
                tipmsg, ret = self.rg_reslab_del13(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/添加样本[]
            elif cmd == 'reserchingQuery' and (cmdID == 14 or cmdID == 15):
                tipmsg, ret = self.rg_reslab_update15(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/设置
            elif cmd == 'reserchingQuery' and cmdID == 16:
                tipmsg, ret = self.rg_init_reslabList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/删除样本信息
            elif cmd == 'reserchingQuery' and cmdID == 19:
                tipmsg, ret = self.rg_del_reslab19(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/添加样本状态信息
            elif cmd == 'reserchingQuery' and cmdID == 21:
                tipmsg, ret = self.rg_add_reslab_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/修改样本状态信息
            elif cmd == 'reserchingQuery' and cmdID == 22:
                tipmsg, ret = self.rg_update_reslab_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/删除样本状态信息
            elif cmd == 'reserchingQuery' and cmdID == 23:
                tipmsg, ret = self.rg_del_reslab_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/提交标注信息
            elif cmd == 'reserchingQuery' and cmdID == 28:
                tipmsg, ret = self.rgQ_label_commit(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/查询、分页
            elif cmd == 'reserchingQuery' and cmdID == 30:
                tipmsg, ret = self.rgQ_paging(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 执行查看/查询、分页
            elif cmd == 'reserchingQuery' and cmdID == 31:
                tipmsg, ret = self.rgQ_theme_commit(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 科研标注/提取未标注信息
            elif cmd == 'reserching' and cmdID == 1:
                tipmsg, ret = self.rg_get_notlabels(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注诊断/类型、用户信息
            elif cmd == 'reserching' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 科研标注/打开脑电文件
            elif cmd == 'reserching' and cmdID == 8:
                tipmsg, ret = self.rg_openEEGFile(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/读取脑电文件数据块
            elif cmd == 'reserching' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 科研标注/添加样本
            elif cmd == 'reserching' and (cmdID == 11 or cmdID == 12):
                tipmsg, ret = self.rg_update_reslab12(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/删除样本
            elif cmd == 'reserching' and cmdID == 13:
                tipmsg, ret = self.rg_reslab_del13(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/添加样本[]
            elif cmd == 'reserching' and (cmdID == 14 or cmdID == 15):
                tipmsg, ret = self.rg_reslab_update15(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/设置
            elif cmd == 'reserching' and cmdID == 16:
                tipmsg, ret = self.rg_init_reslabList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/添加样本信息
            elif cmd == 'reserching' and cmdID == 17:
                tipmsg, ret = self.rg_insert_reslab17(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/删除样本信息
            elif cmd == 'reserching' and cmdID == 19:
                tipmsg, ret = self.rg_del_reslab19(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/添加样本状态信息
            elif cmd == 'reserching' and cmdID == 21:
                tipmsg, ret = self.rg_add_reslab_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/修改样本状态信息
            elif cmd == 'reserching' and cmdID == 22:
                tipmsg, ret = self.rg_update_reslab_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/删除样本状态信息
            elif cmd == 'reserching' and cmdID == 23:
                tipmsg, ret = self.rg_del_reslab_state(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 科研标注/提交标注信息
            elif cmd == 'reserching' and cmdID == 28:
                tipmsg, ret = self.rg_label_commit(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 科研标注/查询、分页
            elif cmd == 'reserching' and cmdID == 30:
                tipmsg, ret = self.rg_paging(clientAddr, REQmsg)
                REQmsg[3] = ret

                # 学习评估/提取诊断信息
            elif cmd == 'testAssess' and cmdID == 1:
                tipmsg, ret = self.da_get_contents(clientAddr, REQmsg)
                REQmsg[3] = ret
                # 学习评估/提取班级学生信息
            elif cmd == 'testAssess' and cmdID == 2:
                tipmsg, ret = self.da_get_ClassStudent(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/类型、用户信息
            elif cmd == 'testAssess' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/打开脑电文件
            elif cmd == 'testAssess' and cmdID == 8:
                tipmsg, ret = self.da_openEEGFile(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 学习评估/读取脑电文件数据块
            elif cmd == 'testAssess' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 学习评估/添加样本
            elif cmd == 'testAssess' and (cmdID == 11 or cmdID == 12):
                tipmsg, ret = self.dt_update_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/删除样本
            elif cmd == 'testAssess' and cmdID == 13:
                tipmsg, ret = self.dt_del_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/添加样本[]
            elif cmd == 'testAssess' and (cmdID == 14 or cmdID == 15):
                tipmsg, ret = self.dt_update_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/提取样本信息
            elif cmd == 'testAssess' and cmdID == 16:
                tipmsg, ret = self.dt_init_resultList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/添加样本信息
            elif cmd == 'testAssess' and cmdID == 17:
                tipmsg, ret = self.dt_update_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/删除样本信息
            elif cmd == 'testAssess' and cmdID == 19:
                tipmsg, ret = self.dt_del_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/添加样本状态信息
            elif cmd == 'testAssess' and cmdID == 21:
                tipmsg, ret = self.dt_add_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/修改样本状态信息
            elif cmd == 'testAssess' and cmdID == 22:
                tipmsg, ret = self.dt_update_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/删除样本状态信息
            elif cmd == 'testAssess' and cmdID == 23:
                tipmsg, ret = self.dt_del_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/删除班级（课堂）信息
            elif cmd == 'testAssess' and cmdID == 24:
                tipmsg, ret = self.da_del_class(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/删除学员学习测试记录
            elif cmd == 'testAssess' and cmdID == 25:
                tipmsg, ret = self.da_del_studentsTest(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/提取诊断信息
            elif cmd == 'testAssess' and cmdID == 26:
                tipmsg, ret = self.da_get_diag(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习评估/提取课堂测试内容
            elif cmd == 'testAssess' and cmdID == 27:
                tipmsg, ret = self.da_get_classContents(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/提取诊断信息
            elif cmd == 'diagTest' and cmdID == 1:
                tipmsg, ret = self.dl_get_contents(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/类型、用户信息
            elif cmd == 'diagTest' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/打开脑电文件
            elif cmd == 'diagTest' and cmdID == 8:
                tipmsg, ret = self.dl_openEEGFile(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 学习测试/读取脑电文件数据块
            elif cmd == 'diagTest' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 学习测试/添加样本
            elif cmd == 'diagTest' and (cmdID == 11 or cmdID == 12):
                tipmsg, ret = self.dt_update_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/删除样本
            elif cmd == 'diagTest' and cmdID == 13:
                tipmsg, ret = self.dt_del_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/添加样本[]
            elif cmd == 'diagTest' and (cmdID == 14 or cmdID == 15):
                tipmsg, ret = self.dt_update_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/提取样本信息
            elif cmd == 'diagTest' and cmdID == 16:
                tipmsg, ret = self.dt_init_resultList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/添加样本信息
            elif cmd == 'diagTest' and cmdID == 17:
                tipmsg, ret = self.dt_update_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/删除样本信息
            elif cmd == 'diagTest' and cmdID == 19:
                tipmsg, ret = self.dt_del_result(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/添加样本状态信息
            elif cmd == 'diagTest' and cmdID == 21:
                tipmsg, ret = self.dt_add_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/修改样本状态信息
            elif cmd == 'diagTest' and cmdID == 22:
                tipmsg, ret = self.dt_update_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/删除样本状态信息
            elif cmd == 'diagTest' and cmdID == 23:
                tipmsg, ret = self.dt_del_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 学习测试/保存并提交诊断信息
            elif cmd == 'diagTest' and cmdID == 28:
                tipmsg, ret = self.dt_diagTest_commit(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 诊断学习/提取诊断信息
            elif cmd == 'diagTraining' and cmdID == 1:
                tipmsg, ret = self.dl_get_contents(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断学习/提取学习信息
            elif cmd == 'diagTraining' and cmdID == 2:
                tipmsg, ret = self.dl_study_get(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断学习/计时结束学习信息
            elif cmd == 'diagTraining' and cmdID == 3:
                tipmsg, ret = self.dl_study_end(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 诊断学习/类型、用户信息
            elif cmd == 'diagTraining' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断学习/类打开脑电文件
            elif cmd == 'diagTraining' and cmdID == 8:
                tipmsg, ret = self.dl_openEEGFile(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 诊断学习/读取脑电文件数据块
            elif cmd == 'diagTraining' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 诊断学习/设置
            elif cmd == 'diagTraining' and cmdID == 16:
                tipmsg, ret = self.init_SampleList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断学习/提取诊断信息
            elif cmd == 'diagTraining' and cmdID == 25:
                tipmsg, ret = self.dl_diag_get(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 脑电会诊/提取诊断信息【首窗口直接查看】
            elif cmd == 'consulting' and cmdID == 3:
                tipmsg, ret = self.diag_get(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 脑电会诊/类型、用户信息
            elif cmd == 'consulting' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 脑电会诊/脑电文件
            elif cmd == 'consulting' and cmdID == 7:
                tipmsg, ret = self.get_fileNameByIdDate(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/打开脑电文件
            elif cmd == 'consulting' and cmdID == 8:
                tipmsg, ret = self.openEEGFile(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 脑电会诊/读取脑电文件数据块
            elif cmd == 'consulting' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 脑电会诊/添加样本
            elif cmd == 'consulting' and (cmdID == 11 or cmdID == 12):
                tipmsg, ret = self.update_sampleInfo12(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/删除样本
            elif cmd == 'consulting' and cmdID == 13:
                tipmsg, ret = self.del_sample13(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/添加样本[]
            elif cmd == 'consulting' and (cmdID == 14 or cmdID == 15):
                tipmsg, ret = self.update_sampleInfo15(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/提取样本信息
            elif cmd == 'consulting' and cmdID == 16:
                tipmsg, ret = self.init_SampleList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/添加样本信息
            elif cmd == 'consulting' and cmdID == 17:
                tipmsg, ret = self.insert_sample17(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/删除样本信息
            elif cmd == 'consulting' and cmdID == 19:
                tipmsg, ret = self.del_sample19(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/添加样本状态信息
            elif cmd == 'consulting' and cmdID == 21:
                tipmsg, ret = self.add_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/修改样本状态信息
            elif cmd == 'consulting' and cmdID == 22:
                tipmsg, ret = self.update_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/删除样本状态信息
            elif cmd == 'consulting' and cmdID == 23:
                tipmsg, ret = self.del_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/提取未诊断信息
            elif cmd == 'consulting' and cmdID == 24:
                tipmsg, ret = self.diags_notDiag_get(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/提取诊断信息
            elif cmd == 'consulting' and cmdID == 25:
                tipmsg, ret = self.diag_get(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/填写诊断信息
            elif cmd == 'consulting' and cmdID == 26:
                tipmsg, ret = self.diag_add(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/修改诊断信息
            elif cmd == 'consulting' and cmdID == 27:
                tipmsg, ret = self.diag_update(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/保存并提交诊断信息
            elif cmd == 'consulting' and cmdID == 28:
                tipmsg, ret = self.diag_commit(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 脑电会诊/拒绝诊断信息
            elif cmd == 'consulting' and cmdID == 29:
                tipmsg, ret = self.diag_refused(clientAddr, REQmsg)
                REQmsg[3] = ret

            # 诊断查询/提取诊断信息
            elif cmd == 'manualQuery' and cmdID == 1:
                tipmsg, ret = self.mq_get_diags_Diagnosed(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断查询/类型、用户信息
            elif cmd == 'manualQuery' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断查询/类 /脑电文件
            elif cmd == 'manualQuery' and cmdID == 7:
                tipmsg, ret = self.get_fileNameByIdDate(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断查询/类打开脑电文件
            elif cmd == 'manualQuery' and cmdID == 8:
                tipmsg, ret = self.openEEGFile(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 诊断查询/类/读取脑电文件数据块
            elif cmd == 'manualQuery' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 诊断查询/设置
            elif cmd == 'manualQuery' and cmdID == 16:
                tipmsg, ret = self.init_SampleList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断查询/提取诊断信息
            elif cmd == 'manualQuery' and cmdID == 25:
                tipmsg, ret = self.diag_get(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 诊断查询/查询、分页
            elif cmd == 'manualQuery' and cmdID == 30:
                tipmsg, ret = self.mq_paging(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/类型、用户信息
            elif cmd == 'manual' and cmdID == 4:
                tipmsg, ret = self.get_type_info(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/脑电文件
            elif cmd == 'manual' and cmdID == 7:
                tipmsg, ret = self.get_fileNameByIdDate(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/打开脑电文件
            elif cmd == 'manual' and cmdID == 8:
                tipmsg, ret = self.openEEGFile(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 标注诊断/读取脑电文件数据块
            elif cmd == 'manual' and (cmdID == 9 or cmdID == 10):
                tipmsg, ret = self.load_dataDynamical(clientAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            # 标注诊断/添加样本
            elif cmd == 'manual' and (cmdID == 11 or cmdID == 12):
                tipmsg, ret = self.update_sampleInfo12(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/删除样本
            elif cmd == 'manual' and cmdID == 13:
                tipmsg, ret = self.del_sample13(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/添加样本[]
            elif cmd == 'manual' and (cmdID == 14 or cmdID == 15):
                tipmsg, ret = self.update_sampleInfo15(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/设置
            elif cmd == 'manual' and cmdID == 16:
                tipmsg, ret = self.init_SampleList(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/添加样本信息
            elif cmd == 'manual' and cmdID == 17:
                tipmsg, ret = self.insert_sample17(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/删除样本信息
            elif cmd == 'manual' and cmdID == 19:
                tipmsg, ret = self.del_sample19(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/添加样本状态信息
            elif cmd == 'manual' and cmdID == 21:
                tipmsg, ret = self.add_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/修改样本状态信息
            elif cmd == 'manual' and cmdID == 22:
                tipmsg, ret = self.update_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/删除样本状态信息
            elif cmd == 'manual' and cmdID == 23:
                tipmsg, ret = self.del_sampleInfo_state(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/提取未诊断信息
            elif cmd == 'manual' and cmdID == 24:
                tipmsg, ret = self.diags_notDiag_get(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/提取诊断信息
            elif cmd == 'manual' and cmdID == 25:
                tipmsg, ret = self.diag_get(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/填写诊断信息
            elif cmd == 'manual' and cmdID == 26:
                tipmsg, ret = self.diag_add(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/修改诊断信息
            elif cmd == 'manual' and cmdID == 27:
                tipmsg, ret = self.diag_update(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/保存并提交诊断信息
            elif cmd == 'manual' and cmdID == 28:
                tipmsg, ret = self.diag_commit(clientAddr, REQmsg)
                REQmsg[3] = ret
            # 标注诊断/拒绝诊断信息
            elif cmd == 'manual' and cmdID == 29:
                tipmsg, ret = self.diag_refused(clientAddr, REQmsg)
                REQmsg[3] = ret
            ##===dsj ]====

            # 创建会诊
            elif cmd == 'createCons' and cmdID == 1:
                tipmsg, ret = self.getDoctorInfo(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'createCons' and cmdID == 2:
                tipmsg, ret = self.getCpltCheckInfo(cmdID)
                REQmsg[3] = ret
            elif cmd == 'createCons' and cmdID == 3:
                tipmsg, ret = self.getHistoryCons(cmdID)
                REQmsg[3] = ret
            elif cmd == 'createCons' and cmdID == 4:
                tipmsg, ret = self.createCons(cmdID, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createCons' and cmdID == 6:
                tipmsg, ret = self.getAllConsInfo(cmdID, REQmsg[3], userID)
                REQmsg[3] = ret
            elif cmd == 'createCons' and cmdID == 7:
                tipmsg, ret = self.inqConsInfo(cmdID, REQmsg[3], userID)
                REQmsg[3] = ret
            elif cmd == 'createCons' and cmdID == 8:
                tipmsg, ret = self.getSearchDoctorInfo(cmdID, REQmsg[3])
                REQmsg[3] = ret

            # 获取病人信息
            elif cmd == 'patientManager' and cmdID == 1:
                tipmsg, ret = self.getPatientInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            # 新增病人信息
            elif cmd == 'patientManager' and cmdID == 2:
                tipmsg, ret = self.addPatientInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            # 删除病人信息
            elif cmd == 'patientManager' and cmdID == 3:
                tipmsg, ret = self.delPatientInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            # 编辑病人信息
            elif cmd == 'patientManager' and cmdID == 4:
                tipmsg, ret = self.updatePatientInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            # 查询病人信息
            elif cmd == 'patientManager' and cmdID == 5:
                tipmsg, ret = self.inqPatientInfo(cmdID, REQmsg[3][0], REQmsg[3][1], REQmsg)
                REQmsg[3] = ret
            elif cmd == 'patientManager' and cmdID == 6:
                tipmsg, ret = self.patientPaging(cmdID, REQmsg)
                REQmsg[3] = ret

            # 创建课堂
            elif cmd == 'createLesson' and cmdID == 1:
                tipmsg, ret = self.getLessonInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 2:
                tipmsg, ret = self.getDiagCheckID(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 3:
                tipmsg, ret = self.getFileName(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 4:
                tipmsg, ret = self.addLesson(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 5:
                tipmsg, ret = self.delLesson(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 6:
                tipmsg, ret = self.updateLesson(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 7:
                tipmsg, ret = self.getStudentInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 8:
                tipmsg, ret = self.updateStudentInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 9:
                tipmsg, ret = self.getContentInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 11:
                tipmsg, ret = self.updateContentInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 13:
                tipmsg, ret = self.inquiryLessonInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 14:
                tipmsg, ret = self.getCheckUserID(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 16:
                tipmsg, ret = self.addStudent(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 17:
                tipmsg, ret = self.getlessonStudent(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 18:
                tipmsg, ret = self.delStudent(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 19:
                tipmsg, ret = self.addLessonContent(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 20:
                tipmsg, ret = self.delLessonContent(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 21:
                tipmsg, ret = self.studentPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 22:
                tipmsg, ret = self.searchStudentPageInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 23:
                tipmsg, ret = self.eegPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'createLesson' and cmdID == 24:
                tipmsg, ret = self.searchEegPageInfo(macAddr, REQmsg)
                REQmsg[3] = ret

            # 算法管理
            elif cmd == 'algorithm' and cmdID == 1:
                tipmsg, ret = self.getAlgorithmInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'algorithm' and cmdID == 2:
                tipmsg, ret = self.addAlgorithmInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'algorithm' and cmdID == 3:
                tipmsg, ret = self.delAlgorithmInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'algorithm' and cmdID == 4:
                tipmsg, ret = self.inquiryAlgorithmInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'algorithm' and cmdID == 5:
                tipmsg, ret = self.addAlgorithmFile(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'algorithm' and cmdID == 6:
                tipmsg, ret = self.getAlgorithmFileName(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'algorithm' and cmdID == 7:
                tipmsg, ret = self.algorithmInfoPaging(macAddr, REQmsg)
                REQmsg[3] = ret



            # 样本统计模块
            # 样本统计
            elif cmd == 'sampleState' and cmdID == 1:
                tipmsg, ret = self.getSpecificInfo(cmdID, REQmsg[3])
                REQmsg[3] = ret
            # 获取选择的样本类型数量
            elif cmd == 'sampleState' and cmdID == 2:
                tipmsg, ret = self.getSpecificNum(cmdID, REQmsg[3])
                REQmsg[3] = ret
            # 获取样本详细信息
            elif cmd == 'sampleState' and cmdID == 3:
                tipmsg, ret = self.getSpecificDetail(cmdID, REQmsg[3])
                REQmsg[3] = ret
            # 根据过滤器信息获取样本信息
            elif cmd == 'sampleState' and cmdID == 4:
                tipmsg, ret = self.getSpecNumFromFlt(cmdID, REQmsg[3])
                REQmsg[3] = ret

            # 构建集合模块
            elif cmd == 'setBuild' and cmdID == 1:
                tipmsg, ret = self.getSetInitData(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 2:
                tipmsg, ret = self.getSet(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 3:
                tipmsg, ret = self.getSetBuildFltData(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 4:
                tipmsg, ret = self.getSetExportInitData(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 5:
                tipmsg, ret = self.getSetExportData(cmdID, userID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 6:
                tipmsg, ret = self.delSet(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 7:
                tipmsg, ret = self.buildSet(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 8:
                tipmsg, ret = self.buildSetGetPg(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 9:
                tipmsg, ret = self.buildSetCancel(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 10:
                tipmsg, ret = self.getSetSearch(cmdID, REQmsg[3])
                REQmsg[3] = ret
            elif cmd == 'setBuild' and cmdID == 11:
                tipmsg, ret = self.getSetDescribe(cmdID, REQmsg[3])
                REQmsg[3] = ret


            # 模型管理
            elif cmd == 'classifier' and cmdID == 1:
                tipmsg, ret = self.getClassifierAlgSetNameRes(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 2:
                tipmsg, ret = self.inquiryClassifierInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 3:
                tipmsg, ret = self.delClassifierInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 4:
                tipmsg, ret = self.cls_getAlgorithmInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 5:
                tipmsg, ret = self.checkClassifierInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 6:
                tipmsg, ret = self.cls_restate(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 7:
                tipmsg, ret = self.checkstate(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 8:
                tipmsg, ret = self.model_transmit_message(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 9:
                tipmsg, ret = self.classifier_id_inquiry(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 10:
                tipmsg, ret = self.classifierPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 11:
                tipmsg, ret = self.classifierPaging_al(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 12:
                tipmsg, ret = self.inquiryCls_alg_Info(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 13:
                tipmsg, ret = self.getClassifier_config(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 14:
                tipmsg, ret = self.getSelectSetInfo(cmdID, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 15:
                tipmsg, ret = self.inquiryCls_set_Info(cmdID, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 16:
                tipmsg, ret = self.classifierPaging_set(cmdID, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 17:
                tipmsg, ret = self.upload_scheme(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'classifier' and cmdID == 18:
                tipmsg, ret = self.upload_model(cmdID, REQmsg)
                REQmsg[3] = ret

            # 模型训练
            elif cmd == 'modelTrain' and cmdID == 1:
                tipmsg, ret = self.getModelInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 2:
                tipmsg, ret = self.get_classifierInfo_by_setId_and_algId(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 3:
                tipmsg, ret = self.runProcessForTrain(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 4:
                tipmsg, ret = self.modelAlgInfoPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 5:
                tipmsg, ret = self.modelInquiryAlgInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 6:
                tipmsg, ret = self.modelSetInfoPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 7:
                tipmsg, ret = self.modelInquirySetInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 8:
                tipmsg, ret = self.matchAlgSet(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 9:
                tipmsg, ret = self.getTrainPerformance(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 10:
                tipmsg, ret = self.getProgress(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTrain' and cmdID == 11:
                tipmsg, ret = self.train_cancel(macAddr, REQmsg)
                REQmsg[3] = ret

            # 脑电扫描
            elif cmd == 'auto' and cmdID == 1:
                tipmsg, ret = self.getAutoInitData(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 2:
                tipmsg, ret = self.getPatientMeasureDay(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 3:
                tipmsg, ret = self.getPatientFile(macAddr, REQmsg)
                REQmsg[3] = ret

                # 模型测试
            elif cmd == 'modelTest' and cmdID == 1:
                tipmsg, ret = self.getClassifierInfo(REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTest' and cmdID == 2:
                tipmsg, ret = self.isTesting(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'modelTest' and cmdID == 3:
                tipmsg, ret = self.getProgress(macAddr, REQmsg)
                REQmsg[3] = ret

            # 脑电扫描
            elif cmd == 'auto' and cmdID == 1:
                tipmsg, ret = self.getAutoInitData(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 2:
                tipmsg, ret = self.getPatientMeasureDay(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 3:
                tipmsg, ret = self.getPatientFile(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 4:
                tipmsg, ret = self.getFileChannels(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 5:
                tipmsg, ret = self.autoClassifierInfoPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 6:
                tipmsg, ret = self.autoInquiryClassifierInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 7:
                tipmsg, ret = self.runProcessForScan(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 8:
                tipmsg, ret = self.matchClassifierFile(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 9:
                tipmsg, ret = self.getProgress(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'auto' and cmdID == 10:
                tipmsg, ret = self.scan_cancel(macAddr, REQmsg)
                REQmsg[3] = ret

            # 评估标注
            elif cmd == 'assessLabel' and cmdID == 1:
                tipmsg, ret = self.getAssessInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 2:
                tipmsg, ret = self.getModelIdName(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 3:
                tipmsg, ret = self.assessClassifierInfoPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 4:
                tipmsg, ret = self.getAssessFileInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 8:
                tipmsg, ret = self.assessOpenEEGFile(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 9:
                tipmsg, ret = self.load_dataDynamical(macAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 10:
                tipmsg, ret = self.load_dataDynamical(macAddr, REQmsg, self.curUser)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 11:
                tipmsg, ret = self.update_labelListInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 12:
                tipmsg, ret = self.update_labelListInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 13:
                tipmsg, ret = self.update_labelListInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 14:
                tipmsg, ret = self.del_labelListInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 15:
                tipmsg, ret = self.del_labelListInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'assessLabel' and cmdID == 16:
                tipmsg, ret = self.del_labelListInfo(macAddr, REQmsg)
                REQmsg[3] = ret


            # 清理标注
            elif cmd == 'clearLabel' and cmdID == 1:
                tipmsg, ret = self.getClearLabelInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 2:
                tipmsg, ret = self.inquiryScanClassifierInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 3:
                tipmsg, ret = self.scanClassifierInfoPaging(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 4:
                tipmsg, ret = self.getScanInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 5:
                tipmsg, ret = self.getCurClearLabelInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 6:
                tipmsg, ret = self.getScanFileInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 7:
                tipmsg, ret = self.delLabelListInfo(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 8:
                tipmsg, ret = self.delLabelByModelFile(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 9:
                tipmsg, ret = self.getLabelInfoByAssess(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'clearLabel' and cmdID == 10:
                tipmsg, ret = self.getSearchScanFileInfo(macAddr, REQmsg)
                REQmsg[3] = ret

            # EEG 脑电图绘制
            elif cmd == 'EEG' and cmdID == 0:
                tipmsg, ret = self.openEEGFile(macAddr, REQmsg)
                REQmsg[3] = ret
            elif cmd == 'EEG' and cmdID == 1:
                tipmsg, ret = self.loadEEGData(macAddr, REQmsg)
                REQmsg[3] = ret

            else:
                REQmsg[3] = ['0', REQmsg[1], f'未定义命令{REQmsg[1]}']
                tipmsg = [REQmsg[2], f"应答{REQmsg[0]} ", f'未定义命令{REQmsg[1]}', '']
        self.myTip(REQmsg[1], tipmsg)
        return REQmsg


    # EEG 脑电图绘制
    def openEEGFile(self, macAddr, REQmsg):
        patient_id = REQmsg[3][0]
        check_id = REQmsg[3][1]
        file_id = REQmsg[3][2]
        nSecWin = REQmsg[3][3]
        nDotSec = REQmsg[3][4]
        nWinBlock = REQmsg[3][5]
        eeg = self.appUtil.openEEGFile(check_id, file_id)
        if eeg[0] == '0':
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '打开脑电文件失败', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}打开脑电文件失败"]
            return msgtip, ret

        lenBlock = min(nSecWin * nWinBlock * eeg[3], eeg[4])
        nSample = 1 if nDotSec >= eeg[3] else int(round(eeg[3] / nDotSec))
        lenWin = nSecWin * eeg[3] // nSample
        data = self.appUtil.readEEG(check_id, file_id, 0, lenBlock, nSample)
        if data[0] == '0':
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '打开脑电文件失败', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}打开脑电文件失败"]
            return msgtip, ret
        patient = self.dbUtil.getPatientInfo(where_name='patient_id', where_value=patient_id)[0]
        type_info = self.dbUtil.get_typeInfo()
        montage = []
        labels = self.dbUtil.getWinSampleInfo(check_id, file_id, 0, lenBlock)
        for label in labels:
            label[2] // nSample
            label[3] // nSample
        msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '打开脑电文件成功', "", '']
        ret = ['1', REQmsg[1], [patient, type_info, montage, eeg[1], eeg[2], eeg[3], eeg[4], eeg[5], eeg[6], eeg[7], lenBlock // nSample, nSample, lenWin, data[1], labels]]
        return msgtip, ret

    def loadEEGData(self, macAddr, REQmsg):
        msg = REQmsg[3]
        print(msg)
        check_id = msg[0]
        file_id = msg[1]
        min_t = msg[2]
        max_t = msg[3]
        nSample = msg[4]
        eeg = self.appUtil.readEEG(check_id, file_id, min_t, max_t, nSample)
        if eeg[0] == '0':
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '打开脑电文件失败', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}打开脑电文件失败"]
            return msgtip, ret
        data = eeg[1]
        rate = eeg[2]
        begin = min_t // rate
        end = max_t // rate
        labels = self.dbUtil.getWinSampleInfo(check_id, file_id, begin, end)
        for label in labels:
            label[2] // nSample
            label[3] // nSample
        msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '获取脑电数据成功', "", '']
        ret = ['1', REQmsg[1], [data, labels]]
        return msgtip, ret


    def login(self, userAccount, pwd, macAddr):
        case, msg, userInfo = self.curUser.login(userAccount, pwd, macAddr)
        ret = [case, msg, userInfo]
        print(f'RET: {ret}')
        msgtip = ['1', msg, userAccount, '']
        return msgtip, ret

    def logout(self, REQmsg, macAddr):
        userID = REQmsg[2]
        account = REQmsg[3][0]
        result = self.curUser.logout(userID, macAddr)
        if result:
            msg = result[2]
            if result[0] == 1:
                msgtip = [account, msg, '', '']
                ret = ['1', REQmsg[1], msg, '']
            else:
                msgtip = [account, msg, '', '']
                ret = ['0', REQmsg[1], msg, '']
        else:
            msgtip = [account, f"获取当前用户信息错误，退出失败！！！", '', '']
            ret = ['0', REQmsg[1], f"获取当前用户信息错误，退出失败！！！", '']
        return msgtip, ret

    # 修改密码
    def changePwd(self, REQmsg):
        try:
            uid = REQmsg[3][0]
            account = REQmsg[3][1]
            oldPwd = REQmsg[3][2]
            newPwd = REQmsg[3][3]
            cmdID = REQmsg[1]
            user_info = self.dbUtil.getUserInfo('uid', uid)
            if user_info:
                if oldPwd != user_info[0][2]:
                    msgtip = [account, f"原密码错误", '', '']
                    ret = ['0', cmdID, f"原密码错误", False]
                else:
                    user_msg = [uid, newPwd]
                    result = self.dbUtil.update_userInfo(user_msg, flag='1')
                    if result:
                        msgtip = [account, f"修改密码成功", '', '']
                        ret = ['1', cmdID, f"修改密码成功", True]
                    else:
                        msgtip = [account, f"修改密码失败", '', '']
                        ret = ['1', cmdID, f"修改密码失败", True]
            return msgtip, ret
        except Exception as e:
            print("changePwd", e)
            account = REQmsg[3][1]
            cmdID = REQmsg[1]
            msgtip = [account, f"修改密码失败:{e}", '', '']
            ret = ['1', cmdID, f"修改密码失败:{e}", True]
            return msgtip, ret

    # 用户管理模块
    # 根据传入参数获取数据库用户信息
    def getUserInfo(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 12
            reset = REQmsg[3][2]
            ui_size = self.dbUtil.getUserInfoLen()
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal:
                _curPageIndex = ptotal
            if _curPageIndex == 1:
                result = self.dbUtil.getUserInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows + 1)
            else:
                result = self.dbUtil.getUserInfoByPage(offset=((_curPageIndex - 1) * _Pagerows + 1), psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, ptotal, reset]
            return msgtip, ret
        except Exception as e:
            print('getUserInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    # 根据传入参数添加数据库用户信息
    def addUserInfo(self, macAddr, REQmsg):
        # print('addUserInfo')
        try:
            user_info = REQmsg[3]
            r, result = self.dbUtil.addUserInfo(user_info)
            isSearch = REQmsg[3][12]
            if r == '1':
                _curPageIndex = REQmsg[3][11]
                if _curPageIndex <= 0:
                    _curPageIndex = 1
                _Pagerows = 12
                if isSearch:
                    key_word = REQmsg[3][13]
                    key_value = REQmsg[3][14]
                    result = self.dbUtil.getSearchUserInfoByPage(where_name=key_word, where_value=key_value,
                                                                 offset=(_curPageIndex - 1) * _Pagerows,
                                                                 psize=_Pagerows)
                    ui_size = self.dbUtil.getUserInfoLen(where_name=key_word, where_like=key_value)
                    ptotal = ceil(ui_size[0][0] / _Pagerows)
                else:
                    ui_size = self.dbUtil.getUserInfoLen()
                    ptotal = ceil(ui_size[0][0] / _Pagerows)
                    if _curPageIndex > ptotal:
                        _curPageIndex = ptotal
                    if _curPageIndex == 1:
                        result = self.dbUtil.getUserInfoByPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                               psize=_Pagerows + 1)
                    else:
                        result = self.dbUtil.getUserInfoByPage(offset=((_curPageIndex - 1) * _Pagerows + 1),
                                                               psize=_Pagerows)
                msgtip = [REQmsg[1], f"添加用户信息成功", f'{REQmsg[2]}', '']
                ret = ['1', REQmsg[1], result, ptotal, isSearch]
                return msgtip, ret
            else:
                msgtip = [REQmsg[1], f"添加用户信息失败", f'{result}', '']
                ret = ['0', REQmsg[1], user_info]
                return msgtip, ret
        except Exception as e:
            print('addUserInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    # 根据传入参数删除用户信息
    def delUserInfo(self, macAddr, REQmsg):
        # print('delUserInfo')
        try:
            msgtip, ret = self.curUser.delUserInfo(REQmsg)
            return msgtip, ret
        except Exception as e:
            print('delUserInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    # 根据传入参数编辑用户信息
    def updateUserInfo(self, macAddr, REQmsg):
        # print('updateUserInfo')
        try:
            msgtip, ret = self.curUser.updateUserInfo(REQmsg)
            return msgtip, ret
        except Exception as e:
            print('updateUserInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def userPaging(self, macAddr, REQmsg):
        try:
            isSearch = REQmsg[3][3]
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 12
            if isSearch:
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                result = self.dbUtil.getSearchUserInfoByPage(where_name=key_word, where_value=key_value,
                                                             offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            else:
                if _curPageIndex == 1:
                    result = self.dbUtil.getUserInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows + 1)
                else:
                    result = self.dbUtil.getUserInfoByPage(offset=((_curPageIndex - 1) * _Pagerows + 1),
                                                           psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, isSearch]
            return msgtip, ret
        except Exception as e:
            print('userPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def inquiryUserInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            _curPageIndex = REQmsg[3][2]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][3]
            if _Pagerows <= 0:
                _Pagerows = 12
            result = self.dbUtil.getSearchUserInfoByPage(where_name=key_word, where_value=key_value,
                                                         offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            ui_size = self.dbUtil.getUserInfoLen(where_name=key_word, where_like=key_value)
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, ptotal]
            return msgtip, ret
        except Exception as e:
            print('inquiryUserInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    # 导联配置模块
    # 根据传入参数获取导联配置信息
    def getMontage(self, macAddr, REQmsg):
        try:
            r, montageData = self.appUtil.getMontage()
            if r == '0':
                msgtip = [REQmsg[1], f"获取导联配置信息失败", f'{REQmsg[2]}', '']
                ret = ['0', REQmsg[1], montageData]
                return msgtip, ret
            elif r == '1':
                msgtip = [REQmsg[1], f"获取导联配置信息成功", f'{REQmsg[2]}', '']
                ret = ['1', REQmsg[1], montageData]
                return msgtip, ret
        except Exception as e:
            print('getMontage', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '配置文件不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}配置文件不成功"]
            return msgtip, ret

    # 根据传入参数添加导联方案
    def addMontageScheme(self, macAddr, REQmsg):
        try:
            result = self.appUtil.addMontageScheme(REQmsg[3][0])
            if result[0] == '1':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['1', REQmsg[1], REQmsg[3][0]]
                return msgtip, ret
            elif result[0] == '0':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['0', REQmsg[1], REQmsg[3][0]]
                return msgtip, ret
        except Exception as e:
            print('addMontageScheme', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '配置文件不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}配置文件不成功"]
            return msgtip, ret

    # 根据传入参数编辑导联方案
    def editMontageScheme(self, macAddr, REQmsg):
        try:
            result = self.appUtil.editMontageScheme(where_name=REQmsg[3][0], set_name=REQmsg[3][1])
            if result[0] == '1':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['1', REQmsg[1], REQmsg[3]]
                return msgtip, ret
            elif result[0] == '0':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['0', REQmsg[1], REQmsg[3]]
                return msgtip, ret
        except Exception as e:
            print('editMontageScheme', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '配置文件不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}配置文件不成功"]
            return msgtip, ret

    # 根据传入参数删除导联方案
    def delMontageScheme(self, macAddr, REQmsg):
        try:
            result = self.appUtil.delMontageScheme(REQmsg[3][0])
            if result[0] == '1':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['1', REQmsg[1], REQmsg[3]]
                return msgtip, ret
            elif result[0] == '0':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['0', REQmsg[1], REQmsg[3]]
                return msgtip, ret
        except Exception as e:
            print('delMontageScheme', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '配置文件不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}配置文件不成功"]
            return msgtip, ret

    # 根据传入参数保存导联方案通道
    def saveMontageChannel(self, macAddr, REQmsg):
        try:
            result = self.appUtil.saveMontageChannel(REQmsg[3][0], REQmsg[3][1])
            if result[0] == '1':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['1', REQmsg[1], REQmsg[3]]
                return msgtip, ret
            elif result[0] == '0':
                msgtip = [REQmsg[1], f"{result[1]}", f'{REQmsg[2]}', '']
                ret = ['0', REQmsg[1], REQmsg[3]]
                return msgtip, ret
        except Exception as e:
            print('saveMontageChannel', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '配置文件不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}配置文件不成功"]
            return msgtip, ret

    # 标注类型模块
    # 根据传入参数获取数据库标注类型
    def getTypeInfo(self, REQmsg):
        try:
            print('getTypeInfo')
            account = REQmsg[3][0]
            name = REQmsg[3][1]
            value = REQmsg[3][2]
            type_info = self.dbUtil.get_typeInfo(name, value)
            if type_info:
                msgtip = [account, f"查询标注类型信息成功", '', '']
                ret = ['1', REQmsg[1], f"查询标注类型信息成功", type_info]
                return msgtip, ret
            else:
                msgtip = [account, f"查询标注类型信息失败", '', '']
                ret = ['0', REQmsg[1], f"查询标注类型信息失败", type_info]
                return msgtip, ret
        except Exception as e:
            print('getTypeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"查询标注类型信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"查询标注类型信息失败:{e}", '']
            return msgtip, ret

    # 根据传入参数增加数据库标注类型
    def addTypeInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            type_info = REQmsg[3][1:]
            result = self.dbUtil.add_typeInfo(type_info)
            if result:
                msgtip = [account, f"添加标注类型信息成功", '', '']
                ret = ['1', REQmsg[1], f"添加标注类型信息成功", type_info]
                # REQmsg[3] = ret
                return msgtip, ret
            else:
                msgtip = [account, f"添加标注类型信息失败", '', '']
                ret = ['0', REQmsg[1], f"添加标注类型信息失败", type_info]
                return msgtip, ret
        except Exception as e:
            print('addTypeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"添加标注类型信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"添加标注类型信息失败:{e}", '']
            return msgtip, ret

    # 根据传入参数删除数据库标注类型
    def delTypeInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            type_info = REQmsg[3][1:]
            type_id = type_info[0]
            result = self.dbUtil.del_typeInfo('type_id', type_id)
            if result:
                msgtip = [account, f"删除标注类型信息成功", '', '']
                ret = ['1', REQmsg[1], f"删除标注类型信息成功", type_info]
                return msgtip, ret
            else:
                msgtip = [account, f"删除标注类型信息失败", '', '']
                ret = ['0', REQmsg[1], f"删除标注类型信息失败", type_info]
                return msgtip, ret
        except Exception as e:
            print('delTypeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"删除标注类型信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"删除标注类型信息失败:{e}", '']
            return msgtip, ret

    # 根据传入参数更新数据库标注类型
    def updateTypeInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            type_info = REQmsg[3][1:]
            value = REQmsg[3][1]
            type_id = REQmsg[3][2]
            result = self.dbUtil.update_typeInfo(value, 'type_id', type_id)
            if result:
                msgtip = [account, f"修改标注类型信息成功", '', '']
                ret = ['1', REQmsg[1], f"修改标注类型信息成功", type_info]
                return msgtip, ret
            else:
                msgtip = [account, f"修改标注类型信息失败", '', '']
                ret = ['0', REQmsg[1], f"修改标注类型信息失败", type_info]
                return msgtip, ret
        except Exception as e:
            print('updateTypeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"修改标注类型信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"修改标注类型信息失败:{e}", '']
            return msgtip, ret


    # 脑电导入模块
    # 根据传入参数获取数据库病人诊断信息
    def getPatientCheckInfo(self, REQmsg):
        try:
            print('getPatientCheckInfo')
            account = REQmsg[3][0]
            uid = REQmsg[3][1]
            value = REQmsg[3][2]
            rpc, patientCheck_info = self.dbUtil.get_patientCheckInfo(uid)
            rf, file_info = self.dbUtil.get_fileInof_detail(uid)
            if (rpc or rf) == '0':
                print("patientCheck_info:", patientCheck_info)
                print("file_info:", file_info)
                account = REQmsg[3][0]
                patientCheck_info = None
                patient_info = None
                doctor_info = None
                file_info = None
                msgtip = [account, f"查询病人诊断信息失败", '', '']
                ret = ['0', REQmsg[1], f"查询病人诊断信息失败,操作数据库出错",
                       [patientCheck_info, patient_info, doctor_info, file_info]]
                return msgtip, ret
            else:
                msgtip = [account, f"查询病人诊断信息成功", '', '']
                ret = ['1', REQmsg[1], f"查询病人诊断成功", [patientCheck_info, None, None, file_info]]
                return msgtip, ret
        except Exception as e:
            print('getPatientCheckInfo', e)
            account = REQmsg[3][0]
            patientCheck_info = None
            patient_info = None
            doctor_info = None
            file_info = None
            msgtip = [account, f"查询病人诊断信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"查询病人诊断信息失败:{e}",
                   [patientCheck_info, patient_info, doctor_info, file_info]]
            return msgtip, ret


    # 根据传入参数删除数据库病人诊断信息
    # 不仅要删除检查信息，相关脑电记录（包括文件和数据库记录）都需要删除

    def delPatientCheckInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            check_info = REQmsg[3][1:]
            check_id = check_info[0]
            result = self.dbUtil.del_patientCheckInfo('check_id', check_id)
            if result:
                result_1 = self.appUtil.removeFile(check_id=check_id)
                if result_1:
                    msgtip = [account, f"删除病人诊断信息成功", '', '']
                    ret = ['1', REQmsg[1], f"删除病人诊断信息成功", check_info]
                    return msgtip, ret
                else:
                    msgtip = [account, f"删除病人诊断信息成功,删除远程脑电文件失败", '', '']
                    ret = ['0', REQmsg[1], f"删除病人诊断信息成功,删除远程脑电文件失败", check_info]
                    return msgtip, ret
            else:
                msgtip = [account, f"删除病人诊断信息失败", '', '']
                ret = ['0', REQmsg[1], f"删除病人诊断信息失败", check_info]
                return msgtip, ret
        except Exception as e:
            print('delPatientCheckInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"删除病人诊断信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"删除病人诊断信息失败:{e}", None]
            return msgtip, ret

        # 根据传入参数增加数据库病人检查信息

    def addCheckInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            check_info = REQmsg[3][1:]
            result = self.dbUtil.add_checkInfo(check_info)
            if result[0] == '1':
                msgtip = [account, result[1], '', '']
                ret = ['1', REQmsg[1], result[1], check_info]
                return msgtip, ret
            else:
                msgtip = [account, result[1], '', '']
                ret = ['0', REQmsg[1], result[1], check_info]
                return msgtip, ret
        except Exception as e:
            print('addCheckInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"添加脑电检查信息失败：{e}", '', '']
            ret = ['0', REQmsg[1], f"添加脑电检查信息失败：{e}", None]
            return msgtip, ret

    # 检查用户基本配置
    # TODO:思考这里需要添加更新check_info操作吗
    def checkMakeFileNameXXX(self, REQmsg):
        try:
            account = REQmsg[3][0]
            user_id = REQmsg[3][1]
            filemsg = REQmsg[3][2]
            freq = int(REQmsg[3][3])
            # 获取用户基本配置信息
            congfig_id = filemsg[4]
            ru, user_config = self.dbUtil.query_configData('config_id', congfig_id)
            if ru == '1':
                # 截取最需要的部分
                # [sampling_rate, notch, low_pass, high_pass]
                # user_config = (250, 50, 100, 0.5)
                if user_config:
                    user_config = user_config[0]
                    user_config = user_config[2:-1]

                    sampling_rate = int(user_config[0])
                    # 判断用户当前配置是否适合处理该脑电文件
                    if (freq >= sampling_rate):
                        try:
                            # 制作文件名
                            check_id = filemsg[1]
                            # 这里增加一个锁，保证服务端同时只为一个用户生成文件名，并添加数据库记录
                            self.filename_mutex.acquire()
                            filename, file_id = self.appUtil.makeFilePath(check_id)
                            filemsg[2] = file_id
                            self.dbUtil.add_fileInfo(filemsg)
                            self.filename_mutex.release()
                        except Exception as e:
                            print('checkMakeFileName_makeFilename', e)
                            return
                        if filename:
                            msgtip = [account, f"检查脑电文件配置成功，生成文件名成功", '', '']
                            ret = ['1', REQmsg[1], f"检查脑电文件配置成功，生成文件名成功", [user_config, filename]]
                            return msgtip, ret
                        else:
                            msgtip = [account, f"检查脑电文件配置成功，生成文件名失败", '', '']
                            ret = ['0', REQmsg[1], f"检查脑电文件配置成功，生成文件名失败", [user_config]]
                            return msgtip, ret
                    # 较低采样率不进行转化
                    else:
                        msgtip = [account, f"当前脑电文件采样率为:{freq}和用户基本配置采样率:{sampling_rate}不符!!!!",
                                  '', '']
                        ret = ['2', REQmsg[1],
                               f"当前脑电文件采样率为:{freq}和用户基本配置采样率:{sampling_rate}不符!!!!\n请重新去配置选择模块选合适的功能！！",
                               [user_config]]
                        return msgtip, ret
                else:
                    msgtip = [account, f"未在数据库找到当前配置信息！！", '', '']
                    ret = ['0', REQmsg[1], f"未在数据库找到当前配置信息！！", [None]]
                    return msgtip, ret


            else:
                msgtip = [account, f"获取配置失败", '', '']
                ret = ['0', REQmsg[1], f"获取配置失败", [None]]
                return msgtip, ret
        except Exception as e:
            print('checkMakeFileName', e)
            account = REQmsg[3][0]
            msgtip = [account, f"脑电上传失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"脑电上传失败:{e}", [None]]
            return msgtip, ret

    def checkConfig(self, REQmsg):
        try:
            account = REQmsg[3][0]
            user_id = REQmsg[3][1]
            filemsg = REQmsg[3][2]
            freq = REQmsg[3][3]
            # 获取用户基本配置信息
            congfig_id = filemsg[4]
            ru, user_config = self.dbUtil.query_configData('config_id', congfig_id)
            if ru == '1':
                # 截取最需要的部分
                # [sampling_rate, notch, low_pass, high_pass]
                # user_config = (250, 50, 100, 0.5)
                if user_config:
                    user_config = user_config[0]
                    user_config = user_config[2:-1]

                    sampling_rate = int(user_config[0])
                    # 判断用户当前配置是否适合处理该脑电文件
                    if (freq > sampling_rate):
                        msgtip = [account, f"检查脑电文件配置成功", '', '']
                        ret = ['1', REQmsg[1], f"检查脑电文件配置成功", [user_config],filemsg]
                        return msgtip, ret
                    # 较低采样率不进行转化
                    else:
                        msgtip = [account, f"当前脑电文件采样率为:{freq}和用户基本配置采样率:{sampling_rate}不符!!!!", '', '']
                        ret = ['2', REQmsg[1], f"当前脑电文件采样率为:{freq}和用户基本配置采样率:{sampling_rate}不符!!!!\n请重新去配置选择模块选合适的功能！！",[user_config]]
                        return msgtip, ret
                else:
                    msgtip = [account, f"未在数据库找到当前配置信息！！", '', '']
                    ret = ['0', REQmsg[1], f"未在数据库找到当前配置信息！！", [None]]
                    return msgtip, ret
            else:
                msgtip = [account, f"获取配置失败", '', '']
                ret = ['0', REQmsg[1], f"获取配置失败", [None]]
                return msgtip, ret
        except Exception as e:
            print('checkConfig', e)
            account = REQmsg[3][0]
            msgtip = [account, f"脑电上传失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"脑电上传失败:{e}", [None]]
            return msgtip, ret

    # 生成文件名
    def makeFileName(self,REQmsg):
        msgtip ,ret = self.EEGUploadService.makeFileName(REQmsg)
        return msgtip ,ret

    # 根据传入参数写入脑电数据
    def writeEEG(self,REQmsg):
        try:
            print("writeEEG里的REQmSG:",REQmsg)
            msgtip,ret = self.EEGUploadService.writeEEG(REQmsg)
            print("EEGUpload返回的信息：{msgtip}---{ret}",msgtip,ret)
            return msgtip,ret
        except Exception as e:
            print("writeEEG",e)

    # 根据传入参数更新数据库脑电检查信息
    def updateCheckInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            state = REQmsg[3][1]
            checkInfo = REQmsg[3][2]
            if state == 'Send':
                result = self.dbUtil.update_checkInfo(checkInfo)
                if result:
                    check_id = checkInfo[0]
                    result = self.dbUtil.del_fileInfo(check_id=check_id, state='notUploaded')
                    if result:
                        msgtip = [account, f"修改脑电检查信息并删除多余file_info信息成功", '', '']
                        ret = ['1', REQmsg[1], f"修改脑电检查信息并删除多余file_info信息成功", checkInfo]
                        return msgtip, ret
                else:
                    msgtip = [account, f"修改脑电检查信息失败", '', '']
                    ret = ['0', REQmsg[1], f"修改脑电检查信息失败", checkInfo]
                    return msgtip, ret
            elif state == 'Update':
                pass
            else:
                msgtip = [account, f"无法处理此类型信息", '', '']
                ret = ['0', REQmsg[1], f"发送脑电检查信息上传完成失败", checkInfo]
                return msgtip, ret
        except Exception as e:
            print('updateCheckInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"脑电检查信息更新出错！！{e}", '', '']
            ret = ['0', REQmsg[1], f"脑电检查信息更新出错！！{e}", None]
            return msgtip, ret

        # 根据传入参数获取脑电检查信息

    def getFileInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            uid = REQmsg[3][1]
            value = REQmsg[3][2]
            rf, file_info = self.dbUtil.get_fileInof_detail(uid)
            if rf == '1':
                msgtip = [account, f"查询脑电数据信息成功", '', '']
                ret = ['1', REQmsg[1], f"查询脑电数据信息成功", file_info]
                return msgtip, ret
            else:
                file_info = None
                msgtip = [account, f"查询脑电数据信息失败", '', '']
                ret = ['0', REQmsg[1], f"查询脑电数据信息失败", file_info]
                return msgtip, ret
        except Exception as e:
            print('getFileInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"查询脑电数据信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"查询脑电数据信息失败:{e}", None]
            return msgtip, ret

    def delFileInfo(self,REQmsg):
        print('delFileInfo:', REQmsg)
        try:
            account = REQmsg[3][0]
            check_id = REQmsg[3][1]
            file_id = REQmsg[3][2]
            rt = self.dbUtil.del_fileInfo(check_id=check_id, state='', file_id=file_id, flag='')
            if rt:
                msgtip = [account, "删除脑电文件信息成功或无对应信息需要删除",'','']
                ret = ['1',REQmsg[1],"删除脑电文件信息成功或无对应信息需要删除",None]
                return msgtip, ret
            else:
                msgtip = [account, "删除脑电文件信息失败", '', '']
                ret = ['0', REQmsg[1], "删除脑电文件信息失败", None]
                return msgtip, ret

        except Exception as e:
            msgtip = [account, f"删除脑电文件信息失败{e}", '', '']
            ret = ['0', REQmsg[1], f"删除脑电文件信息失败{e}", None]
            return msgtip, ret
            print('delFileInfo', e)


    def getChoosePatientInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            flag = REQmsg[3][1]
            # 获取所有病人信息
            if flag == '1':
                perNum = REQmsg[3][2]
                rp, patient_info, totalNum = self.dbUtil.get_patientIdName(flag='1', offset=perNum)
                if rp == '1':
                    msgtip = [account, f"查询病人详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人详细信息成功",
                           [flag, patient_info, totalNum]]
                    return msgtip, ret

                else:
                    msgtip = [account, f"查询病人详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人详细信息失败", [flag, None, None]]
                    return msgtip, ret
            # 获取无条件翻页病人信息
            elif flag == '2':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                rt, patient_info = self.dbUtil.get_patientIdName(flag='2', start=start, offset=perNum)
                if rt == '1':
                    msgtip = [account, f"查询病人信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人信息成功", [flag, patient_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询病人信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人信息失败",
                           [flag, None]]
                    return msgtip, ret

            # 获取病人信息的重置
            elif flag == '3':
                perNum = REQmsg[3][2]
                rp, patient_info, totalNum = self.dbUtil.get_patientIdName(flag='1', offset=perNum)
                if rp == '1':
                    msgtip = [account, f"查询病人详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人详细信息成功",
                           [flag, patient_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询病人详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人详细信息失败", [flag, None, None]]
                    return msgtip, ret
            # 有条件获取病人信息首页
            elif flag == '4':
                perNum = REQmsg[3][2]
                key_word = REQmsg[3][3]
                key_value = REQmsg[3][4]
                rp, patient_info, totalNum = self.dbUtil.get_patientIdName(flag='1', offset=perNum, where_name=key_word,
                                                                           where_value=key_value)
                if rp == '1':
                    msgtip = [account, f"查询病人详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人详细信息成功",
                           [flag, patient_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询病人详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人详细信息失败", [flag, None, None]]
                    return msgtip, ret
            # 获取有条件翻页病人信息
            elif flag == '5':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                rt, patient_info = self.dbUtil.get_patientIdName(flag='2', start=start, offset=perNum,
                                                                 where_name=key_word, where_value=key_value)
                if rt == '1':
                    msgtip = [account, f"查询病人信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人信息成功", [flag, patient_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询病人信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人信息失败",
                           [flag, None]]
                    return msgtip, ret

        except Exception as e:
            print('getChoosePatientInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"病人详细信息查询失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"病人详细信息查询失败:{e}", [None, None, None, None, None]]
            return msgtip, ret

        # 获取医生详细信息

    def getChooseDoctorInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            flag = REQmsg[3][1]
            # 获取所医生信息
            if flag == '1':
                perNum = REQmsg[3][2]
                rp, doctor_info, totalNum = self.dbUtil.get_doctorIdName(flag='1', offset=perNum)
                if rp == '1':
                    msgtip = [account, f"查询医生详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询医生详细信息成功",
                           [flag, doctor_info, totalNum]]
                    return msgtip, ret

                else:
                    msgtip = [account, f"查询医生详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询医生详细信息失败", [flag, None, None]]
                    return msgtip, ret


            # 获取无条件翻页医生信息
            elif flag == '2':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                rt, doctor_info = self.dbUtil.get_doctorIdName(flag='2', start=start, offset=perNum)
                if rt == '1':
                    msgtip = [account, f"查询医生信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询医生信息成功", [flag, doctor_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询医生信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询医生信息失败",
                           [flag, None]]
                    return msgtip, ret

            # 获取医生信息的重置
            elif flag == '3':
                perNum = REQmsg[3][2]
                rp, doctor_info, totalNum = self.dbUtil.get_doctorIdName(flag='1', offset=perNum)
                if rp == '1':
                    msgtip = [account, f"查询医生详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询医生详细信息成功",
                           [flag, doctor_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询医生详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询医生详细信息失败", [flag, None, None]]
                    return msgtip, ret
            # 有条件获取医生信息首页
            elif flag == '4':
                perNum = REQmsg[3][2]
                key_word = REQmsg[3][3]
                key_value = REQmsg[3][4]
                rp, doctor_info, totalNum = self.dbUtil.get_doctorIdName(flag='1', offset=perNum, where_name=key_word,
                                                                         where_value=key_value)
                if rp == '1':
                    msgtip = [account, f"查询医生详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询医生详细信息成功",
                           [flag, doctor_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询医生详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询医生详细信息失败", [flag, None, None]]
                    return msgtip, ret
            # 获取有条件翻页医生信息
            elif flag == '5':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                rt, doctor_info = self.dbUtil.get_doctorIdName(flag='2', start=start, offset=perNum,
                                                               where_name=key_word, where_value=key_value)
                if rt == '1':
                    msgtip = [account, f"查询医生信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询医生信息成功", [flag, doctor_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询医生信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询医生信息失败",
                           [flag, None]]
                    return msgtip, ret

        except Exception as e:
            print('getChooseDoctorInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"医生详细信息查询失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"医生详细信息查询失败:{e}", [None, None, None, None, None]]
            return msgtip, ret

    # 任务设置
    # 根据传入参数获取标注主题信息
    def getThemeInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            flag = REQmsg[3][1]
            # 获取所有标注主题信息
            if flag == '1':
                perNum = REQmsg[3][2]
                rr, theme_info, totalNum = self.dbUtil.get_themeInfo(flag='1', offset=perNum)
                if rr == '1':
                    msgtip = [account, f"查询标注主题信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询标注主题信息成功",
                           [flag, theme_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询标注主题信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询标注主题信息失败", [flag, None, None]]
                    return msgtip, ret



            # 获取某一标注主题的标注任务相关详细信息
            elif flag == '2':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                rt, theme_info = self.dbUtil.get_themeInfo(flag='2', start=start, offset=perNum)
                if rt == '1':
                    msgtip = [account, f"标注主题分页信息查询成功", '', '']
                    ret = ['1', REQmsg[1], f"标注主题分页信息查询成功", [flag, theme_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"标注主题分页信息查询失败", '', '']
                    ret = ['0', REQmsg[1], f"标注主题分页信息查询失败",
                           [flag, None]]
                    return msgtip, ret

            # 获取标注主题信息重置
            elif flag == '3':
                perNum = REQmsg[3][2]
                rp, theme_info, totalNum = self.dbUtil.get_themeInfo(flag='1', offset=perNum)
                if rp == '1':
                    msgtip = [account, f"查询标注主题信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询标注主题信息成功",
                           [flag, theme_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询标注主题信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询标注主题信息失败", [flag, None, None]]
                    return msgtip, ret

            # 获取有条件标注主题信息首页
            elif flag == '4':
                perNum = REQmsg[3][2]
                key_word = REQmsg[3][3]
                key_value = REQmsg[3][4]
                rp, theme_info, totalNum = self.dbUtil.get_themeInfo(flag='1', offset=perNum, where_name=key_word,
                                                                     where_value=key_value)
                if rp == '1':
                    msgtip = [account, f"标注主题信息查询成功", '', '']
                    ret = ['1', REQmsg[1], f"标注主题信息查询成功",
                           [flag, theme_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"标注主题信息查询失败", '', '']
                    ret = ['0', REQmsg[1], f"标注主题信息查询失败", [flag, None, None]]
                    return msgtip, ret

            # 获取有条件标注主题信息分页
            elif flag == '5':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                rt, theme_info = self.dbUtil.get_themeInfo(flag='2', start=start, offset=perNum,
                                                           where_name=key_word, where_value=key_value)
                if rt == '1':
                    msgtip = [account, f"标注主题分页信息查询成功", '', '']
                    ret = ['1', REQmsg[1], f"标注主题分页信息查询成功", [flag, theme_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"标注主题分页信息查询失败", '', '']
                    ret = ['0', REQmsg[1], f"标注主题分页信息查询失败",
                           [flag, None]]
                    return msgtip, ret

            # 获取某一标注主题的标注任务相关详细信息
            elif flag == '6':
                theme_id = REQmsg[3][2]
                rt, task_info = self.dbUtil.get_taskInfo('theme_id', theme_id)
                if rt == '1':
                    msgtip = [account, f"查询某个标注主题信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询某个标注主题信息成功", [flag, task_info, theme_id]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询某个标注主题信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询某个标注主题信息失败",
                           [flag, task_info, theme_id]]
                    return msgtip, ret

        except Exception as e:
            print('getThemeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"标注主题信息查询失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"标注主题信息查询失败:{e}", [None, None, None, None, None]]
            return msgtip, ret

    # 根据传入参数增加数据库标注主题信息
    def addThemeInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            theme_info = REQmsg[3][1:]
            result, info = self.dbUtil.add_themeInfo(theme_info)
            if result:
                msgtip = [account, f"添加标注主题信息成功", '', '']
                ret = ['1', REQmsg[1], f"添加标注主题信息成功", theme_info]
                return msgtip, ret
            else:
                info = str(info)
                msgtip = [account, info, '', '']
                ret = ['0', REQmsg[1], info, theme_info]
                return msgtip, ret
        except Exception as e:
            print('addThemeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"添加标注主题信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"添加标注主题信息失败:{e}", None]
            return msgtip, ret

    # 根据传入参数删除数据库标注主题信息
    def delThemeInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            theme_info = REQmsg[3][1:]
            theme_id = theme_info[0]
            # 先删除相关标注表的相关内容
            result_one = self.dbUtil.del_detailInfo(theme_id, flag='2')
            # 删除标注任务
            result = self.dbUtil.del_taskInfo(theme_id)
            if result and result_one:
                # 删除标注主题
                result = self.dbUtil.del_themeInfo('theme_id', theme_id)
                if result:
                    msgtip = [account, f"删除标注主题信息成功", '', '']
                    ret = ['1', REQmsg[1], f"删除标注主题信息成功", theme_info]
                    return msgtip, ret
                else:
                    msgtip = [account, f"删除标注主题信息失败", '', '']
                    ret = ['0', REQmsg[1], f"删除标注主题信息失败", theme_info]
                    return msgtip, ret
            else:
                msgtip = [account, f"删除标注任务信息失败", '', '']
                ret = ['0', REQmsg[1], f"删除标注任务信息失败", theme_info]
                return msgtip, ret
        except Exception as e:
            print('delThemeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"删除标注任务信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"删除标注任务信息失败:{e}", None]
            return msgtip, ret

    # 根据传入参数更新数据库标注主题信息
    def updateThemeInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            theme_info = REQmsg[3][1:]
            result = self.dbUtil.update_themeInfo(theme_info)
            if result:
                msgtip = [account, f"修改标注主题信息成功", '', '']
                ret = ['1', REQmsg[1], f"修改标注主题信息成功", theme_info]
                return msgtip, ret
            else:
                msgtip = [account, f"修改标注主题信息失败", '', '']
                ret = ['0', REQmsg[1], f"修改标注主题信息失败", theme_info]
                return msgtip, ret
        except Exception as e:
            print('updateThemeInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"修改标注主题信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"修改标注主题信息失败:{e}", None]
            return msgtip, ret

    # 根据传入参数获取标注任务信息
    def getTaskInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            rt, task_info = self.dbUtil.get_taskInfo()
            # task_info1= self.dbUtil.get_taskInfo('theme_id', 1)
            if rt == '1':
                msgtip = [account, f"查询标注任务信息成功", '', '']
                ret = ['1', REQmsg[1], f"查询标注任务信息成功", task_info]
                return msgtip, ret
            else:
                msgtip = [account, f"查询标注任务信息失败", '', '']
                ret = ['0', REQmsg[1], f"查询标注任务信息失败", None]
                return msgtip, ret
        except Exception as e:
            print('getTaskInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"查询标注任务信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"查询标注任务信息失败:{e}", None]
            return msgtip, ret

    # 根据传入参数增加数据库标注任务信息
    def addTaskInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            theme_id = REQmsg[3][1]
            task_info = REQmsg[3][2]
            result_flag = []
            result, result_flag = self.dbUtil.add_taskInfo(theme_id, task_info, result_flag)
            if result:
                # 没有重复情况
                if not result_flag:
                    msgtip = [account, f"添加标注主题详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"添加标注主题详细信息成功", '']
                    return msgtip, ret
                else:
                    # 全部重复情况
                    if sum(result_flag) == len(task_info):
                        msgtip = [account, f"添加标注主题详细信息失败", '', '']
                        ret = ['1', REQmsg[1], f"添加的标注任务在原标注主题中已经存在，所以添加失败！！！", '']
                        return msgtip, ret
                    # 部分重复情况
                    else:
                        msgtip = [account, f"添加的标注主题详细信息未重复部分添加成功， 重复部分添加失败！！", '', '']
                        ret = ['1', REQmsg[1], f"添加的标注主题详细信息未重复部分添加成功，重复部分添加失败！！", '']
                        return msgtip, ret

            else:
                msgtip = [account, f"添加标注主题详细信息失败", '', '']
                ret = ['0', REQmsg[1], f"添加标注主题详细信息失败", '']
                return msgtip, ret
        except Exception as e:
            print('addTaskInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"添加标注主题详细信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"添加标注主题详细信息失败:{e}", '']
            return msgtip, ret

    # 根据传入参数删除数据库标注任务信息
    # 先别删除，方便后面更新
    def delTaskInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            task_info = REQmsg[3][1]
            row = REQmsg[3][2]
            # 删除标注任务相关的脑电标注
            result_one = self.dbUtil.del_detailInfo(task_info, flag='1')
            # 删除标注任务
            result = self.dbUtil.del_taskInfo(task_info, flag='1')
            if result and result_one:
                msgtip = [account, f"删除标注主题信息成功", '', '']
                ret = ['1', REQmsg[1], f"删除标注主题信息成功", task_info, row]
                return msgtip, ret
            else:
                msgtip = [account, f"删除标注任务信息失败", '', '']
                ret = ['0', REQmsg[1], f"删除标注任务信息失败", task_info, row]
                return msgtip, ret
        except Exception as e:
            print('delTaskInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"删除标注任务信息失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"删除标注任务信息失败:{e}", None, None]
            return msgtip, ret

    # 根据传入参数更新数据库标注任务信息
    # 先别删除，方便后面更新
    def updateTaskInfo(self, REQmsg):
        try:
            pass
        except Exception as e:
            print('updateTaskInfo', e)

    # 获取病人详细信息
    def getChooseDetailInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            flag = REQmsg[3][1]
            # 获取所有病人信息
            if flag == '1':
                perNum = REQmsg[3][2]
                theme_id = REQmsg[3][3]
                config_id = REQmsg[3][4]
                rp, patient_info, totalNum, file_info = self.dbUtil.get_FileInfo1(flag='1', offset=perNum,
                                                                                  config_id=config_id)
                if rp == '1':
                    msgtip = [account, f"查询病人详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人详细信息成功",
                           [flag, patient_info, totalNum, file_info, theme_id]]
                    return msgtip, ret

                else:
                    msgtip = [account, f"查询病人详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人详细信息失败", [flag, None, None, None, None]]
                    return msgtip, ret
            # 获取无条件翻页病人信息
            elif flag == '2':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                theme_id = REQmsg[3][4]
                config_id = REQmsg[3][5]
                rt, patient_info = self.dbUtil.get_FileInfo1(flag='2', start=start, offset=perNum,
                                                             config_id=config_id)
                if rt == '1':
                    msgtip = [account, f"查询某个标注主题信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询某个标注主题信息成功", [flag, patient_info, theme_id]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询某个标注主题信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询某个标注主题信息失败",
                           [flag, None, None]]
                    return msgtip, ret

            # 获取病人信息的重置
            elif flag == '3':
                perNum = REQmsg[3][2]
                theme_id = REQmsg[3][3]
                config_id = REQmsg[3][4]
                rp, patient_info, totalNum, file_info = self.dbUtil.get_FileInfo1(flag='1', offset=perNum,
                                                                                  config_id=config_id)
                if rp == '1':
                    msgtip = [account, f"查询病人详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人详细信息成功",
                           [flag, patient_info, totalNum, file_info, theme_id]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询病人详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人详细信息失败", [flag, None, None, None, None]]
                    return msgtip, ret
            # 有条件获取病人信息首页
            elif flag == '4':
                perNum = REQmsg[3][2]
                key_word = REQmsg[3][3]
                key_value = REQmsg[3][4]
                theme_id = REQmsg[3][5]
                config_id = REQmsg[3][6]
                rp, patient_info, totalNum, file_info = self.dbUtil.get_FileInfo1(flag='1', offset=perNum,
                                                                                  where_name=key_word,
                                                                                  where_value=key_value,
                                                                                  config_id=config_id)
                if rp == '1':
                    msgtip = [account, f"查询病人详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人详细信息成功",
                           [flag, patient_info, totalNum, file_info, theme_id]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询病人详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人详细信息失败", [flag, None, None, None, None]]
                    return msgtip, ret
            # 获取有条件翻页病人信息
            elif flag == '5':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                theme_id = REQmsg[3][6]
                config_id = REQmsg[3][7]
                rt, patient_info = self.dbUtil.get_FileInfo1(flag='2', start=start, offset=perNum,
                                                             where_name=key_word, where_value=key_value,
                                                             config_id=config_id)
                if rt == '1':
                    msgtip = [account, f"查询病人信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询病人信息成功", [flag, patient_info, theme_id]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询病人信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询病人信息失败",
                           [flag, None, None]]
                    return msgtip, ret

        except Exception as e:
            print('addDetailInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"病人详细信息查询失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"病人详细信息查询失败:{e}", [None, None, None, None, None]]
            return msgtip, ret

    # 根据传入参数启动标注主题
    def startTheme(self, REQmsg):
        try:
            account = REQmsg[3][0]
            theme_id = REQmsg[3][1]
            row = REQmsg[3][2]

            # 查看当前标注主题是否有任务信息
            rt, task_info = self.dbUtil.get_taskInfo('theme_id', theme_id)
            if rt == '1':
                if task_info:
                    # 该标注主题下有标注任务才能启动标注主题
                    result = self.dbUtil.update_ThemeState(theme_id, 'labelling')
                    if result:
                        msgtip = [account, f"启动当前标注主题成功", '', '']
                        ret = ['1', REQmsg[1], f"启动当前标注主题成功", theme_id, row]
                        return msgtip, ret
                    else:
                        msgtip = [account, f"启动当前标注主题失败", '', '']
                        ret = ['0', REQmsg[1], f"启动当前标注主题失败", theme_id, row]
                        return msgtip, ret
                else:
                    msgtip = [account, f"当前标注主题无详细标注任务，请添加详细标注任务后启动！！！！！", '', '']
                    ret = ['0', REQmsg[1], f"当前标注主题无详细标注任务，请添加详细标注任务后启动！！！！！", theme_id,
                           row]
                    return msgtip, ret
            else:
                msgtip = [account, f"查询该标注主题失败，启动失败", '', '']
                ret = ['0', REQmsg[1], f"查询该标注主题失败，启动失败", theme_id, row]
                return msgtip, ret





        except Exception as e:
            print('startTheme', e)
            account = REQmsg[3][0]
            msgtip = [account, f"启动当前标注主题失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"启动当前标注主题失败:{e}", None]
            return msgtip, ret

    # 获取标注员信息
    def getChooseMarkerInfo(self, REQmsg):
        try:
            account = REQmsg[3][0]
            flag = REQmsg[3][1]
            # 获取所有标注人员信息
            if flag == '1':
                perNum = REQmsg[3][2]
                rp, marker_info, totalNum = self.dbUtil.get_markerIdName(flag='1', offset=perNum)
                if rp == '1':
                    msgtip = [account, f"查询标注人员详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询标注人员详细信息成功",
                           [flag, marker_info, totalNum]]
                    return msgtip, ret

                else:
                    msgtip = [account, f"查询标注人员详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询标注人员详细信息失败", [flag, None, None]]
                    return msgtip, ret


            # 获取无条件翻页标注人员信息
            elif flag == '2':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                rt, marker_info = self.dbUtil.get_markerIdName(flag='2', start=start, offset=perNum)
                if rt == '1':
                    msgtip = [account, f"查询标注人员信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询标注人员信息成功", [flag, marker_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询标注人员信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询标注人员信息失败",
                           [flag, None]]
                    return msgtip, ret

            # 获取标注人员信息的重置
            elif flag == '3':
                perNum = REQmsg[3][2]
                rp, marker_info, totalNum = self.dbUtil.get_markerIdName(flag='1', offset=perNum)
                if rp == '1':
                    msgtip = [account, f"查询标注人员详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询标注人员详细信息成功",
                           [flag, marker_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询标注人员详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询标注人员详细信息失败", [flag, None, None]]
                    return msgtip, ret
            # 有条件获取标注人员信息首页
            elif flag == '4':
                perNum = REQmsg[3][2]
                key_word = REQmsg[3][3]
                key_value = REQmsg[3][4]
                rp, marker_info, totalNum = self.dbUtil.get_markerIdName(flag='1', offset=perNum,
                                                                         where_name=key_word,
                                                                         where_value=key_value)
                if rp == '1':
                    msgtip = [account, f"查询标注人员详细信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询标注人员详细信息成功",
                           [flag, marker_info, totalNum]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询标注人员详细信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询标注人员详细信息失败", [flag, None, None]]
                    return msgtip, ret
            # 获取有条件翻页标注人员信息
            elif flag == '5':
                perNum = REQmsg[3][2]
                start = REQmsg[3][3]
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                rt, marker_info = self.dbUtil.get_markerIdName(flag='2', start=start, offset=perNum,
                                                               where_name=key_word, where_value=key_value)
                if rt == '1':
                    msgtip = [account, f"查询标注人员信息成功", '', '']
                    ret = ['1', REQmsg[1], f"查询标注人员信息成功", [flag, marker_info]]
                    return msgtip, ret
                else:
                    msgtip = [account, f"查询标注人员信息失败", '', '']
                    ret = ['0', REQmsg[1], f"查询标注人员信息失败",
                           [flag, None]]
                    return msgtip, ret

        except Exception as e:
            print('getChooseMarkerInfo', e)
            account = REQmsg[3][0]
            msgtip = [account, f"标注人员详细信息查询失败:{e}", '', '']
            ret = ['0', REQmsg[1], f"标注人员详细信息查询失败:{e}", [None, None, None, None, None]]
            return msgtip, ret

    def getConfigData(self, cmdID):
        configInfo = self.dbUtil.queryConfigData()
        msgtip = [cmdID, f"获取全部基本配置信息", '', '']
        print(configInfo)
        ret = ['1', cmdID, f"获取全部基本配置信息", configInfo]
        return msgtip, ret

    def addBasicConfig(self, cmdID, config):
        print(f'addBasicConfig: {config}')
        self.dbUtil.addBasicConfig(config)
        if config[5] == 1:
            for i, c in enumerate(self.curUser.config):
                print(f'c: {c}')
                if c[6] == 1:
                    self.dbUtil.updateBasicConfig('config_id', c[0], set_name='`default`', set_value=0)
        self.curUser.config = self.dbUtil.queryConfigData()
        msgtip = [cmdID, f"添加新的基本配置信息", '', '']
        ret = ['1', cmdID, f"添加新的基本配置信息", self.curUser.config[len(self.curUser.config) - 1]]
        return msgtip, ret

    def delBasicConfig(self, cmdID, config):
        print(f'delBasicConfig: {config}')
        if config[6] == 1:
            msgtip = [cmdID, f"admin正在删除默认配置，返回错误信息", '', '']
            ret = ['0', cmdID, f"admin正在删除默认配置，返回错误信息", '当前正在尝试删除默认配置，请先设置其他默认配置!']
            return msgtip, ret
        if not self.dbUtil.delBasicConfig('config_id', config[0]):
            msgtip = [cmdID, f"删除配置失败", '', '']
            ret = ['0', cmdID, f"删除配置失败", '删除配置失败，当前配置正在被用户使用']
            return msgtip, ret
        for i, c in enumerate(self.curUser.config):
            print(f'c: {c}')
            if c[0] == config[0]:
                self.curUser.config.remove(c)
        print(f'config: {self.curUser.config}')
        msgtip = [cmdID, f"删除新的基本配置信息", '', '']
        ret = ['1', cmdID, f"删除新的基本配置信息", config[0]]
        return msgtip, ret

    def updateBasicConfig(self, cmdID, config):
        print(f'updateBasicConfig: {config}')
        for i, c in enumerate(self.curUser.config):
            print(f'c: {c}')
            if c[0] == config[0]:
                if str(c[1]) != config[1] or str(c[2]) != config[2] or str(c[3]) != config[3] or str(c[4]) != config[
                    4] or str(c[5]) != config[5]:
                    if self.dbUtil.checkConfigisUsed(c[0]):
                        msgtip = [cmdID, f"修改配置失败", '', '']
                        ret = ['0', cmdID, f"修改配置失败", '修改配置失败，当前配置正在被用户使用']
                        return msgtip, ret
        if config[6] == 1:
            config_t = self.dbUtil.queryConfigData('default', 1)[0]
            if config_t != None or len(config_t) != 0:
                self.dbUtil.updateBasicConfig('config_id', config_t[0], set_name='`default`', set_value=0)
            else:
                msgtip = [cmdID, f"取消默认配置失败，请设置其他配置为默认配置", '', '']
                ret = ['0', cmdID, f"取消默认配置失败，请设置其他配置为默认配置",
                       '取消默认配置失败，请设置其他配置为默认配置']
                return msgtip, ret
        self.dbUtil.updateBasicConfig('config_id', config[0], config)
        self.curUser.config = self.dbUtil.queryConfigData()
        msgtip = [cmdID, f"修改新的基本配置信息", '', '']
        ret = ['1', cmdID, f"修改新的基本配置信息", self.curUser.config]
        return msgtip, ret


    # 创建会诊
    # 获取医生信息
    def getDoctorInfo(self, cmdID, data):
        try:
            print(f'getDoctorInfo data: {data}')
            doctorInfo = self.dbUtil.getDoctorInfo(column='name, phone, email, uid, account')
            start = (int(data[0]) - 1) * int(data[1])
            msgtip = [cmdID, f"获取医生信息", '数据库操作成功', '']
            ret = ['1', cmdID, [len(doctorInfo), doctorInfo[start:start + data[1]]]]
            return msgtip, ret
        except Exception as e:
            print('getDoctorInfo', e)
            msgtip = [cmdID, f"获取医生信息失败", '数据库操作失败', '']
            ret = ['0', cmdID, f'获取医生信息失败, e: {e}']
            return msgtip, ret

    # 获取搜索的医生信息
    def getSearchDoctorInfo(self, cmdID, data):
        try:
            print(f'getSearchDoctorInfo data: {data}')
            doctorInfo = self.dbUtil.getDoctorInfo(column='name, phone, email, uid, account', where_name=data[3],
                                                   where_like=data[4])
            start = (int(data[0]) - 1) * int(data[1])
            msgtip = [cmdID, f"获取医生信息", '数据库操作成功', '']
            ret = ['1', cmdID, [len(doctorInfo), doctorInfo[start:start + data[1]]]]
            return msgtip, ret
        except Exception as e:
            print('getSearchDoctorInfo', e)
            msgtip = [cmdID, f"获取医生信息失败", '数据库操作失败', '']
            ret = ['0', cmdID, f'获取医生信息失败, e: {e}']
            return msgtip, ret

    # 获取完整的脑电检查信息
    def getCpltCheckInfo(self, cmdID):
        try:
            cpltCheckInfo = self.dbUtil.getCpltCheckInfo()
            print(f'cpltCheckInfo: {cpltCheckInfo}')
            msgtip = [cmdID, f"获取完整的脑电会诊信息", '数据库操作成功', '']
            ret = ['1', cmdID, cpltCheckInfo]
            return msgtip, ret
        except Exception as e:
            print('getCpltCheckInfo', e)
            msgtip = [cmdID, f"获取完整的脑电会诊信息失败", '数据库操作失败', '']
            ret = ['0', cmdID, f'获取完整的脑电会诊信息失败, e: {e}']
            return msgtip, ret

    # 获取完整的脑电检查信息
    def getHistoryCons(self, cmdID):
        try:
            cpltHistoryConsInfo = []
            historyConsInfo = self.dbUtil.getHistoryCons()
            # print(f'getHistoryCons: {historyConsInfo}')
            # for consInfo in historyConsInfo:
            #     cpltCheckInfo = self.dbUtil.getCpltCheckInfo(where_name='check_id', where_value=consInfo[0])
            #     cpltHistoryConsInfo.append([consInfo, cpltCheckInfo])

            msgtip = [cmdID, f"获取历史会诊信息", '数据库操作成功', '']
            ret = ['1', cmdID, historyConsInfo]
            return msgtip, ret
        except Exception as e:
            print('getHistoryCons', e)
            msgtip = [cmdID, f"获取历史会诊信息失败", '数据库操作失败', '']
            ret = ['0', cmdID, f'获取历史会诊信息失败, e: {e}']
            return msgtip, ret

    # 创建会诊
    def createCons(self, cmdID, REQmsg):
        try:
            print(f'createCons REQmsg: {REQmsg}')
            doctors = REQmsg[3][3]
            checkID = REQmsg[3][0]
            message = REQmsg[3][1]
            date = REQmsg[3][2]
            diagInfo = []
            messageRev = []
            phoneRev = []

            tempDiagInfo = self.dbUtil.getDiagInfo(where_name='check_id', where_value=checkID)
            print(tempDiagInfo)
            if len(tempDiagInfo) > 0:
                tempID = [item[1] for item in tempDiagInfo]
                print(f'tempID: {tempID}')
                for doctor in doctors:
                    if doctor[3] in tempID:
                        self.dbUtil.updateCons('state', 'notDiagnosed', 'uid', int(doctor[3]))
                    else:
                        self.dbUtil.createCons([(checkID, doctor[3], date)])
                msgtip = [cmdID, f"更新会诊信息成功", '更新会诊信息成功', '']
                ret = ['1', cmdID, '更新会诊信息成功']
                return msgtip, ret

            for doctor in doctors:
                diagInfo.append([checkID, doctor[3], date])
                if doctor[2] != '':
                    messageRev.append(doctor[2])
                if doctor[1] != '':
                    phoneRev.append(doctor[1])

            self.dbUtil.createCons(diagInfo)
            if len(doctors) == 1:
                self.dbUtil.updateCheckInfo('state', 'diagnosing', 'check_id', checkID)
            else:
                self.dbUtil.updateCheckInfo('state', 'consulting', 'check_id', checkID)

            print(f'messageRev: {messageRev}, phoneRev: {phoneRev}, message: {message}, diagInfo: {diagInfo}')
            # if messageRev is not None and len(messageRev) > 0:
            #     # 发送邮件
            #     self.appUtil.sendEmail(messageRev, message)
            # 发送手机短线
            # if messageRev is not None and len(phoneRev) > 0:
            #   for phone in phoneRev:
            #       self.appUtil.sendPhoneMsg(phone, message)
            msgtip = [cmdID, f"创建会诊", '创建会诊', '']
            ret = ['1', cmdID, '创建会诊成功']
            return msgtip, ret
        except Exception as e:
            print('createCons', e)
            msgtip = [cmdID, f"创建会诊失败", '创建会诊失败', '']
            ret = ['0', cmdID, f'创建会诊失败, e: {e}']
            return msgtip, ret

    # 获取全部会诊信息
    def getAllConsInfo(self, cmdID, data, userID):
        try:
            print(f'getAllConsInfo REQmsg: {data}')
            start = (int(data[0]) - 1) * int(data[1])
            consInfo = self.dbUtil.getAllConsInfo(userID=userID)
            print(f'consInfo: {consInfo}')
            msgtip = [cmdID, f"获取完整的脑电会诊信息", '数据库操作成功', '']
            ret = ['1', cmdID, [len(consInfo), consInfo[start:start + data[1]]]]
            return msgtip, ret
        except Exception as e:
            print('getAllConsInfo', e)
            msgtip = [cmdID, f"获取完整的脑电会诊信息失败", '数据库操作失败', '']
            ret = ['0', cmdID, f'获取完整的脑电会诊信息失败, e: {e}']
            return msgtip, ret

    # 获取查询的会诊信息
    def inqConsInfo(self, cmdID, data, userID):
        try:
            print(f'inqConsInfo REQmsg: {data}')
            if data[2][0] != '' and data[2][1] != '' and data[1] !='':
                consInfo = self.dbUtil.getAllConsInfo(where_name=data[0], where_like=data[1], date1=data[2][0],
                                                      date2=data[2][1], userID=userID)
            elif data[1] =='' and (data[2][0] != '' and data[2][1] != '' ):
                consInfo = self.dbUtil.getAllConsInfo(date1=data[2][0],
                                                      date2=data[2][1], userID=userID)
            else:
                consInfo = self.dbUtil.getAllConsInfo(where_name=data[0], where_like=data[1], userID=userID)
            print(f'consInfo: {consInfo}')
            start = (int(data[3]) - 1) * int(data[4])
            msgtip = [cmdID, f"获取搜索的脑电信息", '数据库操作成功', '']
            ret = ['1', cmdID, [len(consInfo), consInfo[start:start + data[4]],data[3]]]
            return msgtip, ret
        except Exception as e:
            print('inqConsInfo', e)
            msgtip = [cmdID, f"获取搜索的脑电信息失败", '数据库操作失败', '']
            ret = ['0', cmdID, f'获取搜索的脑电信息失败, e: {e}']
            return msgtip, ret


        # 病人管理模块
        # 根据传入参数获取病人信息

    def getPatientInfo(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 12
            patient_info = self.dbUtil.getPatientInfo()
            ui_size = len(patient_info)
            ptotal = ceil(ui_size / _Pagerows)
            if ptotal != 0:
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                result = self.dbUtil.getPatientInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
                ret = ['1', REQmsg[1], result, ptotal]
                return msgtip, ret
            else:
                result = 0
                msgtip = [REQmsg[1], f"无病人信息", '', '']
                # print(msgtip)
                ret = ['2', REQmsg[1], result, ptotal]
                return msgtip, ret
        except Exception as e:
            print('getPatientInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

        # 根据传入参数新增病人信息

    def addPatientInfo(self, macAddr, REQmsg):
        try:
            patientInfo = REQmsg[3]
            r, result = self.dbUtil.addPatientInfo(patient_info=patientInfo)
            if r == '1':
                _curPageIndex = REQmsg[3][7]
                _Pagerows = 12
                ui_size = self.dbUtil.getPatientInfo(count=True)
                ptotal = ceil(ui_size[0][0] / _Pagerows)
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                result = self.dbUtil.getPatientInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
                ret = ['1', REQmsg[1], REQmsg[3], result, ptotal, _curPageIndex]
                msgtip = [REQmsg[2], f"添加病人信息成功", '数据库操作成功', '']
                return msgtip, ret
            elif r == '0':
                msgtip = [REQmsg[2], f"添加病人信息失败", '数据库操作失败', f'失败原因(result)']
                ret = ['0', REQmsg[1], patientInfo]
                return msgtip, ret
        except Exception as e:
            print('addPatientInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getCurConfigData(self, cmdID, userID):
        defalutID = self.curUser.users[userID][12]
        for c in self.curUser.config:
            if c[0] == defalutID:
                msgtip = [cmdID, f"获取默认基本配置信息", '', '']
                ret = ['1', cmdID, f"获取默认基本配置信息", c]
                return msgtip, ret
        msgtip = [cmdID, f"无默认配置文件", '', '']
        ret = ['0', cmdID, f"无默认配置文件", '']
        return msgtip, ret

    def getAllConfigData(self, cmdID, config):
        configInfo = self.curUser.config
        msgtip = [cmdID, f"获取全部基本配置信息", '', '']
        print(configInfo)
        ret = ['1', cmdID, f"获取全部基本配置信息", configInfo]
        return msgtip, ret

    def chgCurUserConfigData(self, cmdID, userID, data):
        print(f'chgCurUserConfigData data: {data}')
        try:
            print(self.curUser.users)
            self.curUser.users[userID][12] = int(data[0])
            print(self.curUser.users)
            msgtip = [cmdID, f"修改用户配置", '', '']
            ret = ['1', cmdID, f"修改用户配置"]
            return msgtip, ret
        except Exception as e:
            print('chgCurUserConfigData', e)
            msgtip = [cmdID, f"修改用户配置失败", '', '']
            ret = ['0', cmdID, f"修改用户配置失败"]
            return msgtip, ret

        # 根据传入参数删除病人信息

    def delPatientInfo(self, macAddr, REQmsg):
        try:
            del_id = REQmsg[3][0]
            _curPageIndex = REQmsg[3][2]
            r, result = self.dbUtil.delPatientInfo('patient_id', del_id)
            if r == '1':
                msgtip = [REQmsg[2], f"删除病人信息成功", '数据库操作成功', '']
                _Pagerows = 12
                ui_size = self.dbUtil.getPatientInfo(count=True)
                ptotal = ceil(ui_size[0][0] / _Pagerows)
                if ptotal != 0:
                    if _curPageIndex > ptotal:
                        _curPageIndex = ptotal
                    result = self.dbUtil.getPatientInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
                    ret = ['1', REQmsg[1], REQmsg[3], result, ptotal, _curPageIndex]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"无病人信息", '数据库操作成功', '']
                    ret = ['2', REQmsg[1], REQmsg[3], [], ptotal, _curPageIndex]
                    return msgtip, ret
            elif r == '0':
                msgtip = [REQmsg[2], f"删除病人信息失败", '数据库操作失败', f'失败原因(result)']
                ret = ['0', REQmsg[1], REQmsg[3]]
                return msgtip, ret
        except Exception as e:
            print('delPatientInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def updatePatientInfo(self, macAddr, REQmsg):
        try:
            r, result = self.dbUtil.updatePatientInfo('patient_id', REQmsg[3][1], REQmsg[3][0])
            if r == '1':
                msgtip = [REQmsg[2], f"编辑病人信息成功", '数据库操作成功', '']
                ret = ['1', REQmsg[1], REQmsg[3]]
                return msgtip, ret
            elif r == '0':
                msgtip = [REQmsg[2], f"编辑病人信息失败", '数据库操作失败', f'失败原因(result)']
                ret = ['0', REQmsg[1], REQmsg[3]]
                return msgtip, ret
        except Exception as e:
            print('updatePatientInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def inqPatientInfo(self, cmdID, key, value, REQmsg):
        try:
            print(f'inqPatientInfo REQmsg: {key}, {value}')
            patientInfo = self.dbUtil.getPatientInfo(where_name=key, where_like=value)
            totalPage = ceil(len(patientInfo) / REQmsg[3][3])
            start = (REQmsg[3][2] - 1) * REQmsg[3][3]
            patientInfo = patientInfo[start:start + REQmsg[3][3]]
            msgtip = [cmdID, f"获取病人信息", '数据库操作成功', '']
            ret = ['1', cmdID, [totalPage, patientInfo]]
            return msgtip, ret
        except Exception as e:
            print('inqPatientInfo', e)
            msgtip = [cmdID, f"获取病人信息失败", '数据库操作失败', '']
            ret = ['0', cmdID, f'创建会诊失败, e: {e}']
            return msgtip, ret

    def patientPaging(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 12
            result = self.dbUtil.getPatientInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result]
            return msgtip, ret
        except Exception as e:
            print('userPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    ### dsj ==[===

    # 执行查看/提交主题(可用，不可用)
    def rgQ_theme_commit(self, clientAddr, REQmsg):
        if REQmsg[1] == 31:
            theme_id = REQmsg[3][0]
            stat = REQmsg[3][1]
            r0, d0 = self.dbUtil.task_get(theme_id=theme_id,
                                          other_sql="(state ='notStarted' or state= 'labelling' or state= 'labelled')")
            if r0 == '0':
                ret = [r0, REQmsg[1], f'统计当前主题的任务记录不成功:{d0}']
                msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/统计当前主题的任务记录不成功:{d0}", '数据库操作', "不成功",""]
            elif len(d0)>0:
                ret = ['0', REQmsg[1], f'{REQmsg[0]}/主题不能设置{stat}，有任务{len(d0)}条未处理.']
                msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/主题不能设置{stat}", '数据库操作', "有任务{len(d0)}条未处理.", ""]
            else:
                usql=f"update  theme set state='{stat}' where theme_id={theme_id}"
                r=self.dbUtil.myExecuteSql(usql)
                if r=="":
                    ret = ['1', REQmsg[1], f'{REQmsg[0]}/主题设置{stat}，操作成功。']
                    msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/主题设置{stat}", '数据库操作', "成功", ""]
                else:
                    ret = ['0', REQmsg[1], f'{REQmsg[0]}/主题设置{stat}，数据库操作不成功{r}']
                    msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/主题设置{stat}", '数据库操作', "不成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret


    #执行查看/查询、分页
    def rgQ_paging(self, clientAddr, REQmsg):
        if REQmsg[1] == 30:
            _uid = REQmsg[3][0]
            _curPageIndex = REQmsg[3][1]
            _Pagerows = REQmsg[3][2]
            if _Pagerows <= 0:
                _Pagerows = 12
            paging = REQmsg[3][3]

            theme_name = REQmsg[3][4]
            theme_state = REQmsg[3][5]
            task_state = REQmsg[3][6]
            sql_where = f" theme.uid={_uid}   and theme.state in ('evaluating','labelling')  " \
                        f"and  task.state in ('labelled','qualified','notqualified') "
            if theme_name is not None and theme_name != '':
                sql_where += f" and  theme.name like '%{theme_name}%' "
            if theme_state is not None and theme_state != '':
                sql_where += f" and  theme.state = '{theme_state}' "
            else:
                sql_where += f""
            if task_state is not None and task_state != '':
                sql_where += f" and  task.state = '{task_state}' "

            r, d = self.dbUtil.rg_get_labels(where_task=sql_where)

            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:执行查看/[分页查询]提取标注信息", '数据库操作', "不成功", ""]
            else:
                rn = len(d)
                ptotal = ceil(rn / _Pagerows)
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                if _curPageIndex <= 0:
                    _curPageIndex = 1
                pids = ""
                uids = ""
                themeids = ""
                retData = []
                b = (_curPageIndex - 1) * _Pagerows
                for i in range(b, min(b + _Pagerows, rn)):
                    retData.append(d[i])
                    if pids == '':
                        pids += str(d[i][9])
                        uids += str(d[i][12])
                        themeids += str(d[i][0])
                    else:
                        pids += "," + str(d[i][9])
                        uids += "," + str(d[i][12])
                        themeids += "," + str(d[i][0])

                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if pr == '0':
                    pd = None
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                if ur == '0':
                    ud = None
                sql = f" SELECT theme_id, count(*) FROM task where theme_id in  ({themeids}) and state in ('notStarted', 'labelling', 'labelled') " \
                      "group by theme_id"
                thr, thd = self.dbUtil.myQueryExt(sql)
                if thr == '0':
                    thd = None
                ret = [r, REQmsg[1], retData, pd, _curPageIndex, ptotal, rn, paging,ud,thd]
                msgtip = [REQmsg[2], f"应答:执行查看/[分页查询]标注信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 执行查看/提交标注信息(合格，不合格)

    def rgQ_label_commit(self, clientAddr, REQmsg):
        if REQmsg[1] == 28:
            theme_id = REQmsg[3][0]
            check_id = REQmsg[3][1]
            file_id = REQmsg[3][2]
            uid = REQmsg[3][3]
            stat = REQmsg[3][4]
            # 'qualified', 'notqualified'
            sql1 = f" UPDATE theme SET state = 'evaluating' WHERE theme_id = {theme_id} "
            sql2 = f" UPDATE task SET state = '{stat}' WHERE theme_id = {theme_id} and check_id = {check_id} and " \
                   f"file_id ={file_id} and uid = {uid}"
            if stat == 'qualified':
                sqls = [sql2]
                r, d = self.dbUtil.myExecuteTranSql(sqls)
            elif stat == 'notqualified':
                # sql3 = f" delete from reslab where theme_id={theme_id} and check_id={check_id} and  file_id={file_id} and  uid={uid}"
                sqls = [sql2]
                r, d = self.dbUtil.myExecuteTranSql(sqls)
            else:
                r = '0'
                d = '状态只能是qualified或notqualified'
            if r == '1':
                ret = [r, REQmsg[1], f'{REQmsg[0]}/标注设置[{stat}],操作成功']
                msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/标注设置[{stat}]", '数据库操作', "成功", ""]
            else:
                ret = [r, REQmsg[1], f'{REQmsg[0]}/标注设置[{stat}],操作不成功:{d}']
                msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/标注设置[{stat}]", '数据库操作', f"不成功{d}", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 执行查看/提取未标注信息

    def rgQ_get_labels(self, clientAddr, REQmsg):
        if REQmsg[1] == 1:
            _uid = REQmsg[3][0]
            _curPageIndex = REQmsg[3][1]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][2]
            if _Pagerows <= 0:
                _Pagerows = 12
            # sql_where = f" task.uid={_uid} and (task.state='notStarted' or task.state='labelling') "
            #sql_where = f" theme.state in ('evaluating','notUsable','usable') and  theme.uid={_uid}  "
            sql_where = f" theme.state in ('evaluating','labelling') and  theme.uid={_uid} and " \
                        f" task.state in ('labelled','qualified','notqualified') "
            r, d = self.dbUtil.rg_get_labels(where_task=sql_where)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], "应答:执行查看/提取课堂内容信息", '数据库操作', "不成功", ""]
            else:
                rn = len(d)
                ptotal = ceil(rn / _Pagerows)
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                if _curPageIndex <= 0:
                    _curPageIndex = 1
                pids = ""
                uids = ""
                themeids = ""
                retData = []
                b = (_curPageIndex - 1) * _Pagerows
                for i in range(b, min(b + _Pagerows, rn)):
                    retData.append(d[i])
                    if pids == '':
                        pids += str(d[i][9])
                        uids += str(d[i][12])
                        themeids += str(d[i][0])
                    else:
                        pids += "," + str(d[i][9])
                        uids += "," + str(d[i][12])
                        themeids += "," + str(d[i][0])
                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if pr == '0':
                    pd = None
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                if ur == '0':
                    ud = None
                sql=f" SELECT theme_id, count(*) FROM task where theme_id in  ({themeids}) and state in ('notStarted', 'labelling', 'labelled') " \
                     "group by theme_id"
                thr, thd = self.dbUtil.myQueryExt(sql)
                if thr == '0':
                    thd = None
                ret = [r, REQmsg[1], d, pd,ud,thd,_curPageIndex, ptotal, rn]
                msgtip = [REQmsg[2], "应答:执行查看/提取标注信息", '数据库操作', "成功",""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret


    # 科研标注/查询、分页
    def rg_paging(self, clientAddr, REQmsg):
        if REQmsg[1] == 30:
            _uid = REQmsg[3][0]
            _curPageIndex = REQmsg[3][1]
            _Pagerows = REQmsg[3][2]
            if _Pagerows <= 0:
                _Pagerows = 12
            paging = REQmsg[3][3]

            theme_name = REQmsg[3][4]
            theme_state = REQmsg[3][5]
            task_state = REQmsg[3][6]

            sql_where = f"  theme.state!='creating' and  task.uid={_uid} and (task.state='notStarted' or task.state='labelling') "
            if theme_name is not None and theme_name != '':
                sql_where += f" and  theme.name like '%{theme_name}%' "
            if theme_state is not None and theme_state != '':
                sql_where += f" and  theme.state = '{theme_state}' "
            if task_state is not None and task_state != '':
                sql_where += f" and  task.state = '{task_state}' "

            r, d = self.dbUtil.rg_get_labels(where_task=sql_where)

            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:科研标注/[分页查询]提取标注信息", '数据库操作', "不成功", ""]
            else:
                rn = len(d)
                ptotal = ceil(rn / _Pagerows)
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                if _curPageIndex <= 0:
                    _curPageIndex = 1
                pids = ""
                retData = []
                b = (_curPageIndex - 1) * _Pagerows
                for i in range(b, min(b + _Pagerows, rn)):
                    retData.append(d[i])
                    if pids == '':
                        pids += str(d[i][9])
                    else:
                        pids += "," + str(d[i][9])
                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if pr == '0':
                    pd = None

                ret = [r, REQmsg[1], retData, pd, _curPageIndex, ptotal, rn, paging]
                msgtip = [REQmsg[2], f"应答:科研标注/[分页查询]标注信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/提交标注信息
    def rg_label_commit(self, clientAddr, REQmsg):
        if REQmsg[1] == 28:
            theme_id = REQmsg[3][0]
            check_id = REQmsg[3][1]
            file_id = REQmsg[3][2]
            uid = REQmsg[3][3]
            # r, d = self.dbUtil.task_update(theme_id, check_id, file_id, uid, 'labelled')
            sql1 = f"UPDATE task SET state = 'labelled' WHERE theme_id = {theme_id} and check_id = {check_id} and " \
                   f"file_id ={file_id} and uid = {uid}"
            sql2 = f"UPDATE theme SET state = 'evaluating' WHERE theme_id = {theme_id} and  state != 'evaluating' "
            sqls = [sql1, sql2]
            r, d = self.dbUtil.myExecuteTranSql(sqls)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/完成任务标注", '数据库操作', f"不成功{d}", ""]
            else:
                ret = [r, REQmsg[1], f'{REQmsg[0]}/完成任务标注成功']
                msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/完成任务标注", f'数据库操作', "成功", ""]
            # self.diag_mutex.acquire()
            # r0, d0 = self.dbUtil.task_get(theme_id=theme_id,
            #                               other_sql="(state ='notStarted' or state= 'labelling')")
            # if r0 == '0':
            #     ret = [r0, f'提取当前主题的任务记录不成功:{d0}']
            #     msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/提取当前主题的任务记录不成功:{d0}", '数据库操作', "不成功",
            #               ""]
            # else:
            #     if len(d0) > 1:
            #         r, d = self.dbUtil.task_update(theme_id, check_id, file_id, uid, 'labelled')
            #     else:
            #         sql1 = f" UPDATE task SET state = 'labelled' WHERE theme_id = {theme_id} and check_id = {check_id} and " \
            #                f"file_id ={file_id} and uid = {uid}"
            #         sql2 = f"UPDATE theme SET state = 'evaluating' WHERE theme_id = {theme_id} "
            #         sqls = [sql1, sql2]
            #         r, d = self.dbUtil.myExecuteTranSql(sqls)
            #     if r == '0':
            #         ret = [r, d]
            #         msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/完成任务标注", '数据库操作', f"不成功{d}", ""]
            #     else:
            #         ret = [r, REQmsg[1], f'{REQmsg[0]}/完成任务标注成功']
            #         msgtip = [REQmsg[2], f"应答:{REQmsg[0]}/完成任务标注", f'数据库操作', "成功", ""]
            # self.diag_mutex.release()
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/删除样本状态信息
    def rg_del_reslab_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 23:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                rn, err = self.dbUtil.reslab_del(check_id, file_id, _start, pick_channel, _end, uid, type_id,
                                                 theme_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/修改样本状态信息
    def rg_update_reslab_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 22:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                rn, err = self.dbUtil.reslab_update(check_id, file_id, _start, pick_channel, _end, uid,
                                                    type_id, theme_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/添加样本状态信息
    def rg_add_reslab_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 21:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                rn, err = self.dbUtil.reslab_add(check_id, file_id, _start, pick_channel,
                                                 _end, uid, type_id, theme_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/删除样本
    def rg_del_reslab19(self, clientAddr, REQmsg):
        if REQmsg[1] == 19:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                rn, err = self.dbUtil.reslab_del(check_id, file_id, _start, pick_channel, _end, uid, type_id,
                                                 theme_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/添加样本
    def rg_insert_reslab17(self, clientAddr, REQmsg):
        if REQmsg[1] == 17:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                rn, err = self.dbUtil.reslab_add(check_id, file_id, _start, pick_channel, _end, uid,
                                                 type_id, theme_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/提取样本信息？？？
    def rg_init_reslabList(self, clientAddr, REQmsg):
        if REQmsg[1] == 16:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            channels = REQmsg[3][2]
            type_names = REQmsg[3][3]
            user_names = REQmsg[3][4]
            status_show = REQmsg[3][5]
            theme_id = REQmsg[3][6]
            try:
                rn, retData = self.dbUtil.reslabList_get(theme_id, check_id, file_id, channels, type_names,
                                                         user_names, status_show)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', retData]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{retData}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', retData]
            except Exception as e:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", f'数据库操作不成功{e}', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功{e}"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/添加或修改样本
    def rg_reslab_update15(self, clientAddr, REQmsg):
        if REQmsg[1] == 14 or REQmsg[1] == 15:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                if REQmsg[1] == 14:
                    rn, err = self.dbUtil.reslab_add(check_id, file_id, _start, pick_channel,
                                                     _end, uid, type_id, theme_id)
                else:
                    rn, err = self.dbUtil.reslab_update(check_id, file_id, _start, pick_channel, _end, uid,
                                                        type_id, theme_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", '']
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
                ret = ['0', REQmsg[1], '数据库操作不成功']
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']

        return msgtip, ret

    # 科研标注/删除样本
    def rg_reslab_del13(self, clientAddr, REQmsg):
        if REQmsg[1] == 13:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                rn, err = self.dbUtil.reslab_del(check_id, file_id, _start, pick_channel, _end, uid, type_id,
                                                 theme_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], '数据库操作', "成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 科研标注/添加样本
    def rg_update_reslab12(self, clientAddr, REQmsg):
        if REQmsg[1] == 11 or REQmsg[1] == 12:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            theme_id = REQmsg[3][7]
            try:
                if REQmsg[1] == 11:
                    r, err = self.dbUtil.reslab_add(check_id, file_id, _start, pick_channel,
                                                    _end, uid, type_id, theme_id)
                else:
                    r, err = self.dbUtil.reslab_update(check_id, file_id, _start, pick_channel, _end, uid,
                                                       type_id, theme_id)
                if r == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", '']
                    ret = ['1', REQmsg[1], '数据库操作', "成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}手动标注", '未定义命令', '', '']
        return msgtip, ret

        # 科研标注/打开脑电文件

    def rg_openEEGFile(self, clientAddr, REQmsg):
        if REQmsg[1] == 8:
            tmp_type_info = self.dbUtil.get_typeInfo()

            tmp_type_filter = [x[1] for x in tmp_type_info]

            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            patient_id = REQmsg[3][2]
            theme_id = REQmsg[3][3]
            uid = REQmsg[3][4]
            task_state = REQmsg[3][5]

            ret = self.appUtil.openEEGFile(check_id, file_id)
            if ret[0] == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件无效", '{:>03}.bdf'.format(file_id), ""]
                return msgtip, ret
            raw = ret[1]
            self.appUtil.closeEEGfile(raw)
            _channels = ret[2]

            _patientInfo = self.dbUtil.get_patientInfo('patient_id', patient_id)

            _channels = tuple(_channels) if len(_channels) != 1 else "('{}')".format(_channels[0])
            _type_names = tuple(tmp_type_filter) if len(tmp_type_filter) != 1 else "('{}')".format(
                tmp_type_filter[0])
            _user_uids = "('{}')".format(uid)
            _status_show = True
            rn1, _sample_list = self.dbUtil.reslabList_get(theme_id, check_id, file_id, _channels, _type_names,
                                                           _user_uids,
                                                           _status_show)
            _status_info = []
            if rn1 == '0':
                _sample_list = []
            else:
                for sa in _sample_list:
                    if sa[0]=='all':
                        _status_info.append(sa)
            if task_state == 'notStarted':
                r3, d3 = self.dbUtil.task_update(theme_id, check_id, file_id, uid, 'labelling')
            REPData = ['1', _patientInfo, _sample_list, ret[2], ret[3],
                       ret[4], ret[5], ret[6], ret[7], ret[8], ret[9], _status_info]

            msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '成功', '']
        else:
            REPData = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '未定义命令', '']
        return msgtip, REPData


    # 科研标注/提取未标注信息
    def rg_get_notlabels(self, clientAddr, REQmsg):
        if REQmsg[1] == 1:
            _uid = REQmsg[3][0]

            _curPageIndex = REQmsg[3][1]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][2]
            if _Pagerows <= 0:
                _Pagerows = 12

            sql_where = f"  theme.state!='creating' and  task.uid={_uid} and (task.state='notStarted' or task.state='labelling') "
            #sql_where = f" theme.state='labelling' and  task.uid={_uid}  "
            r, d = self.dbUtil.rg_get_labels(where_task=sql_where)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], "应答:学习评估/提取课堂内容信息", '数据库操作', "不成功", ""]
            else:
                rn = len(d)
                ptotal = ceil(rn / _Pagerows)
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                if _curPageIndex <= 0:
                    _curPageIndex = 1
                pids = ""
                retData = []
                b = (_curPageIndex - 1) * _Pagerows
                for i in range(b, min(b + _Pagerows, rn)):
                    retData.append(d[i])
                    if pids == '':
                        pids += str(d[i][9])
                    else:
                        pids += "," + str(d[i][9])
                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if pr == '0':
                    pd = None
                ret = [r, REQmsg[1], retData, pd, _curPageIndex, ptotal, rn]
                # pids = ""
                # for dInfo in d:
                #     if pids == '':
                #         pids += str(dInfo[9])
                #     else:
                #         pids += "," + str(dInfo[9])
                #
                # pr, pd = self.dbUtil.get_patientNameByPids(pids)
                # if pr == '0':
                #     pd = None
                # ret = [r, REQmsg[1], d, pd]
                msgtip = [REQmsg[2], "应答:科研标注/提取标注信息", '数据库操作', "成功",""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    #  学习评估/提取课堂测试内容
    def da_get_classContents(self, clientAddr, REQmsg):
        if REQmsg[1] == 27:
            sql=f" SELECT content.check_id, content.file_id, content.uid, check_info.check_number ,check_info.patient_id FROM  " \
                f" content  right join check_info on content.check_id = check_info.check_id  where content.purpose = 'test' and content.class_id = {REQmsg[3][0]} "
            r, d = self.dbUtil.myQueryExt(sql)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:学习评估/提取课堂测试内容", '数据库操作', "不成功", ""]
            else:
                uids = ""
                for dInfo in d:
                    if uids == '':
                        uids += str(dInfo[2])
                    else:
                        uids += "," + str(dInfo[2])
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                if ur == '0':
                    ud = None
                ret = [r, REQmsg[1], d, ud]

                msgtip = [REQmsg[2], f"应答:学习评估/提取课堂测试内容", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    #  学习评估/提取诊断信息
    def da_get_diag(self, clientAddr, REQmsg):
        if REQmsg[1] == 26:
            r, d = self.dbUtil.diag_get(check_id=REQmsg[3][0], uid=REQmsg[3][1])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:学习评估/提取诊断信息", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:学习评估/提取诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习评估/删除学员学习测试信息
    def da_del_studentsTest(self, clientAddr, REQmsg):
        if REQmsg[1] == 25:
            class_id = REQmsg[3][0]
            stUid = REQmsg[3][1]
            stUid = tuple(stUid) if len(stUid) != 1 else "('{}')".format(stUid[0])
            sql1 = f"delete from study where class_id={class_id} and uid in {stUid}"
            sql2 = f"delete from student where class_id={class_id} and uid in {stUid}"
            sql3 = f"delete from result where class_id={class_id} and uid in {stUid}"

            sqls = [sql1, sql2, sql3]
            r, d = self.dbUtil.myExecuteTranSql(sqls)
            if r == '0':
                REPData = ['0', REQmsg[1], f"删除学员学习测试信息不成功:{d}"]
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}删除学员学习测试信息不成功", f'{d}', "不成功", ""]
                return msgtip, REPData
            REPData = ['1', REQmsg[1], f"删除学员学习测试信息成功"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}删除学员学习测试信息成功", '数据库操作', "成功", ""]
        else:
            REPData = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}删除学员学习测试信息", '未定义命令', '']
        return msgtip, REPData

    # 学习评估/删除课堂学员学习测试信息
    def da_del_class(self, clientAddr, REQmsg):
        if REQmsg[1] == 24:
            class_id = REQmsg[3][0]
            r, d = self.dbUtil.dl_student_get(class_id=class_id, other_where="state !='tested'")
            if r == '0':
                REPData = ['0', REQmsg[1], f"删除课堂及学习测试信息,统计未完成测试学生信息不成功:{d}"]
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}删除课堂,统计未完成测试学生信息不成功", f'{d}', "不成功", ""]
                return msgtip, REPData
            if len(d) > 0:
                REPData = ['0', REQmsg[1], f"删除课堂及学习测试信息,本课堂还有:{len(d)}学员未完成测试，不能删除"]
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}课堂有{len(d)}学员未完成测试，不能删除", f'{len(d)}未完成测试',
                          "不成功", ""]
                return msgtip, REPData
            sql1 = f"delete from study where class_id={class_id} "
            sql2 = f"delete from student where class_id={class_id}"
            sql3 = f"delete from content where class_id={class_id}"
            sql4 = f"delete from result where class_id={class_id}"
            sql5 = f"delete from class where class_id={class_id}"
            sqls = [sql1, sql2, sql3, sql4, sql5]
            r, d = self.dbUtil.myExecuteTranSql(sqls)
            if r == '0':
                REPData = ['0', REQmsg[1], f"删除课堂及学习测试信息不成功:{d}"]
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}删除课堂及学习测试信息不成功", f'{d}', "不成功", ""]
                return msgtip, REPData
            REPData = ['1', REQmsg[1], f"删除课堂及学习测试信息成功"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}删除课堂及学习测试信息成功", '数据库操作', "成功", ""]
        else:
            REPData = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}删除课堂及学习测试信息", '未定义命令', '']
        return msgtip, REPData

    # 学习评估/打开脑电数据文件
    def da_openEEGFile(self, clientAddr, REQmsg, curUser):
        if REQmsg[1] == 8:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            patient_id = REQmsg[3][2]
            did = REQmsg[3][3]
            class_id = REQmsg[3][4]
            suid = REQmsg[3][5]

            ret = self.appUtil.openEEGFile(check_id, file_id)
            if ret[0] == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件无效", '{:>03}.bdf'.format(file_id), ""]
                return msgtip, ret
            raw = ret[1]
            self.appUtil.closeEEGfile(raw)
            _channels = ret[2]

            _patientInfo = self.dbUtil.get_patientInfo('patient_id', patient_id)
            sr, _studentInfo = self.dbUtil.dl_student_get(class_id=class_id, uid=suid, userInfo=True)

            _channels = tuple(_channels) if len(_channels) != 1 else "('{}')".format(_channels[0])

            _status_show = True

            # rn2, _status_info = self.dbUtil.get_statusInfo(check_id, file_id)
            # if rn2 == '0':
            #     _status_info = None

            samr, samp = self.dbUtil.da_get_sampleInfoByUID(check_id, file_id, did, True)
            if samr == '0':
                samp = None

            rn1, _sample_list = self.dbUtil.result_get(class_id, check_id, file_id, did, suid)
            _status_info = []
            if rn1 == '0':
                _sample_list = None
            else:
                for sa in _sample_list:
                    if sa[0] == 'all':
                        _status_info.append(sa)
            # if _status_info == []:
            #     _status_info = None
            sql1 = f"select count(*) from result where class_id={class_id} and sUid={suid} and check_id={check_id} " \
                   f" and file_id={file_id}  and uid={did}"
            qsum = self.dbUtil.myQuery(sql1)
            if qsum is None:
                qsum = -1
            else:
                qsum = int(qsum[0][0])
            sql2 = f"select count(*) from result right join sample_info on  " \
                   f" result.check_id=sample_info.check_id and  result.file_id=sample_info.file_id and " \
                   f" result.uid=sample_info.uid and  result.channel=sample_info.channel and" \
                   f" result.begin=sample_info.begin and result.type_id=sample_info.type_id  " \
                   f" where result.class_id={class_id} and result.uid={did} and result.sUid={suid} and " \
                   f" result.check_id={check_id} and result.file_id={file_id}"
            asum = self.dbUtil.myQuery(sql2)
            if asum is None:
                asum = -1
            else:
                asum = int(asum[0][0])
            REPData = ['1', _patientInfo, _sample_list, ret[2], ret[3],
                       ret[4], ret[5], ret[6], ret[7], ret[8], ret[9], _status_info, samp, qsum, asum, _studentInfo]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '成功', '']
        else:
            REPData = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '未定义命令', '']
        return msgtip, REPData

    # 学习评估/提取班级学生
    def da_get_ClassStudent(self, clientAddr, REQmsg):
        if REQmsg[1] == 2:
            class_id = REQmsg[3][0]
            # r, d = self.dbUtil.dl_student_get(class_id=class_id, other_where="student.state='tested'",userInfo=True)
            userInfo= self.curUser.users.get(REQmsg[2])
            if userInfo[8]:
                r, d = self.dbUtil.dl_student_get(class_id=class_id, userInfo=True)
            else:
                r, d = self.dbUtil.dl_student_get(class_id=class_id,uid=REQmsg[2], userInfo=True)

            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], "应答:学习评估/提取班级学生信息", '数据库操作', "不成功", ""]
            else:
                stuids = ""
                for dInfo in d:
                    if stuids == '':
                        stuids += str(dInfo[1])
                    else:
                        stuids += "," + str(dInfo[1])
                if stuids != "":
                    qr, qnum = self.dbUtil.da_get_resultNumByClass(class_id, stuids)
                    ar, anum = self.dbUtil.da_get_resultAnswerTrueNumByClass(class_id, stuids)
                else:
                    qr='0'
                    ar='0'
                if qr == '0':
                    qnum = None
                if ar == '0':
                    anum = None
                ret = [r, REQmsg[1], d, qnum, anum]
                msgtip = [REQmsg[2], "应答:学习评估/提取班级学生信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习评估/提取学习信息
    def da_get_contents(self, clientAddr, REQmsg):
        if REQmsg[1] == 1:
            _uid = REQmsg[3][0]
            sql_where = f" SELECT * FROM class where uid={_uid} or class_id in " \
                        f"(SELECT class_id FROM student where uid={_uid} and state ='tested')"
            r, d = self.dbUtil.myQueryExt(sql_where)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], "应答:学习评估/提取课堂信息", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], "应答:学习评估/提取课堂信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习测试/完成学习测试
    def dt_diagTest_commit(self, clientAddr, REQmsg):
        if REQmsg[1] == 28:
            class_id = REQmsg[3][0]
            uid = REQmsg[3][1]
            sql1 = f"select count(*) from result where class_id={class_id} and suid={uid}"
            qsum = self.dbUtil.myQuery(sql1)
            if qsum is None:
                ret = ['0', REQmsg[1], '统计应标注记录总数不成功。']
                msgtip = [REQmsg[2], f"应答:学习测试/完成学习测试信息", '数据库操作', "统计应标注记录总数不成功",
                          ""]
                return msgtip, ret
            sql2 = f"select count(*) from result,sample_info where result.class_id={class_id} and result.suid={uid} and " \
                   f" result.check_id=sample_info.check_id and  result.file_id=sample_info.file_id and " \
                   f" result.uid=sample_info.uid and result.channel=sample_info.channel" \
                   f" and result.begin=sample_info.begin and result.type_id=sample_info.type_id "
            asum = self.dbUtil.myQuery(sql2)
            if asum is None:
                ret = ['0', REQmsg[1], '统计学员标注正确的记录数不成功。']
                msgtip = [REQmsg[2], f"应答:学习测试/完成学习测试信息", '数据库操作',
                          "统计学员标注正确的记录数不成功", ""]
                return msgtip, ret
            q = int(qsum[0][0])
            a = int(asum[0][0])
            if q==0:
                q=1
                a=1
            sql = f" grade={int(a * 100 / q)},state = 'tested'"
            r, d = self.dbUtil.dl_student_update(class_id=class_id, uid=uid, setSQL=sql)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:学习测试/完成学习测试信息", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], f'学习测试/完成学习测试信息成功：总数{qsum}，正确{asum},比例{int(a * 100 / q)}%']
                msgtip = [REQmsg[2], f"应答:学习测试/完成学习测试信息", f'数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习测试/删除样本状态信息
    def dt_del_sampleInfo_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 23:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            class_id = REQmsg[3][7]
            suid = REQmsg[3][8]
            try:
                rn, err = self.dbUtil.result_del(class_id, check_id, file_id, _start, pick_channel, _end, uid,suid ,
                                                 type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习测试/修改样本状态信息
    def dt_update_sampleInfo_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 22:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            class_id = REQmsg[3][7]
            suid = REQmsg[3][8]

            try:
                rn, err = self.dbUtil.result_update(class_id, check_id, file_id, _start, pick_channel, _end, uid, suid,
                                                    type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习测试/添加样本状态信息
    def dt_add_sampleInfo_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 21:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            class_id = REQmsg[3][7]
            suid = REQmsg[3][8]
            try:
                rn, err = self.dbUtil.result_add(class_id, check_id, file_id, _start, pick_channel, _end, uid,
                                                 suid,type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习测试/提取样本信息？？？
    def dt_init_resultList(self, clientAddr, REQmsg):
        if REQmsg[1] == 16:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            channels = REQmsg[3][2]
            type_names = REQmsg[3][3]
            user_names = REQmsg[3][4]
            status_show = REQmsg[3][5]
            class_id = REQmsg[3][6]
            suid = REQmsg[3][7]
            try:
                rn, retData = self.dbUtil.resultList_get(class_id, check_id, file_id, channels, type_names,
                                                         user_names, status_show,suid)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', retData]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{retData}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', retData]
            except Exception as e:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", f'数据库操作不成功{e}', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功{e}"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习测试/删除样本
    def dt_del_result(self, clientAddr, REQmsg):
        if REQmsg[1] == 13 or REQmsg[1] == 19:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            class_id = REQmsg[3][7]
            suid = REQmsg[3][8]
            try:
                rn, err = self.dbUtil.del_result(class_id, check_id, file_id, _start, pick_channel, _end, uid,
                                                 type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], '数据库操作', "成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 学习测试/添加、修改样本
    def dt_update_result(self, clientAddr, REQmsg):
        if REQmsg[1] == 11 or REQmsg[1] == 12 or REQmsg[1] == 14 or REQmsg[1] == 15 or REQmsg[1] == 17:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            class_id = REQmsg[3][7]
            suid = REQmsg[3][8]
            try:
                if REQmsg[1] == 11 or REQmsg[1] == 14 or REQmsg[1] == 17:
                    rn, err = self.dbUtil.result_add(class_id, check_id, file_id, _start, pick_channel, _end, uid,
                                                     suid,type_id)
                else:
                    rn, err = self.dbUtil.result_update(class_id, check_id, file_id, _start, pick_channel, _end,
                                                        uid,suid, type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", '']
                    ret = ['1', REQmsg[1], '数据库操作', "成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}手动标注", '未定义命令', '', '']
        return msgtip, ret

    # 诊断学习/添加学习记录，并统计时长，处理完成状态
    def study_add(self, class_id, uid, start_time):
        r, d = self.dbUtil.dl_study_end(class_id, uid, start_time)
        if r == '1':
            r, st = self.dbUtil.dl_student_get(class_id, uid)
            if r == '1' and len(st) == 1 and st[0][2] == 'studying':
                sql = "SELECT sum(hour(TIMEDIFF(end,start))*360+ minute(TIMEDIFF(end,start))*60+second(TIMEDIFF(end,start)))/60 FROM study where end>start " \
                      f" and class_id={class_id} and uid = {uid}"
                sttime = self.dbUtil.myQuery(sql)
                sql = f"SELECT time FROM class where class_id={class_id} "
                cltime = self.dbUtil.myQuery(sql)
                if sttime is not None and cltime is not None:
                    if cltime[0][0] <= sttime[0][0]:
                        self.dbUtil.dl_student_update(class_id, uid, "state = 'studied'")
        return r, d

    # 诊断学习/结束计时
    def dl_study_end(self, clientAddr, REQmsg):
        if REQmsg[1] == 3:
            class_id = REQmsg[3][0]
            uid = REQmsg[3][1]
            r, d = self.study_add(class_id, uid, REQmsg[3][2])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:诊断学习/更新学习结束时间", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:诊断学习/更新学习结束时间", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 诊断学习/提取学习计时
    def dl_study_get(self, clientAddr, REQmsg):
        if REQmsg[1] == 2:
            r, d = self.dbUtil.study_get(class_id=REQmsg[3][0], uid=REQmsg[3][1])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:诊断学习/提取学习信息", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:诊断学习/提取学习信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 诊断学习/提取诊断信息
    def dl_diag_get(self, clientAddr, REQmsg):
        if REQmsg[1] == 25:
            r, d = self.dbUtil.diag_get(check_id=REQmsg[3][0])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:诊断学习/提取诊断信息", '数据库操作', "不成功", ""]
            else:
                pids = ""
                uids = ""
                for dInfo in d:
                    if pids == '':
                        pids += str(dInfo[0])
                        uids += str(dInfo[2])
                    else:
                        pids += "," + str(dInfo[0])
                        uids += "," + str(dInfo[2])
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if ur == '0':
                    ud = None
                if pr == '0':
                    pd = None
                ret = [r, REQmsg[1], d, ud, pd]
                msgtip = [REQmsg[2], f"应答:诊断学习/提取诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 诊断学习/提取学习信息
    def dl_get_contents(self, clientAddr, REQmsg):
        ltip = {'diagTest': '学习测试', 'diagTraining': '诊断学习'}
        if REQmsg[1] == 1:
            _uid = REQmsg[3][0]
            if REQmsg[0] == 'diagTraining':
                if len(REQmsg[3]) == 4:
                    r, d = self.study_add(REQmsg[3][1], REQmsg[3][2], REQmsg[3][3])
                sql_where = " class.start<=current_timestamp() and  current_timestamp()<=class.end and  content.purpose='training'"
                st_where = f" student.uid={_uid} and (student.state ='beforeStudy' or student.state ='studying' or student.state ='studied')"
            else:
                sql_where = " class.start<=current_timestamp() and  current_timestamp()<=class.end and content.purpose='test'"
                st_where = f" student.uid={_uid} and (student.state ='studied' or student.state ='testing')"
            r, d = self.dbUtil.dl_get_contents(where_class=sql_where, where_student=st_where)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/提取课堂内容信息", '数据库操作', "不成功", ""]
            else:
                sr, sd = self.dbUtil.dl_student_get(other_where=st_where)
                if sr == '0':
                    sd = None
                pids = ""
                uids = ""
                for dInfo in d:
                    if pids == '':
                        pids += str(dInfo[8])
                        uids += str(dInfo[11])
                    else:
                        pids += "," + str(dInfo[8])
                        uids += "," + str(dInfo[11])
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if ur == '0':
                    ud = None
                if pr == '0':
                    pd = None
                ret = [r, REQmsg[1], d, ud, pd, sd]
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/提取提取课堂内容信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    def dl_openEEGFile(self, clientAddr, REQmsg, curUser):
        if REQmsg[1] == 8:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            patient_id = REQmsg[3][2]
            uid = REQmsg[3][3]

            ret = self.appUtil.openEEGFile(check_id, file_id)
            if ret[0] == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件无效", '{:>03}.bdf'.format(file_id), ""]
                return msgtip, ret
            raw = ret[1]
            self.appUtil.closeEEGfile(raw)
            _channels = ret[2]

            _patientInfo = self.dbUtil.get_patientInfo('patient_id', patient_id)

            _channels = tuple(_channels) if len(_channels) != 1 else "('{}')".format(_channels[0])

            _status_show = True

            # rn2, _status_info = self.dbUtil.get_statusInfo(check_id, file_id)
            #
            # if rn2 == '0':
            #     _status_info = None

            class_id = REQmsg[3][4]
            suid = REQmsg[3][5]
            r, st = self.dbUtil.dl_student_get(class_id, suid)
            if r == '1' and len(st) == 1:
                if REQmsg[0] == 'diagTest':
                    if st[0][2] == 'studied':
                        samr, samp = self.dbUtil.dl_get_sampleInfoByClassID(class_id)
                        if samr == '0':
                            REPData = ['0', REQmsg[1], f"应答{REQmsg[0]}提取导师标注样本信息不成功：{samp}"]
                            msgtip = [REQmsg[2], f"应答{REQmsg[0]}导师标注样本信息不成功：", f'{samp}', '']
                            return msgtip, REPData
                        sql_values = ""
                        for sample in samp:
                            if sql_values != "":
                                sql_values += ','
                            sql_values += f"({class_id},{sample[0]},{sample[1]},{sample[2]},{suid},{sample[3]}," \
                                          f"'{sample[4]}',{sample[5]},NULL)"
                        if sql_values != "":
                            sql1 = f"update student set state='testing' where class_id= {class_id} and uid={suid}"
                            sql_values = f"insert into result(class_id,check_id,file_id,uid,sUid,begin,channel,end,type_id) " \
                                         f"values {sql_values}"
                            sqlt = [sql1, sql_values]
                            r, dtime = self.dbUtil.myExecuteTranSql(sqlt)
                            if r == '0':
                                REPData = ['0', REQmsg[1], f"应答{REQmsg[0]}生成测试样本不成功{dtime}"]
                                msgtip = [REQmsg[2], f"应答{REQmsg[0]}生成测试样本不成功", f'{dtime}', '']
                                return msgtip, REPData
                        else:
                            r, dtime = self.dbUtil.dl_student_update(class_id=class_id, uid=suid,
                                                                     setSQL="state='testing'")

                    rn1, _sample_list = self.dbUtil.result_get(class_id, check_id, file_id, uid,suid)
                    _status_info = []
                    if rn1 == '0':
                        _sample_list = None
                    else:
                        for sa in _sample_list:
                            if sa[0]=='all':
                                _status_info.append(sa)
                    REPData = ['1', _patientInfo, _sample_list, ret[2], ret[3],
                               ret[4], ret[5], ret[6], ret[7], ret[8], ret[9], _status_info]
                else:
                    rn1, _sample_list = self.dbUtil.dl_get_sampleListInfo(check_id, file_id, uid)
                    _status_info = []
                    if rn1 == '0':
                        _sample_list = None
                    else:
                        for sa in _sample_list:
                            if sa[0] == 'all':
                                 _status_info.append(sa)
                    # if _status_info == []:
                    #     _status_info = None
                    now = datetime.datetime.now()
                    start_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    if st[0][2] == 'beforeStudy':
                        sqls = [f"update student set state='studying' where class_id={class_id} and uid={suid}",
                                f"INSERT INTO study(class_id,uid,start,end) VALUES ({class_id},{suid}, '{start_time}','{start_time}')"]
                        r, dtime = self.dbUtil.myExecuteTranSql(sqls)
                    else:
                        r, dtime = self.dbUtil.dl_study_start(class_id, suid, start_time)
                    if r == '0':
                        REPData = ['1', _patientInfo, _sample_list, ret[2], ret[3],
                                   ret[4], ret[5], ret[6], ret[7], ret[8], ret[9], _status_info, None, None]
                    else:
                        REPData = ['1', _patientInfo, _sample_list, ret[2], ret[3],
                                   ret[4], ret[5], ret[6], ret[7], ret[8], ret[9], _status_info, class_id,
                                   start_time]
            else:
                rn1, _sample_list = self.dbUtil.result_get(class_id, check_id, file_id, uid,suid)
                _status_info = []
                if rn1 == '0':
                    _sample_list = None
                else:
                    for sa in _sample_list:
                         if sa[0] == 'all':
                            _status_info.append(sa)
                # if _status_info == []:
                #     _status_info = None
                REPData = ['1', _patientInfo, _sample_list, ret[2], ret[3],
                           ret[4], ret[5], ret[6], ret[7], ret[8], ret[9], _status_info]

            msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '成功', '']
        else:
            REPData = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '未定义命令', '']
        return msgtip, REPData


    # 诊断查询/查询、分页
    def mq_paging(self, clientAddr, REQmsg):
        if REQmsg[1] == 30:
            _uid = REQmsg[3][0]
            _curPageIndex = REQmsg[3][1]

            _Pagerows = REQmsg[3][2]
            if _Pagerows <= 0:
                _Pagerows = 12
            paging = REQmsg[3][3]
            qname = REQmsg[3][4]
            qvalue = REQmsg[3][5]
            mdate1 = REQmsg[3][6]
            mdate2 = REQmsg[3][7]

            where_sql = ''
            pname = ''
            if qvalue is not None and qvalue != "":
                if qname == "检查单号":
                    where_sql = f" check_info.check_number like '%{qvalue}%' "
                elif qname == "病人姓名":
                    pname = qvalue
                elif qname == "测量日期":
                    where_sql = f" measure_date = '{qvalue}' "
                elif qname == "医生名称":
                    where_sql = f" diag.uid in (select uid FROM user_info where name like '%{qvalue}%') "
            if mdate1 is not None and mdate1 != "":
                if where_sql == '':
                    where_sql = f" sign_date >= '{mdate1} 00:00:00' "
                else:
                    where_sql += f" and sign_date >= '{mdate1} 00:00:00' "
            if mdate2 is not None and mdate2 != "":
                if where_sql == '':
                    where_sql = f" sign_date <= '{mdate2} 23:59.59' "
                else:
                    where_sql += f" and sign_date <= '{mdate2} 23:59.59' "
            r, d = self.dbUtil.diag_getByPage(pname=pname, diag_state='diagnosed', other_where=where_sql)
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:诊断查询/提取诊断信息", '数据库操作', "不成功", ""]
            else:
                rn = len(d)
                ptotal = ceil(rn / _Pagerows)
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                if _curPageIndex <= 0:
                    _curPageIndex = 1
                pids = ""
                uids = ""
                retData = []
                b = (_curPageIndex - 1) * _Pagerows
                for i in range(b, min(b + _Pagerows, rn)):
                    retData.append(d[i])
                    if pids == '':
                        pids += str(d[i][0])
                        uids += str(d[i][2])
                    else:
                        pids += "," + str(d[i][0])
                        uids += "," + str(d[i][2])
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if ur == '0':
                    ud = None
                if pr == '0':
                    pd = None
                ret = [r, REQmsg[1], retData, ud, pd, _curPageIndex, ptotal, rn, paging]
                msgtip = [REQmsg[2], f"应答:诊断查询/分页查询诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 诊断查询/提取诊断信息

    def mq_get_diags_Diagnosed(self, clientAddr, REQmsg):
        if REQmsg[1] == 1:
            _uid = REQmsg[3][0]
            _uid = ''
            _curPageIndex = REQmsg[3][1]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][2]
            if _Pagerows <= 0:
                _Pagerows = 12
            # r, rn = self.dbUtil.diag_getRecords(uid=_uid, diag_state='diagnosed')
            #r, d = self.dbUtil.diag_getRecords(diag_state='diagnosed')
            r, d = self.dbUtil.diag_getByPage(diag_state='diagnosed')
            if r == '0':
                ret = [r, f'统计记录数不成功{r}']
                msgtip = [REQmsg[2], f"应答:诊断查询/提取诊断信息", '统计记录数不成功', f"{r}", ""]
                return msgtip, ret
            rn = len(d)
            ptotal = ceil(rn / _Pagerows)
            if _curPageIndex > ptotal:
                _curPageIndex = ptotal
            if _curPageIndex <= 0:
                _curPageIndex = 1
            pids = ""
            uids = ""
            retData = []
            b = (_curPageIndex - 1) * _Pagerows
            for i in range(b, min(b + _Pagerows, rn)):
                retData.append(d[i])
                if pids == '':
                    pids += str(d[i][0])
                    uids += str(d[i][2])
                else:
                    pids += "," + str(d[i][0])
                    uids += "," + str(d[i][2])
            ur, ud = self.dbUtil.get_userNameByUids(uids)
            pr, pd = self.dbUtil.get_patientNameByPids(pids)
            if ur == '0':
                ud = None
            if pr == '0':
                pd = None
            ret = [r, REQmsg[1], retData, ud, pd, _curPageIndex, ptotal, rn]
            # rn = rn[0]
            # ptotal = ceil(rn / _Pagerows)
            # if _curPageIndex > ptotal:
            #     _curPageIndex = ptotal
            #
            # r, d = self.dbUtil.diag_getByPage(diag_state='diagnosed',
            #                                   offset=(_curPageIndex - 1) * _Pagerows,
            #                                   psize=_Pagerows)
            # if r == '0':
            #     ret = [r, d]
            #     msgtip = [REQmsg[2], f"应答:诊断查询/提取诊断信息", '数据库操作', "不成功", ""]
            # else:
            #     pids = ""
            #     uids = ""
            #     for dInfo in d:
            #         if pids == '':
            #             pids += str(dInfo[0])
            #             uids += str(dInfo[2])
            #         else:
            #             pids += "," + str(dInfo[0])
            #             uids += "," + str(dInfo[2])
            #     ur, ud = self.dbUtil.get_userNameByUids(uids)
            #     pr, pd = self.dbUtil.get_patientNameByPids(pids)
            #     if ur == '0':
            #         ud = None
            #     if pr == '0':
            #         pd = None
            #     ret = [r, REQmsg[1], d, ud, pd, _curPageIndex, ptotal, rn]
            msgtip = [REQmsg[2], f"应答:诊断查询/提取诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/拒绝诊断信息

    def diag_refused(self, clientAddr, REQmsg):
        # ltip = {'consulting': '脑电会诊', 'manual': '标注诊断'}
        ltip = {'consulting': '脑电诊断', 'manual': '脑电诊断'}
        if REQmsg[1] == 29:
            check_id = REQmsg[3][0]
            uid = REQmsg[3][1]
            sql=f"select * from sample_info where check_id={check_id} and uid={uid}"
            r0, d0 = self.dbUtil.myQueryExt(sql)
            if r0=='0':
                ret = [r0, REQmsg[1], f'统计标注信息不成功:{d0}，不能拒绝。']
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/拒绝诊断信息", f'统计标注信息:{d0}', "不成功", ""]
                return msgtip, ret
            elif len(d0)>0:
                ret = ['0', REQmsg[1], f'已经标注:{len(d0)}条记录，不能拒绝。']
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/拒绝诊断信息", f'已经标注:{len(d0)}条记录', "不能拒绝", ""]
                return msgtip, ret
            if REQmsg[0] == 'consulting':
                self.diag_mutex.acquire()
                r0, d0 = self.dbUtil.diag_get(check_id=REQmsg[3][0], diag_state='notDiagnosed')
                if r0 == '0':
                    ret = [r0, f'提取会诊记录操作不成功:{d0}']
                    msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/拒绝诊断信息", '数据库操作', "不成功", ""]
                else:
                    if len(d0) > 1:
                        r, d = self.dbUtil.diag_update(REQmsg[3], state='refused')
                    else:
                        r, d = self.dbUtil.diag_refused(REQmsg[3][0], REQmsg[3][1])
                self.diag_mutex.release()
            else:
                r, d = self.dbUtil.diag_refused(REQmsg[3][0], REQmsg[3][1])
            if r == '0':
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/拒绝诊断信息", '数据库操作', "不成功", ""]
            else:
                # r1, d1 = self.dbUtil.get_userPhoneEmailByCheckid(check_id)
                # if r1 == '0':
                #     ret = [r, REQmsg[1], d]
                #     msgtip = [REQmsg[2], f"应答:标注诊断/拒绝诊断信息", '数据库操作', "成功", ""]
                # else:
                #     conte=f"拒绝诊断：{ REQmsg[3][3]}-{REQmsg[3][2]}脑电数据. 谢谢！---{REQmsg[3][4]}"
                #     r2, d2=self.appUtil.sendPhoneMsg(d1[0][2],conte)
                #     r3, d3 = self.appUtil.sendEmail(d1[0][3],conte)
                #     if r2=='1' :
                #        ss='[短信发送操作]'
                #     else:
                #       ss = f'[短信发送操作：{d2}]'
                #     if r3=='1':
                #        ss+="[邮件发送操作]"
                #     else:
                #         ss += f'[邮件发送操作：{d3}]'
                ret = [r, REQmsg[1], f'{ltip[REQmsg[0]]}/拒绝诊断']
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/拒绝诊断信息", f'数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断(会诊/提交诊断信息

    def diag_commit(self, clientAddr, REQmsg):
        # ltip = {'consulting': '脑电会诊', 'manual': '标注诊断'}
        ltip = {'consulting': '脑电诊断', 'manual': '脑电诊断'}
        if REQmsg[1] == 28:
            if REQmsg[0] == 'consulting':
                sql = f"select * from file_info where check_id={REQmsg[3][0][0]} and state='uploaded' and file_id not in" \
                      f" (select file_id from sample_info where check_id={REQmsg[3][0][0]} and uid={REQmsg[3][0][2]})"
                r0, d0 = self.dbUtil.myQueryExt(sql)
                if r0 == '0':
                    ret = [r0, REQmsg[1], f'提取检查单脑电文件信息不成功:{d0}，不能[完成]操作。']
                    msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/完成诊断操作不成功",
                              f'提取检查单脑电文件信息不成功:{d0}', "不能[完成]操作", ""]
                    return msgtip, ret
                if len(d0) > 0:
                    ret = ['0', REQmsg[1], f'未标注脑电文件数:{len(d0)}，不能[完成]操作。']
                    msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/完成诊断操作不成功",
                              f'未标注脑电文件数:{len(d0)}', "不能[完成]操作", ""]
                    return msgtip, ret

                self.diag_mutex.acquire()
                r0, d0 = self.dbUtil.diag_get(check_id=REQmsg[3][0][0], diag_state='notDiagnosed')
                if r0 == '0':
                    ret = [r0, REQmsg[1], f'提取会诊记录操作不成功:{d0}']
                    msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/完成诊断信息", '数据库操作', "不成功", ""]
                else:
                    if len(d0) > 1:
                        r, d = self.dbUtil.diag_update(REQmsg[3][0], state='diagnosed')
                    else:
                        r, d = self.dbUtil.diag_commit(REQmsg[3][0])
                self.diag_mutex.release()
            else:
                r, d = self.dbUtil.diag_commit(REQmsg[3][0])
            if r == '0':
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/完成诊断信息", '数据库操作', "不成功", ""]
            else:
                # r1, d1 = self.dbUtil.get_userPhoneEmailByCheckid(REQmsg[3][0][0])
                # if r1 == '0':
                #     ret = [r, REQmsg[1], d]
                #     msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/诊断完成信息", '数据库操作', "成功", ""]
                # else:
                #     conte = f"完成诊断：{REQmsg[3][2]}-{REQmsg[3][1]}脑电数据. 谢谢！---{REQmsg[3][3]}"
                #     r2, d2 = self.appUtil.sendPhoneMsg(d1[0][2], conte)
                #     r3, d3 = self.appUtil.sendEmail(d1[0][3], conte)
                #     if r2 == '1':
                #         ss = '[短信发送操作]'
                #     else:
                #         ss = f'[短信发送操作：{d2}]'
                #     if r3 == '1':
                #         ss += "[邮件发送操作]"
                #     else:
                #         ss += f'[邮件发送操作：{d3}]'
                ret = [r, REQmsg[1], f'{ltip[REQmsg[0]]}/完成诊断']
                msgtip = [REQmsg[2], f"应答:{ltip[REQmsg[0]]}/完成诊断信息", f'数据库操作', "成功", ""]

        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/修改诊断信息

    def diag_update(self, clientAddr, REQmsg):
        titleinfo = {'manual': '标注诊断', 'manualQuery': '诊断查询', 'consulting': '脑电会诊'}
        if REQmsg[1] == 27:
            r, d = self.dbUtil.diag_update(REQmsg[3])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:ltip[REQmsg[0]]/修改诊断信息", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:ltip[REQmsg[0]]/修改诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/填写诊断信息

    def diag_add(self, clientAddr, REQmsg):
        if REQmsg[1] == 26:
            r, d = self.dbUtil.diag_add(REQmsg[3])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:标注诊断/填写诊断信息", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:标注诊断/填写诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 标注诊断/提取诊断信息
    def diag_get(self, clientAddr, REQmsg):
        titleinfo = {'manual': '标注诊断', 'manualQuery': '诊断查询', 'consulting': '脑电会诊',
                     'diagTraining': '诊断学习'}
        if REQmsg[1] == 25 or REQmsg[0] == 'consulting' and REQmsg[1] == 3:
            r, d = self.dbUtil.diag_get(check_id=REQmsg[3][0], uid=REQmsg[3][1])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:{titleinfo[REQmsg[0]]}/提取诊断信息", '数据库操作', "不成功", ""]
            else:
                ret = [r, REQmsg[1], d]
                msgtip = [REQmsg[2], f"应答:{titleinfo[REQmsg[0]]}/提取诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 诊断标注/提取未诊断信息

    def diags_notDiag_get(self, clientAddr, REQmsg):
        titleinfo = {'manual': '标注诊断', 'manualQuery': '诊断查询', 'consulting': '脑电会诊'}
        if REQmsg[1] == 24:
            if REQmsg[0] == 'manual':
                r, d = self.dbUtil.diag_get(check_id='', uid=REQmsg[3][0], diag_state='notDiagnosed',
                                            other_where="check_info.state='diagnosing'")
            else:
                r, d = self.dbUtil.diag_get_forConsulting(uid=REQmsg[3][0])
            if r == '0':
                ret = [r, d]
                msgtip = [REQmsg[2], f"应答:{titleinfo[REQmsg[0]]}/提取未诊断信息", '数据库操作', "不成功", ""]
            else:
                pids = ""
                uids = ""
                for dInfo in d:
                    if pids == '':
                        pids += str(dInfo[0])
                        uids += str(dInfo[2])
                    else:
                        pids += "," + str(dInfo[0])
                        uids += "," + str(dInfo[2])
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                pr, pd = self.dbUtil.get_patientNameByPids(pids)
                if ur == '0':
                    ud = None
                if pr == '0':
                    pd = None
                ret = [r, REQmsg[1], d, ud, pd]
                msgtip = [REQmsg[2], f"应答:{titleinfo[REQmsg[0]]}/提取未诊断信息", '数据库操作', "成功", ""]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 标注诊断/删除样本状态信息
    def del_sampleInfo_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 23:
            # self.dbUtil.del_sampleInfo(self.patient_id, self.measure_date, self.file_name, start, pick_channel, end,uid, type_id)
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                rn, err = self.dbUtil.del_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid, type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/修改样本状态信息

    def update_sampleInfo_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 22:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                rn, err = self.dbUtil.update_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid, type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/添加样本状态信息

    def add_sampleInfo_state(self, clientAddr, REQmsg):
        if REQmsg[1] == 21:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                rn, err = self.dbUtil.add_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid, type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 标注诊断/删除样本

    def del_sample19(self, clientAddr, REQmsg):
        if REQmsg[1] == 19:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                rn, err = self.dbUtil.del_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid,
                                                     type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/添加样本

    def insert_sample17(self, clientAddr, REQmsg):
        if REQmsg[1] == 17:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                rn, err = self.dbUtil.add_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid, type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}数据库操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

    # 标注诊断/提取样本信息？？？
    def init_SampleList(self, clientAddr, REQmsg):
        if REQmsg[1] == 16:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            channels = REQmsg[3][2]
            type_names = REQmsg[3][3]
            user_names = REQmsg[3][4]
            status_show = REQmsg[3][5]
            try:
                rn, retData = self.dbUtil.get_sampleListInfo(check_id, file_id, channels, type_names, user_names,
                                                             status_show)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', retData]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{retData}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', retData]
            except Exception as e:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", f'数据库操作不成功{e}', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功{e}"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/添加样本

    def update_sampleInfo15(self, clientAddr, REQmsg):
        if REQmsg[1] == 14 or REQmsg[1] == 15:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                if REQmsg[1] == 14:
                    rn, err = self.dbUtil.add_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid,
                                                         type_id)
                else:
                    rn, err = self.dbUtil.update_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid,
                                                            type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", '']
                    ret = ['1', REQmsg[1], f"应答{REQmsg[0]}操作成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
                ret = ['0', REQmsg[1], '数据库操作不成功']
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']

        return msgtip, ret

    # 标注诊断/删除样本
    def del_sample13(self, clientAddr, REQmsg):
        if REQmsg[1] == 13:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                rn, err = self.dbUtil.del_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid, type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", ""]
                    ret = ['1', REQmsg[1], '数据库操作', "成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ""]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/添加样本

    def update_sampleInfo12(self, clientAddr, REQmsg):
        if REQmsg[1] == 11 or REQmsg[1] == 12:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            _start = REQmsg[3][2]
            pick_channel = REQmsg[3][3]
            _end = REQmsg[3][4]
            uid = REQmsg[3][5]
            type_id = REQmsg[3][6]
            try:
                if REQmsg[1] == 11:
                    rn, err = self.dbUtil.add_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid,
                                                         type_id)
                else:
                    rn, err = self.dbUtil.update_sampleInfo(check_id, file_id, _start, pick_channel, _end, uid,
                                                            type_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', err]
                    ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{err}"]
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作', "成功", '']
                    ret = ['1', REQmsg[1], '数据库操作', "成功"]
            except:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}手动标注", '未定义命令', '', '']
        return msgtip, ret

    # 标注诊断/读取脑电文件数据块
    def load_dataDynamical(self, clientAddr, REQmsg, curUser):
        if REQmsg[1] == 9 or REQmsg[1] == 10:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            ret = self.appUtil.openEEGFile(check_id, file_id)

            if ret[0] == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}读数据块", '打开文件Raw为空', ""]
                ret = ['0', REQmsg[1], '打开文件Raw为空']
                return msgtip, ret
            raw = ret[1]
            _index_channels = ret[3]
            REQdata = REQmsg[3][2]
            ret_data = self.appUtil.readEEGfile(raw, _index_channels, REQdata[1], REQdata[2])
            self.appUtil.closeEEGfile(raw)

            if ret_data[0] == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}读数据块", '打开文件Raw为空', ""]
                ret = ['0', REQmsg[1], '打开文件Raw为空']
            else:
                ret = ['1', REQmsg[1], REQdata[0], ret_data[1], ret_data[2]]
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}读数据块", '成功', ""]
        return msgtip, ret



        # 标注诊断/打开脑电文件


        # 标注诊断/检测文件

    def get_fileNameByIdDate(self, clientAddr, REQmsg):
        if REQmsg[1] == 7:
            rn, pre_info = self.dbUtil.get_fileNameByIdDate(REQmsg[3][0])
            if rn == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', pre_info]
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功:{pre_info}"]
            else:
                ret = ['1', pre_info]
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '提取文件', '']
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}提取文件", '未定义命令', '']
        return msgtip, ret

        # 标注诊断/类型、用户信息
    def get_type_info(self, clientAddr, REQmsg):
        if REQmsg[1] == 4:
            type_info = self.dbUtil.get_typeInfo()
            user_manualinfo = self.dbUtil.getUserInfo()
            r, montage = self.appUtil.getMontage()
            if r == '0':
                montage = None
            ret = ['1', type_info, user_manualinfo, montage]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '提取类型信息', '']
        else:
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}提取类型信息", '未定义命令', '']
        return msgtip, ret

    ### dsj ==]===

    # 创建课堂
    def inquiryLessonInfo(self, macAddr, REQmsg):
        try:
            key = REQmsg[3][0]
            value = REQmsg[3][1]
            lesson_info = self.dbUtil.getLessonInfo(where_name=key, where_like=value)
            Info_without_id = []
            Info_withID = []
            for i in lesson_info:
                teacher_info_m = self.dbUtil.getUserInfo(where_name='uid', where_value=i[1])
                id = []
                id.append(i[0])
                lesson_info_m = list(i)[1:]
                temp = lesson_info_m[6]
                lesson_info_m[6] = lesson_info_m[3]
                lesson_info_m[3] = temp
                id.extend(lesson_info_m)
                Info_withID.append(id)
                lesson_info_m[0] = teacher_info_m[0][3]
                Info_without_id.append(lesson_info_m)
            msgtip = [REQmsg[1], f"获取查询课堂信息", '', '']
            ret = ['1', REQmsg[1], lesson_info, Info_without_id, Info_withID]
            return msgtip, ret
        except Exception as e:
            print('inquiryLessonInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getLessonInfo(self, macAddr, REQmsg):
        try:
            student_info = self.dbUtil.getUserInfo(where_name='student', where_value=1)
            # patient_info = self.dbUtil.getPatientInfo()
            lesson_info = self.dbUtil.getLessonInfo()
            Info_without_id = []
            Info_withID = []
            for i in lesson_info:
                teacher_info_m = self.dbUtil.getUserInfo(where_name='uid', where_value=i[1])
                id = []
                id.append(i[0])
                lesson_info_m = list(i)[1:]
                temp = lesson_info_m[6]
                lesson_info_m[6] = lesson_info_m[3]
                lesson_info_m[3] = temp
                id.extend(lesson_info_m)
                Info_withID.append(id)
                lesson_info_m[0] = teacher_info_m[0][3]
                Info_without_id.append(lesson_info_m)
            msgtip = [REQmsg[2], f"获取全部课堂信息", '', '']
            ret = ['1', REQmsg[2], lesson_info, student_info, 1, Info_without_id, Info_withID]
            return msgtip, ret
        except Exception as e:
            print('getLessonInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def searchEegPageInfo(self, clientAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            _curPageIndex = REQmsg[3][2]
            _Pagerows = REQmsg[3][3]
            class_id = REQmsg[3][4]
            info = self.dbUtil.getEegInfobyPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                psize=_Pagerows, where_name=key_word, where_like=key_value)
            ui_size2 = self.dbUtil.getCheckLen(where_name=key_word, where_like=key_value)
            ui_size1 = self.dbUtil.getCheckLen()
            len = ui_size1[0][0] - ui_size2[0][0]
            ptotal = ceil(len / _Pagerows)
            pids = ""
            uids = ""
            for dInfo in info:
                if pids == '':
                    pids += str(dInfo[2])
                    uids += str(dInfo[4])
                else:
                    pids += "," + str(dInfo[2])
                    uids += "," + str(dInfo[4])
            ur, ud = self.dbUtil.get_userNameByUids(uids)
            pr, pd = self.dbUtil.get_patientNameByPids(pids)
            if ur == '0':
                ud = None
            if pr == '0':
                pd = None
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作成功', ]
            ret = ['1', f"应答{REQmsg[2]}", info, ud, pd, _curPageIndex, ptotal, class_id]
            return msgtip, ret
        except Exception as e:
            print('searchEegPageInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret

    def eegPaging(self, clientAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            _Pagerows = REQmsg[3][1]
            class_id = REQmsg[3][3]
            is_search = REQmsg[3][4]
            if is_search:
                key_word = REQmsg[3][5]
                key_value = REQmsg[3][6]
                info = self.dbUtil.getEegInfobyPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                    psize=_Pagerows, where_name=key_word, where_like=key_value)
            else:
                info = self.dbUtil.getEegInfobyPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            pids = ""
            uids = ""
            for dInfo in info:
                if pids == '':
                    pids += str(dInfo[2])
                    uids += str(dInfo[4])
                else:
                    pids += "," + str(dInfo[2])
                    uids += "," + str(dInfo[4])
            ur, ud = self.dbUtil.get_userNameByUids(uids)
            pr, pd = self.dbUtil.get_patientNameByPids(pids)
            if ur == '0':
                ud = None
            if pr == '0':
                pd = None
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作成功', ]
            ret = ['1', f"应答{REQmsg[2]}", info, ud, pd, class_id, _curPageIndex, is_search]
            return msgtip, ret
        except Exception as e:
            print('eegPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret

    def getDiagCheckID(self, clientAddr, REQmsg):
        try:
            class_id = REQmsg[3][0]
            _curPageIndex = REQmsg[3][1]
            _Pagerows = REQmsg[3][2]
            first_time = REQmsg[3][3]
            row = REQmsg[3][4]
            ui_size1 = self.dbUtil.getCheckLen()
            len = ui_size1[0][0]
            ptotal = ceil(len / _Pagerows)
            if ptotal > 0 and _curPageIndex > ptotal:
                _curPageIndex = ptotal
            result = self.dbUtil.getDiagCheckID(where_name='state', where_value='diagnosed',
                                                offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            pids = ""
            uids = ""
            for dInfo in result:
                if pids == '':
                    pids += str(dInfo[2])
                    uids += str(dInfo[4])
                else:
                    pids += "," + str(dInfo[2])
                    uids += "," + str(dInfo[4])
            ur, ud = self.dbUtil.get_userNameByUids(uids)
            pr, pd = self.dbUtil.get_patientNameByPids(pids)
            if ur == '0':
                ud = None
            if pr == '0':
                pd = None
            ret = ['1', REQmsg[1], result, ud, pd, class_id, row, ptotal, first_time]
            print(ret)
            msgtip = [REQmsg[2], f"应答:提取已诊断病例", '数据库操作', "成功", ""]
            return msgtip, ret
        except Exception as e:
            print(e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getFileName(self, clientAddr, REQmsg):
        rn, pre_info = self.dbUtil.getFileName(REQmsg[3][0], REQmsg[3][1])
        if rn == '0':
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', pre_info]
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{pre_info}"]
        else:
            ret = ['1', pre_info, REQmsg[3][2]]
            print(ret)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '提取文件', '']
        return msgtip, ret

    def addLesson(self, clientAddr, REQmsg):
        try:
            lesson_info = REQmsg[3][0]
            rn, class_id = self.dbUtil.addLesson(lesson_info=lesson_info)
            if rn == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', class_id]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{class_id}"]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                ret = ['1', lesson_info, class_id]
                return msgtip, ret
        except Exception as e:
            print('addLesson', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def addStudent(self, clientAddr, REQmsg):
        try:
            student_id = REQmsg[3][0]
            class_id = REQmsg[3][1]
            rn, r = self.dbUtil.addLessonStudent(class_id=class_id, student_id=student_id)
            if rn == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', class_id]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{class_id}"]
                return msgtip, ret
            else:
                _curPageIndex = REQmsg[3][2]
                is_search = REQmsg[3][3]
                _Pagerows = 12
                if is_search:
                    key_word = REQmsg[3][4]
                    key_value = REQmsg[3][5]
                    ui_size1 = self.dbUtil.getStudentLen(where_name=key_word, where_like=key_value)
                    ui_size2 = self.dbUtil.getStudentLen(where_value=class_id)
                    len = ui_size1[0][0] - ui_size2[0][0]
                    ptotal = ceil(len / _Pagerows)
                    if _curPageIndex > ptotal:
                        _curPageIndex = ptotal
                    info = self.dbUtil.getStudentInfobyPage(where_value=class_id,
                                                            offset=(_curPageIndex - 1) * _Pagerows,
                                                            psize=_Pagerows, where_name=key_word,
                                                            where_like=key_value)
                else:
                    ui_size1 = self.dbUtil.getStudentLen()
                    ui_size2 = self.dbUtil.getStudentLen(where_value=class_id)
                    len = ui_size1[0][0] - ui_size2[0][0]
                    ptotal = ceil(len / _Pagerows)
                    if _curPageIndex > ptotal:
                        _curPageIndex = ptotal
                    info = self.dbUtil.getStudentInfobyPage(where_value=class_id,
                                                            offset=(_curPageIndex - 1) * _Pagerows,
                                                            psize=_Pagerows)
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                ret = ['1', f"应答{REQmsg[0]}", info, ptotal, _curPageIndex, is_search]
                return msgtip, ret
        except Exception as e:
            print('addLesson', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def delStudent(self, clientAddr, REQmsg):
        try:
            student_id = REQmsg[3][0]
            class_id = REQmsg[3][1]
            rn, class_id = self.dbUtil.delLessonStudent(where_name=class_id, where_value=student_id, flag=1)
            if rn == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', class_id]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{class_id}"]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                ret = ['1', f"应答{REQmsg[0]}", class_id, student_id]
                return msgtip, ret
        except Exception as e:
            print('delStudent', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getlessonStudent(self, clientAddr, REQmsg):
        try:
            class_id = REQmsg[3][0]
            _curPageIndex = REQmsg[3][1]
            _Pagerows = REQmsg[3][2]
            first_time = REQmsg[3][3]
            ui_size1 = self.dbUtil.getStudentLen()
            ui_size2 = self.dbUtil.getStudentLen(where_value=class_id)
            len = ui_size1[0][0] - ui_size2[0][0]
            ptotal = ceil(len / _Pagerows)
            if _curPageIndex > ptotal:
                _curPageIndex = ptotal
            info = self.dbUtil.getStudentInfobyPage(where_value=class_id, offset=(_curPageIndex - 1) * _Pagerows,
                                                    psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作成功', ]
            ret = ['1', f"应答{REQmsg[2]}", info, class_id, ptotal, _curPageIndex, first_time]
            return msgtip, ret
        except Exception as e:
            print('getlessonStudent', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret

    def studentPaging(self, clientAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            _Pagerows = REQmsg[3][1]
            class_id = REQmsg[3][3]
            is_search = REQmsg[3][4]
            if is_search:
                key_word = REQmsg[3][5]
                key_value = REQmsg[3][6]
                info = self.dbUtil.getStudentInfobyPage(where_value=class_id,
                                                        offset=(_curPageIndex - 1) * _Pagerows,
                                                        psize=_Pagerows, where_name=key_word, where_like=key_value)
            else:
                info = self.dbUtil.getStudentInfobyPage(where_value=class_id,
                                                        offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作成功', ]
            ret = ['1', f"应答{REQmsg[2]}", info, class_id, _curPageIndex, is_search]
            return msgtip, ret
        except Exception as e:
            print('getlessonStudent', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret

    def searchStudentPageInfo(self, clientAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            _curPageIndex = REQmsg[3][2]
            _Pagerows = REQmsg[3][3]
            class_id = REQmsg[3][4]
            info = self.dbUtil.getStudentInfobyPage(where_value=class_id, offset=(_curPageIndex - 1) * _Pagerows,
                                                    psize=_Pagerows, where_name=key_word, where_like=key_value)
            ui_size1 = self.dbUtil.getStudentLen(where_name=key_word, where_like=key_value)
            ui_size2 = self.dbUtil.getStudentLen(where_value=class_id)
            len = ui_size1[0][0] - ui_size2[0][0]
            ptotal = ceil(len / _Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作成功', ]
            ret = ['1', f"应答{REQmsg[2]}", info, class_id, _curPageIndex, ptotal]
            return msgtip, ret
        except Exception as e:
            print('searchStudentPageInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret

    def delLesson(self, clientAddr, REQmsg):
        try:
            del_id = REQmsg[3][0]
            r1, msg1 = self.dbUtil.delLessonStudent(where_name='class_id', where_value=del_id)
            r2, msg2 = self.dbUtil.delLessonContent(where_name='class_id', where_value=del_id)
            if r1 == '0' or r2 == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', del_id]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{del_id}"]
                return msgtip, ret
            else:
                rn, msg = self.dbUtil.delLesson(where_name='class_id', where_value=del_id)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ]
                    ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                    ret = ['1', del_id]
                    return msgtip, ret
        except Exception as e:
            print('delLesson', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def updateLesson(self, clientAddr, REQmsg):
        try:
            lesson_info = REQmsg[3][0]
            user_id = REQmsg[3][1]
            config_id = REQmsg[3][2]
            rn, e = self.dbUtil.updateLesson(lesson_info[0], user_id, config_id, lesson_info)
            if rn == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', e]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{e}"]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功']
                ret = ['1', lesson_info]
                return msgtip, ret
        except Exception as e:
            print('updateLesson', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getStudentInfo(self, macAddr, REQmsg):
        try:
            class_id = REQmsg[3][0]
            row = REQmsg[3][1]
            print(class_id)
            student_info = self.dbUtil.getStudentInfo(where_name='class_id', where_value=class_id)
            msgtip = [REQmsg[1], f"获取课堂学员信息", '', '']
            print(student_info)
            ret = ['1', REQmsg[1], student_info, row]
            return msgtip, ret
        except Exception as e:
            print('getStudentInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def updateStudentInfo(self, macAddr, REQmsg):
        try:
            user_id = REQmsg[3][2]
            class_id = REQmsg[3][1]
            student_id = REQmsg[3][0]
            r1, msg1 = self.dbUtil.delLessonStudent(where_name='class_id', where_value=class_id)
            if r1 == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', class_id]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{class_id}"]
                return msgtip, ret
            else:
                r2, lesson_student = self.dbUtil.addLessonStudent(class_id=class_id, student_id=student_id)
                if r2 == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ]
                    ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                    ret = ['1', student_id]
                    return msgtip, ret
        except Exception as e:
            print('updateStudentInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getContentInfo(self, macAddr, REQmsg):
        try:
            class_id = REQmsg[3][0]
            row = REQmsg[3][1]
            print(class_id)
            content_info = self.dbUtil.getContentInfo(where_name='class_id', where_value=class_id)
            if content_info == []:
                msgtip = [REQmsg[1], f"获取培训内容信息为空", '', '']
                ret = ['1', REQmsg[1], content_info]
                return msgtip, ret
            res = []
            for i in content_info:
                temp = list(i)
                check_id = temp[1]
                uid = temp[3]
                info = self.dbUtil.getCheckID(where_name='check_id', where_value=check_id)
                check_num = info[0][1]
                patient_id = info[0][2]
                temp[1] = check_num
                patient_info = self.dbUtil.getPatientInfo(where_name='patient_id', where_value=patient_id)
                patient_name = patient_info[0][1]
                temp.append(patient_name)
                user_info = self.dbUtil.getUserInfo(where_name='uid', where_value=uid)
                user_name = user_info[0][3]
                temp.append(user_name)
                res.append(temp)
            msgtip = [REQmsg[1], f"获取培训内容信息", '', '']
            ret = ['1', REQmsg[1], content_info, res, row]
            return msgtip, ret
        except Exception as e:
            print('getContentInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def updateContentInfo(self, macAddr, REQmsg):
        try:
            class_id = REQmsg[3][0]
            check_id = REQmsg[3][1]
            user_id = REQmsg[3][2]
            file_id = REQmsg[3][3]
            purpose = self.dbUtil.getContentPurpose(where_name='class_id', where_value=class_id)
            content_purpose = purpose[0][1]
            print(f"purpose:{purpose}")
            r, r1 = self.dbUtil.delLessonContent(where_name='class_id', where_value=class_id)
            if r1 == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', class_id]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{class_id}"]
                return msgtip, ret
            else:
                r2, lesson_content = self.dbUtil.addLessonContent(class_id=class_id, file_id=file_id,
                                                                  user_id=user_id,
                                                                  check_id=check_id, purpose=content_purpose)
                if r2 == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ]
                    ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                    ret = ['1', class_id]
                    return msgtip, ret
        except Exception as e:
            print('updateContentInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def addLessonContent(self, macAddr, REQmsg):
        try:
            class_id = REQmsg[3][0]
            check_id = REQmsg[3][1]
            user_id = REQmsg[3][2]
            file_id = REQmsg[3][3]
            content_purpose = REQmsg[3][4]
            # lesson_content = self.dbUtil.getContentInfo(where_name='class_id', where_value=class_id)
            r2, lesson_content = self.dbUtil.addLessonContent(class_id=class_id, file_id=file_id,
                                                              user_id=user_id,
                                                              check_id=check_id, purpose=content_purpose)
            if r2 == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                ret = ['1', class_id]
                return msgtip, ret
        except Exception as e:
            print('addLessonContent', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def delLessonContent(self, macAddr, REQmsg):
        try:
            del_info = REQmsg[3]
            for i in del_info:
                check_num = i[1]
                check_info = self.dbUtil.getCheckID(where_name='check_number', where_value=check_num)
                i[1] = check_info[0][0]
                uid_name = i[2]
                use_info = self.dbUtil.getUserInfo(where_name='name', where_value=uid_name)
                i[2] = use_info[0][0]
                i[3][0] = int(i[3][0])
            r, r1 = self.dbUtil.delLessonContent(where_value=del_info, flag=1)
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', ]
                ret = ['1', del_info]
                return msgtip, ret
        except Exception as e:
            print('delLessonContent', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getCheckUserID(self, macAddr, REQmsg):
        try:
            check_id = REQmsg[3][0]
            file_id = REQmsg[3][1]
            class_id = REQmsg[3][2]
            res = []
            user_info = self.dbUtil.getCheckUserID(check_id)
            print(f"user_info:{user_info}")
            if user_info == []:
                res.append(['当前文件无标注用户'])
            else:
                uids = ''
                for j in user_info:
                    if uids == '':
                        uids += str(j[1])
                    else:
                        uids += "," + str(j[1])
                ur, ud = self.dbUtil.get_userNameByUids(uids)
                if ur == '0':
                    ud = None
                for k in ud:
                    # temp1 = temp
                    # temp1.extend(list(k))
                    res.append(k)
            print(res)
            msgtip = [REQmsg[1], f"获取诊断标注用户信息", '', '']
            ret = ['1', res, class_id]
            return msgtip, ret
        except Exception as e:
            print('getFileUserID', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getSpecificInfo(self, cmdID, REQmsg):
        print(f'getSpecificInfo REQmsg: {REQmsg}')
        try:
            if len(REQmsg) == 0:
                specificInfo = self.dbUtil.getSpecificInfo()
            else:
                specificInfo = self.dbUtil.getSpecificInfo(REQmsg[0])
            msgtip = [cmdID, f"获取样本统计类型信息", '', '']
            print(specificInfo)
            ret = ['1', cmdID, f"获取样本统计类型信息", specificInfo]
            return msgtip, ret
        except Exception as e:
            print('getSpecificInfo', e)

    def getSpecificNum(self, cmdID, REQmsg):
        print(f'getSpecificNum REQmsg: {REQmsg}')
        try:
            specificNum = self.dbUtil.getSpecificNum(REQmsg[0], REQmsg[1], REQmsg[2])
            msgtip = [cmdID, f"获取选择的样本统计信息", '', '']
            print(specificNum)
            ret = ['1', cmdID, f"获取选择的样本统计信息", specificNum]
            return msgtip, ret
        except Exception as e:
            print('getSpecificNum', e)

    # 获取样本的详细信息
    def getSpecificDetail(self, cmdID, REQmsg):
        print(f'getSpecificDetail REQmsg: {REQmsg}')
        try:
            specificAttr = REQmsg[0]
            result = {}
            for key, attr in specificAttr.items():
                filter_info = self.dbUtil.getFilterItemByTypeInfo(*attr)

                if len(filter_info) == 0:
                    msgtip = [cmdID, f"数据库无相关数据，请添加", '', '']
                    ret = ['0', cmdID, f"数据库无相关数据，请添加"]
                    return msgtip, ret

                print(f'key: {key}, attr: {filter_info}')
                result[key] = filter_info
            print(f'result: {result}')
            msgtip = [cmdID, f"获取选择的样本详细信息", '', '']
            ret = ['1', cmdID, f"获取选择的样本详细信息", result]
            return msgtip, ret
        except Exception as e:
            print('getSpecificDetail', e)

    def getSpecNumFromFlt(self, cmdID, REQmsg):
        print(f'getSpecNumFromFltRes REQmsg: {REQmsg}')
        try:
            result = self.dbUtil.getSampleNumWithFlts(*REQmsg)
            msgtip = [cmdID, f"根据过滤器信息获取样本信息", '', '']
            ret = ['1', cmdID, f"根据过滤器信息获取样本信息", result]
            return msgtip, ret
        except Exception as e:
            print('getSpecNumFromFltRes', e)

    # 构建集合
    def getSetInitData(self, cmdID, REQmsg):
        print(f'getSetBuildTypeInfo REQmsg: {REQmsg}')
        try:
            typeInfo = self.dbUtil.getSpecificInfo(REQmsg[0])
            stateInfo = self.dbUtil.getSpecificInfo(REQmsg[1])
            setInfo = self.dbUtil.getSetBuildInfo(after='set_info')
            setAllInfo = [len(setInfo), setInfo[:int(REQmsg[4][1])]]
            modelInfo = self.dbUtil.getSetBuildInfo(selColumn=REQmsg[2][0], after=REQmsg[2][1])
            # montage = ['default'] + [item['name'] for item in self.appUtil.getMontage()[1]]
            montage = self.appUtil.getMontage()[1]
            sampleRate = self.dbUtil.queryConfigData('config_id', REQmsg[3])
            negativeScheme = self.dbUtil.getNegativeScheme(column='classifier_name')
            themeInfo = self.dbUtil.getSetBuildInfo(after='theme')
            msgtip = [cmdID, f"获取波形类型和状态类型", '', '']
            ret = ['1', cmdID, f"获取波形类型和状态类型",
                   [typeInfo, stateInfo, setAllInfo, modelInfo, montage, sampleRate, negativeScheme, themeInfo]]
            return msgtip, ret
        except Exception as e:
            print('getSetBuildTypeInfo', e)
            msgtip = [cmdID, f"获取波形类型和状态类型失败", '', '']
            ret = ['0', cmdID, f"获取波形类型和状态类型失败, e: {e}"]
            return msgtip, ret

    def getSetBuildFltData(self, cmdID, REQmsg):
        print(f'getSetBuildFltData REQmsg: {REQmsg}')
        try:
            theme_ids = [item[0] for item in REQmsg[4]]
            result = self.dbUtil.getFilterItemByTypeInfo2(REQmsg[0], REQmsg[1], REQmsg[2], REQmsg[3], theme_ids)
            if len(result) == 0:
                msgtip = [cmdID, f"构建集合获取选择的样本详细信息失败", '', '']
                ret = ['0', cmdID, f"构建集合获取选择的样本详细信息失败", '数据库没有所选择类型的数据']
                return msgtip, ret

            print(f'result: {result}')
            msgtip = [cmdID, f"构建集合获取选择的样本详细信息", '', '']
            ret = ['1', cmdID, f"构建集合获取选择的样本详细信息", result]
            return msgtip, ret
        except Exception as e:
            print('getSetBuildFltData', e)
            msgtip = [cmdID, f"构建集合获取选择的样本详细信息失败", '', '']
            ret = ['0', cmdID, f"构建集合获取选择的样本详细信息失败, e: {e}"]
            return msgtip, ret

    # 获取集合的一些基本信息，为接下来导出做准备
    def getSetExportInitData(self, cmdID, REQmsg):
        print(f'getSetExportInitData REQmsg: {REQmsg}')
        try:
            setInfo = self.dbUtil.getSetExportInitData(where_name='set_id', where_value=REQmsg[1])
            print(f'set_id: {setInfo}')
            if len(setInfo) == 0:
                msgtip = [cmdID, f"数据集信息有误，无法下载", '', '']
                ret = ['0', cmdID, f"数据集信息有误，无法下载", ['wrongSetname']]
            else:
                blockSize = 1024 * 1024  # 1M

                if REQmsg[2] == 'training':
                    filePath = 'data/train_set/' + setInfo[0][4] + '.npz'
                else:
                    filePath = 'data/test_set/' + setInfo[0][5] + '.npz'
                print(f'filePath: {filePath}')

                fileSize = path.getsize(filePath)
                # 计算块数，使用math.ceil进行上取整
                blockN = ceil(fileSize / blockSize)
                print(f'blockN: {blockN}')

                result = ['rightSetname', filePath, blockN]
                msgtip = [cmdID, f"获取数据导出基本信息", '', '']
                ret = ['1', cmdID, f"获取数据导出基本信息", result]
            return msgtip, ret
        except Exception as e:
            print('getSetExportInitData', e)
            msgtip = [cmdID, f"获取数据导出基本信息失败", '', '']
            ret = ['0', cmdID, f"获取数据导出基本信息失败, e: {e}"]
            return msgtip, ret

    # 根据block id导出数据
    def getSetExportData(self, cmdID, userID, REQmsg):
        print(f'getSetExportData REQmsg: {REQmsg}')
        try:
            print(self.curUser.users[userID])
            # TODO 使用线程目前遇到的问题，
            #  1: 如果使用线程的话，那么肯定不能直接使用self，否则有其他人也导出数据的时候会出问题，只能挂在每个用户下 (找不到地方挂)
            # if self.curUser.users[userID][15]:
            #     thread = setExportThread(appUtil=self.appUtil)
            #     thread.start()

            blockSize = 1024 * 1024  # 1M
            data = self.appUtil.readByte(file_path=REQmsg[1], block_size=blockSize,
                                         block_id=int(REQmsg[2].split('=')[1]))
            result = [f'{REQmsg[2]}', data]
            msgtip = [cmdID, f"返回{REQmsg[2]}数据", '', '']
            ret = ['1', cmdID, f"返回{REQmsg[2]}数据", result]
            print(f'data.type: {type(result[1])}')
            return msgtip, ret
        except Exception as e:
            print('getSetExportData', e)
            msgtip = [cmdID, f"返回{REQmsg[2]}数据失败", '', '']
            ret = ['1', cmdID, f"返回{REQmsg[2]}数据失败, e: {e}"]
            return msgtip, ret

    # 获取集合信息
    def getSet(self, cmdID, REQmsg):
        print(f'getSet REQmsg: {REQmsg}')
        try:
            start = (int(REQmsg[0]) - 1) * int(REQmsg[1])
            print(f'start: {start}')
            setInfo = self.dbUtil.getSetBuildInfo(after=f'set_info')
            msgtip = [cmdID, f"获取集合信息", '', '']
            ret = ['1', cmdID, f"获取集合信息", [len(setInfo), setInfo[start:start + REQmsg[1]]]]
            return msgtip, ret
        except Exception as e:
            print('getSet', e)
            msgtip = [cmdID, f"获取集合信息失败", '', '']
            ret = ['0', cmdID, f"获取集合信息失败, e: {e}", ['删除失败']]
            return msgtip, ret

    # 删除集合信息
    def delSet(self, cmdID, REQmsg):
        print(f'delSet REQmsg: {REQmsg}')
        try:
            classifier_info = self.dbUtil.getSetBuildInfo('set_id', f'classifier where set_id = {REQmsg[0]}')
            if len(classifier_info) != 0:
                msgtip = [cmdID, f"删除setId={REQmsg[0]}集合信息失败, 存在与之相关联的分类器", '', '']
                ret = ['0', cmdID, f"删除setId={REQmsg[0]}集合信息失败, 存在与之相关联的分类器",
                       ['删除失败, 存在与之相关联的分类器']]
                return msgtip, ret

            if self.dbUtil.delSet(REQmsg[0]):
                msgtip = [cmdID, f"删除setId={REQmsg[0]}集合信息成功", '', '']
                ret = ['1', cmdID, f"删除setId={REQmsg[0]}集合信息成功", ['删除成功', REQmsg[0]]]
                # 删除本地文件
                trainFilePath = 'data/train_set/' + REQmsg[3] + '.npz'
                testFilePath = 'data/test_set/' + REQmsg[4] + '.npz'
                print(f'trainFilePath: {trainFilePath}, testFilePath: {testFilePath}')
                if path.exists(trainFilePath):
                    # 删除文件训练文件
                    remove(trainFilePath)
                if path.exists(testFilePath):
                    # 删除文件训练文件
                    remove(testFilePath)
            else:
                msgtip = [cmdID, f"删除setId={REQmsg[0]}集合信息失败", '', '']
                ret = ['0', cmdID, f"删除setId={REQmsg[0]}集合信息失败", ['删除失败']]
            return msgtip, ret
        except Exception as e:
            print('delSet', e)
            msgtip = [cmdID, f"删除setId={REQmsg[0]}集合信息失败", '', '']
            ret = ['0', cmdID, f"删除setId={REQmsg[0]}集合信息失败, e: {e}", ['删除失败']]
            return msgtip, ret

    # 构建集合
    def buildSet(self, cmdID, REQmsg):
        print(f'buildSet REQmsg: {REQmsg}')
        try:
            if hasattr(self, 'setBuildService') and self.setBuildService is not None:
                msgtip = [cmdID, f"当前有其他用户正在构建数据集，请稍等", '', '']
                ret = ['0', cmdID, f"当前有其他用户正在构建数据集，请稍等", ["当前有其他用户正在构建数据集，请稍等"]]
                return msgtip, ret

            # 判断集合名称是否重复
            setInfo = self.dbUtil.getSetBuildInfo(selColumn="set_name", after='set_info')
            print(f'setInfo: {setInfo}')
            setInfo = [info[0] for info in setInfo]
            if REQmsg[0] in setInfo:
                msgtip = [cmdID, f"当前数据集名重复，请重新命名", '', '']
                ret = ['0', cmdID, f"当前数据集名重复，请重新命名", ["当前数据集名重复，请重新命名"]]
                return msgtip, ret

            data = json.loads(REQmsg[1])

            if REQmsg[3] == 'wave':
                self.setBuildService = \
                    randomWave(self.dbUtil, self.appUtil, REQmsg[0], REQmsg[1], REQmsg[2])
            else:
                if data['scheme'] == 'State Neg Model 1':
                    print(f'scheme: State Neg Model 1')
                    # self.setBuildService = \
                    #     EEGDeepState(self.dbUtil, self.appUtil, REQmsg[0], REQmsg[1], REQmsg[2])
                else:
                    print(f'scheme: Random')
                    self.setBuildService = \
                        randomState(self.dbUtil, self.appUtil, REQmsg[0], REQmsg[1], REQmsg[2])

            msgtip = [cmdID, f"开始构建数据集", '', '']
            ret = ['1', cmdID, f"开始构建数据集", ['start', 0]]
            return msgtip, ret

        except Exception as e:
            print('buildSet', e)
            msgtip = [cmdID, f"构建数据集失败", '', '']
            ret = ['0', cmdID, f"构建数据集失败, e: {e}", ["构建失败"]]
            return msgtip, ret

    # 获取构建集合的进度
    def buildSetGetPg(self, cmdID, REQmsg):
        try:
            print(f'buildSetGetPg: {REQmsg}')
            if self.setBuildService != None:
                msgtip = [cmdID, f"构建数据集ing", '', '']
                if self.setBuildService.isStop:
                    ret = ['0', cmdID, f"构建失败，原因为：{self.setBuildService.errorReason}",
                           [self.setBuildService.errorReason]]
                else:
                    progress = self.setBuildService.getProgress()
                    ret = ['1', cmdID, f"构建数据集ing", ['building', progress]]
                    if progress == 100:
                        self.setBuildService = None
                return msgtip, ret
            else:
                print(f'线程为None')
        except Exception as e:
            print('buildSetGetPg', e)
            msgtip = [cmdID, f"构建数据集失败", '', '']
            ret = ['0', cmdID, f"构建数据集失败, e: {e}"]
            return msgtip, ret

    # 取消构建数据集
    def buildSetCancel(self, cmdID, REQmsg):
        try:
            print(f'buildSetCancel: {REQmsg}')
            if self.setBuildService != None:
                # TODO 在这边取消构建数据集
                self.setBuildService.isStop = True
                self.setBuildService = None
                msgtip = [cmdID, f"构建数据集ing", '', '']
                ret = ['1', cmdID, f"构建数据集ing", [True, f"取消构建数据集成功"]]
                return msgtip, ret
            else:
                print(f'线程为None')
        except Exception as e:
            print('buildSetCancel', e)
            msgtip = [cmdID, f"取消构建数据集失败", '', '']
            ret = ['0', cmdID, f"取消数据集失败, e: {e}", [False, f"取消构建数据集失败"]]
            return msgtip, ret

    # 获取数据集搜索的结果
    def getSetSearch(self, cmdID, REQmsg):
        print(f'getSetSearch REQmsg: {REQmsg}')
        try:
            start = (int(REQmsg[0]) - 1) * int(REQmsg[1])
            print(f'start: {start}')
            setInfo = self.dbUtil.getSetBuildInfo(after=f"set_info where set_name like '%{REQmsg[3]}%'")
            msgtip = [cmdID, f"获取集合信息", '', '']
            ret = ['1', cmdID, f"获取集合信息", [len(setInfo), setInfo[start:start + REQmsg[1]]]]
            return msgtip, ret
        except Exception as e:
            print('getSetSearch', e)
            msgtip = [cmdID, f"获取集合信息失败", '', '']
            ret = ['0', cmdID, f"获取集合信息失败, e: {e}", ['获取搜索数据集失败']]
            return msgtip, ret

    # 获取数据集搜索的结果
    def getSetDescribe(self, cmdID, REQmsg):
        print(f'getSetDescribe REQmsg: {REQmsg}')
        try:
            trainInfoPath = f'data/train_set/{REQmsg[3]}.npz'
            testInfoPath = f'data/test_set/{REQmsg[4]}.npz'
            msgtip = [cmdID, f"获取数据集详细信息", '', '']
            ret = ['1', cmdID, f"获取数据集详细信息", [self.appUtil.getSetLabelInfo(trainInfoPath),
                                                       self.appUtil.getSetLabelInfo(testInfoPath)]]
            return msgtip, ret
        except Exception as e:
            print('getSetSearch', e)
            msgtip = [cmdID, f"获取集合信息失败", '', '']
            ret = ['0', cmdID, f"获取集合信息失败, e: {e}", ['获取搜索数据集失败']]
            return msgtip, ret

        # 算法管理

    def getAlgorithmInfo(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 12
            reset = REQmsg[3][2]
            ui_size = self.dbUtil.getAlgorithmInfoLen()
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal and ptotal > 0:
                _curPageIndex = ptotal
            result = self.dbUtil.getAlgorithmInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, ptotal, reset]
            return msgtip, ret
        except Exception as e:
            print('getPatientInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def addAlgorithmInfo(self, macAddr, REQmsg):
        try:
            alg_info = REQmsg[3][0]
            r, r1 = self.dbUtil.addAlgorithmInfo(alg_info=alg_info)
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
                return msgtip, ret
            else:
                alg_id = r1
                training_filename = 'training.{:>08}'.format(alg_id)
                test_filename = 'test.{:>08}'.format(alg_id)
                predict_filename = 'predict.{:>08}'.format(alg_id)
                alg_info_d = [training_filename, 'ready', test_filename, 'ready', predict_filename, 'ready']
                print(alg_info_d)
                r2, r3 = self.dbUtil.updateAlgorithmInfo(alg_info=alg_info_d, alg_id=alg_id)
                if r2 == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', ]
                    ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
                    return msgtip, ret
                else:
                    _Pagerows = 12
                    ui_size = self.dbUtil.getAlgorithmInfoLen()
                    ptotal = ceil(ui_size[0][0] / _Pagerows)
                    result = self.dbUtil.getAlgorithmInfoByPage(offset=(ptotal - 1) * _Pagerows, psize=_Pagerows)
                    msgtip = [REQmsg[1], f"添加算法信息成功", '', '']
                    # print(msgtip)
                    ret = ['1', REQmsg[1], result, ptotal]
                    return msgtip, ret
        except Exception as e:
            print('addAlgorithmInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def delAlgorithmInfo(self, macAddr, REQmsg):
        try:
            del_id = REQmsg[3][0]
            is_search = REQmsg[3][2]
            r, r1 = self.dbUtil.delAlgorithmInfo(where_name='alg_id', where_value=del_id)
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', del_id]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{del_id}"]
                return msgtip, ret
            else:
                training_filename = 'training.{:>08}.py'.format(del_id)
                test_filename = 'test.{:>08}.py'.format(del_id)
                predict_filename = 'predict.{:>08}.py'.format(del_id)
                rn, r2 = self.appUtil.delAlgorithmFile(training_filename, test_filename, predict_filename)
                if rn == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '删除文件操作不成功', del_id]
                    ret = ['0', f"应答{REQmsg[0]}删除文件操作不成功:{del_id}"]
                    return msgtip, ret
                else:
                    _curPageIndex = REQmsg[3][1]
                    if _curPageIndex <= 0:
                        _curPageIndex = 1
                    _Pagerows = 12
                    if is_search:
                        key_word = REQmsg[3][3]
                        key_value = REQmsg[3][4]
                        if key_word == 'type' and key_value == '波形':
                            key_value = 'waveform'
                        if key_word == 'type' and key_value == '状态':
                            key_value = 'state'
                        ui_size = self.dbUtil.getAlgorithmInfoLen(where_name=key_word, where_like=key_value)
                        ptotal = ceil(ui_size[0][0] / _Pagerows)
                        if ptotal == 0:
                            result = []
                        elif _curPageIndex > ptotal and ptotal > 0:
                            _curPageIndex = ptotal
                            result = self.dbUtil.getSearchAlgorithmInfoByPage(where_name=key_word, where_value=key_value,
                                                                              offset=(_curPageIndex - 1) * _Pagerows,
                                                                              psize=_Pagerows)
                        else:
                            result = self.dbUtil.getSearchAlgorithmInfoByPage(where_name=key_word,
                                                                              where_value=key_value,
                                                                              offset=(_curPageIndex - 1) * _Pagerows,
                                                                              psize=_Pagerows)
                    else:
                        ui_size = self.dbUtil.getAlgorithmInfoLen()
                        ptotal = ceil(ui_size[0][0] / _Pagerows)
                        if ptotal == 0:
                            result = []
                        elif _curPageIndex > ptotal and ptotal > 0:
                            _curPageIndex = ptotal
                            result = self.dbUtil.getAlgorithmInfoByPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                                        psize=_Pagerows)
                        else:
                            result = self.dbUtil.getAlgorithmInfoByPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                                        psize=_Pagerows)
                    msgtip = [REQmsg[1], f"删除算法信息成功", '', '']
                    ret = ['1', REQmsg[1], result, ptotal, _curPageIndex]
                    return msgtip, ret
        except Exception as e:
            print('delAlgorithmInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def algorithmInfoPaging(self, macAddr, REQmsg):
        try:
            isSearch = REQmsg[3][3]
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 12
            if isSearch:
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                if key_word == 'type' and key_value == '波形':
                    key_value = 'waveform'
                if key_word == 'type' and key_value == '状态':
                    key_value = 'state'
                result = self.dbUtil.getSearchAlgorithmInfoByPage(where_name=key_word, where_value=key_value,
                                                                  offset=(_curPageIndex - 1) * _Pagerows,
                                                                  psize=_Pagerows)
            else:
                result = self.dbUtil.getAlgorithmInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, isSearch]
            return msgtip, ret
        except Exception as e:
            print('algorithmInfoPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def inquiryAlgorithmInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            if key_word == 'type' and key_value == '波形':
                key_value = 'waveform'
            if key_word == 'type' and key_value == '状态':
                key_value = 'state'
            _curPageIndex = REQmsg[3][2]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][3]
            if _Pagerows <= 0:
                _Pagerows = 12
            result = self.dbUtil.getSearchAlgorithmInfoByPage(where_name=key_word, where_value=key_value,
                                                              offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            ui_size = self.dbUtil.getAlgorithmInfoLen(where_name=key_word, where_like=key_value)
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            ret = ['1', REQmsg[1], result, ptotal]
            msgtip = [REQmsg[1], f"应答{REQmsg[2]}获取查询算法信息", '数据库操作成功', '']
            return msgtip, ret
        except Exception as e:
            print('inquiryAlgorithmInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def addAlgorithmFile(self, macAddr, REQmsg):
        try:
            state = REQmsg[3][0]
            alg_id = REQmsg[3][1]
            file_state = REQmsg[3][2]
            mac = REQmsg[3][3]
            # 实现算法文件上传协议5.1部分
            if state == 'start':
                alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)
                # 判断数据库是否有这条记录
                if alg_info:
                    if file_state == 'training':
                        d_state = alg_info[0][4]
                        flag = 1
                    elif file_state == 'test':
                        d_state = alg_info[0][9]
                        flag = 2
                    elif file_state == 'predict':
                        d_state = alg_info[0][14]
                        flag = 3
                    if d_state != 'ready':
                        msgtip = [REQmsg[2], f"数据库算法文件状态错误", '', '']
                        ret = ['1', REQmsg[2], f"数据库算法文件状态错误", ['wrongSite', alg_id, file_state]]
                        return msgtip, ret
                    else:
                        self.dbUtil.updateAlgorithmInfo(alg_info=['notUploaded', 0], alg_id=alg_id, state=state,
                                                        mac=mac, flag=flag)
                        msgtip = [REQmsg[2], f"发送上传算法文件请求，并更新数据库算法信息成功", '', '']
                        ret = ['1', REQmsg[2], f"发送上传算法文件请求，并更新数据库算法信息成功",
                               ['waiting', alg_id, file_state, 1]]
                        return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"数据库无文件记录", '', '']
                    ret = ['1', REQmsg[2], f"数据库无文件记录", ['unknownError']]
                    return msgtip, ret
            # 实现算法文件上传协议5.2部分
            elif state == 'uploading':
                data = REQmsg[3][4]
                alg_info = []
                if file_state == 'training':
                    alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id,
                                                            where_state='training_state', state=state)
                elif file_state == 'test':
                    alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id,
                                                            where_state='test_state', state=state)
                elif file_state == 'predict':
                    alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id,
                                                            where_state='predict_state', state=state)
                # 判断数据库是否有这条记录
                if alg_info:
                    if file_state == 'training':
                        d_mac = alg_info[0][6]
                        d_block_id = alg_info[0][5]
                        file_name = alg_info[0][2]
                        flag = 1
                    elif file_state == 'test':
                        d_mac = alg_info[0][11]
                        d_block_id = alg_info[0][10]
                        file_name = alg_info[0][7]
                        flag = 2
                    elif file_state == 'predict':
                        d_mac = alg_info[0][16]
                        d_block_id = alg_info[0][15]
                        file_name = alg_info[0][12]
                        flag = 3
                    if d_mac != mac:
                        msgtip = [REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", '', '']
                        ret = ['0', REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", ['wrongSite']]
                        return msgtip, ret
                    else:
                        block_id = REQmsg[3][5]
                        path = os.path.join(self.appUtil.root_path, 'classifier', 'algorithms\\')
                        file_name = file_name + '.py'
                        file_path = os.path.join(path, file_name)
                        if d_block_id + 1 == block_id and block_id == 1:
                            self.makeFileName1(file_path)
                            self.appUtil.writeByte(file_path, data)
                            self.dbUtil.updateAlgorithmInfo(alg_info=['uploading', block_id], alg_id=alg_id, flag=flag)
                            msgtip = [REQmsg[2], f"传输算法文件数据块成功，并更新数据库算法信息成功", '', '']
                            ret = ['1', REQmsg[2], f"传输算法文件数据块成功，并更新数据库算法信息成功",
                                   ['waiting', alg_id, file_state, block_id + 1]]
                            return msgtip, ret
                        elif d_block_id + 1 == block_id:
                            self.appUtil.writeByte(file_path, data)
                            self.dbUtil.updateAlgorithmInfo(alg_info=['uploading', block_id], alg_id=alg_id, flag=flag)
                            msgtip = [REQmsg[2], f"传输算法文件数据块成功，并更新数据库算法信息成功", '', '']
                            ret = ['1', REQmsg[2], f"传输算法文件数据块成功，并更新数据库算法信息成功",
                                   ['waiting', alg_id, file_state, block_id + 1]]
                            return msgtip, ret
                        else:
                            msgtip = [REQmsg[2], f"传输算法文件数据块块号与数据库块号不符", '', '']
                            ret = ['0', REQmsg[2], f"传输算法文件数据块块号与数据库块号不符",
                                   ['waiting', alg_id, file_state, d_block_id + 1]]
                            return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"数据库无文件记录", '', '']
                    ret = ['1', REQmsg[2], f"数据库无文件记录", ['wrongServer']]
                    return msgtip, ret
            # 实现算法文件上传协议5.3部分
            elif state == 'uploaded':
                alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)
                # 判断数据库是否有这条记录
                if alg_info:
                    if file_state == 'training':
                        d_mac = alg_info[0][6]
                        d_block_id = alg_info[0][5]
                        flag = 1
                    elif file_state == 'test':
                        d_mac = alg_info[0][11]
                        d_block_id = alg_info[0][10]
                        flag = 2
                    elif file_state == 'predict':
                        d_mac = alg_info[0][16]
                        d_block_id = alg_info[0][15]
                        flag = 3
                    if d_mac != mac:
                        msgtip = [REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", '', '']
                        ret = ['1', REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", ['wrongSite']]
                        return msgtip, ret
                    else:
                        self.dbUtil.updateAlgorithmInfo(alg_info=['uploaded'], alg_id=alg_id, flag=flag, state=state)
                        msgtip = [REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功", '', '']
                        ret = ['1', REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功",
                               ['uploaded', alg_id, file_state, d_block_id + 1]]
                        return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"数据库算法文件状态错误", '', '']
                    ret = ['1', REQmsg[2], f"数据库算法文件状态错误", ['unknownError']]
                    return msgtip, ret
            # 实现算法文件上传协议5.4部分
            elif state == 'clean':
                alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)
                # 判断数据库是否有这条记录
                if alg_info:
                    if file_state == 'training':
                        d_mac = alg_info[0][6]
                        file_name = alg_info[0][2]
                        d_state = alg_info[0][4]
                        flag = 1
                    elif file_state == 'test':
                        d_mac = alg_info[0][11]
                        file_name = alg_info[0][7]
                        d_state = alg_info[0][9]
                        flag = 2
                    elif file_state == 'predict':
                        d_mac = alg_info[0][16]
                        file_name = alg_info[0][12]
                        d_state = alg_info[0][14]
                        flag = 3
                    if d_mac != mac:
                        msgtip = [REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", '', '']
                        ret = ['1', REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", ['wrongSite']]
                        return msgtip, ret
                    else:
                        if d_state == 'ready':
                            msgtip = [REQmsg[2], f"数据库无文件上传记录", '', '']
                            ret = ['1', REQmsg[2], f"数据库无文件上传记录", ['unknownError']]
                            return msgtip, ret
                        elif d_state == 'notUploaded' or d_state == 'uploading':
                            msgtip = [REQmsg[2], f"数据库无文件上传记录", '', '']
                            ret = ['1', REQmsg[2], f"数据库无文件上传记录",
                                   ['recover', alg_id, file_state, file_name, d_mac]]
                            return msgtip, ret
                        elif d_state == 'uploaded':
                            msgtip = [REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功", '', '']
                            ret = ['1', REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功",
                                   ['uploaded', alg_id, file_state, d_mac]]
                            return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"数据库算法文件状态错误", '', '']
                    ret = ['1', REQmsg[2], f"数据库算法文件状态错误", ['wrongServer']]
                    return msgtip, ret
            # 实现算法文件上传协议协议5.5
            elif state == 'continue':
                alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)
                # 判断数据库是否有这条记录
                if alg_info:
                    if file_state == 'training':
                        d_mac = alg_info[0][6]
                        d_block_id = alg_info[0][5]
                        d_state = alg_info[0][4]
                        flag = 1
                    elif file_state == 'test':
                        d_mac = alg_info[0][11]
                        d_block_id = alg_info[0][10]
                        d_state = alg_info[0][9]
                        flag = 2
                    elif file_state == 'predict':
                        d_mac = alg_info[0][16]
                        d_block_id = alg_info[0][15]
                        d_state = alg_info[0][14]
                        flag = 3
                    if d_mac != mac:
                        msgtip = [REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", '', '']
                        ret = ['1', REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", ['wrongSite']]
                        return msgtip, ret
                    else:
                        if d_state == 'ready':
                            msgtip = [REQmsg[2], f"数据库无文件上传记录", '', '']
                            ret = ['1', REQmsg[2], f"数据库无文件上传记录", ['unknownError']]
                            return msgtip, ret
                        elif d_state == 'notUploaded' or d_state == 'uploading':
                            msgtip = [REQmsg[2], f"数据库无文件上传记录", '', '']
                            ret = ['1', REQmsg[2], f"数据库无文件上传记录",
                                   ['waiting', alg_id, file_state, d_block_id + 1]]
                            return msgtip, ret
                        elif d_state == 'uploaded':
                            msgtip = [REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功", '', '']
                            ret = ['1', REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功",
                                   ['uploaded', alg_id, file_state, d_mac]]
                            return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"数据库算法文件状态错误", '', '']
                    ret = ['1', REQmsg[2], f"数据库算法文件状态错误", ['unknownError']]
                    return msgtip, ret
            # 实现算法文件上传协议协议5.6
            elif state == 'unknown':
                alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)
                # 判断数据库是否有这条记录
                if alg_info:
                    if file_state == 'training':
                        d_mac = alg_info[0][6]
                        file_name = alg_info[0][2]
                        d_state = alg_info[0][4]
                        flag = 1
                    elif file_state == 'test':
                        d_mac = alg_info[0][11]
                        file_name = alg_info[0][7]
                        d_state = alg_info[0][9]
                        flag = 2
                    elif file_state == 'predict':
                        d_mac = alg_info[0][16]
                        file_name = alg_info[0][12]
                        d_state = alg_info[0][14]
                        flag = 3
                    if d_mac != mac:
                        msgtip = [REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", '', '']
                        ret = ['1', REQmsg[2], f"上传文件客户端mac地址与数据库mac地址不符", ['wrongSite']]
                        return msgtip, ret
                    else:
                        if d_state == 'ready':
                            msgtip = [REQmsg[2], f"数据库无文件上传记录", '', '']
                            ret = ['1', REQmsg[2], f"数据库无文件上传记录", ['unknownError']]
                            return msgtip, ret
                        elif d_state == 'notUploaded' or d_state == 'uploading':
                            msgtip = [REQmsg[2], f"数据库无文件上传记录", '', '']
                            ret = ['1', REQmsg[2], f"数据库无文件上传记录",
                                   ['recover', alg_id, file_state, file_name, d_mac]]
                            return msgtip, ret
                        elif d_state == 'uploaded':
                            msgtip = [REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功", '', '']
                            ret = ['1', REQmsg[2], f"传输算法文件完成，并更新数据库算法信息成功", ['uploaded']]
                            return msgtip, ret
                else:
                    msgtip = [REQmsg[2], f"数据库算法文件状态错误", '', '']
                    ret = ['1', REQmsg[2], f"数据库算法文件状态错误", ['unknownError']]
                    return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"算法文件请求状态无法处理", '', '']
                ret = ['1', REQmsg[1], f"算法文件请求状态无法处理"]
                return msgtip, ret
        except Exception as e:
            print('addAlgorithmFile', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def makeFileName1(self, file_path):
        with open(file_path, 'w') as file:
            pass

    def getAlgorithmFileName(self, macAddr, REQmsg):
        try:
            alg_id = REQmsg[3][0]
            state = REQmsg[3][1]
            if len(REQmsg[3]) == 2:
                if state == 'training':
                    self.dbUtil.recoverAlgorithmInfo(alg_id=alg_id, state='training')
                    file_name = 'training.{:>08}.py'.format(alg_id)
                    self.appUtil.recoverAlgorithmFile(file_name)
                elif state == 'test':
                    self.dbUtil.recoverAlgorithmInfo(alg_id=alg_id, state='test')
                    file_name = 'test.{:>08}.py'.format(alg_id)
                    self.appUtil.recoverAlgorithmFile(file_name)
                elif state == 'predict':
                    self.dbUtil.recoverAlgorithmInfo(alg_id=alg_id, state='predict')
                    file_name = 'predict.{:>08}.py'.format(alg_id)
                    self.appUtil.recoverAlgorithmFile(file_name)
            if state == 'training':
                algorithm_info = self.dbUtil.getAlgorithmFileName(alg_id=alg_id, training_state='ready')
            elif state == 'test':
                algorithm_info = self.dbUtil.getAlgorithmFileName(alg_id=alg_id, test_state='ready')
            elif state == 'predict':
                algorithm_info = self.dbUtil.getAlgorithmFileName(alg_id=alg_id, predict_state='ready')
            if algorithm_info == []:
                msgtip = [REQmsg[1], f"不存在该算法记录", '', '']
                ret = ['0', REQmsg[1]]
                return msgtip, ret
            else:
                file_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)
                if state == 'training':
                    file_name = file_info[0][2]
                elif state == 'test':
                    file_name = file_info[0][7]
                elif state == 'predict':
                    file_name = file_info[0][12]
                msgtip = [REQmsg[1], f"获取文件名成功", '', '']
                ret = ['1', REQmsg[1], alg_id, state, file_name]
            return msgtip, ret
        except Exception as e:
            print('getAlgorithmFileName', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    # 模型训练

    def getModelInfo(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 8
            alg_reset = REQmsg[3][4]
            set_reset = REQmsg[3][5]
            ui_size = self.dbUtil.getAlgorithmInfoLen()
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal and ptotal > 0:
                _curPageIndex = ptotal
            result = self.dbUtil.getAlgorithmInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            if alg_reset == True:
                msgtip = [REQmsg[1], f"刷新算法页面信息", '', '']
                ret = ['1', REQmsg[1], result, ptotal, ' ', ' ', ' ', ' ', True, False]
                return msgtip, ret
            _curPageIndex_1 = REQmsg[3][2]
            if _curPageIndex_1 <= 0:
                _curPageIndex_1 = 1
            _Pagerows_1 = REQmsg[3][3]
            if _Pagerows_1 <= 0:
                _Pagerows_1 = 10
            ui_size_1 = self.dbUtil.getsetLen()
            ptotal_1 = ceil(ui_size_1[0][0] / _Pagerows_1)
            if _curPageIndex_1 > ptotal_1 and ptotal_1 > 0:
                _curPageIndex_1 = ptotal_1
            result_1 = self.dbUtil.get_set_info_by_page(offset=(_curPageIndex_1 - 1) * _Pagerows_1, psize=_Pagerows_1)
            if set_reset == True:
                msgtip = [REQmsg[1], f"刷新算法页面信息", '', '']
                ret = ['1', REQmsg[1], result_1, ptotal_1, ' ', ' ', ' ', ' ', False, True]
                return msgtip, ret
            type_info = self.dbUtil.get_typeInfo()
            set_file_type = self.appUtil.get_set_file_type()
            msgtip = [REQmsg[1], f"获取模型训练界面信息", '', '']
            ret = ['1', REQmsg[1], result, ptotal, result_1, ptotal_1, type_info, set_file_type, False, False]
            return msgtip, ret
        except Exception as e:
            print('getModelInfo ', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def get_classifierInfo_by_setId_and_algId(self, macAddr, REQmsg):
        try:
            info = REQmsg[3]
            classiferInfo = self.dbUtil.getclassifierInfo_1(where_name=info, flag=1)
            msgtip = [REQmsg[1], f"获取对应算法和数据集的模型信息", '', '']
            # print(msgtip)
            ret = ['1', REQmsg[1], classiferInfo]
            return msgtip, ret
        except Exception as e:
            print('get_classifierInfo_by_setId_and_algId ', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def modelAlgInfoPaging(self, macAddr, REQmsg):
        try:
            isSearch = REQmsg[3][3]
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 8
            if isSearch:
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                if key_word == 'type' and key_value == '波形':
                    key_value = 'waveform'
                if key_word == 'type' and key_value == '状态':
                    key_value = 'state'
                result = self.dbUtil.getSearchAlgorithmInfoByPage(where_name=key_word, where_value=key_value,
                                                                  offset=(_curPageIndex - 1) * _Pagerows,
                                                                  psize=_Pagerows)
            else:
                result = self.dbUtil.getAlgorithmInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, isSearch]
            return msgtip, ret
        except Exception as e:
            print('modelAlgInfoPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def modelInquiryAlgInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            if key_word == 'type' and key_value == '波形':
                key_value = 'waveform'
            if key_word == 'type' and key_value == '状态':
                key_value = 'state'
            _curPageIndex = REQmsg[3][2]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][3]
            if _Pagerows <= 0:
                _Pagerows = 8
            result = self.dbUtil.getSearchAlgorithmInfoByPage(where_name=key_word, where_value=key_value,
                                                              offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            ui_size = self.dbUtil.getAlgorithmInfoLen(where_name=key_word, where_like=key_value)
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            ret = ['1', REQmsg[1], result, ptotal]
            msgtip = [REQmsg[1], f"应答{REQmsg[2]}获取查询算法信息", '数据库操作成功', '']
            return msgtip, ret
        except Exception as e:
            print('modelInquiryAlgInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def modelSetInfoPaging(self, macAddr, REQmsg):
        try:
            isSearch = REQmsg[3][3]
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 10
            if isSearch:
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                result = self.dbUtil.getSearchSetInfoByPage(where_name=key_word, where_value=key_value,
                                                            offset=(_curPageIndex - 1) * _Pagerows,
                                                            psize=_Pagerows)
            else:
                result = self.dbUtil.get_set_info_by_page(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, isSearch]
            return msgtip, ret
        except Exception as e:
            print('modelSetInfoPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def modelInquirySetInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            _curPageIndex = REQmsg[3][2]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][3]
            if _Pagerows <= 0:
                _Pagerows = 10
            result = self.dbUtil.getSearchSetInfoByPage(where_name=key_word, where_value=key_value,
                                                        offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            ui_size = self.dbUtil.getsetLen(where_name=key_word, where_value=key_value)
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            ret = ['1', REQmsg[1], result, ptotal]
            msgtip = [REQmsg[1], f"应答{REQmsg[2]}获取查询数据集信息", '数据库操作成功', '']
            return msgtip, ret
        except Exception as e:
            print('modelInquirySetInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def if_algobject_exist(self):
        if hasattr(self, 'train') or hasattr(self, 'predict'):
            return False
        else:
            return True

    def matchAlgSet(self, macAddr, REQmsg):
        try:
            flag = self.if_algobject_exist()
            if not flag:
                msgtip = [REQmsg[1], f"当前服务器存在正在执行的训练、测试或扫描任务", '', '']
                ret = ['0', f"当前服务器存在正在执行的训练、测试或扫描任务"]
                return msgtip, ret
            else:
                alg_id = REQmsg[3][0]
                set_id = REQmsg[3][1]
                config_id = REQmsg[3][2]
                alg_name = REQmsg[3][3]
                self.train = trainAlg(dbUtil=self.dbUtil, alg_id=alg_id, set_id=set_id
                                      , alg_name=alg_name, config_id=config_id)
                result = self.train.match()
                if result:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '匹配操作成功', "", '']
                    ret = ['1', f"应答{REQmsg[0]}匹配操作成功", alg_id, set_id]
                    return msgtip, ret
                else:
                    del self.train
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '匹配操作不成功', "", '']
                    ret = ['0', f"应答{REQmsg[0]}匹配操作不成功", alg_id, set_id]
                    return msgtip, ret
        except Exception as e:
            print('matchAlgSet', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '匹配操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}匹配操作不成功"]
            return msgtip, ret

    def getTrainPerformance(self, macAddr, REQmsg):
        try:
            path = os.path.join(self.appUtil.root_path, 'classifier', 'result', 'train_acc.pkl')
            f = open(path, 'rb')
            performance = pickle.load(f)
            msgtip = [REQmsg[1], f"获取训练性能成功", '', '']
            ret = ['1', REQmsg[1], performance]
            return msgtip, ret
        except Exception as e:
            print('getTrainPerformance', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def runProcessForTrain(self, macAddr, REQmsg):
        try:
            result = self.train.run()
            if result == True:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程成功', "", '']
                ret = ['1', REQmsg[1], f"应答{REQmsg[0]}开启进程成功"]
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程失败', "", '']
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}开启进程失败"]
            return msgtip, ret
        except Exception as e:
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}开启进程不成功"]
            print('runProcessForTrain', e)
            return msgtip, ret

    def train_cancel(self, macAddr, REQmsg):
        try:
            if hasattr(self, 'train'):
                del self.train
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '撤销训练算法对象成功', "", '']
            ret = ['1', REQmsg[1], f"应答{REQmsg[0]}撤销训练算法对象成功"]
            return msgtip, ret
        except Exception as e:
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '撤销训练算法对象失败', "", '']
            ret = ['0', f"应答{REQmsg[0]}撤销训练算法对象失败"]
            print('train_cancel', e)
            return msgtip, ret

    def getProgress(self, macAddr, REQmsg):
        try:
            msgtip = [REQmsg[2], f"读取进度信息", '', '']
            if REQmsg[0] == 'modelTrain' and REQmsg[1] == 10:
                result, progress = self.train.getProgress()
                if result == False:
                    ret = ['1', REQmsg[2], result, progress, self.train.classifierName, self.train.result]
                    del self.train
                else:
                    ret = ['1', REQmsg[2], result, progress, self.train.epoch]
                return msgtip, ret
            elif REQmsg[0] == 'auto' and REQmsg[1] == 9:
                result, progress = self.predict.getProgress()
                if result == False:
                    ret = ['1', REQmsg[2], result, progress, self.predict.classifierName, self.predict.result]
                    del self.predict
                else:
                    ret = ['1', REQmsg[2], result, progress, self.predict.scan_num, self.predict.total_scan_num]
                return msgtip, ret
            elif REQmsg[0] == 'modelTest' and REQmsg[1] == 3:
                result, progress = self.test.getProgress()
                if result == False:
                    ret = ['1', REQmsg[2], result, progress, self.test.classifierName, self.test.result]
                    del self.test
                else:
                    ret = ['1', REQmsg[2], result, progress, self.test.scan_num, self.test.total_scan_num]
                return msgtip, ret
        except Exception as e:
            print('getProgress', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '读取进度不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}读取进度不成功"]
            return msgtip, ret

    # 模型测试

    def isTesting(self, macAddr, REQmsg):
        if hasattr(self, 'test'):
            msgtip = [REQmsg[1], f"运行进程训练模型", '', '']
            ret = ['0', REQmsg[1], f"服务器正在训练其他模型,请稍后"]
            return msgtip, ret
        else:
            self.test = testAlg(self.dbUtil, REQmsg[3][0])
            return self.runProcessForTest(macAddr, REQmsg)

    def runProcessForTest(self, macAddr, REQmsg):
        try:
            result = self.test.run()
            if result == True:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程成功', "", '']
                ret = ['1', REQmsg[1], f"应答{REQmsg[0]}开启进程成功"]
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程失败', "", '']
                ret = ['0', REQmsg[1], f"应答{REQmsg[0]}开启进程失败"]
            return msgtip, ret
        except Exception as e:
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '进程开启不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}进程开启不成功"]
            print('runProcessForTest', e)
            return msgtip, ret

    # def call_test_method(self, macAddr, REQmsg):
    #     acquired = self.testing_mutex.acquire(False)
    #     if acquired:
    #         # 如果成功获取到锁，则调用 locked_method
    #         msgtip, ret = self.runProcessForTest(macAddr, REQmsg)
    #         return msgtip, ret
    #     else:
    #         msgtip = [REQmsg[1], f"运行进程训练模型", '', '']
    #         ret = ['0', REQmsg[1], f"服务器正在训练其他模型,请稍后"]
    #         return msgtip, ret
    #
    # # 模型测试
    # def runProcessForTest(self, macAddr, REQmsg):
    #     try:
    #         try:
    #             path = os.path.join(self.appUtil.root_path, 'server_root', 'classifier', 'algorithms\\')
    #             cur_file_path = os.path.join(self.appUtil.root_path, 'server_root', 'classifier', 'models\\')
    #             classifier_id = REQmsg[3][0]
    #             Fisrt_Train_flag = REQmsg[3][1]
    #             print(classifier_id)
    #             classifier_info = self.dbUtil.getClassifierById(classifier_id)
    #             algorithm_info = self.dbUtil.getAlgorithmById(classifier_info[2])
    #             test_algorithm_filename = algorithm_info[7]
    #             set_file_type = self.appUtil.get_set_file_type()
    #             cur_filename = classifier_info[1]
    #             config_id = classifier_info[11]
    #             config_info = self.dbUtil.queryConfigData(where_name='config_id', where_value=config_id)
    #             sample_rate = config_info[0][2]
    #             set_info = self.dbUtil.get_set_info(where_name='set_id', where_value=classifier_info[3])
    #             tmp = set_info[0][3].split('+')[0].split(' ')
    #             # 样本中每种波形的长度，如果长度多余2种，设置样本不同长标记为真
    #             sample_len = set()
    #             for i in tmp:
    #                 # 转换成秒，乘上采样率
    #                 sl = int(i.split('-')[1]) / 1000 * sample_rate
    #                 sample_len.add(int(sl))
    #             sample_len = list(sample_len)[0]
    #             cur_model_path = os.path.join(cur_file_path, cur_filename)
    #             events_dic_path = os.path.join(self.appUtil.root_path, 'server_root', 'classifier',
    #                                            'algorithms',
    #                                            'events_dic.pkl')
    #             train_set_file = os.path.join(self.appUtil.root_path, 'server_root', 'data', 'train_set',
    #                                           set_info[0][4] + set_file_type)
    #             test_set_file = os.path.join(self.appUtil.root_path, 'server_root', 'data', 'test_set',
    #                                          set_info[0][5] + set_file_type)
    #             parameter = [1, config_id, set_info[0][4], set_info[0][5], True, classifier_info[3],
    #                          set_info[0][3], self.get_set_channel_info(set_info[0][3]), config_id,
    #                          set_file_type,
    #                          cur_filename, 'Test', classifier_info[2], Fisrt_Train_flag]
    #             test_parameter = {'mode': 1, 'sample_len': sample_len,
    #                               'trainset_file_path': train_set_file,
    #                               'testset_file_path': test_set_file,
    #                               'model_path_without_file_storage_format': cur_model_path,
    #                               'model_path_with_file_storage_format': cur_model_path + '.npz',
    #                               'state_predict': True,
    #                               'set_id': classifier_info[3],
    #                               'set_description': set_info[0][3],
    #                               'set_channel_info': self.get_set_channel_info(set_info[0][3]),
    #                               'sample_rate': sample_rate}
    #             parameter_path = os.path.join(path, 'buffer.pkl')
    #             f = open(parameter_path, 'wb')
    #             pickle.dump(test_parameter, f)
    #             f.close()
    #             self.save_events_dic(events_dic_path)
    #             self.p = QProcess()
    #             self.Train_loop = QEventLoop()
    #             self.Train_result = ProcessResult()
    #             self.Train_result.msgtip = [REQmsg[1], f"开启模型测试进程", '', '']
    #             self.Train_result.ret = ['1', '算法运行成功']
    #             self.p.readyReadStandardOutput.connect(self.handle_stdout)
    #             self.p.readyReadStandardError.connect(self.handle_stderr)
    #             self.p.stateChanged.connect(self.handle_state)
    #             self.p.finished.connect(partial(self.process_finished, parameter, sample_rate))
    #             self.p.start("python", [path + test_algorithm_filename + '.py'])
    #             print('runProcessForTest:测试开始')
    #             self.Train_loop.exec_()
    #             return self.Train_result.msgtip, self.Train_result.ret
    #         finally:
    #             self.testing_mutex.release()
    #     except Exception as e:
    #         msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程不成功', "", '']
    #         ret = ['0', REQmsg[1], f"应答{REQmsg[0]}开启进程不成功"]
    #         print('runProcessForTest', e)
    #         return msgtip, ret

    # def test_performance_set(self, list):
    #     try:
    #         test_performance_path = os.path.join(self.appUtil.root_path, 'server_root', 'classifier', 'algorithms',
    #                                              'test_performance.pkl')
    #         f = open(test_performance_path, 'rb')
    #         test_performance = pickle.load(f)
    #         f.close()
    #         os.remove(test_performance_path)
    #         cls_info = self.dbUtil.getclassifierInfo(where_name=list, flag=1)
    #         classifier_id = cls_info[0][0]
    #         tmp = ''
    #         for tp in test_performance:
    #             tmp = tmp + tp
    #         test_performance = tmp
    #         self.dbUtil.updateClassifierInfo('test_performance', test_performance, 'classifier_id', classifier_id)
    #     except Exception as e:
    #         print('test_performance_set', e)

    def check_algorithm_running_result(self):
        try:
            path = os.path.join(self.appUtil.root_path, 'classifier/algorithms', 'result.pkl')
            f = open(path, 'rb')
            self.result = pickle.load(f)
            f.close()
            os.remove(path)
        except:
            self.result = {'if_finished': False}

    def if_algorithm_process_finished_successfully(self):
        # True/False
        return self.result['if_finished']

        # 训练性能存储

    def train_performance_set(self, list):
        try:
            train_performance_path = os.path.join(self.appUtil.root_path, 'classifier', 'algorithms',
                                                  'train_performance.pkl')
            f = open(train_performance_path, 'rb')
            train_performance = pickle.load(f)
            f.close()
            os.remove(train_performance_path)
            cls_info = self.dbUtil.getclassifierInfo(where_name=list, flag=1)
            classifier_id = cls_info[0][0]
            tmp = ''
            for tp in train_performance:
                tmp = tmp + tp
            train_performance = tmp
            self.dbUtil.updateClassifierInfo('train_performance', train_performance, 'classifier_id', classifier_id)
        except Exception as e:
            print('train_performance_set', e)

    def get_setOfclassifier_samples_length(self, sampling_rate, set_info):
        try:
            tmp = set_info[3].split('+')[0].split(' ')
            tmp1 = set_info[3].split('+')[5].split('-')[0]
            # 样本中每种波形的长度，如果长度多余2种，设置样本不同长标记为真
            sample_len = set()
            for i in tmp:
                # 转换成秒，乘上采样率
                sl = int(i.split('-')[1]) / 1000 * sampling_rate
                sample_len.add(int(sl))
            return list(sample_len)
        except Exception as e:
            print('get_setOfclassifier_samples_length', e)


    def myTip(self, cmdId, tipMsg):
        row = self.tabV_model.rowCount()
        if row > 9:
            self.tabV_model.removeRow(0)
            row = 9

        now = datetime.datetime.now()
        item = QStandardItem(now.strftime("%Y-%m-%d %H:%M:%S"))
        self.tabV_model.setItem(row, 0, item)
        uInfo = self.curUser.users.get(tipMsg[0])
        if uInfo is None:
            item = QStandardItem(str(tipMsg[0]))
        else:
            item = QStandardItem(uInfo[1])
        self.tabV_model.setItem(row, 1, item)
        item = QStandardItem(tipMsg[1])
        self.tabV_model.setItem(row, 2, item)
        item = QStandardItem(tipMsg[2])
        self.tabV_model.setItem(row, 3, item)
        if len(tipMsg) > 3:
            item = QStandardItem(tipMsg[3])
            self.tabV_model.setItem(row, 4, item)
        else:
            tipMsg.append("")
        #self.dbUtil.sys_log(cmdId, tipMsg)

    def get_set_channel_info(self, set_description):
        return set_description.split('+')[3]

    # 模型测试
    def getClassifierInfo(self, REQmsg):
        try:
            pageSize = REQmsg[3][0]
            page = REQmsg[3][1]
            classifier_name = REQmsg[3][2]
            count = self.dbUtil.getClassifierCount(classifier_name)
            classifierInfo = self.dbUtil.getClassifierInfo(pageSize, page, classifier_name)
            msgtip = [REQmsg[1], f"获取分类器信息成功", f'{REQmsg[2]}', '']
            ret = ['1', REQmsg[1], [count, classifierInfo]]
            return msgtip, ret
        except Exception as e:
            print('getClassifierInfo', e)
   # 模型管理
    def getClassifierAlgSetNameRes(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _pagerows = REQmsg[3][1]
            if _pagerows <= 0:
                _pagerows = 12
            classiferInfo = self.dbUtil.get_classifier_alg_set_name()
            ui_size = len(classiferInfo)
            ptotal = ceil(ui_size / _pagerows)  # 总页数
            if ptotal!=0:
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                result = self.dbUtil.getClsInfoByPage(offset=(_curPageIndex - 1) * _pagerows, psize=_pagerows)
                msgtip = [REQmsg[1], f"获取系统存在的模型信息", '', '']
                # print(msgtip)
                ret = ['1', REQmsg[1], result, ptotal]
                return msgtip, ret
            else:
                result=0
                msgtip = [REQmsg[1], f"无模型信息", '', '']
                # print(msgtip)
                ret = ['0', REQmsg[1], result, ptotal]
                return msgtip, ret
        except Exception as e:
            print('getClassifierAlgSetNameRes', e)
    def inquiryClassifierInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            key_state =REQmsg[3][4]
            classifier_info = self.dbUtil.get_classifier_alg_set_name(where_name=key_word, where_value=key_value,
                                                                      state_value=key_state,fuzzy_search=True)
            totalPage = ceil(len(classifier_info) / REQmsg[3][3])
            start = (REQmsg[3][2] - 1) * REQmsg[3][3]
            classifier_info = classifier_info[start:start + REQmsg[3][3]]
            msgtip = [REQmsg[0], f"获取查询模型信息", '', '']
            # print(msgtip)
            ret = ['1', REQmsg[0], [totalPage, classifier_info]]
            return msgtip, ret
        except Exception as e:
            print('inquiryAlgorithmInfo', e)
            msgtip = [REQmsg[0], f"获取查询模型信息", '', '']
            ret = ['0', REQmsg[0], e]
            return msgtip, ret
    def delClassifierInfo(self, macAddr, REQmsg):
        try:
            cls_info = REQmsg[3][0]
            _curPageIndex=REQmsg[3][2]
            classifier_info = self.dbUtil.getclassifierInfo(where_name='classifier_name', where_value=cls_info[0])
            cls_state=classifier_info[0][5]
            r, r1 = self.dbUtil.delClassifierInfo(where_name='classifier_name', where_value=classifier_info[0][1])
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', classifier_info[0]]
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{classifier_info[0]}"]
                return msgtip, ret
            else:
                if cls_state != 'ready':
                    row = REQmsg[3][1]
                    modal_path = os.path.join(self.appUtil.root_path, 'classifier', 'models')
                    file_path = os.path.join(modal_path, classifier_info[0][4])
                    try:
                        os.remove(file_path)
                        msgtip = [REQmsg[0], f"删除模型文件成功", '', '']
                        _Pagerows = 12
                        ui_size = self.dbUtil.get_classifier_alg_set_name(count=True)
                        ptotal = ceil(ui_size[0][0] / _Pagerows)
                        if ptotal!=0:
                            if _curPageIndex > ptotal:
                                _curPageIndex = ptotal
                            result = self.dbUtil.getClsInfoByPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                                        psize=_Pagerows)
                            ret = ['1', REQmsg[0], row,result,ptotal,_curPageIndex]
                            return msgtip, ret
                        else:
                            result = 0
                            msgtip = [REQmsg[0], f"无模型信息", '', '']
                            ret = ['2', REQmsg[0], result, ptotal]
                            return msgtip, ret
                    except Exception as e:
                        msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '删除文件操作不成功']
                        ret = ['0', f"应答{REQmsg[0]}删除文件操作不成功:{e}",e.args]
                        return msgtip, ret
                else:
                    msgtip = [REQmsg[0], f"仅删除数据库信息成功", '', '']
                    _Pagerows=12
                    ui_size=self.dbUtil.get_classifier_alg_set_name(count=True)
                    ptotal=ceil(ui_size[0][0]/_Pagerows)
                    if ptotal!=0:
                        if _curPageIndex>ptotal:
                            _curPageIndex=ptotal
                        result =self.dbUtil.getClsInfoByPage(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
                        ret = ['1',REQmsg[0],0,result,ptotal,_curPageIndex]
                        return msgtip, ret
                    else:
                        result = 0
                        msgtip = [REQmsg[0], f"无模型信息", '', '']
                        ret = ['2', REQmsg[0], result, ptotal]
                        return msgtip, ret
        except Exception as e:
            print('delClassifierInfo', e)
            msgtip = [REQmsg[0], f"删除模型信息失败", '', '']
            ret = ['0', REQmsg[0], e]
            return msgtip, ret

    def cls_getAlgorithmInfo(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _pagerows = REQmsg[3][1]
            if _pagerows <= 0:
                _pagerows = 12
            algorithm_info = self.dbUtil.getAlgorithmInfo(where_name='type', where_value=REQmsg[3][2])
            ui_size = len(algorithm_info)
            ptotal = ceil(ui_size / _pagerows)  # 总页数
            if ptotal != 0:
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                result = self.dbUtil.getalgorithmInfoByPage(where_name='type', where_value=REQmsg[3][2],
                                                            offset=(_curPageIndex - 1) * _pagerows, psize=_pagerows)
                msgtip = [REQmsg[1], f"获取全部算法信息", '', '']
                # print(msgtip)
                ret = ['1', REQmsg[1], result, ptotal]
                return msgtip, ret
            else:
                result = 0
                msgtip = [REQmsg[0], f"无算法信息", '', '']
                ret = ['2', REQmsg[0], result, ptotal]
                return msgtip, ret
        except Exception as e:
            print('getAlgorithmInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret
    def checkClassifierInfo(self, macAddr, REQmsg):
        try:
            cls_info = REQmsg[3][1]
            classifier_info = self.dbUtil.getclassifierInfo(where_name='classifier_name', where_value=cls_info)
            msgtip = [REQmsg[1], f"获取系统存在的模型信息", '', '']
            ret = ['1', REQmsg[1], classifier_info]
            return msgtip, ret
        except Exception as re:
            print('DataBaseUtil.checkClassifierInfo:', re)
    def cls_restate(self, macAddr, REQmsg):
        try:
            cls_id=REQmsg[3][0]
            modal_path = os.path.join(self.appUtil.root_path, 'classifier', 'models')
            filename=self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=cls_id)
            file_path = os.path.join(modal_path, filename[0][4])
            os.remove(file_path)
            self.dbUtil.update_trans_ClassifierInfo(set_name='state', set_value='ready',
                                                    where_name='classifier_id', where_value=cls_id)
            self.dbUtil.update_trans_ClassifierInfo(set_name='filename', set_value='',
                                                    where_name='classifier_id', where_value=cls_id)
            self.dbUtil.update_trans_ClassifierInfo(set_name='block_id', set_value=0,
                                                    where_name='classifier_id', where_value=cls_id)
            msgtip = [REQmsg[1], f"协议7.1重置状态", '', '']
            ret = ['1', REQmsg[1], REQmsg[3]]
            return msgtip, ret
        except Exception as e:
            print('cls_restate', e)
    def checkstate(self, macAddr, REQmsg):  # REQData[3]='classifier_name,alg_id,filename, epoch_length'
        try:
            cls_info = REQmsg[3][0]
            classifier_info = self.dbUtil.getClsRecord(where_name='classifier_name', where_value=cls_info,
                                                                        where_state='state', state='ready')
            msgtip = [REQmsg[1], f"查询模型记录和状态", '', '']
            ret = ['1', REQmsg[1], classifier_info]
            return msgtip, ret
        except Exception as e:
            print('checkstate', e)
    def model_transmit_message(self, macAddr, REQmsg):
        try:
            if REQmsg[3][0] == 'start':  # 5.1
                cls_info = REQmsg[3][1]  # start, classifier_id, filename, block_id,本机mac地址
                classifier_info = self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=cls_info)
                if classifier_info:  # 存在记录
                    if self.dbUtil.getclassifierInfo(where_name='state', where_value='ready'):  # 存在且state=ready
                        self.dbUtil.update_trans_ClassifierInfo(set_name='state', set_value='notUploaded',
                                                                where_name='classifier_id', where_value=cls_info)
                        self.dbUtil.update_trans_ClassifierInfo(set_name='block_id', set_value=0,
                                                                where_name='classifier_id', where_value=cls_info)
                        self.dbUtil.update_trans_ClassifierInfo(set_name='mac', set_value=REQmsg[3][4],
                                                                where_name='classifier_id', where_value=cls_info)
                        msgtip = [REQmsg[1], f"更新state,block_idm,mac", '', '']
                        ret = ['1', REQmsg[1], ['waiting', 1, REQmsg[3]]]  # 向客户端发送“waiting，block_id=1”
                        return msgtip, ret
                    else:
                        msgtip = [REQmsg[1], f"错误！记录存在但state不为ready", '', '']
                        ret = ['1', REQmsg[1], ['wrongSite']]
                        return msgtip, ret
                else:
                    msgtip = [REQmsg[1], f"错误！记录不存在unknownError1", '', '']
                    ret = ['1', REQmsg[1], ['unknownError']]
                    return msgtip, ret
            elif REQmsg[3][0] == 'uploading':  # 5.2
                cls_info = REQmsg[3][1]  # “uploading，classifier_id,filename，block_id，数据块,mac”
                cls_id_judge = self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=cls_info)
                if cls_id_judge and (cls_id_judge[0][5]!='ready') and (cls_id_judge[0][5]!='built'):  # 满足d10.classifier_id=classifier_id且d10.state!=”ready”且d10.state!=”built”的记录
                    if cls_id_judge[0][7]==REQmsg[3][5]:
                        if cls_id_judge[0][6]==(REQmsg[3][3] - 1):
                            if REQmsg[3][3] == 1:

                                if os.path.exists(self.model_path + REQmsg[3][2]):
                                    os.remove(self.model_path + REQmsg[3][2])
                                try:
                                    with open(self.model_path + REQmsg[3][2], 'wb+') as file:
                                        file.write(REQmsg[3][4])
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='block_id', set_value=REQmsg[3][3],
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='state', set_value='uploading',
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    n = REQmsg[3][3] + 1
                                    temporary2 = REQmsg[3][:4] + REQmsg[3][5:]
                                    msgtip = [REQmsg[1], f"成功接收数据块{REQmsg[3][3]},接下来接收{n}", '', '']
                                    ret = ['1', REQmsg[1], ['waiting', n, temporary2]]
                                    return msgtip, ret  # todo:传输数据块
                                except IOError:
                                    print("打开文件失败")
                                    os.remove(REQmsg[3][2])
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='state', set_value='ready',
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='mac', set_value='DEFAULT',
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    msgtip = [REQmsg[1], f"错误！打开文件失败 wrongServer", '', '']
                                    ret = ['1', REQmsg[1], ['wrongServer']]
                                    return msgtip, ret
                            else:  # REQmsg[3][3]＞1
                                try:
                                    with open(self.model_path + REQmsg[3][2], 'rb+') as file:
                                        last_write_position = (REQmsg[3][3] - 1) * 5 * 1024*1024
                                        file.seek(last_write_position)
                                        file.write(REQmsg[3][4])
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='block_id', set_value=REQmsg[3][3],
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='state', set_value='uploading',
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    n = REQmsg[3][3] + 1
                                    temporary2 = REQmsg[3][:4] + REQmsg[3][5:]
                                    msgtip = [REQmsg[1], f"成功接收数据块{REQmsg[3][3]},接下来接收{n}", '', '']
                                    ret = ['1', REQmsg[1], ['waiting', n, temporary2]]
                                    return msgtip, ret
                                except IOError:
                                    print("打开文件失败")
                                    os.remove(REQmsg[3][2])
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='state', set_value='ready',
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    self.dbUtil.update_trans_ClassifierInfo(set_name='mac', set_value='DEFAULT',
                                                                            where_name='classifier_id',
                                                                            where_value=cls_info)
                                    msgtip = [REQmsg[1], f"错误！打开文件失败 wrongServer", '', '']
                                    ret = ['1', REQmsg[1], ['wrongServer']]
                                    return msgtip, ret
                        else:
                            n = cls_id_judge[0][6] + 1
                            REQmsg.insert(-1, n)
                            msgtip = [REQmsg[1], f"block_id!=d10.block_id+1", '', '']
                            ret = ['1', REQmsg[1],
                                   ['waiting', n, REQmsg[3]]]  # state,classifier_id, filename, block_id,本机mac地址
                            return msgtip, ret
                    else:
                        msgtip = [REQmsg[1], f"错误！mac地址不符", '', '']
                        ret = ['1', REQmsg[1], ['wrongSite']]
                        return msgtip, ret
                else:
                    msgtip = [REQmsg[1], f"错误！记录不存在 wrongServer", '', '']
                    ret = ['1', REQmsg[1], ['wrongServer']]
                    return msgtip, ret
            elif REQmsg[3][0] == 'uploaded':  # 5.3
                cls_info = REQmsg[3][1]  # “uploaded,classifier_id,filename,block_id和本机mac地址”
                if self.dbUtil.getClsRecord(where_name='classifier_id', where_value=cls_info,
                                            where_state='mac', state=REQmsg[3][4]):  # 判断mac=d10.mac
                    self.dbUtil.update_trans_ClassifierInfo(set_name='state', set_value='uploaded',
                                                            where_name='classifier_id', where_value=cls_info)
                    msgtip = [REQmsg[1], f" uploaded1", '', '']
                    ret = ['1', REQmsg[1], ['uploaded']]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[1], f"错误！mac地址不符", '', '']
                    ret = ['1', REQmsg[1], ['wrongSite']]
                    return msgtip, ret
            elif REQmsg[3][0] == 'clean' or REQmsg[3][0] == 'unknown':  # 5.4 or #5.6
                cls_info = REQmsg[3][1]  # clean:“clean,classifier_id,filename，block_id,mac”  unknwn:“unknown,classifier_id,filename，mac”
                cls_id_judge = self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=cls_info)
                if cls_id_judge:
                    if cls_id_judge[0][7]==REQmsg[3][3]:# 存在且mac=d10.mac
                        if cls_id_judge[0][5]=='ready':
                            msgtip = [REQmsg[1], f"错误！状态有误", '', '']
                            ret = ['1', REQmsg[1], ['unknownError']]
                            return msgtip, ret
                        elif cls_id_judge[0][5]=='notUploaded' or cls_id_judge[0][5]=='uploading':
                            msgtip = [REQmsg[1], f" RECOVER", '', '']
                            ret = ['1', REQmsg[1], ['recover', REQmsg[3][1], REQmsg[3][2], '', REQmsg[3][3]]]  # ''为冗余补充
                            return msgtip, ret
                        elif cls_id_judge[0][5]=='uploaded':
                            msgtip = [REQmsg[1], f" uploaded2", '', '']
                            ret = ['1', REQmsg[1], ['uploaded']]
                            return msgtip, ret
                    else:
                        msgtip = [REQmsg[1], f"错误！mac地址不符", '', '']
                        ret = ['1', REQmsg[1], ['wrongSite']]
                        return msgtip, ret
                else:
                    msgtip = [REQmsg[1], f"错误！记录不存在unknownError2", '', '']
                    ret = ['1', REQmsg[1], ['unknownError']]
                    return msgtip, ret
            elif REQmsg[3][0] == 'continue':  # 5.5
                cls_info = REQmsg[3][1]  # “continue,classifier_id,filename,mac”
                cls_id_judge = self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=cls_info)
                if cls_id_judge:
                    if cls_id_judge[0][7]==REQmsg[3][3]:# 存在且mac=d10.mac
                        if cls_id_judge[0][5]=='ready':
                            msgtip = [REQmsg[1], f"错误！状态有误", '', '']
                            ret = ['1', REQmsg[1], ['unknownError']]
                            return msgtip, ret
                        elif cls_id_judge[0][5]=='notUploaded' or cls_id_judge[0][5]=='uploading':
                            cls_tempt = self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=cls_info)
                            n = cls_tempt[0][6] + 1
                            REQmsg[3].insert(-1, n)
                            msgtip = [REQmsg[1], f" waiting #5.5", '', '']
                            ret = ['1', REQmsg[1], ['waiting', n, REQmsg[3]]]
                            return msgtip, ret
                        elif cls_id_judge[0][5]=='uploaded':
                            msgtip = [REQmsg[1], f" uploaded3", '', '']
                            ret = ['1', REQmsg[1], ['uploaded']]
                            return msgtip, ret
                    else:
                        msgtip = [REQmsg[1], f"错误！mac地址不符", '', '']
                        ret = ['1', REQmsg[1], ['wrongSite']]
                        return msgtip, ret
                else:
                    msgtip = [REQmsg[1], f"错误！记录不存在unknownError3", '', '']
                    ret = ['1', REQmsg[1], ['unknownError']]
                    return msgtip, ret
        except Exception as e:
            print('model_transmit_message', e)
    def classifier_id_inquiry(self, macAddr, REQmsg):
        classifier_file_name = REQmsg[3][0]
        classifier_info = self.dbUtil.getclassifierInfo(where_name='filename', where_value=classifier_file_name)
        msgtip = [REQmsg[1], f"步骤七 查询已存在模型的信息", '', '']
        ret = ['1', REQmsg[1], classifier_info]
        return msgtip, ret
    def classifierPaging(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _pagerows = REQmsg[3][1]
            if _pagerows <= 0:
                _pagerows = 12
            result = self.dbUtil.getClsInfoByPage(offset=(_curPageIndex - 1) * _pagerows, psize=_pagerows)
            msgtip = [REQmsg[2], f"数据库操作成功，页面控制", '', '']
            # print(msgtip)
            ret = ['1', REQmsg[1], result]
            return msgtip, ret
        except Exception as e:
            print('userPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret
    def classifierPaging_al(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            category = REQmsg[3][3]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _pagerows = REQmsg[3][1]
            if _pagerows <= 0:
                _pagerows = 12
            result = self.dbUtil.getalgorithmInfoByPage(where_name='type', where_value=category,
                                                        offset=(_curPageIndex - 1) * _pagerows, psize=_pagerows)
            msgtip = [REQmsg[2], f"数据库操作成功，页面控制", '', '']
            # print(msgtip)
            ret = ['1', REQmsg[1], result]
            return msgtip, ret
        except Exception as e:
            print('userPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret
    def inquiryCls_alg_Info(self, macAddr, REQmsg):
        try:
            ket_value = REQmsg[3][0]
            catagory = REQmsg[3][3]
            alg_info = self.dbUtil.Inqcls_and_type(where_name='alg_name', where_like=ket_value, where_state='type',
                                                   state=catagory)
            totalPage = ceil(len(alg_info) / REQmsg[3][2])
            start = (REQmsg[3][1] - 1) * REQmsg[3][2]
            alg_info = alg_info[start:start + REQmsg[3][2]]
            msgtip = [REQmsg[0], f"获取查询算法信息", '', '']
            # print(msgtip)
            ret = ['1', REQmsg[0], [totalPage, alg_info]]
            return msgtip, ret
        except Exception as e:
            print('inquiryAlgorithmInfo', e)
            msgtip = [REQmsg[0], f"获取查询算法信息", '', '']
            ret = ['0', REQmsg[0], e]
            return msgtip, ret
    def getClassifier_config(self, cmdID, config):
        configInfo = self.curUser.config
        msgtip = [cmdID, f"获取全部基本配置信息", '', '']
        print(configInfo)
        ret = ['1', cmdID, f"获取全部基本配置信息", configInfo]
        return msgtip, ret

    def getSelectSetInfo(self, cmdID, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _pagerows = REQmsg[3][1]
            if _pagerows <= 0:
                _pagerows = 12
            Set_info = self.dbUtil.Inqcls_set(where_type=REQmsg[3][2])
            ui_size = len(Set_info)
            ptotal = ceil(ui_size / _pagerows)  # 总页数
            if ptotal != 0:
                if _curPageIndex > ptotal:
                    _curPageIndex = ptotal
                result = self.dbUtil.Inqcls_set(where_type=REQmsg[3][2],
                                                            offset=(_curPageIndex - 1) * _pagerows, psize=_pagerows)
                msgtip = [REQmsg[1], f"模型管理：获取数据集信息", '', '']
                # print(msgtip)
                ret = ['1', REQmsg[1], result, ptotal]
                return msgtip, ret
            else:
                result = 0
                msgtip = [REQmsg[0], f"模型管理：无对应数据集信息", '', '']
                ret = ['2', REQmsg[0], result, ptotal]
                return msgtip, ret
        except Exception as e:
            print('getSetInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret
    def inquiryCls_set_Info(self, macAddr, REQmsg):
        try:
            key_value = REQmsg[3][0]
            catagory = REQmsg[3][3]
            set_info = self.dbUtil.Inquiryset(where_name='set_name', where_like=key_value,
                                                   where_type=catagory)
            totalPage = ceil(len(set_info) / REQmsg[3][2])
            start = (REQmsg[3][1] - 1) * REQmsg[3][2]
            set_info = set_info[start:start + REQmsg[3][2]]
            msgtip = [REQmsg[0], f"获取查询数据集信息", '', '']
            # print(msgtip)
            ret = ['1', REQmsg[0], [totalPage, set_info]]
            return msgtip, ret
        except Exception as e:
            print('inquiryCls_set_Info', e)
            msgtip = [REQmsg[0], f"获取查询数据集信息", '', '']
            ret = ['0', REQmsg[0], e]
            return msgtip, ret
    def classifierPaging_set(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            category = REQmsg[3][3]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _pagerows = REQmsg[3][1]
            if _pagerows <= 0:
                _pagerows = 12
            result = self.dbUtil.getsetInfoByPage(where_type=category,offset=(_curPageIndex - 1) * _pagerows, psize=_pagerows)
            msgtip = [REQmsg[2], f"数据库操作成功，页面控制", '', '']
            # print(msgtip)
            ret = ['1', REQmsg[1], result]
            return msgtip, ret
        except Exception as e:
            print('usersetPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[1], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def upload_scheme(self,macAddr,REQmsg):
        try:
            cls_info = REQmsg[3][0]
            classifier_info = self.dbUtil.getclassifierInfo(where_name='classifier_name', where_value=cls_info)
            if classifier_info:
                msgtip = [REQmsg[1], f"模型名字重复", '', '']
                ret = ['0', REQmsg[1], classifier_info]
                return msgtip, ret
            else:
                type = REQmsg[3][8]
                nb_class=REQmsg[3][7]
                sample_lenth=REQmsg[3][3]
                alg_info = self.dbUtil.get_al_setInfo(where_table='algorithm', where_name='alg_id', where_value=REQmsg[3][1])
                set_info = self.dbUtil.get_al_setInfo(where_table='set_info',where_name='set_id', where_value=REQmsg[3][2])
                flag = self.modelmatch(alg_info,set_info, type, nb_class, sample_lenth)
                if flag == True:
                    self.dbUtil.add_init_ClassifierInfo(classifier_name=REQmsg[3][0], alg_id=REQmsg[3][1],
                                                        set_id=REQmsg[3][2], filename='',
                                                        state='ready', train_performance='',
                                                        test_performance='',
                                                        epoch_length=REQmsg[3][3], config_id=REQmsg[3][4],
                                                        channels=REQmsg[3][5],mac=macAddr,classifierUnit=REQmsg[3][6])
                    msgtip = [REQmsg[1], f"保存模型", '', '']
                    ret = ['1', REQmsg[1], REQmsg[3]]
                    return msgtip, ret
                else:
                    msgtip = [REQmsg[1], f"模型匹配失败", '', '']
                    ret = ['2', REQmsg[3][0]]
                    return msgtip, ret
        except Exception as re:
            print('DataBaseUtil.checkClassifierInfo:', re)
    def upload_model(self,cmdID,REQmsg):
        try:
            cls_name=REQmsg[3][0][0]
            classifier_info = self.dbUtil.getclassifierInfo(where_name='classifier_name', where_value=cls_name)
            file_name='classifier00000'+str(classifier_info[0][0])+'.'+str(REQmsg[3][1])
            if classifier_info[0][5]=='ready':
                self.dbUtil.add_init_ClassifierInfo(classifier_name=cls_name, filename=file_name)
                msgtip = [REQmsg[1], f"模型准备上传", '', '']
                ret = ['1', cls_name]
                print(ret)
                return msgtip, ret
            else:
                msgtip = [REQmsg[1], f"选择的模型不是准备上传状态", '', '']
                ret = ['0', cls_name]
                return msgtip, ret
        except Exception as re:
            print('DataBaseUtil.checkClassifierInfo:', re)
    def modelmatch(self,alg_info,set_info,type,nb_class,sample_lenth):
        if (alg_info[0][17] == 'waveform' and type != 'wave'):
            return False
        if (alg_info[0][17] == 'state' and type != 'state'):
            return False
        algPara = json.loads(alg_info[0][3])
        setPara =json.loads(set_info[0][3])
        if nb_class != algPara['nb_class']:
            return False
        if sample_lenth!=algPara['sample_len'] or sample_lenth!=setPara['span']:
            return False
        return True

    # 脑电扫描
    def getAutoInitData(self, macAddr, REQmsg):
        try:
            res, montage_list = self.appUtil.getMontage()
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 8
            alg_reset = REQmsg[3][2]
            ui_size = self.dbUtil.getClassifierInfoLen()
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal and ptotal > 0:
                _curPageIndex = ptotal
            classifier_info = self.dbUtil.getClassifierInfoByPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                                  psize=_Pagerows)
            if alg_reset:
                msgtip = [REQmsg[2], f"获取脑电扫描界面信息", '', '']
                ret = ['1', REQmsg[2], montage_list, classifier_info, '1', ptotal, alg_reset]
                return msgtip, ret
            patient_info = self.dbUtil.get_patientNameId()
            msgtip = [REQmsg[2], f"获取脑电扫描界面信息", '', '']
            ret = ['1', REQmsg[2], montage_list, classifier_info, patient_info, ptotal, alg_reset]
            return msgtip, ret
        except Exception as e:
            print('getAutoInitData', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getPatientMeasureDay(self, macAddr, REQmsg):
        try:
            patient_id = REQmsg[3][0]
            measure_day = self.dbUtil.get_measure_day(patient_id)
            msgtip = [REQmsg[2], f"获取对应病人的开单日期信息", '', '']
            ret = ['1', REQmsg[2], measure_day]
            return msgtip, ret
        except Exception as e:
            print('getPatientMeasureDay', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getPatientFile(self, macAddr, REQmsg):
        try:
            check_id = REQmsg[3][0]
            check_number = str(check_id).zfill(11)
            path = os.path.join(self.appUtil.root_path, 'data', 'formated_data')
            file_id = self.dbUtil.get_patient_file(check_id)
            pre_info = []
            pre_info_file_size = []
            for i in file_id:
                file_name = "{:>03}.bdf".format(i[0])
                pre_info.append([check_id, file_name, i[0]])
                file_path = os.path.join(path, check_number, file_name)
                if os.path.exists(file_path):
                    # 如果数据库中存在而实际文件不存在，需要进行异常处理
                    size = os.path.getsize(file_path)
                    file_size = self.convert_size(size)
                else:
                    file_size = "not exists"
                pre_info_file_size.append(file_size)
            msgtip = [REQmsg[2], f"获取对应病人的脑电文件信息", '', '']
            ret = ['1', REQmsg[2], pre_info, pre_info_file_size]
            return msgtip, ret
        except Exception as e:
            print('getPatientFile', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[2]}数据库操作不成功"]
            return msgtip, ret

    def autoClassifierInfoPaging(self, macAddr, REQmsg):
        try:
            isSearch = REQmsg[3][3]
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 8
            if isSearch:
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                result = self.dbUtil.getSearchClassifierInfoByPage(where_name=key_word, where_value=key_value,
                                                                   offset=(_curPageIndex - 1) * _Pagerows,
                                                                   psize=_Pagerows)
            else:
                result = self.dbUtil.getClassifierInfoByPage(offset=(_curPageIndex - 1) * _Pagerows,
                                                             psize=_Pagerows)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, isSearch]
            return msgtip, ret
        except Exception as e:
            print('autoClassifierInfoPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def autoInquiryClassifierInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            _curPageIndex = REQmsg[3][2]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][3]
            if _Pagerows <= 0:
                _Pagerows = 8
            result = self.dbUtil.getSearchClassifierInfoByPage(where_name=key_word, where_value=key_value,
                                                               offset=(_curPageIndex - 1) * _Pagerows,
                                                               psize=_Pagerows)
            ui_size = self.dbUtil.getClassifierInfoLen(where_name=key_word, where_value=key_value)
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            ret = ['1', REQmsg[1], result, ptotal]
            msgtip = [REQmsg[1], f"应答{REQmsg[2]}获取查询分类器信息", '数据库操作成功', '']
            return msgtip, ret
        except Exception as e:
            print('autoInquiryClassifierInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getFileChannels(self, macAddr, REQmsg):
        try:
            check_id = REQmsg[3][0]
            file_name = REQmsg[3][1]
            selected_file_info = REQmsg[3][2]
            raw = self.load_file_raw(check_id, file_name)
            channel_info = raw.info['ch_names']
            channel_list = []
            for item in channel_info:
                item = item.split(' ')
                channel_list.append(item[-1])
            msgtip = [REQmsg[2], f"获取对应病人的脑电文件通道信息", '', '']
            ret = ['1', REQmsg[2], channel_list, file_name, check_id, selected_file_info]
            return msgtip, ret
        except Exception as e:
            print('getFileChannels', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[2]}", '获取脑电文件通道失败', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[2]}获取脑电文件通道失败"]
            return msgtip, ret

    def runProcessForScan(self, macAddr, REQmsg):
        try:
            result = self.predict.run()
            if result == True:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程成功', "", '']
                ret = ['1', REQmsg[1], f"应答{REQmsg[0]}开启进程成功"]
            else:
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程失败', "", '']
                ret = ['1', REQmsg[1], f"应答{REQmsg[0]}开启进程失败"]
            return msgtip, ret
        except Exception as e:
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '开启进程失败', "", '']
            ret = ['0', f"应答{REQmsg[0]}开启进程失败"]
            print('runProcessForScan', e)
            return msgtip, ret

    def matchClassifierFile(self, macAddr, REQmsg):
        try:
            flag = self.if_algobject_exist()
            if not flag:
                msgtip = [REQmsg[1], f"当前服务器存在正在执行的训练、测试或扫描任务", '', '']
                ret = ['0', f"当前服务器存在正在执行的训练、测试或扫描任务"]
                return msgtip, ret
            else:
                classifier_id = REQmsg[3][0]
                check_id = REQmsg[3][1]
                file_id = REQmsg[3][2]
                scan_channels_info = REQmsg[3][3]
                time_stride = REQmsg[3][4]
                alg_info = self.dbUtil.getAlgorithmInfoByClassifierName(classifier_id)
                alg_id = alg_info[0][0]
                alg_name = alg_info[0][1]
                alg_state = alg_info[0][14]
                if alg_state != 'uploaded':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '匹配操作成功', "", '']
                    ret = ['0', f"当前分类器未上传预测文件", classifier_id]
                    return msgtip, ret
                self.predict = predictAlg(dbUtil=self.dbUtil, classifier_id=classifier_id, file_id=file_id,
                                          check_id=check_id, scan_file_channel_list=scan_channels_info,
                                          time_stride=time_stride, uid=REQmsg[2], alg_name=alg_name, alg_id=alg_id)
                result = self.predict.match()
                if result:
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '匹配操作成功', "", '']
                    ret = ['1', f"应答{REQmsg[0]}匹配操作成功", classifier_id]
                    return msgtip, ret
                else:
                    del self.predict
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '匹配操作不成功', "", '']
                    ret = ['0', f"应答{REQmsg[0]}匹配操作不成功", classifier_id]
                    return msgtip, ret
        except Exception as e:
            print('matchAlgSet', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '匹配操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}匹配操作不成功"]
            return msgtip, ret

    def scan_cancel(self, macAddr, REQmsg):
        try:
            if hasattr(self, 'predict'):
                del self.predict
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '撤销预测算法对象成功', "", '']
            ret = ['1', REQmsg[1], f"应答{REQmsg[0]}撤销预测算法对象成功"]
            return msgtip, ret
        except Exception as e:
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '撤销预测算法对象失败', "", '']
            ret = ['0', f"应答{REQmsg[0]}撤销预测算法对象失败"]
            print('scan_cancel', e)
            return msgtip, ret

    # 加载脑电文件

    def load_file_raw(self, check_id, file_name):
        try:
            path = self.get_filepath_by_name(check_id, file_name)
            raw = mne.io.read_raw_bdf(path)
            return raw
        except Exception as e:
            return e

    # 通过脑电名称，获取脑电文件存储路径
    def get_filepath_by_name(self, check_id, file_name):
        try:
            check_number = str(check_id).zfill(11)
            path = os.path.join(self.appUtil.root_path, 'data', 'formated_data')
            file_path = os.path.join(path, check_number, file_name)
            return file_path
        except Exception as e:
            return e

    def convert_size(self, text):
        """
        文件大小单位换算
        :text: 文件字节
        :return: 返回字节大小对应单位的数值
        """
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024
        for i in range(len(units)):
            if (text / size) < 1:
                return "%.2f%s" % (text, units[i])  # 返回值保留小数点后两位
            text = text / size

    # 清理标注
    def getClearLabelInfo(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 24
            alg_reset = REQmsg[3][2]
            ui_size = self.dbUtil.get_fileByModelLen()
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal and ptotal > 0:
                _curPageIndex = ptotal
            classifier_info = self.dbUtil.get_fileByModel(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            result = []
            for i in classifier_info:
                j = 0
                temp = []
                if j == 0:
                    temp.append(self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=i[0])[0][1])
                    j += 1
                if j == 1:
                    temp.append(len(self.dbUtil.get_fileNameByModel('mid', i[0])))
                    j += 1
                if j == 2:
                    temp.append((self.dbUtil.get_model_label_number('mid', i[0]))[0][0])
                    j += 1
                if j == 3:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 1))[0][0])
                    j += 1
                if j == 4:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 0))[0][0])
                result.append(temp)
            if not alg_reset:
                config_id = REQmsg[3][3]
                sample_rate = self.dbUtil.queryConfigData('config_id', config_id)[0][2]
                msgtip = [REQmsg[2], f"获取清理标注界面信息", '', '']
                ret = ['1', REQmsg[2], result, ptotal, alg_reset, sample_rate]
            else:
                msgtip = [REQmsg[2], f"获取清理标注界面信息", '', '']
                ret = ['1', REQmsg[2], result, ptotal, alg_reset]
            return msgtip, ret
        except Exception as e:
            print('getClearLabelInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def inquiryScanClassifierInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            _curPageIndex = REQmsg[3][2]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][3]
            if _Pagerows <= 0:
                _Pagerows = 24
            ui_size = self.dbUtil.get_fileByModelLen(where_name=key_word, where_value=key_value)
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal and ptotal > 0:
                _curPageIndex = ptotal
            if ptotal == 0:
                msgtip = [REQmsg[2], f"获取清理标注界面信息", '', '']
                ret = ['1', REQmsg[2], [], ptotal]
                return msgtip, ret
            classifier_info = self.dbUtil.get_fileByModel(where_name=key_word, where_value=key_value,
                                                          offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            result = []
            for i in classifier_info:
                j = 0
                temp = []
                if j == 0:
                    temp.append(self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=i[0])[0][1])
                    j += 1
                if j == 1:
                    temp.append(len(self.dbUtil.get_fileNameByModel('mid', i[0])))
                    j += 1
                if j == 2:
                    temp.append((self.dbUtil.get_model_label_number('mid', i[0]))[0][0])
                    j += 1
                if j == 3:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 1))[0][0])
                    j += 1
                if j == 4:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 0))[0][0])
                result.append(temp)
            msgtip = [REQmsg[2], f"获取清理标注界面信息", '', '']
            ret = ['1', REQmsg[2], result, ptotal]
            return msgtip, ret
        except Exception as e:
            print('inquiryScanClassifierInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def scanClassifierInfoPaging(self, macAddr, REQmsg):
        try:
            isSearch = REQmsg[3][3]
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 24
            if isSearch:
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                classifier_info = self.dbUtil.get_fileByModel(where_name=key_word, where_value=key_value,
                                                              offset=(_curPageIndex - 1) * _Pagerows,
                                                              psize=_Pagerows)
            else:
                classifier_info = self.dbUtil.get_fileByModel(offset=(_curPageIndex - 1) * _Pagerows,
                                                              psize=_Pagerows)
            result = []
            for i in classifier_info:
                j = 0
                temp = []
                if j == 0:
                    temp.append(self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=i[0])[0][1])
                    j += 1
                if j == 1:
                    temp.append(len(self.dbUtil.get_fileNameByModel('mid', i[0])))
                    j += 1
                if j == 2:
                    temp.append((self.dbUtil.get_model_label_number('mid', i[0]))[0][0])
                    j += 1
                if j == 3:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 1))[0][0])
                    j += 1
                if j == 4:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 0))[0][0])
                result.append(temp)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, isSearch]
            return msgtip, ret
        except Exception as e:
            print('scanClassifierInfoPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getScanInfo(self, macAddr, REQmsg):
        try:
            model_name = REQmsg[3][0]
            back = REQmsg[3][1]
            model_id = self.dbUtil.getclassifierId(model_name)[0][0]
            classifier_info = self.dbUtil.get_fileNameByModel(where_name='mid', where_value=model_id)
            result = []
            for i in classifier_info:
                j = 0
                temp = []
                if j == 0:
                    file_name = "{:>03}.bdf".format(i[2])
                    temp.append(file_name)
                    j += 1
                if j == 1:
                    temp.append(str(self.dbUtil.get_patientNameByCheckId(i[1])[0][0]))
                    j += 1
                if j == 2:
                    temp.append((self.dbUtil.get_model_label_number('mid', i[0], i[1], i[2]))[0][0])
                    j += 1
                if j == 3:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 1, i[1], i[2]))[0][0])
                    j += 1
                if j == 4:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 0, i[1], i[2]))[0][0])
                result.append(temp)
            msgtip = [REQmsg[2], f"获取清理标注界面信息", '', '']
            ret = ['1', REQmsg[2], result, classifier_info, back]
            return msgtip, ret
        except Exception as e:
            print('getScanInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getCurClearLabelInfo(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 24
            ui_size = self.dbUtil.getClassifierInfoLen()
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal and ptotal > 0:
                _curPageIndex = ptotal
            classifier_info = self.dbUtil.get_fileByModel(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            result = []
            for i in classifier_info:
                j = 0
                temp = []
                if j == 0:
                    temp.append(self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=i[0])[0][1])
                    j += 1
                if j == 1:
                    temp.append(len(self.dbUtil.get_fileNameByModel('mid', i[0])))
                    j += 1
                if j == 2:
                    temp.append((self.dbUtil.get_model_label_number('mid', i[0]))[0][0])
                    j += 1
                if j == 3:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 1))[0][0])
                    j += 1
                if j == 4:
                    temp.append((self.dbUtil.get_model_label_assess('mid', i[0], 0))[0][0])
                result.append(temp)
            msgtip = [REQmsg[2], f"返回上一级页面信息", '', '']
            ret = ['1', REQmsg[2], result, ptotal]
            return msgtip, ret
        except Exception as e:
            print('getClearLabelInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getScanFileInfo(self, macAddr, REQmsg):
        try:
            model_id = REQmsg[3][0]
            check_id = REQmsg[3][1]
            file_id = REQmsg[3][2]
            reset = REQmsg[3][3]
            label_info = self.dbUtil.getScanFileInfo(model_id, check_id, file_id)
            result = []
            for i in label_info:
                i = list(i)
                if i[5]:
                    i[5] = self.dbUtil.get_my_typeInfo(where_name='type_id', where_value=i[5])[0][1]
                else:
                    i[5] = ''
                result.append(i)
            msgtip = [REQmsg[2], f"返回上一级页面信息", '', '']
            ret = ['1', REQmsg[2], result, reset]
            return msgtip, ret
        except Exception as e:
            print('getClearLabelInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def delLabelListInfo(self, macAddr, REQmsg):
        try:
            del_info = REQmsg[3]
            model_id = del_info[0][0]
            check_id = del_info[0][1]
            file_id = del_info[0][2]
            r, rn = self.dbUtil.delLabelListInfo(del_info)
            label_info = self.dbUtil.getScanFileInfo(model_id, check_id, file_id)
            for i in label_info:
                i = list(i)
                if i[5]:
                    i[5] = self.dbUtil.get_typeInfo(where_name='type_id', where_value=i[5])[0][1]
                else:
                    i[5] = ''
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功']
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{model_id}", label_info]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"删除文件标注信息成功", '', '']
                ret = ['1', REQmsg[2], label_info]
                return msgtip, ret
        except Exception as e:
            print('delLabelListInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def delLabelByModelFile(self, macAddr, REQmsg):
        try:
            model_id = REQmsg[3][0]
            check_id = REQmsg[3][1]
            file_id = REQmsg[3][2]
            r, rn = self.dbUtil.delLabelByModelFile(model_id, check_id, file_id)
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功']
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{model_id}"]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"删除文件全部标注信息成功", '', '']
                ret = ['1', REQmsg[2]]
                return msgtip, ret
        except Exception as e:
            print('delLabelByModelFile', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getLabelInfoByAssess(self, macAddr, REQmsg):
        try:
            model_id = REQmsg[3][0]
            check_id = REQmsg[3][1]
            file_id = REQmsg[3][2]
            flag = REQmsg[3][3]
            label_info = self.dbUtil.getLabelInfoByAssess(model_id, check_id, file_id, flag)
            msgtip = [REQmsg[2], f"查询已标注信息成功", '', '']
            ret = ['1', REQmsg[2], label_info, flag]
            return msgtip, ret
        except Exception as e:
            print('getLabelInfoByAssess', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getSearchScanFileInfo(self, macAddr, REQmsg):
        try:
            key_word = REQmsg[3][0]
            key_value = REQmsg[3][1]
            model_id = REQmsg[3][2]
            check_id = REQmsg[3][3]
            file_id = REQmsg[3][4]
            index = REQmsg[3][5]
            if key_word == 'begin' or key_word == 'end':
                config_id = self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=model_id)[0][11]
                sample_rate = self.dbUtil.getSample_rate(where_name='config_id', where_value=config_id)[0][0]

                t_seconds = int(key_value.split(':')[0]) * 3600 + int(key_value.split(':')[1]) * 60 + float(
                    key_value.split(':')[2])
                if key_word == 'begin':
                    key_value = int(t_seconds * sample_rate)
                else:
                    key_value = int(t_seconds * sample_rate) - 1
            label_info = self.dbUtil.getSearchScanFileInfo(model_id, check_id, file_id, key_word, key_value)
            result = []
            for i in label_info:
                i = list(i)
                if i[5]:
                    i[5] = self.dbUtil.get_my_typeInfo(where_name='type_id', where_value=i[5])[0][1]
                else:
                    i[5] = ''
                result.append(i)
            msgtip = [REQmsg[2], f"返回上一级页面信息", '', '']
            ret = ['1', REQmsg[2], result, index]
            return msgtip, ret
        except Exception as e:
            print('getSearchScanFileInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    # 评估标注
    def getAssessInfo(self, clientAddr, REQmsg):
        try:
            type_info = self.dbUtil.get_typeInfo()
            user_info = self.dbUtil.getUserInfo()
            r, montage = self.appUtil.getMontage()
            if r == '0':
                montage = None
            ret = ['1', type_info, user_info, montage]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '提取类型信息', '']
            return msgtip, ret
        except Exception as e:
            print('getAssessInfo', e)
            ret = ['0', f"应答{REQmsg[0]}未定义命令"]
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}提取类型信息", '未定义命令', '']
            return msgtip, ret

    def getModelIdName(self, macAddr, REQmsg):
        try:
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 24
            alg_reset = REQmsg[3][2]
            ui_size = self.dbUtil.get_fileByModelLen()
            ptotal = ceil(ui_size[0][0] / _Pagerows)
            if _curPageIndex > ptotal and ptotal > 0:
                _curPageIndex = ptotal
            classifier_info = self.dbUtil.get_fileByModel(offset=(_curPageIndex - 1) * _Pagerows, psize=_Pagerows)
            result = []
            for i in classifier_info:
                temp = []
                temp.append(i[0])
                temp.append(self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=i[0])[0][1])
                result.append(temp)
            msgtip = [REQmsg[2], f"获取评估标注界面信息", '', '']
            ret = ['1', REQmsg[2], result, ptotal, alg_reset]
            return msgtip, ret
        except Exception as e:
            print('getModelIdName', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def assessClassifierInfoPaging(self, macAddr, REQmsg):
        try:
            isSearch = REQmsg[3][3]
            _curPageIndex = REQmsg[3][0]
            if _curPageIndex <= 0:
                _curPageIndex = 1
            _Pagerows = REQmsg[3][1]
            if _Pagerows <= 0:
                _Pagerows = 12
            if isSearch:
                key_word = REQmsg[3][4]
                key_value = REQmsg[3][5]
                classifier_info = self.dbUtil.get_fileByModel(where_name=key_word, where_value=key_value,
                                                              offset=(_curPageIndex - 1) * _Pagerows,
                                                              psize=_Pagerows)
            else:
                classifier_info = self.dbUtil.get_fileByModel(offset=(_curPageIndex - 1) * _Pagerows,
                                                              psize=_Pagerows)
            result = []
            for i in classifier_info:
                temp = []
                temp.append(i[0])
                temp.append(self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=i[0])[0][1])
                result.append(temp)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作成功', "", '']
            ret = ['1', REQmsg[1], result, isSearch]
            return msgtip, ret
        except Exception as e:
            print('assessClassifierInfoPaging', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def getAssessFileInfo(self, macAddr, REQmsg):
        try:
            model_id = REQmsg[3][0]
            classifier_info = self.dbUtil.get_fileNameByModel(where_name='mid', where_value=model_id)
            result = []
            for i in classifier_info:
                j = 0
                temp = []
                if j == 0:
                    file_name = "{:>03}.bdf".format(i[2])
                    temp.append(file_name)
                    j += 1
                if j == 1:
                    temp.append(str(self.dbUtil.get_patientNameByCheckId(i[1])[0][0]))
                    j += 1
                if j == 2:
                    temp.append(str(self.dbUtil.get_measure_day_by_checkId(i[1])[0][1]))
                    j += 1
                if j == 3:
                    temp.append(str(self.dbUtil.get_measure_day_by_checkId(i[1])[0][0]))
                temp.append(str(self.dbUtil.get_patientIdByCheckId(i[1])[0][0]))
                result.append(temp)
            msgtip = [REQmsg[2], f"获取清理标注界面信息", '', '']
            ret = ['1', REQmsg[2], result, classifier_info]
            return msgtip, ret
        except Exception as e:
            print('getAssessFileInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def assessOpenEEGFile(self, clientAddr, REQmsg):
        try:
            if REQmsg[1] == 8:
                tmp_type_info = self.dbUtil.get_typeInfo()
                tmp_user_info = self.dbUtil.getUserInfo()

                tmp_type_filter = [x[1] for x in tmp_type_info]
                tmp_user_filter = [x[3] for x in tmp_user_info]
                check_id = REQmsg[3][0]
                file_id = REQmsg[3][1]
                patient_id = REQmsg[3][2]
                model_id = REQmsg[3][3]
                ret = self.appUtil.openEEGFile(check_id, file_id)
                if ret[0] == '0':
                    msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件无效", '{:>03}.bdf'.format(file_id), ""]
                    return msgtip, ret
                raw = ret[1]
                self.appUtil.closeEEGfile(raw)
                _channels = ret[2]

                _patientInfo = self.dbUtil.get_patientInfo('patient_id', patient_id)

                _channels = tuple(_channels) if len(_channels) != 1 else "('{}')".format(_channels[0])
                _type_names = tuple(tmp_type_filter) if len(tmp_type_filter) != 1 else "('{}')".format(
                    tmp_type_filter[0])
                _user_names = tuple(tmp_user_filter) if len(tmp_user_filter) != 1 else "('{}')".format(
                    tmp_user_filter[0])
                _status_show = True
                rn1, _sample_list = self.dbUtil.get_label_ListInfo(check_id, file_id, model_id, _channels,
                                                                   _type_names,
                                                                   _user_names,
                                                                   _status_show)
                rn2, _status_info = self.dbUtil.get_lable_statusInfo(check_id, file_id, model_id)
                if rn1 == '0':
                    _sample_list = None
                if rn2 == '0':
                    _status_info = None

                REPData = ['1', _patientInfo, _sample_list, ret[2], ret[3],
                           ret[4], ret[5], ret[6], ret[7], ret[8], ret[9], _status_info]

                msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '成功', '']
            else:
                REPData = ['0', f"应答{REQmsg[0]}未定义命令"]
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}打开EEG文件", '未定义命令', '']
            return msgtip, REPData
        except Exception as e:
            print('assessOpenEEGFile', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def update_labelListInfo(self, macAddr, REQmsg):
        try:
            update_info = REQmsg[3]
            model_id = update_info[0]
            check_id = update_info[1]
            file_id = update_info[2]
            start = update_info[3]
            pick_channel = update_info[4]
            end = update_info[5]
            mtype_id = update_info[6]
            uid = update_info[7]
            utype_id = update_info[8]
            r, rn = self.dbUtil.update_labelListInfo(model_id, check_id, file_id, start,
                                                     pick_channel, end, mtype_id, uid, utype_id)
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功']
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{REQmsg[1]}", update_info]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"修改标注信息成功", '', '']
                ret = ['1', REQmsg[2], update_info]
                return msgtip, ret
        except Exception as e:
            print('update_labelListInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret

    def del_labelListInfo(self, macAddr, REQmsg):
        try:
            del_info = REQmsg[3]
            model_id = del_info[0]
            check_id = del_info[1]
            file_id = del_info[2]
            start = del_info[3]
            pick_channel = del_info[4]
            end = del_info[5]
            mtype_id = del_info[6]
            r, rn = self.dbUtil.del_labelListInfo(model_id, check_id, file_id, start,
                                                  pick_channel, end, mtype_id)
            if r == '0':
                msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功']
                ret = ['0', f"应答{REQmsg[0]}数据库操作不成功:{REQmsg[1]}", del_info]
                return msgtip, ret
            else:
                msgtip = [REQmsg[2], f"删除标注信息成功", '', '']
                ret = ['1', REQmsg[2], del_info]
                return msgtip, ret
        except Exception as e:
            print('del_labelListInfo', e)
            msgtip = [REQmsg[2], f"应答{REQmsg[0]}", '数据库操作不成功', "", '']
            ret = ['0', REQmsg[2], f"应答{REQmsg[0]}数据库操作不成功"]
            return msgtip, ret
