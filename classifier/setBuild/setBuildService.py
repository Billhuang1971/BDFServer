import json
from collections import defaultdict
import numpy as np
import mne
from classifier.setBuild.runThread import runThread


class setBuildService:
    def __init__(self, dbUtil, appUtil, setName, description, config_id):
        self.dbUtil = dbUtil
        self.appUtil = appUtil
        self.setName = setName
        self.description = description
        self.config_id = config_id

        # 解析description得到的数据
        self.type = ""
        self.sampleRate = 0
        self.span = 0
        self.nChannel = 0
        self.channels = []
        self.source = ""
        self.themeID = []
        self.minSpan = 0
        self.ratio = 0
        self.trainRatio = 0
        self.scheme = ""
        self.extension = ""
        self.content = []

        # 其他数据
        self.progress = 0
        self.buildThread = None
        self.sequence = ""
        self.posIndexList = []
        self.eegData = None
        self.eegLength = 0
        self.posSamples = []
        self.posLabel = []
        self.totalPosNum = 0
        self.curFilePosNum = 0
        self.negSamples = []
        self.totalNegNum = 0
        self.curFileNegNum = 0
        self.isDefault = False

        # self.simulateThread()
        self.buildThread = runThread(self.optimize, self.build, self.saveData)
        self.buildThread.start()

        # error
        self.errorReason = ''
        self.isStop = False

    def simulateThread(self):
        print(f'simulateThread')
        self.optimize()
        self.build()
        self.saveData()

    def getProgress(self):
        return self.progress

    def updateProgress(self, progress):
        self.progress = self.progress + progress
        print(f'updateProgress progress: {progress}, curProgress: {self.progress}')

    def resolve(self):
        print(f'resolve')
        data = json.loads(self.description)
        self.type = data['type']
        self.sampleRate = data['sampleRate']
        self.span = data['span']
        self.nChannel = data['nChannel']
        self.channels = data['channels']
        if 'Default' in self.channels:
            self.isDefault = True
        self.source = data['source']
        self.themeID = data['themeID']
        self.minSpan = data['minSpan']
        self.ratio = data['ratio']
        self.trainRatio = data['trainRatio']
        self.scheme = data['scheme']
        self.extension = data['extension']

        # 转换content
        content_dict = defaultdict(lambda: {
            "fileName": "",
            "themeID": self.themeID,
            "channels": self.channels,
            "check_id": 0,
            "file_id": 0,
            "fileContent": []
        })

        for operation in data['content']:
            typeID, labeller, patient_id, file_ids = operation
            check_id, file_id = file_ids

            key = (check_id, file_id)
            file_path = f"data/formated_data/{str(check_id).zfill(11)}/{str(file_id).zfill(3)}.bdf"

            if not content_dict[key]["fileName"]:
                content_dict[key]["fileName"] = file_path
                content_dict[key]["check_id"] = check_id
                content_dict[key]["file_id"] = file_id

            content_dict[key]["fileContent"].append({
                "labeller": str(labeller),
                "typeID": str(typeID)
            })

        self.content = json.dumps({"content": list(content_dict.values())})
        # print(json.dumps(self.content, indent=4))

        # 更新进度条
        self.updateProgress(5)

    def serialize(self):
        print(f'setBuildService serialize')

    def optimize(self):
        if self.isStop:
            return
        self.resolve()
        self.serialize()

    def checkData(self):
        pass

    def build(self):
        print(f'build')
        data = json.loads(self.sequence)
        for item in data['sequence']:
            if self.isStop:
                return
            # 开始执行一个个的方法
            method = getattr(self, item['funcName'], None)
            # 检查是否成功获取了方法并且它是可调用的
            if callable(method):
                # 调用方法
                method(*item['parameters'])
            else:
                print(f"Method {item['funcName']} 未找到.")

    def cenExtend(self, data):
        print(f'cenExtend: {data.shape}')
        maxSample = self.span
        current_length = data.shape[1]
        if current_length >= maxSample:
            # 如果数据长度超过maxSample，截断到maxSample
            extended_data = data[:, :maxSample]
        else:
            # 计算需要补充的长度
            extension_length = maxSample - current_length
            pre_extension = extension_length // 2
            post_extension = extension_length - pre_extension

            # pre_data = np.flip(data[:, pre_extension], axis=0)
            # post_data = np.flip(data[:, -post_extension:], axis=0)

            # 使用数组的第一个和最后一个值进行扩展
            pre_data = np.tile(data[:, 0], (pre_extension, 1)).T
            post_data = np.tile(data[:, -1], (post_extension, 1)).T
            print(f'pre_data: {pre_data.shape}, post_data: {post_data.shape}')

            # 在原始数据前后添加数据
            extended_data = np.hstack((pre_data, data, post_data))
        print(f'extended_data.shape: {extended_data.shape}')
        self.posSamples.append(extended_data)
        self.curFilePosNum += 1

    def maxExtend(self, data):
        print(f'setBuildService maxExtend')

    def saveData(self):
        print(f'saveData')

    def getPosIndexList(self, fileName, check_id, file_id, fileContent):
        print(f'getPosIndexList fileName: {fileName}, check_id: {check_id}, '
              f'file_id: {file_id}, fileContent: {fileContent}')
        print(f'type: {self.type}, source: {self.source}')

        # 获取uid集合和type_id集合
        fltList = [(item['labeller'], item['typeID']) for item in fileContent]

        # 替换通道
        if self.isDefault:
            self.channels = self.appUtil.getDefChannels(fileName)
        print(f'channels: {self.channels}')
        if self.type == 'state' and (not self.isDefault):
            self.curChannels = self.appUtil.getDefChannels(fileName)
            print(f'eegChannels: {self.curChannels}')
            if not set(self.channels).issubset(
                    set([name.replace('-REF', '').replace('EEG ', '') for name in self.curChannels])):
                self.isStop = True
                self.errorReason = '部分导联不存在于EEG文件中，请重新选择导联.'
                return

        self.posIndexList = self.dbUtil.getPosIndexList(check_id, file_id, self.span,
                                                        self.minSpan, self.channels, fltList,
                                                        self.type, self.themeID)
        # 根据第一个值做一个排序，方便之后二分查早使用
        self.posIndexList = sorted(self.posIndexList, key=lambda x: x[0])
        print(f'posIndexList.len: {len(self.posIndexList)}')

        self.curFilePosNum = len(self.posIndexList)
        # 计算负例的数量
        if self.ratio == 0:
            self.curFileNegNum = 0
        else:
            self.curFileNegNum = int(len(self.posIndexList) / self.ratio)

    def getEEGData(self, fileName):
        print(f'getEEGData fileName: {fileName}')
        self.eegData = self.appUtil.getEEGData(self.isDefault, fileName, self.channels, self.type)

        if self.type == 'state' and (not self.isDefault):
            print('根据通道选择数据')
            tempChannels = [name.replace('-REF', '').replace('EEG ', '') for name in self.curChannels]
            selected_channels_index = [tempChannels.index(channel) for channel in self.channels]
            print(f'selected_channels_index: {selected_channels_index}')
            self.eegData = self.eegData.get_data()[np.array(selected_channels_index), :]
        elif self.type == 'state' and self.isDefault:
            if self.scheme == 'State Neg Model 1':
                print(f'采用默认通道')
                # 这里是临时这样处理
                bipolar_pairs = [
                    ('Fp1', 'F7'), ('F7', 'M1'), ('M1', 'T3'), ('T3', 'T5'),
                    ('T5', 'O1'), ('Fp1', 'F3'), ('F3', 'C3'), ('C3', 'P3'),
                    ('P3', 'O1'), ('AFz', 'Fz'), ('Fz', 'Cz'), ('Cz', 'Pz'),
                    ('Pz', 'Oz'), ('Fp2', 'F4'), ('F4', 'C4'), ('C4', 'P4'),
                    ('P4', 'O2'), ('Fp2', 'F8'), ('F8', 'M2'), ('M2', 'T4'),
                    ('T4', 'T6'), ('T6', 'O2')
                ]
                self.eegData.rename_channels(lambda x: x.split('-')[0][4:])  # 移除原始参考后缀
                # 创建双极参考通道
                self.eegData = mne.set_bipolar_reference(self.eegData,
                                                         anode=[pair[0] for pair in bipolar_pairs],
                                                         cathode=[pair[1] for pair in bipolar_pairs],
                                                         copy=True)
                selected_channels = ['Fp1-F7', 'F7-M1', 'M1-T3', 'T3-T5', 'T5-O1', 'Fp1-F3', 'F3-C3',
                                     'C3-P3', 'P3-O1', 'AFz-Fz', 'Fz-Cz', 'Cz-Pz', 'Pz-Oz', 'Fp2-F4',
                                     'F4-C4', 'C4-P4', 'P4-O2', 'Fp2-F8', 'F8-M2', 'M2-T4', 'T4-T6',
                                     'T6-O2']
                self.channels = selected_channels
                self.eegData.pick(selected_channels)
                self.eegData.filter(l_freq=1, h_freq=45, l_trans_bandwidth='auto', h_trans_bandwidth='auto',
                           filter_length='auto', phase='zero', fir_window='hamming')
                # 降采样，256果然是太大了
                print(f"sfreq: {self.eegData.info['sfreq']}")
                self.eegData = self.eegData.resample(128)

                # 新版的这个有滤波
                self.eegData = self.eegData.get_data()
                print(f'raw_data: {self.eegData.shape}')
            else:
                self.eegData = self.eegData.get_data()
        else:
            self.eegData = self.eegData.get_data()

        self.eegLength = self.eegData.shape[1]
        print(f'eegData.shape: {self.eegData.shape}')

    def getPos(self):
        print(f'getPos')
        self.curFilePosNum = 0
        for item in self.posIndexList:
            data = self.firstGetData(item[0], item[1], item[2])
            self.extend(data)
            self.posLabel.append(item[3])
            self.secondGetData()

        self.totalPosNum = len(self.posSamples)
        # self.posSamples = np.array(self.posSamples)
        # print(f'posSamples: {self.posSamples.shape}')

    def firstGetData(self, begin, end, channel):
        # print(f'firstGetData begin: {begin}, end: {end}, channel: {channel}, channels: {self.channels}')
        if channel == 'all':
            selected_data = self.eegData[:, begin:end]
        else:
            if channel in self.channels:
                channel_index = self.channels.index(channel)
                selected_data = self.eegData[channel_index:channel_index + 1, begin:end]
                print(f'channel_index: {channel_index}, selected_data: {selected_data.shape}')
            else:
                raise ValueError(f"Channel {channel} not found in channel list")
        return selected_data

    def secondGetData(self):
        # print(f'secondGetData')
        pass

    def extend(self, data):
        if self.extension == 'center':
            self.cenExtend(data)
        else:
            self.maxExtend(data)

    def searchNeg(self):
        print(f'setBuildService searchNeg')

    def buildModel(self):
        pass

    def modelNeg(self):
        pass
