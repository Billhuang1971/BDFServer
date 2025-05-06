import ast
import os
import pickle
import sys

import mne
import numpy as np
import torch

from classifier.algorithms.alg import AlgorithmTemplate


class predictAlgorithm(AlgorithmTemplate):

    def __init__(self, modelFileName, eegFileName, time_stride, scan_file_channel_list, sample_rate, sample_len,
                 unitFactor, model_trained_sample_rate, alg_type, set_temp):
        super().__init__(modelFileName)
        self.eegFileName = eegFileName
        self.scan_file_channel_list = ast.literal_eval(scan_file_channel_list)
        self.sample_rate = int(sample_rate)
        self.sample_len = int(sample_len)
        self.unitFactor = int(unitFactor)
        self.raw = None
        self.file_channel = None
        self.predict_labels_list = None
        self.wave_save_batch_size = 1000
        self.state_save_batch_size = 10
        self.model_trained_sample_rate = int(model_trained_sample_rate)
        self.time_stride = np.round(
            float(time_stride) * self.sample_len / self.model_trained_sample_rate, decimals=1)
        self.state_predict = alg_type
        self.scan_label = []
        # path = os.path.join(os.path.dirname(__file__))[:-21]
        # set_dic_path = os.path.join(path, 'classifier\\', 'algorithms\\', 'set_dic.pkl')
        # events_dic_f = open(set_dic_path, 'rb')
        # set = pickle.load(events_dic_f)
        self.set_temp = ast.literal_eval(set_temp)
        print("---- set_temp", self.set_temp)
        counter = 1
        self.label_mapping = {}
        for i in self.set_temp:
            self.label_mapping[counter] = i
            counter += 1
        print("---- label_mapping", self.label_mapping)
        if not self.set_temp == set():
            self.import_model = False
        else:
            self.import_model = True
        print("---- import_model", self.import_model)

    def load_model(self, modelFile):
        print("load_model function is called")
        sys.stdout.flush()
        raise Exception

    def load(self):
        self.model = torch.load(self.modelFileName, weights_only=False)

    # 预测算法方法，实际运行需重写该方法
    def predict(self):
        print("predict function is called")
        sys.stdout.flush()
        raise Exception

    def run(self):
        self.channels = self.get_channels_name()
        self.load_model(self.modelFileName)
        # 获取待扫描脑电文件中的通道名称数组
        if self.state_predict == 'state':
            self.start_state_predict()
        # 波形标注
        else:
            self.start_wave_predict()
        self.result = True
        print("result:{}finished".format(self.result))

    # 获取raw中的通道名称
    def get_channels_name(self):
        raw = self.get_scanset_raw()
        included_channels = raw.info['ch_names']
        # print('input channel name:', included_channels)
        channel_new = []
        for item in included_channels:
            item = item.split(' ')
            channel_new.append(item[-1])
        # channel_new = ['Fp1-REF', 'F3-REF', ‘O1-REF’。。。。]仅表示通道存储形式，不代表实际存储数据内容
        # print('renamed channel name:', channel_new)
        return channel_new

    # 通过格式化脑电文件存储路径获取脑电文件的mne库中raw对象
    def get_scanset_raw(self):
        raw = mne.io.read_raw_bdf(input_fname=self.eegFileName)
        return raw

    # 开始波形标注
    def start_wave_predict(self):
        self.raw = self.get_scanset_raw()
        label_num = 0
        # 事件id随便设置就行
        event_id = 1
        # 维护2个起始点下标列表，一个对应脑电文件中的实际采样点下标，一个对应重采样后的脑电数据采样点下标
        self.epoch_start_point_list = mne.make_fixed_length_events(self.raw, event_id, duration=self.time_stride)
        self.epoch_start_point_list = self.epoch_start_point_list[:, 0].tolist()
        self.raw_timepoint_num = self.raw.n_times
        self.predict_labels_list = {}
        self.scanned_num = 0
        self.total_scan_num = len(self.epoch_start_point_list)
        for ch in self.scan_file_channel_list:
            self.predict_labels_list[ch] = np.array([])
        start_end_timepoints = []
        for s_t in self.epoch_start_point_list:
            self.scanned_num += 1
            # 将模型训练时的步长转化成与系统匹配的步长：如模型在外面训练时使用100HZ，30s步长为3000采样点的长度，系统内应用250Hz则是7500采样点的长度
            if self.model_trained_sample_rate < self.sample_rate:
                e_t = s_t + self.resample_timepoint(time_point=self.sample_len, target_sample_rate=self.sample_rate,
                                                    origin_sample_rate=self.model_trained_sample_rate)
                # r_st,r_et分别对应导入进来的模型训练时脑电数据的起始点和终点下标，比如一段30s的脑电数据系统内250Hz下是[0，7500），而模型训练时是100Hz对应[0,3000）
                r_st = self.resample_timepoint(time_point=s_t, target_sample_rate=self.model_trained_sample_rate,
                                               origin_sample_rate=self.sample_rate)
                r_et = self.resample_timepoint(time_point=e_t, target_sample_rate=self.model_trained_sample_rate,
                                               origin_sample_rate=self.sample_rate)

            else:
                e_t = s_t + self.sample_len

            # 判断预测段的终点是否越界
            if e_t < self.raw_timepoint_num:
                # 如果模型是在外部训练完成后导入到系统中的且使用数据集与系统中应用的采样率不一致，需要对数据重采样到模型训练时使用数据集的采样率
                if self.model_trained_sample_rate < self.sample_rate:
                    data = self.get_data_between(raw=self.resampled_raw, start=r_st, end=r_et)
                else:
                    data = self.get_data_between(raw=self.raw, start=s_t, end=e_t)

                data = self.get_measureData_conferenceData(channel_list=self.channels,
                                                           channel_subtract_list=self.scan_file_channel_list,
                                                           eeg_data=data)
                data *= self.unitFactor
                data = np.expand_dims(data, axis=1)
                # 开始预测,data:ndarray(1 * n_channels, n_samples)
                predict_labels = self.predict(data=data, channel_list=self.scan_file_channel_list)
                print(self.import_model)
                if not self.import_model:
                    predict_labels = self.label_reverser(predict_labels)
                # 将标签拼接在之前未保存的标签后面
                self.predict_labels_list = self.concatenate_wave_predict_label_list(self.predict_labels_list, predict_labels)
                self.scan_label = self.concatenate_predict_label_list(self.scan_label, predict_labels)
                start_end_timepoints = self.concatenate_start_end_timepoints(start_end_timepoints=start_end_timepoints,
                                                                             start=s_t, end=e_t)
                label_num += len(self.scan_file_channel_list)
            else:
                # 开始出现终点越界情况，后面的可以不用扫了
                break

            # 当标签个数满足存储条件时
            if label_num > self.wave_save_batch_size:
                label_num = 0
                self.store_wave_predictions(self.predict_labels_list, start_end_timepoints)
                # 标签保存，将临时保存数组清空
                self.predict_labels_list = {}
                for ch in self.scan_file_channel_list:
                    self.predict_labels_list[ch] = np.array([])
                start_end_timepoints = []

        # 所有数据都已扫描完毕，对剩余的标注进行保存
        if label_num > 0:
            self.store_wave_predictions(self.predict_labels_list, start_end_timepoints)

    def start_state_predict(self):
        self.raw = self.get_scanset_raw()
        # 事件id随便设置就行
        event_id = 1
        # 维护2个起始点下标列表，一个对应脑电文件中的实际采样点下标，一个对应重采样后的脑电数据采样点下标
        self.epoch_start_point_list = mne.make_fixed_length_events(self.raw, event_id, duration=self.time_stride)
        self.epoch_start_point_list = self.epoch_start_point_list[:, 0].tolist()
        self.raw_timepoint_num = self.raw.n_times
        self.predict_labels_list = []
        start_end_timepoints = []
        self.start_end_timepoints = []
        self.scanned_num = 0
        self.total_scan_num = len(self.epoch_start_point_list)
        for s_t in self.epoch_start_point_list:
            self.scanned_num += 1
            # 将模型训练时的步长转化成与系统匹配的步长：如模型在外面训练时使用100HZ，30s步长为3000采样点的长度，系统内应用250Hz则是7500采样点的长度
            if self.model_trained_sample_rate < self.sample_rate:
                e_t = s_t + self.resample_timepoint(time_point=self.sample_len, target_sample_rate=self.sample_rate,
                                                    origin_sample_rate=self.model_trained_sample_rate)
                # r_st,r_et分别对应导入进来的模型训练时脑电数据的起始点和终点下标，比如一段30s的脑电数据系统内250Hz下是[0，7500），而模型训练时是100Hz对应[0,3000）
                r_st = self.resample_timepoint(time_point=s_t, target_sample_rate=self.model_trained_sample_rate,
                                               origin_sample_rate=self.sample_rate)
                r_et = self.resample_timepoint(time_point=e_t, target_sample_rate=self.model_trained_sample_rate,
                                               origin_sample_rate=self.sample_rate)
                # 对原始脑电进行重采样，使其与模型训练时的脑电数据采样率保持一致
                self.resampled_raw = self.raw.resample(self.model_trained_sample_rate)
            else:
                e_t = s_t + self.sample_len

            # 判断预测段的终点是否越界
            if e_t < self.raw_timepoint_num:
                # 如果模型是在外部训练完成后导入到系统中的且使用数据集与系统中应用的采样率不一致，需要对数据重采样到模型训练时使用数据集的采样率
                if self.model_trained_sample_rate < self.sample_rate:
                    data = self.get_data_between(raw=self.resampled_raw, start=r_st, end=r_et)
                else:
                    data = self.get_data_between(raw=self.raw, start=s_t, end=e_t)
                data = self.get_measureData_conferenceData(channel_list=self.channels,
                                                           channel_subtract_list=self.scan_file_channel_list,
                                                           eeg_data=data)
                data *= self.unitFactor
                data = np.expand_dims(data, axis=0)

                # 开始预测,data:ndarray(1 * n_channels, n_samples)
                predict_labels = self.predict(data=data, channel_list=self.scan_file_channel_list)
                if not self.import_model:
                    predict_labels = self.label_reverser(predict_labels)
                # 将标签拼接在之前未保存的标签后面
                self.predict_labels_list = self.concatenate_predict_label_list(self.predict_labels_list, predict_labels)
                start_end_timepoints = self.concatenate_start_end_timepoints(start_end_timepoints=start_end_timepoints,
                                                                             start=s_t, end=e_t)
                # 被扫描脑电文件的全部标签
                self.scan_label = self.concatenate_predict_label_list(self.scan_label, predict_labels)
            else:
                # 开始出现终点越界情况，后面的可以不用扫了
                break
            # 当标签个数满足存储条件时
            if len(self.predict_labels_list) > self.state_save_batch_size:
                self.store_state_predictions(self.predict_labels_list, start_end_timepoints)
                # 标签保存，将临时保存数组清空
                self.predict_labels_list = []
                start_end_timepoints = []
        # 所有数据都已扫描完毕，对剩余的标注进行保存
        if len(self.predict_labels_list) > 0:
            self.store_state_predictions(self.predict_labels_list, start_end_timepoints)


    # channel_list:脑电文件中按照数据排列顺序的通道列表['A1-REF', 'O1-REF'....]
    # channel_subtract_list = ['A1-REF', 'O1-AV'.....] 你需要数据按照怎样的导联减集方式进行相减操作的导联减集列表
    # eeg_data = np.array 是通过raw.get_data()得到的数据，请确保raw对象是直接从edf文件中读取出来的原始raw,或者是原始raw的copy
    def get_measureData_conferenceData(self, channel_list, channel_subtract_list, eeg_data):
        tmp = []
        for ch in channel_list:
            tmp.append(ch.split('-')[0])
        channel_list = tmp
        eeg_data = eeg_data.copy()
        # 计算平均时排除
        excluded_channel_list = ['Ldelt1', 'Ldelt2', 'Rdelt1', 'Rdelt2', 'A1', 'A2', 'M1', 'M2', 'LOC', 'ROC',
                                 'CHIN1', 'CHIN2', 'ECGL', 'ECGR', 'LAT1', 'LAT2', 'RAT1', 'RAT2',
                                 'CHEST', 'ABD', 'FLOW', 'SNORE', 'DIF5', 'DIF6']
        temp_data = eeg_data.copy()
        ex_chs_idx = tuple([channel_list.index(x) for x in excluded_channel_list if x in channel_list])
        temp_data = np.delete(temp_data, ex_chs_idx, axis=0)
        av_data = np.mean(temp_data, axis=0)
        m_first = True
        c_first = True
        s_first = True
        measure_channel_list = []
        conference_channel_list = []
        for c_s in channel_subtract_list:
            c_s = c_s.split('-')
            measure_channel_list.append(c_s[0])
            conference_channel_list.append((c_s[1]))

        for m_ch in measure_channel_list:
            if m_first:
                m_first = False
                measure_data = np.expand_dims(eeg_data[channel_list.index(m_ch)], axis=0)
            else:
                measure_data = np.concatenate(
                    (measure_data, np.expand_dims(eeg_data[channel_list.index(m_ch)], axis=0)), axis=0)

            measure_data = measure_data.reshape(-1, eeg_data.shape[-1])

        for c_ch in conference_channel_list:
            if c_first:
                c_first = False
                if c_ch == 'REF':
                    conference_data = np.expand_dims(np.zeros(eeg_data.shape[-1]), axis=0)
                elif c_ch == 'AV':
                    conference_data = np.expand_dims(av_data, axis=0)
                else:
                    conference_data = np.expand_dims(eeg_data[channel_list.index(c_ch)], axis=0)

            else:
                if c_ch == 'REF':
                    conference_data = np.concatenate(
                        (conference_data, np.expand_dims(np.zeros(eeg_data.shape[-1]), axis=0)), axis=0)
                elif c_ch == 'AV':
                    conference_data = np.concatenate((conference_data, np.expand_dims(av_data, axis=0)), axis=0)
                else:
                    conference_data = np.concatenate(
                        (conference_data, np.expand_dims(eeg_data[channel_list.index(c_ch)], axis=0)), axis=0)

        for i in range(len(measure_channel_list)):
            if s_first:
                s_first = False
                subtracted_data = np.expand_dims(measure_data[i] - conference_data[i], axis=0)
            else:
                subtracted_data = np.concatenate(
                    (subtracted_data, np.expand_dims(measure_data[i] - conference_data[i], axis=0)), axis=0)

        return subtracted_data

    def get_data_between(self, raw, start, end):
        """
        从mne中的raw对象中获取介于start和end采样点坐标之间的data。

        参数：
        raw: mne.io.Raw对象，表示原始数据。
        start: int，开始采样点的坐标。
        end: int，结束采样点的坐标。

        返回：
        numpy数组，形状为(通道数, end - start)。
        """
        data, _ = raw[:, start:end]
        return data

    def resample_timepoint(self, time_point: int, target_sample_rate: int, origin_sample_rate: int):
        time_point = time_point * target_sample_rate / origin_sample_rate
        return int(time_point)

    def concatenate_predict_label_list(self, predict_label_list, predict_labels):
        if not type(predict_labels) == type(np.array([])):
            predict_labels = np.array([predict_labels], dtype=object)
        if len(predict_label_list) < 1:
            predict_label_list = predict_labels
        else:
            predict_label_list = np.concatenate((predict_label_list, predict_labels), axis=0)
        return predict_label_list

    # 拼接每一段脑电的起点终点采样点下标，用于后面做批量存储
    # start_end_timepoints = [[st,et],[st,et].....]
    def concatenate_start_end_timepoints(self, start_end_timepoints, start, end):
        s_e = np.expand_dims(np.array([start, end]), axis=0)
        if len(start_end_timepoints) < 1:
            start_end_timepoints = s_e
        else:
            start_end_timepoints = np.concatenate((start_end_timepoints, s_e), axis=0)
        return start_end_timepoints

    def concatenate_wave_predict_label_list(self, predict_label_list, predict_labels):
        i = 0
        for ch in predict_label_list:
            if len(predict_label_list[ch]) < 1:
                predict_label_list[ch] = np.array([predict_labels[i]])
            else:
                predict_label_list[ch] = np.concatenate((predict_label_list[ch], np.array([predict_labels[i]])))
            i += 1
        return predict_label_list

    # 状态标注标签保存
    def store_state_predictions(self, predictions, start_end_timepoints):
        predict_dic = {'channels': {
            'all': predictions
        },
            'start_end_timepoints': start_end_timepoints,
            'scanned_num': self.scanned_num,
            'total_scan_num': self.total_scan_num}
        path = os.path.join(os.path.dirname(__file__))
        scan_result_filepath = os.path.join(path, 'predict.pkl')
        self.save_predict_result(predict_dic=predict_dic, file_path=scan_result_filepath)
        self.scanned_num = 0
        # 读取数据库存储进程信息反馈
        input = read_input()
        while not 'complete' in input:
            input = read_input()
        print(input)
        sys.stdout.flush()

    # 波形标注标签保存

    def store_wave_predictions(self, predictions, start_end_timepoints):
        predict_dic = {'channels': {},
                       'start_end_timepoints': start_end_timepoints,
                       'scanned_num': self.scanned_num,
                       'total_scan_num': self.total_scan_num}
        predict_dic['channels'] = predictions
        self.scanned_num = 0
        path = os.path.join(os.path.dirname(__file__))
        scan_result_filepath = os.path.join(path, 'predict.pkl')
        self.save_predict_result(predict_dic=predict_dic, file_path=scan_result_filepath)
        input_value = read_input()
        while True:
            if input_value.find("complete") != -1:
                break
            else:
                input_value = read_input()
        print("当前批次存储完成")

    def save_predict_result(self, predict_dic, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(predict_dic, f)
            f.close()
        print('开始进行数据库存储\n')
        sys.stdout.flush()

    def label_reverser(self, predict_labels):
        for i in range(len(predict_labels)):
            if predict_labels[i] == 0:
                continue
            predict_labels[i] = self.label_mapping[predict_labels[i]]
        return predict_labels


# 接受数据库存储进程的信息，读取写入流
def read_input():
    data = sys.stdin.readline().strip()
    return data

