from classifier.setBuild.stateBuild import stateBuild
import random
from bisect import insort

class randomState(stateBuild):
    def __init__(self, dbUtil, appUtil, setName, description, config_id):
        super().__init__(dbUtil, appUtil, setName, description, config_id)

    def searchNeg(self):
        print(f'searchNeg')
        negSelectedNum = 0  # 已选择的负例数
        negIndexList = []  # 存储已选负例索引的列表

        while negSelectedNum < self.curFileNegNum:
            if self.isStop:
                print(f'State 搜索负例中止')
                return

            current_sample = random.randint(0, self.eegLength - self.span)
            sample_end = current_sample + self.span

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

            if in_pos_index_list:
                continue

            # 检查与已选择的负例重叠
            in_neg_index_list = False
            left, right = 0, negSelectedNum - 1
            while left <= right:
                mid = (left + right) // 2
                mid_interval = negIndexList[mid]
                if self.overlaps((current_sample, sample_end), mid_interval):
                    in_neg_index_list = True
                    break
                if sample_end <= mid_interval[0]:
                    right = mid - 1
                else:
                    left = mid + 1

            if not in_neg_index_list:
                negSelectedNum += 1
                insort(negIndexList, (current_sample, sample_end))
                # 假设有函数来从文件和导联中获取数据
                if len(self.channels) == self.eegData.shape[0]:
                    negSample = self.eegData[:, current_sample:sample_end]
                    print(f'negSample: {negSample.shape}')
                    self.negSamples.append(negSample)
                else:
                    raise ValueError(f"Channel {self.channels} not found in state")

        self.totalNegNum = len(self.negSamples)