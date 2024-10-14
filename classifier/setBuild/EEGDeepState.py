from classifier.setBuild.stateBuild import stateBuild
import os
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score, precision_score
import json
from collections import defaultdict
from bisect import insort
from sklearn.model_selection import train_test_split
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np
import random
import datetime
from torch.utils.data import DataLoader
from torch.autograd import Variable
import torch
from torch import nn
from torch import Tensor
from einops.layers.torch import Rearrange, Reduce
from torch.backends import cudnn

cudnn.benchmark = False
cudnn.deterministic = True


class EEGDeepState(stateBuild):
    def __init__(self, dbUtil, appUtil, setName, description, config_id):
        super().__init__(dbUtil, appUtil, setName, description, config_id)

    def serialize(self):
        print(f'stateBuild EEGDeepState serialize')
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
            sequence[str(index)]['parameters'] = [15 / len(data['content'])]
            index += 1

            sequence[str(index)]['funcName'] = 'searchRanNeg2'
            index += 1

            sequence[str(index)]['funcName'] = 'updateProgress'
            sequence[str(index)]['parameters'] = [20 / len(data['content'])]
            index += 1

        sequence[str(index)]['funcName'] = 'trainModel'
        index += 1

        sequence[str(index)]['funcName'] = 'updateProgress'
        sequence[str(index)]['parameters'] = [20]
        index += 1


        sequence[str(index)]['funcName'] = 'searchNeg'
        index += 1

        sequence[str(index)]['funcName'] = 'updateProgress'
        sequence[str(index)]['parameters'] = [20]
        index += 1

        print(json.dumps({"sequence": list(sequence.values())}, indent=4))
        self.sequence = json.dumps({"sequence": list(sequence.values())})

        self.updateProgress(5)

    # def serialize(self):
    #     print(f'stateBuild EEGDeepState serialize')
    #     print(self.content)
    #
    #     # 解析content
    #     data = json.loads(self.content)
    #     print(data)
    #
    #     sequence = defaultdict(lambda: {
    #         "funcName": "",
    #         "parameters": []
    #     })
    #
    #     index = 0
    #     sequence[str(index)]['funcName'] = 'trainModel'
    #     index += 1
    #
    #     sequence[str(index)]['funcName'] = 'updateProgress'
    #     sequence[str(index)]['parameters'] = [85]
    #     index += 1
    #
    #     sequence[str(index)]['funcName'] = 'searchNeg'
    #     index += 1
    #
    #     sequence[str(index)]['funcName'] = 'updateProgress'
    #     sequence[str(index)]['parameters'] = [85]
    #     index += 1
    #
    #     print(json.dumps({"sequence": list(sequence.values())}, indent=4))
    #     self.sequence = json.dumps({"sequence": list(sequence.values())})
    #
    #     self.updateProgress(5)



    def searchRanNeg(self):
        print(f'searchRanNeg')
        negSelectedNum = 0  # 已选择的负例数
        negIndexList = []  # 存储已选负例索引的列表

        while negSelectedNum < self.curFileNegNum:
        # while negSelectedNum < self.curFileNegNum * 20:
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
                    self.negSamples.append(negSample)
                    print(f'已随机选择到第{negSelectedNum}个负例')
                else:
                    raise ValueError(f"Channel {self.channels} not found in state")

        self.totalNegNum = len(self.negSamples)

    def searchRanNeg2(self):
        print(f'searchRanNeg2')
        print(self.posIndexList[:3])
        print(self.posIndexList[-3:])

        # 现在处理raw_data中不属于annotations_list的部分
        # all_data_segments = []
        # sfreq = 128
        # # 设置开始的样本点和结束的样本点
        # current_sample = int(self.posIndexList[0][0] - sfreq * 600 - 10)
        # raw_end_sample = int(self.posIndexList[-1][1] + sfreq * 600 + 10)
        # current_sample = current_sample if current_sample >= 0 else 0
        # raw_end_sample = raw_end_sample if raw_end_sample <= self.eegData.shape[1] else self.eegData.shape[1]
        # print(f'current_sample: {current_sample / sfreq}, '
        #       f'raw_end_sample: {raw_end_sample / sfreq}, total: {self.eegData.shape[1] / sfreq}')
        #
        # while (current_sample + sfreq) < raw_end_sample:
        #     # 如果当前样本点在任何一个标注范围内，则跳过这一整个范围
        #     segment_end = current_sample + sfreq
        #     in_annotation = False
        #     for start_sample, end_sample, _, _ in self.posIndexList:
        #         if start_sample <= segment_end < end_sample:
        #             # 跳过整个注释的长度
        #             current_sample = end_sample
        #             in_annotation = True
        #             break
        #
        #     if not in_annotation:
        #         # 如果当前样本点不在任何标注范围内，切割一个1秒的数据段
        #         data_segment = self.eegData[:, current_sample:segment_end]
        #         self.negSamples.append(data_segment)
        #         current_sample = segment_end
        #     else:
        #         continue

        sfreq = 128
        # 设置开始的样本点和结束的样本点
        current_sample = int(self.posIndexList[0][0] - sfreq * 600 - 10)
        raw_end_sample = int(self.posIndexList[-1][1] + sfreq * 600 + 10)
        current_sample = current_sample if current_sample >= 0 else 0
        raw_end_sample = raw_end_sample if raw_end_sample <= self.eegData.shape[1] else self.eegData.shape[1]
        print(f'current_sample: {current_sample / sfreq}, '
              f'raw_end_sample: {raw_end_sample / sfreq}, total: {self.eegData.shape[1] / sfreq}')

        large_gap = sfreq * 2700  # 设置大间隙的阈值

        while (current_sample + sfreq) < raw_end_sample:
            # 如果当前样本点在任何一个标注范围内，则跳过这一整个范围
            segment_end = current_sample + sfreq
            in_annotation = False
            for i, (start_sample, end_sample, _, _) in enumerate(self.posIndexList):
                if start_sample <= segment_end < end_sample:
                    # 跳过整个注释的长度
                    current_sample = end_sample
                    in_annotation = True
                    break
                # 检查大间隙
                if i < len(self.posIndexList) - 1:
                    next_start_sample = self.posIndexList[i + 1][0]
                    if end_sample < current_sample and (next_start_sample - end_sample) > large_gap:
                        if current_sample >= end_sample + sfreq * 600 + 10 and segment_end < next_start_sample - sfreq * 600 - 10:
                            in_annotation = True  # 视为在大间隙中，跳过这段区域
                            current_sample = next_start_sample - sfreq * 600 - 10
                            break

            if not in_annotation:
                # 如果当前样本点不在任何标注范围内，也不在大间隙中，切割一个1秒的数据段
                data_segment = self.eegData[:, current_sample:segment_end]
                self.negSamples.append(data_segment)
                current_sample = segment_end
            else:
                continue

        print(f'目前负例数组中存在的数量是{len(self.negSamples)}')

    def searchNeg(self):
        print(f'EEGDeepState searchNeg')
        print(f'self.curFilePosNum: {self.curFilePosNum}')
        select_data = torch.from_numpy((np.expand_dims(self.large_part, axis=1) - self.target_mean) / self.target_std)
        select_label = torch.from_numpy(np.zeros(len(self.large_part)))
        print(f'select_data: {select_data.shape}, select_label: {select_label.shape}')
        select_dataset = torch.utils.data.TensorDataset(select_data.type(torch.FloatTensor),
                                                        select_label.type(torch.LongTensor))
        select_dataloader = torch.utils.data.DataLoader(dataset=select_dataset, batch_size=512, shuffle=False)

        y_pred = torch.tensor([], dtype=torch.long)
        entropy_list = torch.tensor([], dtype=torch.float)
        all_indices = torch.tensor([], dtype=torch.long)  # 收集所有样本的索引
        y_pred2 = torch.tensor([], dtype=torch.long)
        with torch.no_grad():
            self.model.eval()
            for batch_idx, (data, target) in enumerate(select_dataloader):
                target = Variable(target.type(torch.LongTensor))
                _, output = self.model(data)
                probabilities = torch.softmax(output, dim=1)
                _, o = torch.max(output.data, 1)
                y_pred = torch.cat((y_pred, o), dim=0)

                # 计算熵
                entropy = -torch.sum(probabilities * torch.log(probabilities + 1e-5), dim=1)
                entropy_list = torch.cat((entropy_list, entropy), dim=0)
                all_indices = torch.cat((all_indices, torch.arange(batch_idx * data.size(0),
                                                                   (batch_idx + 1) * data.size(0))), dim=0)

                zero_prob = probabilities[:, 0]
                preds_with_high_confidence = ((zero_prob > 0.5) & (probabilities[:, [1, 2, 3]] > 0.4).any(axis=1)).long()

                y_pred2 = torch.cat((y_pred2, preds_with_high_confidence), dim=0)

            # y_pred_np = y_pred.cpu().numpy()
            # test_label_np = select_label.numpy()

            # f1 = f1_score(test_label_np, y_pred_np, average='weighted')
            # print('F1-score: %.6f' % f1)
            # f1_macro = f1_score(test_label_np, y_pred_np, average='macro')
            # print('Macro F1-score: %.6f' % f1_macro)
            # precision = precision_score(test_label_np, y_pred_np, average=None)
            # print('Precision for each class:', precision)

        # 筛选出预测为0的样本的熵及其索引
        # zero_pred_indices = (y_pred == 0)
        zero_pred_indices = torch.where(y_pred2 == 1)[0]
        entropy_zero_preds = entropy_list[zero_pred_indices]
        original_indices = all_indices[zero_pred_indices]

        # 排序熵值
        sorted_indices = torch.argsort(entropy_zero_preds, descending=True)

        # 最终的索引，即整个数据集中的索引
        ones_indices = original_indices[sorted_indices][:self.wrong_class_num]

        print(f'ones_indices: {len(ones_indices)}')
        # print(f'select_data: {self.select_data.shape}, test_label: {self.select_label.shape}')


        if len(ones_indices) >= self.wrong_class_num:
            selected_indices = torch.randperm(len(ones_indices))[:self.wrong_class_num]
            selected_samples_indices = ones_indices[selected_indices].cpu()

            selected_data = self.large_part[selected_samples_indices]
        else:
            print(f"分类为0的预测样本不足{self.wrong_class_num}个。")
            selected_data = self.large_part[ones_indices.cpu()]

        print(f'selected_data: {selected_data.shape}')
        self.negSamples = selected_data
        # print(f'train_data: {train_data.shape}, train_label: {train_label.shape}')
        # counts = np.bincount(train_label.astype(np.int64))
        # # 打印每个类别的数量
        # for i in range(len(counts)):
        #     print(f"类别 {i}: {counts[i]} 个")

    def trainModel(self):
        print(f'trainModel')
        # 先随机凑负例
        self.posLabel = np.array(self.posLabel)
        print(f'posSamples.len: {len(self.posSamples)}, posLabel: {self.posLabel.shape}, '
              f'negSamples.len: {len(self.negSamples)}')
        if self.posLabel.shape[0] != len(self.posSamples):
            raise ValueError(f"saveData error!")

        try:
            if len(self.negSamples) != 0:
                self.posSamples = np.array(self.posSamples)
                self.negSamples = np.array(self.negSamples)
                tempNegTotalNum = int(len(self.posLabel) / self.ratio)
                # self.small_part, self.large_part = train_test_split(self.negSamples, test_size=19 / 20, random_state=42)
                self.small_part, self.large_part = train_test_split(self.negSamples, train_size=tempNegTotalNum, random_state=42)
                self.negSamples = np.array([])
                # self.select_tmp = np.load("classifier/setBuild/sanbo_ds11_class4.npz")
                # self.large_part_label = self.select_tmp['label']
                # self.large_part = self.select_tmp['data'][self.large_part_label == 0]
                # self.small_part = self.negSamples
                print(f'posSamples: {self.posSamples.shape}, '
                      f'small_part: {self.small_part.shape}, large_part: {self.large_part.shape}')
                totalSample = np.concatenate((self.posSamples, self.small_part), axis=0)
                totalLabel = np.concatenate((self.posLabel, np.zeros(len(self.small_part))))
            else:
                totalSample = np.array(self.posSamples)
                totalLabel = self.posLabel
        except Exception as e:
            self.errorReason = '构建数据集包需的文件中，EEG通道数量不一致，请筛选后重新构建'
            print(e)
            self.isStop = True
            return
        print(f'totalSample: {totalSample.shape}, totalLabel: {totalLabel.shape}')

        # 对标签做一个映射
        # 找到唯一标签
        unique_labels = np.unique(totalLabel)
        # 创建映射字典，将唯一标签映射到 0~n
        label_mapping = {label: idx for idx, label in enumerate(unique_labels)}
        # 使用映射字典将原始标签转化为新的标签
        totalLabel = np.vectorize(label_mapping.get)(totalLabel)

        # 打乱标签
        shuffle_num = np.random.permutation(len(totalLabel))
        totalSample = totalSample[shuffle_num, :, :]
        totalLabel = totalLabel[shuffle_num]

        # self.select_tmp = np.load("classifier/setBuild/sanbo_ds11_class4.npz")
        # self.large_part_label = self.select_tmp['label']
        # self.large_part = self.select_tmp['data'][self.large_part_label == 0]

        sEpochs = 0
        epochs = 1

        # f1_score_macro_list = []
        # f1_score_list = []
        # accuracy_list = []
        # precision_list = []

        for i in range(sEpochs, sEpochs + epochs):
            starttime = datetime.datetime.now()

            print('Subject %d' % (i + 1))
            exp = ExP(i + 1)

            # bestAcc, averAcc, Y_true, Y_pred, \
            #     f1_score, f1_score_macro, acc, precision = exp.train(totalSample, totalLabel)
            # f1_score_list.append(f1_score)
            # f1_score_macro_list.append(f1_score_macro)
            # accuracy_list.append(acc)
            # precision_list.append(precision)

            exp.train(totalSample, totalLabel)
            # exp.train(None, None)

            # 计算删除后的数据
            # posSamples, posLabels, negSamples, negLabels = exp.merge_data(i)
            posSamples, posLabels = exp.merge_data(i)
            self.model = exp.model
            self.target_mean = exp.target_mean
            self.target_std = exp.target_std
            # self.wrong_class_num = exp.wrong_class_num
            self.wrong_class_num = 556

            self.posSamples = posSamples
            self.totalPosNum = len(self.posSamples)
            self.posLabel = posLabels
            # self.negSamples = negSamples
            print(f'posSamples: {posSamples.shape}, posLabel: {posLabels.shape}')
            # print('THE BEST ACCURACY IS ' + str(bestAcc))

            endtime = datetime.datetime.now()
            print('subject %d duration: ' % (i + 1) + str(endtime - starttime))

        # f1_score_macro_ave = sum(f1_score_macro_list) / len(f1_score_macro_list)
        # f1_score_ave = sum(f1_score_list) / len(f1_score_list)
        # accuracy_ave = sum(accuracy_list) / len(accuracy_list)
        # precision_ave = sum(precision_list) / len(precision_list)
        # print(f'f1_score_macro_list: {f1_score_macro_list}')
        # print(f'f1_score_list: {f1_score_list}')
        # print(f'accuracy_list: {accuracy_list}')
        # print(f'precision_list: {precision_list}')
        # print(f'f1_score_macro_ave: {f1_score_macro_ave}')
        # print(f'f1_score_ave: {f1_score_ave}')
        # print(f'accuracy_ave: {accuracy_ave}')
        # print(f'precision_ave: {precision_ave}')


class PatchEmbedding(nn.Module):
    def __init__(self, emb_size=40):
        # self.patch_size = patch_size
        super().__init__()
        self.channelScore = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=1, kernel_size=(1, 9),
                      stride=(1, 4), padding=(0, 4)),
            nn.Conv2d(in_channels=1, out_channels=1, kernel_size=(1, 9),
                      stride=(1, 4), padding=(0, 4)),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=(1, 8))
        )

        self.shallownet = nn.Sequential(
            nn.Conv2d(1, 40, (1, 32), (1, 1)),
            nn.Conv2d(40, 40, (22, 1), (1, 1)),
            nn.BatchNorm2d(40),
            nn.ELU(),
            nn.AvgPool2d((1, 64), (1, 8)),
            # pooling acts as slicing to obtain 'patch' along the time dimension as in ViT
            nn.Dropout(0.5),
        )

        self.shallownet1 = nn.Sequential(
            nn.Conv2d(1, 20, (1, 17), (1, 2), padding=(0, 8)),
            nn.Conv2d(20, 20, (22, 1), (1, 2)),
            nn.BatchNorm2d(20),
            nn.ELU(),
            nn.AvgPool2d((1, 32), (1, 8)),
            # pooling acts as slicing to obtain 'patch' along the time dimension as in ViT
            nn.Dropout(0.5),
        )

        self.shallownet2 = nn.Sequential(
            nn.Conv2d(1, 20, (1, 25), (1, 2), padding=(0, 12)),
            nn.Conv2d(20, 20, (22, 1), (1, 2)),
            nn.BatchNorm2d(20),
            nn.ELU(),
            nn.AvgPool2d((1, 32), (1, 8)),
            # pooling acts as slicing to obtain 'patch' along the time dimension as in ViT
            nn.Dropout(0.5),
        )

        self.shallownet3 = nn.Sequential(
            nn.Conv2d(1, 20, (1, 33), (1, 2), padding=(0, 16)),
            nn.Conv2d(20, 20, (22, 1), (1, 2)),
            nn.BatchNorm2d(20),
            nn.ELU(),
            nn.AvgPool2d((1, 32), (1, 8)),
            # pooling acts as slicing to obtain 'patch' along the time dimension as in ViT
            nn.Dropout(0.5),
        )

        self.projection = nn.Sequential(
            nn.Conv2d(60, emb_size, (1, 1), stride=(1, 1)),
            # transpose, conv could enhance fiting ability slightly
            Rearrange('b e (h) (w) -> b (h w) e'),
        )

    def forward(self, x: Tensor) -> Tensor:
        b, _, _, _ = x.shape
        # print(f'x1: {x.shape}')
        x = self.channelScore(x).expand(-1, -1, -1, 128) * x
        x1 = self.shallownet1(x)
        x2 = self.shallownet2(x)
        x3 = self.shallownet3(x)
        # print(f'x1: {x1.shape}, x2: {x2.shape}, x3: {x3.shape}')
        x = torch.cat((x1, x2, x3), dim=1)
        # print(f'x2: {x.shape}')
        x = self.projection(x)
        return x


class ClassificationHead(nn.Sequential):
    def __init__(self, emb_size, n_classes):
        super().__init__()

        self.clshead = nn.Sequential(
            Reduce('b n e -> b e', reduction='mean'),
            nn.LayerNorm(emb_size),
            nn.Linear(emb_size, n_classes)
        )
        self.fc = nn.Sequential(

            nn.Linear(60, 32),
            nn.ELU(),
            nn.Dropout(0.5),
            nn.Linear(32, n_classes)
        )

    def forward(self, x):
        x = x.contiguous().view(x.size(0), -1)
        out = self.fc(x)
        return x, out


class LSTMNet(nn.Module):
    def __init__(self, input_size=1, depth=1):
        super(LSTMNet, self).__init__()
        self.rnn = nn.LSTM(
            input_size=input_size,
            hidden_size=30,
            num_layers=depth,
            batch_first=True,
            bidirectional=True
        )

    def forward(self, x):
        r_out, (h_n, h_c) = self.rnn(x, None)  # None 表示 hidden state 会用全0的 state
        return r_out[:, -1]


class Conformer(nn.Sequential):
    def __init__(self, emb_size=60, depth=1, n_classes=4, **kwargs):
        super().__init__(
            PatchEmbedding(emb_size),
            LSTMNet(input_size=60, depth=depth),
            ClassificationHead(emb_size, n_classes)
        )


class ExP():
    def __init__(self, nsub):
        super(ExP, self).__init__()
        self.batch_size = 64
        self.n_epochs = 15
        self.lr = 0.0005
        self.b1 = 0.5
        self.b2 = 0.999
        self.nSub = nsub

        self.Tensor = torch.FloatTensor
        self.LongTensor = torch.LongTensor

        self.criterion_l1 = torch.nn.L1Loss()
        self.criterion_l2 = torch.nn.MSELoss()
        self.criterion_cls = torch.nn.CrossEntropyLoss()
        self.criterion_cls_none = torch.nn.CrossEntropyLoss(reduction='none')

        self.model = Conformer()
        # self.model = nn.DataParallel(self.model, device_ids=[i for i in range(len(gpus))])
        # self.model = self.model

    def get_source_data(self, totalSample=None, totalLabel=None):
        # train data
        if totalSample is None and totalLabel is None:
            total_data = np.load("classifier/setBuild/sanbo_ds11_class4_n2650.npz")
            self.train_data = total_data['data']
            self.train_label = total_data['label']
        else:
            self.train_data = totalSample
            self.train_label = totalLabel
        self.train_data = np.expand_dims(self.train_data, axis=1)
        print(f'self.train_data: {self.train_data.shape}')

        self.allData = self.train_data.copy()
        print(f'allData: {len(self.allData)}')
        self.allLabel = self.train_label.copy()

        # test data
        self.test_tmp = np.load("classifier/setBuild/sanbo_tds11_class4_n10000.npz")
        self.test_data = self.test_tmp['data']
        self.test_data = np.expand_dims(self.test_data, axis=1)
        self.test_label = self.test_tmp['label']

        self.testData = self.test_data
        self.testLabel = self.test_label
        self.test_label[self.test_label == 1] = 10
        self.test_label[self.test_label == 2] = 1
        self.test_label[self.test_label == 10] = 2

        # select data
        # self.select_tmp = np.load("classifier/setBuild/sanbo_ds11_class4.npz")
        # self.select_data = self.select_tmp['data']
        # self.select_data = np.expand_dims(self.select_data, axis=1)
        # self.select_label = self.select_tmp['label']
        #
        # self.selectData = self.select_data.copy()
        # self.selectLabel = self.select_label.copy()

        # standardize
        self.target_mean = np.mean(self.allData)
        self.target_std = np.std(self.allData)
        self.allData = (self.allData - self.target_mean) / self.target_std
        self.testData = (self.testData - self.target_mean) / self.target_std
        # self.selectData = (self.selectData - self.target_mean) / self.target_std
        # print(f'self.allData: {self.allData.shape}, self.testData: {self.testData.shape}, '
        #       f'self.selectData: {self.selectData.shape}')
        print(f'self.allData: {self.allData.shape}')
        # return self.allData, self.allLabel, self.testData, self.testLabel, self.selectData, self.selectLabel
        return self.allData, self.allLabel,self.testData, self.testLabel, np.array([]), np.array([])

    def train(self, totalSample, totalLabel):
        img, label, test_data, test_label, select_data, select_label = self.get_source_data(totalSample, totalLabel)

        img = torch.from_numpy(img)
        label = torch.from_numpy(label)

        np.savez(f'data/train_set/trainingset.npz', data=img.numpy(), label=label.numpy())

        counts = np.bincount(label)
        # 打印每个类别的数量
        for i in range(len(counts)):
            print(f"类别 {i}: {counts[i]} 个")

        exit()

        dataset = torch.utils.data.TensorDataset(img, label)
        self.dataloader = torch.utils.data.DataLoader(dataset=dataset, batch_size=self.batch_size, shuffle=False)

        test_data = torch.from_numpy(test_data)
        test_label = torch.from_numpy(test_label)

        counts = np.bincount(test_label)
        # 打印每个类别的数量
        for i in range(len(counts)):
            print(f"类别 {i}: {counts[i]} 个")

        test_dataset = torch.utils.data.TensorDataset(test_data.type(self.Tensor), test_label.type(self.LongTensor))
        self.test_dataloader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=self.batch_size,
                                                           shuffle=False)
        #
        # select_data = torch.from_numpy(select_data)
        # select_label = torch.from_numpy(select_label)
        # select_dataset = torch.utils.data.TensorDataset(select_data.type(self.Tensor),
        #                                                 select_label.type(self.LongTensor))
        # self.select_dataloader = torch.utils.data.DataLoader(dataset=select_dataset,
        #                                                      batch_size=self.batch_size,
        #                                                      shuffle=False)

        # Optimizers
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, betas=(self.b1, self.b2))

        # test_data = Variable(test_data.type(self.Tensor))
        # test_label = Variable(test_label.type(self.LongTensor))

        bestAcc = 0
        averAcc = 0
        num = 0
        Y_true = 0
        Y_pred = 0

        train_acc_list = []
        train_loss_list = []
        test_f1_list = []
        test_acc_list = []
        test_acc_micro_list = []
        test_loss_list = []
        test_f1_macro = []

        self.sample_losses = torch.zeros(self.allData.shape[0])
        print(f'sample_losses.shape: {self.sample_losses.shape}')

        for e in range(self.n_epochs):
            # in_epoch = time.time()
            y_train = torch.tensor([], dtype=torch.long)
            y_label = torch.tensor([], dtype=torch.long)
            train_loss = 0
            self.model.train()
            for i, (img, label) in enumerate(self.dataloader):
                img = Variable(img.type(self.Tensor))
                label = Variable(label.type(self.LongTensor))

                tok, outputs = self.model(img)
                loss = self.criterion_cls(outputs, label)
                loss_none = self.criterion_cls_none(outputs, label)

                train_loss += loss.item()
                _, o = torch.max(outputs.data, 1)
                y_train = torch.cat((y_train, o), dim=0)
                y_label = torch.cat((y_label, label), dim=0)

                # 更新样本的累积损失
                self.sample_losses[i * self.batch_size:(i + 1) * self.batch_size] += loss_none.detach()

                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

            # out_epoch = time.time()

            # test process
            if (e + 1) % 1 == 0:
                # train_acc = float(
                #     (y_train == y_label).cpu().numpy().astype(int).sum()) / float(
                #     y_label.size(0))
                # eResult = f"Epoch: {e}   " \
                #           f"Train loss: {train_loss / (i + 1):.6f}   " \
                #           f"Train accuracy: {train_acc:.6f}"
                # print(eResult)
                y_pred = torch.tensor([], dtype=torch.long)
                with torch.no_grad():
                    self.model.eval()
                    test_loss = 0
                    for batch_idx, (data, target) in enumerate(self.test_dataloader):
                        target = Variable(target.type(self.LongTensor))
                        _, o = self.model(data)
                        loss = self.criterion_cls(o, target)
                        _, o = torch.max(o.data, 1)
                        y_pred = torch.cat((y_pred, o), dim=0)
                        test_loss += loss.item()

                    acc = float(
                        (y_pred == test_label).cpu().numpy().astype(int).sum()) / float(
                        test_label.size(0))
                    y_train_np = y_train.cpu().numpy()
                    y_label_np = y_label.cpu().numpy()
                    train_acc = float(
                        (y_train == y_label).cpu().numpy().astype(int).sum()) / float(
                        y_label.size(0))
                    eResult = f"Epoch: {e}   " \
                              f"Train loss: {train_loss / (i + 1):.6f}   " \
                              f"Train accuracy: {train_acc:.6f}   " \
                              f"Test accuracy: {acc:.6f}"
                    print(eResult)
                    cm_train = confusion_matrix(y_label_np, y_train_np)
                    print(cm_train)
                    y_pred_np = y_pred.cpu().numpy()
                    test_label_np = test_label.cpu().numpy()

                    f1 = f1_score(test_label_np, y_pred_np, average='weighted')
                    print('F1-score: %.6f' % f1)
                    # 计算宏平均F1-score
                    f1_macro = f1_score(test_label_np, y_pred_np, average='macro')
                    print('Macro F1-score: %.6f' % f1_macro)
                    precision = precision_score(test_label_np, y_pred_np, average=None)
                    precision_micro = precision_score(test_label_np, y_pred_np,
                                                      average='micro')
                    print(f'Precision: {precision_micro}, each class: {precision}')

                    # 计算混淆矩阵
                    cm = confusion_matrix(test_label_np, y_pred_np)
                    print(cm)

                    # 计算每个类别的准确率
                    class_accuracy = cm.diagonal() / cm.sum(1)
                    for i, cacc in enumerate(class_accuracy):
                        print(f"Class {i} accuracy: {(cacc * 100):.2f}%")

                    num = num + 1
                    averAcc = averAcc + acc
                    if acc > bestAcc:
                        bestAcc = acc
                        Y_true = test_label
                        Y_pred = y_pred

                    # 将各个数据补充到 list 中
                    train_acc_list.append(train_acc)
                    train_loss_list.append(train_loss / (i + 1))
                    test_f1_list.append(f1)
                    test_f1_macro.append(f1_macro)
                    test_acc_list.append(acc)
                    test_loss_list.append(test_loss)
                    test_acc_micro_list.append(precision_micro)

        torch.save(self.model, f'model_ds10_m7_class4_v{self.nSub}.pth')
        np.savez(f'sanbo_ds10_m7_class4_loss_v{self.nSub}.npz', loss=self.sample_losses.cpu().numpy())
        # averAcc = averAcc / num
        # print('The average accuracy is:', averAcc)
        # print('The best accuracy is:', bestAcc)

        # return bestAcc, averAcc, Y_true, Y_pred, test_f1_list[-1], test_f1_macro[-1], \
        #     test_acc_list[-1], test_acc_micro_list[-1]

    def merge_data(self, version):
        print(f'merge_data version: {version}')
        loss = self.sample_losses.cpu().numpy()
        indices_of_zeros = np.where(self.train_label == 0)[0]
        print(f'Loss: {loss.shape}')
        data_of_zeros = loss[indices_of_zeros]

        # 确定要选择的元素数量（最小的 20%）
        n_top_20 = int(len(data_of_zeros) * 0.2)
        # 在标签为 0 的数据中找到最小 20% 的索引
        sorted_indices_of_zeros = np.argsort(data_of_zeros)[:n_top_20]
        # 获取这些最小值的原始索引
        final_indices = indices_of_zeros[sorted_indices_of_zeros]

        # 转换回列表
        wrong_class_indices = list(final_indices)
        self.wrong_class_num = len(wrong_class_indices)
        print("将要删除的样本数量:", len(wrong_class_indices))

        # 删除对应的样本
        train_data = self.train_data.copy()
        train_label = self.train_label.copy()
        train_data = np.delete(train_data, wrong_class_indices, axis=0)
        train_label = np.delete(train_label, wrong_class_indices, axis=0)

        # 确认删除后的数据大小
        print(f'train_data: {train_data.shape}, train_label: {train_label.shape}')
        counts = np.bincount(train_label.astype(np.int64))
        # 打印每个类别的数量
        for i in range(len(counts)):
            print(f"类别 {i}: {counts[i]} 个")

        # np.savez(f'sanbo_ds10_m7_class4_v{version}_temp.npz', data=train_data_new, label=label_new)

        wrong_class_num = len(wrong_class_indices)
        print(f'wrong_class_num: {wrong_class_num}')

        return np.squeeze(train_data, axis=1), train_label

        # np.set_printoptions(threshold=np.inf, suppress=True)

        # # 合并数据
        # combined_data = []
        # combined_labels = []
        #
        # combined_data.append(train_data)
        # combined_labels.append(train_label)
        # combined_data.append(selected_data)
        # combined_labels.append(selected_label)
        #
        # if combined_data:
        #     combined_data = np.concatenate(combined_data)
        #     combined_labels = np.concatenate(combined_labels)
        #
        # indices = np.arange(len(combined_labels))
        # np.random.shuffle(indices)
        # combined_data = combined_data[indices]
        # combined_labels = combined_labels[indices]
        # self.combined_data = combined_data
        # self.combined_labels = combined_labels
        #
        # counts = np.bincount(combined_labels.astype(np.int64))
        # # 打印每个类别的数量
        # for i in range(len(counts)):
        #     print(f"类别 {i}: {counts[i]} 个")
        #
        # print(f'combined_data: {combined_data.shape}, combined_labels: {combined_labels.shape}')
        # np.savez(f'sanbo_ds11_m7_class4_v{version}.npz', data=combined_data,label=combined_labels)
        # return np.squeeze(train_data, axis=1), train_label, np.squeeze(selected_data, axis=1), selected_label
