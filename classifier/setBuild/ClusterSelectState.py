from classifier.setBuild.stateBuild import stateBuild
from bisect import insort
import random
import numpy as np
from scipy.signal import hilbert
from scipy.stats import pearsonr
# from pyentrp import sample_entropy as sampen 安装pip install pyentrp

class ClusterSelectState(stateBuild):
    def __init__(self, dbUtil, appUtil, setName, description, config_id):
        super().__init__(dbUtil, appUtil, setName, description, config_id)
    #description {type,sampleRate,span（样本长度）,nChannel（通道数量）,channels（参考方案）,source,theme_id（主题）,minSpan（最小长度）,ratio（正反比例）, trainRatio（训练集占比）,scheme（负例方案）,extension(延拓方式),content}
    def searchNeg(self):
        self.N = int((1 / self.ratio))  # 一个正例对应的负例数量
        self.class_centers = {}  # 存储各类别的中心
        self.positive_samples = {}  # 按类别存储正例样本
        self.negative_samples = []  # 存储所有负例样本
        self.metric = 'os'
        self.positive_num = len(self.posIndexList)  # 总正例样本
        self.negative_num = self.positive_num * self.N  # 总负例数量
        self.quota = []  # 负例配额
        if self.isStop:
            print(f'Wave 搜索负例中止')
            return

        """生成数据集"""
        # 处理第一个正例样本
        if not self.posIndexList:
            return

        first_anno = self.posIndexList[0]  # start,end,channel,typeID
        sample = self.posSamples[0]  # 样本脑电数据
        label = first_anno[3]  # 标签

        # 初始化类别中心和样本集
        self.positive_samples[label] = [sample]  # 按类别存储样本
        self.class_centers[label] = sample  # 按类别存储样本中心
        D = 0.0  # 距离
        time_range = (0, first_anno[0])  # 上一个样本终止点（0）到本样本的起始点（取两个样本中间的区域）
        self._preprocess_negative_ranges()
        print(time_range)
        print(self.negative_regions[0]['range'])
        if self.negative_regions[0]['quota'] != 0:
            # 为第一个正例生成负例
            D = self._generate_negative_samples(D, time_range, first_anno, 0)

        for i in range(1, len(self.negative_regions) - 1):  # 处理中间的负例挑选
            if self.negative_regions[i]['quota'] == 0:  # 跳过这个区间，并更新样本中心
                curr_anno = self.posIndexList[i]
                # 提取当前正例样本
                sample = self.posSamples[i]
                label = curr_anno[3]

                # 更新类别样本集
                if label not in self.positive_samples:
                    self.positive_samples[label] = []
                self.positive_samples[label].append(sample)

                # 更新类别中心(使用该类所有样本的平均)
                class_samples = self.positive_samples[label]
                self.class_centers[label] = self.compute_center(class_samples)
            else:  # 该区间有额度，可构建负例
                prev_anno = self.posIndexList[i - 1]
                curr_anno = self.posIndexList[i]

                # 提取当前正例样本
                sample = self.posSamples[i]
                label = curr_anno[3]

                # 更新类别样本集
                if label not in self.positive_samples:
                    self.positive_samples[label] = []
                self.positive_samples[label].append(sample)

                # 更新类别中心(使用该类所有样本的平均)
                class_samples = self.positive_samples[label]
                self.class_centers[label] = self.compute_center(class_samples)

                # 更新时间范围
                time_range = (prev_anno[1], curr_anno[0])  # 上一个正例结束点到当前正例起始点
                print(time_range)
                print(self.negative_regions[i]['range'])

                # 生成负例样本
                D = self._generate_negative_samples(D, time_range, curr_anno, i)
        # 最后一个区间的负例挑选
        if self.negative_regions[-1]['quota'] != 0:
            prev_anno = self.posIndexList[-1]
            last_time = len(self.eegData[0])

            # 更新时间范围
            time_range = (prev_anno[1], last_time)  # 最后一个正例至脑电文件结尾
            print(time_range)
            print(self.negative_regions[-1]['range'])

            # 生成负例样本
            D = self._generate_negative_samples(D, time_range, prev_anno, -1)

        self.totalNegNum = len(self.negSamples)  # 最终负例数量
        if self.totalNegNum != self.negative_num:
            self.isStop = True
            self.errorReason = '该脑电文件不足以生成该比例的负例或正负比例设置过大.'

    def _generate_negative_samples(self, D, time_range, current_anno, i):  # i为当前quote下标
        """生成N个负例样本(步骤3的具体实现)"""
        n = 1  # 负例数量
        max_attempts = 10000  # 防止无限循环

        while n <= self.negative_regions[i]['quota'] and max_attempts > 0:
            max_attempts -= 1

            # 随机选择开始时间(确保样本完全在时间范围内)
            max_start = time_range[1] - self.span
            if max_start <= time_range[0]:
                print(f"在{time_range[0]}和{time_range[1]}之间的时间过短，不足以生成负例")
                break
            # 随机选取一个点作为负例样本起始
            current_sample = random.randint(time_range[0], time_range[1])  # 脑电时间长度-样本长度，即取样本起始点
            sample_end = current_sample + self.span  # 样本结束点

            # 随机通道
            # channel_index = random.randint(0, len(self.channels) - 1)
            # 正例同通道
            # channel_index=self.channels.index(current_anno[2])

            # 提取负例样本
            sample = self.eegData[:, current_sample:sample_end]

            # 计算与所有类别中心的最小距离
            min_dist = float('inf')
            for center in self.class_centers.values():
                dist = self.compute_distance(sample, center)  # 计算当前距离（可以换成Fast-DWT等EEG专用度量）
                if dist < min_dist:
                    min_dist = dist

            # 检查距离条件
            if min_dist > D:
                self.negSamples.append(sample)
                D = min_dist  # 更新距离标准
                n += 1

        if max_attempts <= 0:
            remaining = self.negative_regions[i]['quota'] - n + 1
            self.negative_regions[i]['residual'] = 0  # 更新当前区间剩余可分配为0（超过迭代次数仍未分配完说明无法找到了）
            self.negative_regions[i]['quota'] = n  # 更新当前区间实际分配为n（迭代分配出去的负例）
            if remaining > 0:
                # 轮询分配剩余配额
                while remaining > 0:
                    # 按residual降序排序可分配区域
                    valid_regions = sorted(
                        [r for r in self.negative_regions[i + 1:] if r['residual'] > 0],
                        # 仅对该区间之后的区间分配配额（可改为全局的，但要多次扫描）
                        key=lambda x: -x['residual']
                    )
                    if len(valid_regions) == 0:
                        self.isStop = True
                        self.errorReason = f'仍有{remaining}个负例未分配，但已无可分配区间.'
                        return
                    for region in valid_regions:
                        if remaining <= 0:
                            break
                        if region['residual'] > 0:
                            region['quota'] += 1
                            region['residual'] -= 1
                            remaining -= 1
            print(f"在{time_range[0]}和{time_range[1]}之间迭代超时，负例挑选后移")
        return D

    def compute_distance(self, sample, sample2):
        if self.metric == "euclidean":
            return np.linalg.norm(sample - sample2)
        elif self.metric == "pearson":
            return 1 - abs(pearsonr(sample, sample2)[0])  # 相关系数建议用中位数抗噪
        elif self.metric == "plv":
            phase1 = np.angle(hilbert(sample))
            phase2 = np.angle(hilbert(sample))
            return 1 - abs(np.mean(np.exp(1j * (phase1 - phase2))))
        # elif self.metric == "sampen":
        #     return abs(sample_entropy(sample) - sample_entropy(sample2))
        elif self.metric == 'os':
            return np.linalg.norm(sample - sample2)
        else:
            raise ValueError("Invalid metric")

    def compute_center(self, class_samples):  # 度量多选一
        if self.metric == "euclidean":
            return np.mean(class_samples, axis=0)
        elif self.metric == "pearson":
            return np.median(class_samples, axis=0)  # 相关系数建议用中位数抗噪
        elif self.metric == "plv":
            phases = [np.angle(hilbert(s)) for s in class_samples]
            return np.mean(phases, axis=0)  # 相位中心
        # elif metric == "sampen":
        #     return class_samples[0]  # 样本熵无显式中心，取第一个样本代表
        elif self.metric == 'os':
            return np.mean(class_samples, axis=0)
        else:
            raise ValueError("Unsupported metric")

    def _preprocess_negative_ranges(self):
        self.negative_regions = []  # 用字典存储区间信息

        # 定义区间结构初始化函数
        def add_region(start, end, has_quota):
            region = {
                'range': (start, end),  # 负例区间范围
                'weight': 0,  # 理论可分配（权重）
                'quota': 1 if has_quota else 0,  # 实际分配
                'residual': 0  # 剩余可分配
            }
            self.negative_regions.append(region)

        # 第一个区间（文件开始→第一个正例）
        first_pos_start = self.posIndexList[0][0]
        add_region(0, first_pos_start, first_pos_start >= self.span)

        # 中间区间（正例之间）
        for i in range(1, len(self.posIndexList)):
            prev_end = self.posIndexList[i - 1][1]
            curr_start = self.posIndexList[i][0]
            add_region(prev_end, curr_start, (curr_start - prev_end) >= self.span)

        # 最后区间（最后一个正例→文件结束）
        last_pos_end = self.posIndexList[-1][1]
        total_length = len(self.eegData[0])
        add_region(last_pos_end, total_length, (total_length - last_pos_end) >= self.span)

        # 计算权重和容量
        for region in self.negative_regions:
            if region['quota'] == 1:
                region_length = region['range'][1] - region['range'][0]
                region['weight'] = max(1, int((region_length // self.span) * 0.75))  # 这里权重已经按照一定百分比选取了

        self.total_negative_capacity = sum(r['weight'] for r in self.negative_regions)

        # 校验容量
        if self.negative_num > self.total_negative_capacity:
            self.isStop = True
            self.errorReason = '负例池不足或正负比例过大.'

        # 第一轮按权重比例分配
        allocated = 0
        for region in self.negative_regions:
            if region['quota'] == 1:
                theoretical = (region['weight'] / self.total_negative_capacity) * self.negative_num
                region['quota'] = min(int(theoretical), region['weight'])
                region['residual'] = region['weight'] - region['quota']
                allocated += region['quota']

        # 第二轮分配剩余配额
        remaining = self.negative_num - allocated
        if remaining > 0:
            # 轮询分配剩余配额
            while remaining > 0:
                # 按residual降序排序可分配区域
                valid_regions = sorted(
                    [r for r in self.negative_regions if r['residual'] > 0],
                    key=lambda x: -x['residual']
                )
                if len(valid_regions) == 0:
                    print(f"仍有{remaining}未分配，但已无可分配区间")
                    return 0
                for region in valid_regions:
                    if remaining <= 0:
                        break
                    if region['residual'] > 0:
                        region['quota'] += 1
                        region['residual'] -= 1
                        remaining -= 1

        # self.negative_ranges = []#有配额的负例区间
        #
        # # 第一个区间（文件开始→第一个正例）
        # if self.posIndexList[0][0] >= self.span:
        #     self.negative_ranges.append((0, self.posIndexList[0][0]))
        #     self.quota.append(1) #有空间配额为1
        # else:
        #     self.quota.append(0) #无空间配额为0
        #
        # # 中间区间（正例之间）
        # for i in range(1, len(self.posIndexList)):
        #     prev_end = self.posIndexList[i - 1][1]
        #     curr_start = self.posIndexList[i][0]
        #     if curr_start - prev_end >= self.span:
        #         self.negative_ranges.append((prev_end, curr_start))
        #         self.quota.append(1)
        #     else:
        #         self.quota.append(0)
        #
        # # 最后区间（最后一个正例→文件结束）
        # last_end = self.posIndexList[-1][1]
        # if len(self.eegData[0]) - last_end >= self.span:
        #     self.quota.append(1)
        #     self.negative_ranges.append((last_end, len(self.eegData[0])))
        # else:
        #     self.quota.append(0)
        #
        #
        # # 计算各区间权重（按可容纳样本数）
        # self.range_weights = [((r[1] - r[0])//self.span) for r in self.negative_ranges]
        # new_range_weights = [int(weight*0.75) for weight in self.range_weights] #权重取可容纳的3/4
        # self.range_weights = new_range_weights
        # self.total_negative_capacity = sum(self.range_weights)
        # # 收集所有有效区间索引
        # self.valid_indices = [i for i in range(len(self.quota)) if self.quota[i] == 1]
        # if self.negative_num>self.total_negative_capacity:
        #     print("负例池不足，正负比例过大")
        #     return
        # for i in range(len(self.quota)): #若可分配配额（值为1），就计算配额（不能超过该区间最多配额的75%）
        #     j=0
        #     if self.quota[i]==1:
        #         self.quota[i]=int((self.range_weights[j]/self.total_negative_capacity)*self.negative_num)
        #         j=j+1
        #
        # remaining = self.negative_num - sum(self.quota)
        # if remaining > 0:
        #     # 按权重降序排序
        #     sorted_indices = sorted(self.valid_indices, key=lambda x: -self.range_weights[x])
        #     for i in sorted_indices:
        #         if remaining <= 0:
        #             break
        #         self.quota[i] += 1
        #         remaining -= 1





    # def compute_distance(self, sample1: np.ndarray, sample2: np.ndarray) -> float:
    #     """计算两个样本之间的距离(使用欧氏距离)"""
    #     return np.linalg.norm(sample1 - sample2)