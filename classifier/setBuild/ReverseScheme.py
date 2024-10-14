import random

import numpy as np
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from mne.io import read_raw_edf


class reverseScheme(QObject):
    # 反例生成信号,生成一条,进度条数值加1
    gen_done_signal = pyqtSignal(int)

    def __init__(self, DbUtil=None, r_num=None, Ref=None, montage=None, file_name=None, file_length=None,
                 reverseLength=None,
                 addType=None, isType=None, multiple=None, file_exit_montage=None, file_path=None, montage_scheme=None,
                 set_build_thread=None, model=None, sub_model=None):
        """
        :param DbUtil: 数据库类工具对象
        :param Ref: 参考方案
        :param r_num: 要生成的反例数量
        :param montage: 在哪些导联中进行挑选
        :param montage_scheme: 当前使用的导联
        :param file_name: 要挑选反例的文件名
        :param file_length: 要挑选反例的文件的长度（单位为采样点个数）
        :param reverseLength: 反例长度
        :param addType: 已添加的正例（要求生成的反例不含正例类型）
        :param isType: 要返回的反例是波形还是状态 TRUE为波形 False为状态
        :param multiple:  毫秒与采样率的倍率，如采样率250hz 即1000ms内采样250次，倍率为1000/250=4
        :param file_exit_montage: 文件中存在的导联
        :param file_path: 文件路径
        :param set_build_thread: 构建集合线程的对象
        :param model: 主模型路径:str
        :param sub_model: 多个子模型路径:dict
        """
        super().__init__()
        self.DbUtil = DbUtil
        self.Ref = Ref
        self.r_num = int(r_num)
        self.montage = montage
        self.montage_scheme = montage_scheme
        self.file_name = file_name
        self.file_exit_montage = file_exit_montage
        self.file_length = file_length
        self.reverseLength = reverseLength
        self.addType = addType
        self.isType = isType
        self.multiple = multiple
        self.file_path = file_path
        self.set_build_thread = set_build_thread
        self.model = model
        self.sub_model = sub_model

    def random_scheme(self):
        reverseSample = []
        n = 0
        failed_times = 0
        while n < self.r_num:
            if failed_times >= 10:
                return []
            if self.isType:
                montage_random = random.randint(0, len(self.montage) - 1)
                selected_montage = self.montage[montage_random]
                if self.montage_scheme != 'Default':
                    G1 = selected_montage.split('-')[0] + '-REF'
                    G2 = selected_montage.split('-')[1] + '-REF'
                    if G2 != 'AV-REF':
                        if G1 not in self.file_exit_montage or G2 not in self.file_exit_montage:
                            continue
                    else:
                        if G1 not in self.file_exit_montage:
                            continue
            else:
                selected_montage = 'all'
            file_length = int(self.file_length)
            begin = random.randint(0, file_length)
            end = begin + self.reverseLength
            if end > file_length:
                continue
            # begin /= self.multiple
            # end /= self.multiple
            begin = int(begin)
            end = int(end)
            check_set = (self.file_name, begin, end, selected_montage)
            # print(check_set)
            sample = self.DbUtil.ReverseSample_check(check_set)
            if len(sample) == 0:
                reverseSample.append(check_set)
                print(check_set)
                failed_times = 0
                n += 1
                continue
            else:
                m = 0
                for item in sample:
                    if item[4] in self.addType.values():
                        failed_times += 1
                        break
                    else:
                        m += 1
                    if m == len(sample):
                        reverseSample.append(check_set)
                        print(check_set)
                        failed_times = 0
                        n += 1
        return reverseSample

    def cut_data_from_file(self, sample):
        """
        工具方法：根据随机抽取出来的索引从脑电中切出脑电片段
        """
        reverse_sample = []
        file = read_raw_edf(input_fname=self.file_path)
        # file = crop(tmin=begin / 1000, tmax=end / 1000)
        for item in sample:
            eeg = file.copy()
            begin = item[1]
            end = item[2]
            channel = item[3]
            begin = begin * self.multiple / 1000
            end = end * self.multiple / 1000
            try:
                eeg = eeg.crop(tmin=begin, tmax=end)
            except:
                continue
            eeg.load_data()
            eeg = eeg.to_data_frame()
            if self.Ref != 'Default':
                eeg, tag = self.set_build_thread.ModifyEEG_By_Ref(data=eeg, channel=channel, file_name=self.file_name)
                if tag is False:
                    return None
            eeg = self.set_build_thread.generate_per_sample_list(mr_data=eeg, channel=channel)
            reverse_sample.append(eeg)
        reverse_sample = np.array(reverse_sample)

        return reverse_sample


if __name__ == '__main__':
    re = reverseScheme(r_num=1)
    a = re.ea_recog_Scheme(alg_class_name="Conformer", alg_path="data.temp_alg_fold.alg")
