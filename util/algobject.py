import copy
import json
import os
import pickle
import sys
from PyQt5.QtCore import QProcess

from PyQt5.QtWidgets import QApplication

from util.dbUtil import dbUtil


class algObject(object):

    def __init__(self, dbUtil, alg_name=None, alg_id=None):
        self.alg_id = alg_id
        self.algName = alg_name
        self.algFileName = None
        self.algType = None
        self.algPara = None
        self.dbUtil = dbUtil
        self.mProcess = None
        self.progress = []
        self.classifierName = None
        self.modelFileName = None
        self.result = False
        self.epoch = 0
        self.scan_num = 0
        self.total_scan_num = 0
        self.current_file_label_saved_num = 0
        if self.alg_id is not None:
            self.readAlgFile(self.alg_id)

    def run(self):
        pass

    def readAlgFile(self, alg_id):
        pass

    def getProgress(self):
        try:
            if self.mProcess != None:
                if not self.progress:
                    return True, []
                else:
                    copy_progress = copy.deepcopy(self.progress)
                    self.progress.clear()
                    data = copy_progress[-1]
                    if "epoch" in data:
                        self.epoch = int(data[5:6])
                    return True, copy_progress
            else:
                copy_progress = copy.deepcopy(self.progress)
                self.progress.clear()
                return False, copy_progress
        except Exception as e:
            print('getProgress', e)

    def handle_stdout(self):
        pass

    def handle_stderr(self):
        data = self.mProcess.readAllStandardError()
        try:
            stderr = bytes(data).decode("utf-8")
        except Exception as e:
            print(e)
            stderr = bytes(data).decode("gbk")
        print(stderr)
        self.progress.append(stderr)
        QApplication.processEvents()

    # 通过标准输出流实现进程信息交互，将信息传递给系统主程序，并可以通过监测输出信息处理相关错误

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        print(state_name)
        self.progress.append("State changed:" + state_name)

    def process_finished(self):
        pass


class trainAlg(algObject):

    def __init__(self, dbUtil, alg_name, alg_id, set_id, config_id):
        try:
            super().__init__(dbUtil, alg_name, alg_id)
            self.readAlgFile(self.alg_id)
            self.set_id = set_id
            self.config_id = config_id
            self.readTrainingSet(set_id)
            self.train_performance = None
            self.sample_len = None
            path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.set_path = os.path.join(path, 'classifier\\', 'algorithms\\', 'set.pkl')

        except Exception as e:
            print('trainAlg__init__:', e)

    def save_set_info(self,set_info):
        f = open(self.set_path, 'wb')
        pickle.dump(set_info, f)

    def readTrainingSet(self, set_id):
        try:
            set_info = self.dbUtil.get_set_info(where_name='set_id', where_value=set_id)[0]
            Filename = set_info[4] + '.npz'
            path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.trainingSetFilename = os.path.join(path, 'data\\', 'train_set\\', Filename)
            self.setDescription = json.loads(set_info[3])
        except Exception as e:
            print('readTrainingSet', e)

    def match(self):
        try:
            set_type = self.setDescription['type'] #数据集的description
            if set_type == 'wave' and self.algType != 'waveform': #算法和数据集类型匹配
                return False
            if set_type == 'state' and self.algType != 'state':
                return False
            nb_class = self.algPara['nb_class']# alg 表中trainning_para
            content = self.setDescription['content']
            temp = []
            for i in content:
                temp.append(i[0])#添加typeID
            self.set_temp = set(temp)
            self.set_class = len(self.set_temp)
            if self.setDescription['scheme'] != '':
                self.set_class = self.set_class + 1
            if nb_class != self.set_class: #检查分类数目  算法是否等于数据集
                return False
            sample_len = self.algPara['sample_len']
            if sample_len != '':
                if not self.setDescription['span'] == sample_len: #判断span是否等于samplelen
                    return False
            set_info = {'set_temp': self.set_temp, 'set_class': self.set_class}
            self.save_set_info(set_info)
            path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.modelFileName = os.path.join(path, 'classifier\\', 'models\\',
                                              self.algName + str(self.set_id) + '.pth')
            self.classifierName = self.algName + str(self.set_id)
            return True
        except Exception as e:
            print('match', e)
            return False

    def run(self):
        try:
            self.mProcess = QProcess()
            self.mProcess.readyReadStandardOutput.connect(self.handle_stdout)
            self.mProcess.readyReadStandardError.connect(self.handle_stderr)
            self.mProcess.stateChanged.connect(self.handle_state)
            self.mProcess.finished.connect(self.process_finished)
            self.mProcess.start("python", [self.algFileName, self.modelFileName, self.trainingSetFilename])
            return True
        except Exception as e:
            return False

    def process_finished(self):
        try:
            self.mProcess.kill()
            self.mProcess.waitForFinished()
            self.mProcess.deleteLater()
            self.mProcess = None
            if self.result == False:
                print('return')
                return
            else:
                cls_info = self.dbUtil.getclassifierInfo(where_name=[self.alg_id, self.set_id, self.config_id], flag=1)
                if cls_info == []:
                    # config_info = self.dbUtil.queryConfigData(where_name='config_id', where_value=self.config_id)
                    if self.algType == 'waveform':
                        self.dbUtil.addClassifierInfo(classifier_name=self.classifierName, alg_id=self.alg_id,
                                                      set_id=self.set_id,
                                                      filename=self.classifierName + ".pth",
                                                      state='uploaded', train_performance=self.train_performance,
                                                      test_performance=None,
                                                      epoch_length=self.setDescription['span'],
                                                      config_id=self.config_id, classifierUnit='V', channels=None)
                    else:
                        self.dbUtil.addClassifierInfo(classifier_name=self.classifierName, alg_id=self.alg_id,
                                                      set_id=self.set_id,
                                                      filename=self.classifierName + ".pth",
                                                      state='uploaded', train_performance=self.train_performance,
                                                      test_performance=None,
                                                      epoch_length=self.setDescription['span'],
                                                      config_id=self.config_id, classifierUnit='V', channels=json.dumps(self.setDescription['channels']))
                else:
                    self.dbUtil.updateClassifierInfo('train_performance', self.train_performance, 'classifier_id', cls_info[0][0])
        except Exception as e:
            print('process_finished', e)

    def handle_stdout(self):
        data = self.mProcess.readAllStandardOutput()
        try:
            stdout = bytes(data).decode("utf-8")
        except Exception as e:
            print(e)
            stdout = bytes(data).decode("gbk")
        print(stdout)
        if "result:" in stdout and "finished" in stdout:
            start = stdout.index("result:") + len("result:")
            end = stdout.index("finished")
            self.result = stdout[start:end].strip()
            print("截取的结果：", self.result)
        if "train_performance:" in stdout and "finish" in stdout:
            start = stdout.index("train_performance:") + len("train_performance:")
            end = stdout.index("finish")
            self.train_performance = stdout[start:end].strip()
            print("截取的结果：", self.train_performance)
        self.progress.append(stdout)
        QApplication.processEvents()

    def readAlgFile(self, alg_id):
        alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)[0]
        self.algName = alg_info[1]
        alg_name = alg_info[2]
        self.algPara = json.loads(alg_info[3])
        self.algType = alg_info[17]
        path = os.path.dirname(os.path.dirname(__file__))+'\\'
        self.algFileName = os.path.join(path, 'classifier\\', 'algorithms\\', alg_name + '.py')

    def get_classifier_sample_length(self, sampling_rate, set_info):
        try:
            tmp = set_info[3].split('+')[0].split(' ')
            # 样本中每种波形的长度，如果长度多余2种，设置样本不同长标记为真
            sample_len = set()
            for i in tmp:
                # 转换成秒，乘上采样率
                sl = int(i.split('-')[1]) / 1000 * sampling_rate
                sample_len.add(int(sl))
            return list(sample_len)
        except Exception as e:
            print('get_classifier_sample_length', e)


class predictAlg(algObject):

    def __init__(self, dbUtil, classifier_id, file_id, check_id, scan_file_channel_list, time_stride, uid,
                 alg_name=None, alg_id=None):
        try:
            super().__init__(dbUtil, alg_name, alg_id)
            self.classifier_id = classifier_id
            self.file_id = file_id
            self.check_id = check_id
            self.uid = uid
            config_id = self.dbUtil.get_fileInfo(where_name='check_id', where_value=check_id,
                                                 wherename='file_id', wherevalue=file_id)[1][0][3]
            self.scan_file_channel_list = scan_file_channel_list
            self.time_stride = time_stride
            classifier_info = self.dbUtil.getclassifierInfo(where_name='classifier_id', where_value=self.classifier_id)[0]
            model_config_id = classifier_info[11]
            set_id = classifier_info[3]
            self.set_temp = set()
            if set_id:
                set_info = self.dbUtil.get_set_info(where_name='set_id', where_value=set_id)[0]
                self.setDescription = json.loads(set_info[3])
                content = self.setDescription['content']
                temp = []
                for i in content:
                    temp.append(i[0])
                self.set_temp = set(temp)
                # path = os.path.join(os.path.dirname(__file__))[:-16]
                # self.set_path = os.path.join(path, 'server_root\\', 'classifier\\', 'algorithms\\', 'set_dic.pkl')
                # f = open(self.set_path, 'wb')
                # pickle.dump(self.set_temp, f)
            config_info = self.dbUtil.queryConfigData(where_name='config_id', where_value=config_id)
            self.sample_rate = config_info[0][2]
            self.model_train_sample_rate = \
                self.dbUtil.queryConfigData(where_name='config_id', where_value=model_config_id)[0][2]
            self.sample_len = classifier_info[10]
            self.modelUnit = classifier_info[12]
            self.classifierName = classifier_info[1]
            my_path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.modelFileName = os.path.join(my_path, 'classifier\\', 'models\\', classifier_info[4])
            self.scan_result_filepath = os.path.join(my_path, 'classifier\\', 'algorithms\\',
                                                     'predict.pkl')
            path = os.path.join(my_path, 'data', 'formated_data')
            check_number = str(self.check_id).zfill(11)
            file_name = "{:>03}.bdf".format(self.file_id)
            self.eegFileName = os.path.join(path, check_number, file_name)
            # 不进行存储的下标列表
            self.labels_not_annotation = [0, 33]
        except Exception as e:
            print('predictAlg__init__:', e)

    def match(self):
        try:
            if self.model_train_sample_rate > self.sample_rate:
                return False
            else:
                return True
        except Exception as e:
            print('predict_match', e)

    def run(self):
        try:
            unitFactor = 1
            if self.modelUnit == 'V':
                unitFactor = 1
            elif self.modelUnit == 'mV':
                unitFactor = 1000
            elif self.modelUnit == 'muV':
                unitFactor = 100000
            self.mProcess = QProcess()
            # self.lop = QEventLoop()
            self.mProcess.readyReadStandardOutput.connect(self.handle_stdout)
            self.mProcess.readyReadStandardError.connect(self.handle_stderr)
            self.mProcess.stateChanged.connect(self.handle_state)
            self.mProcess.finished.connect(self.process_finished)
            self.mProcess.start("python", [self.algFileName, self.modelFileName, self.eegFileName, self.time_stride,
                                           str(self.scan_file_channel_list), str(self.sample_rate), str(self.sample_len)
                , str(unitFactor), str(self.model_train_sample_rate), self.algType, str(self.set_temp)])
            return True
        except Exception as e:
            return False
            print('run', e)

    def readAlgFile(self, alg_id):
        try:
            alg_info = self.dbUtil.getAlgorithmInfo(where_name='alg_id', where_value=alg_id)[0]
            self.algName = alg_info[1]
            alg_name = alg_info[12]
            self.algPara = alg_info[13]
            self.algType = alg_info[17]
            path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.algFileName = os.path.join(path, 'classifier\\', 'algorithms\\', alg_name + '.py')
        except Exception as e:
            print('readAlgFile', e)

    def handle_stdout(self):
        data = self.mProcess.readAllStandardOutput()
        try:
            stdout = bytes(data).decode("utf-8")
        except Exception as e:
            print(e)
            stdout = bytes(data).decode("gbk")
        print(stdout)
        if "开始进行数据库存储" in stdout:
            self.progress.append("开始进行数据库存储")
            self.predict_dic = self.read_predict_result()
            self.scan_num = self.predict_dic['scanned_num'] + self.scan_num
            self.total_scan_num = self.predict_dic['total_scan_num']
            self.save_predict_labels()
        if "result:" in stdout and "finished" in stdout:
            start = stdout.index("result:") + len("result:")
            end = stdout.index("finished")
            self.result = stdout[start:end].strip()
            print("截取的结果：", self.result)

    # 读取模型预测结果文件
    def read_predict_result(self):
        try:
            with open(self.scan_result_filepath, 'rb') as f:
                predict_dic = pickle.load(f)
                f.close()
                # os.remove(self.scan_result_filepath)
            return predict_dic
        except:
            return

    def process_finished(self):
        try:
            print("finished")
            # 销毁进程
            self.mProcess.kill()
            self.mProcess.waitForFinished()
            # 释放内存
            self.mProcess.deleteLater()
            self.mProcess = None
        except Exception as e:
            print('process_finished', e)

    def save_predict_labels(self):
        try:
            count = 0
            sum = 0
            data = self.predict_dic
            start_end_timepoints = self.predict_dic['start_end_timepoints']
            # 单通道上的样本总数
            for ch in data['channels']:
                labels = data['channels'][ch]
                for i in range(len(labels)):
                    try:
                        sum += 1
                        # self.pgb.pgb_update.emit(sum)
                        # 反例不标注
                        if labels[i] in self.labels_not_annotation:
                            count += 1
                        else:
                            self.dbUtil.add_labelInfo_by_auto(mid=self.classifier_id, check_id=self.check_id,
                                                              file_id=self.file_id, begin=start_end_timepoints[i][0],
                                                              channel=ch, end=start_end_timepoints[i][1] - 1,
                                                              mtype_id=labels[i], uid=self.uid)
                    except:
                        count += 1
            # 当前脑电文件扫描完成
            saved_num = sum - count
            self.current_file_label_saved_num += saved_num
            self.progress.append('成功存储{}条数据, 当前批次存储完成'.format(saved_num))
            send_message_to_process(self.mProcess, "complete")
        except Exception as e:
            print('save_predict_labels', e)

class testAlg(algObject):

    def __init__(self, dbUtil, classifier_id):
        try:
            super().__init__(dbUtil, None, None)
            self.dbUtil = dbUtil
            self.classifier_id = classifier_id
            self.test_performance = None
            classifier_info = self.dbUtil.getClassifierById(classifier_id)
            self.classifierName = classifier_info[1]
            self.readAlgFile(classifier_info[2])
            self.readTestingSet(classifier_info[3])
            my_path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.modelFileName = os.path.join(my_path, 'classifier\\', 'models\\', classifier_info[4])
        except Exception as e:
            print('testAlg__init__:', e)

    def run(self):
        try:
            self.mProcess = QProcess()
            self.mProcess.readyReadStandardOutput.connect(self.handle_stdout)
            self.mProcess.readyReadStandardError.connect(self.handle_stderr)
            self.mProcess.stateChanged.connect(self.handle_state)
            self.mProcess.finished.connect(self.process_finished)
            self.mProcess.start("python", [self.algFileName, self.modelFileName, self.testingSetFilename])
            return True
        except Exception as e:
            print('run', e)
            return False

    def readAlgFile(self, alg_id):
        try:
            alg_info = self.dbUtil.getAlgorithmById(alg_id)
            self.algName = alg_info[1]
            alg_name = alg_info[7]
            self.algPara = alg_info[8]
            self.algType = alg_info[17]
            path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.algFileName = os.path.join(path, 'classifier\\', 'algorithms\\', alg_name + '.py')
        except Exception as e:
            print('readAlgFile', e)

    def handle_stdout(self):
        data = self.mProcess.readAllStandardOutput()
        try:
            stdout = bytes(data).decode("utf-8")
        except Exception as e:
            print(e)
            stdout = bytes(data).decode("gbk")
        print(stdout)
        if "result:" in stdout and "finished" in stdout:
            start = stdout.index("result:") + len("result:")
            end = stdout.index("finished")
            self.result = stdout[start:end].strip()
            print("截取的结果：", self.result)

        if "test_performance:" in stdout and "finish" in stdout:
            start = stdout.index("test_performance:") + len("test_performance:")
            end = stdout.index("finish")
            self.test_performance = stdout[start:end].strip()
            print("截取的结果：", self.test_performance)
            self.progress.append("test_performance: " + self.test_performance)

        if "scan_num:" in stdout and "finish" in stdout:
            start = stdout.index("scan_num:") + len("scan_num:")
            end = stdout.index("finish")
            self.scan_num = stdout[start:end].strip()
            self.total_scan_num = 10
            print("scan_num:", self.scan_num, "  total_scan_num:", self.total_scan_num)
        QApplication.processEvents()


    def process_finished(self):
        try:
            # 销毁进程
            self.mProcess.kill()
            self.mProcess.waitForFinished()
            self.mProcess.deleteLater()
            self.mProcess = None
            # print(self.result)
            if self.result:
                self.dbUtil.updateClassifierInfo('test_performance', self.test_performance, 'classifier_id', self.classifier_id)
        except Exception as e:
            print('process_finished', e)


    def readTestingSet(self, set_id):
        try:
            set_info = self.dbUtil.get_set_info(where_name='set_id', where_value=set_id)[0]
            Filename = set_info[5] + '.npz'
            path = os.path.dirname(os.path.dirname(__file__))+'\\'
            self.testingSetFilename = os.path.join(path, 'data\\', 'test_set\\', Filename)
        except Exception as e:
            print('readTestSet', e)

def send_message_to_process(process, message):
    # QProcess.waitForBytesWritten()
    # 向进程的标准输入流中写入数据
    process.write(message.encode('gbk') + b'\n')
    process.waitForBytesWritten()


if __name__ == '__main__':
    dbUtil = dbUtil()
    test = testAlg(dbUtil, '10')
    test.run()