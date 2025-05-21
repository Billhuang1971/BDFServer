import os
import pickle

import torch

from classifier.algorithms.alg import AlgorithmTemplate


class trainAlgorithm(AlgorithmTemplate):

    def __init__(self, modelFileName, trainingSetFilename):
        super().__init__(modelFileName)
        self.trainingSetFilename = trainingSetFilename
        self.train_performance = None
        self.train_set = None
        self.train_label = None
        # path = os.path.join(os.path.dirname(__file__))[:-11]
        # set_dic_path = os.path.join(path, 'algorithms\\', 'set.pkl')
        # events_dic_f = open(set_dic_path, 'rb')
        # set = pickle.load(events_dic_f)
        # self.set_temp = set['set_temp']
        # self.set_class = set['set_class']
        # events_dic_f.close()

    # 虚函数重写
    def train(self):
        pass

    def save(self):
        torch.save(self.model, self.modelFileName)

    # 系统构建数据集中的标签并非从0开始，甚至标签序号不连续，实际训练或测试过程中我们在计算损失值的时候需要我们的标签时从0开始且连续。
    # 该方法用于将数据集的标签调整为从0开始且每个类别的标签时连续的
    # def label_transfer(self, label_set):
    #     # 原始标签数组
    #     original_labels = label_set
    #     # 创建标签映射字典,{训练时使用标签：数据库中存储标签}
    #     label_mapping = {}
    #     new_labels = []
    #     # 0标签是负例标签，所以从1开始排序
    #     if len(self.set_temp) == self.set_class:
    #         counter = 0
    #     else:
    #         counter = 1
    #     # 遍历原始标签数组
    #     # print(self.label_name)
    #     # sys.stdout.flush()
    #     for label in self.set_temp:
    #         # 检查标签是否已经在映射字典中
    #         if label not in label_mapping and label != 0:
    #             # # WAKE状态标注当成负例处理
    #             # if label == 33:
    #             #     continue
    #             # 若标签不在映射字典中，则将其映射为当前计数器的值，并将计数器加1
    #             label_mapping[label] = counter
    #             counter += 1
    #     # 将原始标签转换为新的连续标签
    #     for i in range(len(label_set)):
    #         if label_set[i] == 0:
    #             continue
    #         # # WAKE状态标注当成负例处理
    #         # if label_set[i] == 33:
    #         #     label_set[i] = 0
    #         #     continue
    #         label_set[i] = label_mapping[label_set[i]]
    #     # print("原始标签数组:", original_labels)
    #     # print("转换后的标签数组:", label_set)
    #     # print("标签映射字典:", label_mapping)
    #     # sys.stdout.flush()
    #     return label_set

    def run(self):
        self.train_set, self.train_label = self.get_dataset(self.trainingSetFilename)
        # self.train_label = self.label_transfer(self.train_label)
        self.train()
        self.save()
        self.result = True
        print("train_performance:{}finish, result:{}finished".format(self.train_performance, self.result))

