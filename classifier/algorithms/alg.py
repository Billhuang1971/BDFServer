import sys

import numpy as np


class AlgorithmTemplate(object):

    def __init__(self, modelFileName=None):
        self.modelFileName = modelFileName
        self.result = False

    # 实际使用需重写该方法
    def run(self):
        print('run function is called')
        sys.stdout.flush()
        raise Exception

    def get_dataset(self, dataset_file_name, ratio=1):
        try:
            dataset = np.load(dataset_file_name, allow_pickle=True)
            set_key = None
            label_key = None
            c_train = np.zeros((1, 1))
            c_rlabel = np.zeros((1, 1))
            for i in dataset.keys():
                if i[0] == 'd':
                    set_key = i
                elif i[0] == 'l':
                    label_key = i
            c_train = dataset[set_key]
            # c_train = dataset[:int(c_train.shape[0] * ratio), :]

            c_rlabel = dataset[label_key]
            for i in range(len(c_rlabel)):
                if c_rlabel[i] == -1:
                    c_rlabel[i] = 0
            # c_rlabel = c_rlabel[:int(c_rlabel.shape[0] * ratio)]

            return c_train, c_rlabel
        except Exception as e:
            print('get_dataset', e)