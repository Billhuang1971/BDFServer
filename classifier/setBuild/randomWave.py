from classifier.setBuild.waveBuild import waveBuild
from bisect import insort
import random


class randomWave(waveBuild):
    def __init__(self, dbUtil, appUtil, setName, description, config_id):
        super().__init__(dbUtil, appUtil, setName, description, config_id)

    def searchNeg(self):
        negSelectedNum = 0  # 已选择的负例数
        negIndexList = []  # 存储已选负例索引的列表
        print(f'curFileNegNum: {self.curFileNegNum}')

        while negSelectedNum < self.curFileNegNum:
            if self.isStop:
                print(f'Wave 搜索负例中止')
                return

            current_sample = random.randint(0, self.eegLength - self.span)
            sample_end = current_sample + self.span
            random_index = random.randint(0, len(self.channels) - 1)
            print(f'current_sample: {current_sample}, random_index: {random_index}')

            # 检查与正例重叠
            in_pos_index_list = False
            left, right = 0, self.curFilePosNum - 1
            while left <= right:
                mid = (left + right) // 2
                mid_interval = self.posIndexList[mid]
                if self.overlaps((current_sample, sample_end), mid_interval):
                    in_pos_index_list = True
                    break
                if sample_end <= mid_interval[0]:
                    right = mid - 1
                else:
                    left = mid + 1

            print(f'in_pos_index_list: {in_pos_index_list}')
            if in_pos_index_list:
                continue

            # 检查与已选择的负例重叠
            in_neg_index_list = False
            left, right = 0, negSelectedNum - 1
            while left <= right:
                mid = (left + right) // 2
                mid_interval = negIndexList[mid]
                if self.overlaps((current_sample, sample_end), mid_interval):
                    print(f'current_sample: {(current_sample, sample_end)}, mid_interval: {mid_interval}')
                    in_neg_index_list = True
                    break
                if sample_end <= mid_interval[0]:
                    right = mid - 1
                else:
                    left = mid + 1

            print(f'in_neg_index_list: {in_neg_index_list}')
            if not in_neg_index_list:
                negSelectedNum += 1
                insort(negIndexList, (current_sample, sample_end))

                negSample = self.eegData[random_index:random_index + 1, current_sample:sample_end]
                print(f'negSample.shape: {negSample.shape}')
                self.negSamples.append(negSample)

        self.totalNegNum = len(self.negSamples)
