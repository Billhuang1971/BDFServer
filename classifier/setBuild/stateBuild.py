import json
from collections import defaultdict
import numpy as np
from classifier.setBuild.setBuildService import setBuildService

from sklearn.model_selection import train_test_split



class stateBuild(setBuildService):
    def __init__(self, dbUtil, appUtil, setName, description, config_id):
        super().__init__(dbUtil, appUtil, setName, description, config_id)

    def serialize(self):
        print(f'stateBuild serialize')
        print(self.content)

        # 解析content
        data = json.loads(self.content)
        print(data)

        sequence = defaultdict(lambda: {
            "funcName": "",
            "parameters": []
        })

        index = 0
        for file in data['content']:
            sequence[str(index)]['funcName'] = 'getPosIndexList'
            sequence[str(index)]['parameters'] = [file['fileName'], file['check_id'], file['file_id'],
                                                  file['fileContent']]
            index += 1

            sequence[str(index)]['funcName'] = 'getEEGData'
            sequence[str(index)]['parameters'] = [file['fileName']]
            index += 1

            sequence[str(index)]['funcName'] = 'getPos'
            index += 1

            sequence[str(index)]['funcName'] = 'updateProgress'
            sequence[str(index)]['parameters'] = [30 / len(data['content'])]
            index += 1

            sequence[str(index)]['funcName'] = 'searchNeg'
            index += 1

            sequence[str(index)]['funcName'] = 'updateProgress'
            sequence[str(index)]['parameters'] = [50 / len(data['content'])]
            index += 1

        print(json.dumps({"sequence": list(sequence.values())}, indent=4))
        self.sequence = json.dumps({"sequence": list(sequence.values())})

        self.updateProgress(10)

    def saveData(self):
        print(f'state saveData')
        if self.totalPosNum == 0:
            print(f'正例数量为0')
            self.errorReason = '正例数量为0'
            self.isStop = True

        if self.isStop:
            return

        self.posLabel = np.array(self.posLabel)
        print(f'posSamples.len: {len(self.posSamples)}, posLabel: {self.posLabel.shape}, '
              f'negSamples.len: {len(self.negSamples)}')
        if self.posLabel.shape[0] != len(self.posSamples):
            raise ValueError(f"saveData error!")

        try:
            if len(self.negSamples) != 0:
                self.posSamples = np.array(self.posSamples)
                print(f'posMean: {np.mean(self.posSamples)}, posStd: {np.std(self.posSamples)}')
                self.negSamples = np.array(self.negSamples)
                totalSample = np.concatenate((self.posSamples, self.negSamples), axis=0)
                totalLabel = np.concatenate((self.posLabel, np.zeros(len(self.negSamples))))
            else:
                totalSample = np.array(self.posSamples)
                print(f'posMean: {np.mean(self.posSamples)}, posStd: {np.std(self.posSamples)}')
                totalLabel = self.posLabel
        except Exception as e:
            self.errorReason = '构建数据集包需的文件中，EEG通道数量不一致，请筛选后重新构建'
            print(e)
            self.isStop = True
            return
        print(f'totalSample: {totalSample.shape}, totalLabel: {totalLabel.shape}')

        id = self.dbUtil.getSetBuildInfo(selColumn='COALESCE(MAX(set_id), 0) + 1', after='set_info')[0][0]
        print(f'id: {id}')

        try:
            if self.trainRatio == 1.0:
                X_train = totalSample
                y_train = totalLabel
                print(f'posMean: {np.mean(X_train)}, posStd: {np.std(X_train)}')
                X_test = np.array([])
                y_test = np.array([])
            else:
                # 使用train_test_split分割数据集和标签
                test_size=round(1 - self.trainRatio,6)#消除精度误差
                X_train, X_test, y_train, y_test = train_test_split(totalSample, totalLabel, train_size=self.trainRatio,
                                                                    test_size=test_size, random_state=42)
            print(f'X_train: {X_train.shape}, X_test: {X_test.shape}, y_train: {y_train.shape}, y_test: {y_test.shape}')
        except Exception as e:
            self.errorReason = f'当前样本数量为{len(totalLabel)}，样本数量过少，请筛选后重新构建'
            print(e)
            self.isStop = True
            return

        saveTrainMes = {f'data-{self.sampleRate}': X_train, f'label-{self.sampleRate}': y_train}
        saveTestMes = {f'data-{self.sampleRate}': X_test, f'label-{self.sampleRate}': y_test}
        np.savez(f'data/train_set/trainingset{str(id).zfill(8)}.npz', **saveTrainMes)
        np.savez(f'data/test_set/testset{str(id).zfill(8)}.npz', **saveTestMes)

        self.dbUtil.addSet([id, self.setName, self.config_id, self.description,
                            f'trainingset{str(id).zfill(8)}', f'testset{str(id).zfill(8)}'])

        self.updateProgress(100 - self.getProgress())

    def maxExtend(self, data):
        print(f'maxExtend: {data.shape}')
        maxSample = self.span
        current_length = data.shape[1]
        if current_length >= maxSample:
            extended_data = data[:, :maxSample]
        else:
            extension_length = maxSample - current_length
            pre_extension = extension_length // 2
            post_extension = extension_length - pre_extension

            # Use minimum and maximum values for extension
            min_value = np.min(data, axis=1)
            max_value = np.max(data, axis=1)
            pre_data = np.full((data.shape[0], pre_extension), min_value)
            post_data = np.full((data.shape[0], post_extension), max_value)
            print(f'pre_data: {pre_data.shape}, post_data: {post_data.shape}')

            extended_data = np.hstack((pre_data, data, post_data))

        print(f'extended_data.shape: {extended_data.shape}')
        self.posSamples.append(extended_data)
        self.curFilePosNum += 1

    def searchNeg(self):
        pass


    def overlaps(self, interval1, interval2):
        """检查两个时间间隔是否有重叠"""
        return not (interval1[1] <= interval2[0] or interval1[0] >= interval2[1])
