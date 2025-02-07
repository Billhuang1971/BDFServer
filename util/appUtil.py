import ast
import datetime

import json

import os
import time, shutil
import re
import mne
import pyedflib
import pypinyin
import numpy as np
import urllib
import urllib.request
import smtplib
from email.mime.text import MIMEText

class appUtil():
    def __init__(self, dbUtil):
        self.root_path=os.path.dirname(os.path.dirname(__file__))+'\\'
        self.algorithm_path = self.root_path + 'client_root\\classifier\\'
        self.dbUtil = dbUtil
        self.model_path = os.path.join(self.root_path,'classifier\\models\\')

    def get_now_datetime(self):
        """
        @Description: 返回当前时间，格式为：年月日时分秒
        """
        return time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime(time.time()))

    def get_now_time(self):
        """
        @Description: 返回当前时间，格式为：时分秒
        """
        return time.strftime('%H-%M-%S', time.localtime(time.time()))

    def get_now_date(self):
        """
        @Description: 返回当前时间，格式为：年月日
        """
        return time.strftime('%Y-%m-%d', time.localtime(time.time()))

    # srcfile 需要复制、移动的文件
    # dstpath 目的地址
    def mymovefile(self, srcfile, dstpath):  # 移动函数
        if not os.path.isfile(srcfile):
            print("%s not exist!" % (srcfile))
        else:
            fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
            if not os.path.exists(dstpath):
                os.makedirs(dstpath)  # 创建路径
            shutil.move(srcfile, dstpath + fname)  # 移动文件
            print("move %s -> %s" % (srcfile, dstpath + fname))

    # srcfile 需要复制、移动的文件
    # dstpath 目的地址
    def mycopyfile(self, srcfile, dstpath):  # 复制函数
        if not os.path.isfile(srcfile):
            print("%s not exist!" % (srcfile))
        else:
            fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
            if not os.path.exists(dstpath):
                os.makedirs(dstpath)  # 创建路径
            shutil.copy(srcfile, dstpath + fname)  # 复制文件
            print("copy %s -> %s" % (srcfile, dstpath + fname))

    # 将文件大小转化为带单位的文件大小
    def convert_size(self, text):
        """
        文件大小单位换算
        :text: 文件字节
        :return: 返回字节大小对应单位的数值
        """
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024
        for i in range(len(units)):
            if (text / size) < 1:
                return "%.2f%s" % (text, units[i])  # 返回值保留小数点后两位
            text = text / size

    # 分离文件名和文件后缀
    def GetFileNameAndExt(self, filename):
        (filepath, tempfilename) = os.path.split(filename);
        (shotname, extension) = os.path.splitext(tempfilename);
        return shotname, extension

    # 从source_dir目录下查找是否存在文件名（不含后缀）为filename的文件，并返回其文件名和文件后缀
    def GetFileNameAndExt_from_dir_byName(self, filename, source_dir):
        ##1.将指定A目录下的文件名取出,并将文件名文本和文件后缀拆分出来
        img = os.listdir(source_dir)  # 得到文件夹下所有文件名称
        s = []

        for fileNum in img:  # 遍历文件夹
            if not os.path.isdir(fileNum):  # 判断是否是文件夹,不是文件夹才打开
                # print(fileNum)  # 打印出文件名
                imgname = os.path.join(source_dir, fileNum)
                # print(imgname)  # 打印出文件路径
                (imgpath, tempimgname) = os.path.split(imgname);  # 将路径与文件名分开
                (shotname, extension) = os.path.splitext(tempimgname);  # 将文件名文本与文件后缀分开
                if shotname == filename:
                    # print(shotname, extension)
                    return shotname, extension

    def GetSocketIpFile(self):
        f = open('service/server.txt')
        d = f.readline()
        f.close()
        sysd = eval(d)
        s_ip = sysd['server_ip']
        s_port = sysd['server_port']
        return s_ip, s_port

    def GetMysqlInfo(self):
        f = open('service/server.txt')
        d = f.readline()
        f.close()
        sysd = eval(d)
        return sysd

    # 整合laod_dataDynamical中打开文件、读文件关闭文件
    def readEEG(self, check_id, file_id, t_min, t_max, nSmaple):
        # 打开文件
        try:
            package='{:>011}'.format(check_id)
            fileNm = '{:>03}.bdf'.format(file_id)
            path = os.path.join(self.root_path,'data', 'formated_data', package, fileNm)
            # 读取BDF文件标识
            with pyedflib.EdfReader(path) as reader:
                # 内部属性包含 recording 字段
                recording_field = reader.recording
                print("Recording Field:", recording_field)
            # 转换为字符串
            recording_str = recording_field.decode("ascii")
            # 提取最后一个部分（按空格分割后取最后一个部分）
            recording_additional = recording_str.split()[-1]
            # print("Extracted Recording Additional Info:", recording_additional)
            local_raw = mne.io.read_raw_bdf(path)
        except (IOError,OSError) as err:
            print(f"openEEGFile：except={err}")
            return ['0', f'读数据块raw_copy不成功:{err}.']
        try:
            local_channels = local_raw.info['ch_names']
            local_sampling_rate = int(local_raw.info['sfreq'])
            local_index_channels = mne.pick_channels(local_channels, include=[])
        except Exception as err:
            local_raw.close()
            print(f"openEEGFile：读EEG文件头异常={err}")
            return ['0', f'读数据块raw_copy不成功:{err}.']

        # 读文件
        try:
            raw_copy = local_raw.copy()
            data, _ = raw_copy[local_index_channels, t_min: t_max]
            data = data * pow(10, 6)
            data = data[:, ::nSmaple]
            ret = ['1', data, local_sampling_rate,recording_additional]
            print(f"readEEGfile：ok:len(data)={len(data)}")
        except Exception as e:
            ret = ['0', f'读数据块raw_copy不成功:{e}.']

        # 关闭文件
        local_raw.close()
        return ret

    def closeEEGfile(self,raw):
        raw.close()
        return

    def readEEGfileXXX(self, raw,t_index_channels, _tmin, _t_max):
        try:
            raw_copy = raw.copy()
            if _tmin != -1:
                if _t_max == -1:
                    raw_copy.crop(tmin=_tmin, include_tmax=True)
                else:
                    raw_copy.crop(tmin=_tmin, tmax=_t_max)
            raw_copy.load_data()
            data, times = raw_copy[t_index_channels, :]
            data = data * (pow(10, 4))
            # data = data * 1037
            ret = ['1', data, times]
            print(f"readEEGfile：ok:len(data)={len(data)}:{times}")
        except Exception as e:
            ret = ['0', f'读数据块raw_copy不成功:{e}.']
        return ret

    def readEEGfile(self, raw, t_index_channels, _tmin, _t_max):
        try:
            raw_copy = raw.copy()
            sfreq = raw.info['sfreq']
            if _tmin != -1:
                if _t_max == -1:
                    # 处理到末尾的情况
                    start_sample = int(_tmin * sfreq)
                    end_sample = raw.n_times  # 直接取到文件末尾
                else:
                    # 计算要截取的数据范围
                    start_sample = int(_tmin * sfreq)
                    end_sample = int(_t_max * sfreq)
            else:
                # 如果 _tmin 为 -1，直接返回全部数据
                start_sample = 0
                end_sample = raw.n_times
            # 检查边界防止越界
            if start_sample < 0 or end_sample > raw.n_times:
                raise ValueError("时间范围超出数据长度！")
            # 获取指定通道和范围的数据
            data, times = raw_copy[t_index_channels, start_sample:end_sample]
            data = data * (pow(10, 4))
            ret = ['1', data, times]
            print(f"readEEGfile：ok:len(data)={len(data[0])}, times={times[-1]}")
        except Exception as e:
            # 捕获异常返回错误信息
            ret = ['0', f'读数据块raw_copy不成功: {e}.']
        return ret

    def openEEGFile(self, check_id, file_id):
        try:
            package='{:>011}'.format(check_id)
            fileNm = '{:>03}.bdf'.format(file_id)
            path = os.path.join(self.root_path,'data', 'formated_data', package, fileNm)
            local_raw = mne.io.read_raw_bdf(path)
        except (IOError,OSError) as err:
            ret = ['0', '打开EEG文件无效', path]
            print(f"openEEGFile：except={err}")
            return ret
        try:
            local_channels = local_raw.info['ch_names']
            local_index_channels = mne.pick_channels(local_channels, include=[])
            local_sampling_rate = int(local_raw.info['sfreq'])
            local_n_times = local_raw.n_times
            local_duration = int(local_n_times // local_sampling_rate)
            meas_date = local_raw.info['meas_date']
            if isinstance(meas_date, tuple):
                meas_date = datetime.datetime.fromtimestamp(meas_date[0])
            local_start_time = meas_date.strftime('%H:%M:%S')
            local_end_time = meas_date + datetime.timedelta(seconds=local_duration)
            local_end_time = local_end_time.strftime('%H:%M:%S')

            ret = ['1', local_channels, local_index_channels,
               local_sampling_rate, local_n_times, local_duration, local_start_time, local_end_time]
            local_raw.close()
            return ret
        except Exception as err:
            local_raw.close()
            print(f"openEEGFile：读EEG文件头异常={err}")
            return ['0', f'读EEG文件头异常:{err}']

    def sendPhoneMsg(self,phone,content):
       statusStr = {
             '0': '短信发送成功',
             '-1': '参数不全',
             '-2': '服务器空间不支持,请确认支持curl或者fsocket,联系您的空间商解决或者更换空间',
             '30': '密码错误',
             '40': '账号不存在',
             '41': '余额不足',
             '42': '账户已过期',
             '43': 'IP地址限制',
             '50': '内容含有敏感词'}
       smsapi = "http://api.smsbao.com/"
       user = 'fyyyfz'
       #md5('dsj123456')
       password = '39b54cd8a6047b8f6dad8e6249ad9043'
       # 要发送的短信内容
       #content = '短信内容:诊断结果，病人'
       # 要发送短信的手机号码
       #phone = '18060475815'
       try:
         content="【脑电智能平台】"+content
         data = urllib.parse.urlencode({'u': user, 'p': password, 'm': phone, 'c': content})
         send_url = smsapi + 'sms?' + data
         response = urllib.request.urlopen(send_url)
         ret = response.read().decode('utf-8')
         if ret=='0':
            return '1', statusStr[ret]
         else:
            return ret, statusStr[ret]
       except Exception as err:
         return '-3', f'{err}'


    def sendEmail(self,rcv,content):
        mail_host = 'smtp.sina.com'
        mail_user = 'coding8@sina.com'
        mail_pass = '131e9643c34bf574'
        sender = 'coding8@sina.com'
        receivers = rcv

        message = MIMEText(content, 'plain', 'utf-8')
        message['Subject'] = '脑电智能平台：诊断信息通知'
        message['From'] = sender
        message['To'] = receivers[0]
        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_host, 25)
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
            return '1',None
        except smtplib.SMTPException as e:
            return '0',f"error:{e}"

    def getMontage(self):
        try:
            with open('data/config.json', "r", encoding='utf8') as fp:
                data = json.load(fp)
                montageData = data.get('montages')
                fp.close()
                return '1',montageData
        except (IOError, OSError) as err:
            #print('getMontage', err)
            return '0', '打开导联文件文件无效'


    def addMontageScheme(self, scheme_name, channels=[]):
        try:
            with open('data/config.json', "r", encoding='utf8') as fp:
                data = json.load(fp)
                fp.close()
            with open('data/config.json', "w", encoding='utf8') as fp:
                new_montage_scheme = {'name': scheme_name, 'channels': channels}
                data['montages'].append(new_montage_scheme)
                json.dump(data, fp, ensure_ascii=False)
                fp.close()
                ret = ['1', '添加导联方案成功']
                return ret
        except (IOError, OSError) as err:
            print('addMontageScheme', err)
            ret = ['0', '打开导联文件文件无效']
            return ret

    def editMontageScheme(self, where_name, set_name):
        try:
            with open('data/config.json', "r", encoding='utf8') as fp:
                data = json.load(fp)
                fp.close()
            with open('data/config.json', "w", encoding='utf8') as fp:
                for i in range(len(data['montages'])):
                    if data['montages'][i]['name'] == where_name:
                        # print(data['montages'][i]['name'])
                        data['montages'][i]['name'] = set_name
                        break
                json.dump(data, fp, ensure_ascii=False)
                fp.close()
                ret = ['1', '编辑导联方案成功']
                return ret
        except (IOError, OSError) as err:
            print('editMontageScheme', err)
            ret = ['0', '打开导联文件文件无效']
            return ret

    def delMontageScheme(self, where_name):
        try:
            with open('data/config.json', "r", encoding='utf8') as fp:
                data = json.load(fp)
                fp.close()
            with open('data/config.json', "w", encoding='utf8') as fp:
                for i in range(len(data['montages'])):
                    if data['montages'][i]['name'] == where_name:
                        del_index = i
                        break
                del data['montages'][del_index]
                json.dump(data, fp, ensure_ascii=False)
                fp.close()
                ret = ['1', '删除导联方案成功']
                return ret
        except (IOError, OSError) as err:
            print('delMontageScheme', err)
            ret = ['0', '打开导联文件文件无效']
            return ret

    def saveMontageChannel(self, where_name, channels):
        try:
            with open('data/config.json', "r", encoding='utf8') as fp:
                data = json.load(fp)
                fp.close()
            with open('data/config.json', "w", encoding='utf8') as fp:
                for i in range(len(data['montages'])):
                    if data['montages'][i]['name'] == where_name:
                        data['montages'][i]['channels'] = channels
                        break
                json.dump(data, fp, ensure_ascii=False)
                fp.close()
                ret = ['1', '保存导联方案通道成功']
                return ret
        except (IOError, OSError) as err:
            print('saveMontageChannel', err)
            ret = ['0', '打开导联文件文件无效']
            return ret


    # 脑电导入模块
    # 实现生成文件名功能
    def makeFilePath(self,check_number):
        """
        根据 check_number 查询 file_info 表，生成文件名。
        文件名格式为：check_id（左填充11位） + '_' + file_id（左填充3位）。
        file_id 为现有最大值加1。

        :param check_number: 表单号。
        :return: 生成的文件名和新文件ID。
        """
        # 查询 file_info 表获取所有 file_id
        rp, file_list , check_id = self.dbUtil.get_fileInfoByCheckNumber(check_number)

        # 如果 file_list 不为空，取最大 file_id，否则从1开始
        max_file_id = max((int(f[1]) for f in file_list), default=0)
        new_file_id = max_file_id + 1

        # 格式化文件名
        filename = f"{str(check_id).rjust(11, '0')}_{str(new_file_id).rjust(3, '0')}"
        return filename, new_file_id ,check_id

    # 整合laod_dataDynamical中打开文件、读文件关闭文件
    # def readEEG(self, check_id, file_id, _t_min, _t_max):
    #     # 打开文件
    #     try:
    #         package = '{:>011}'.format(check_id)
    #         fileNm = '{:>03}.bdf'.format(file_id)
    #         path = os.path.join(self.root_path, 'BDFServer', 'data', 'formated_data', package, fileNm)
    #         local_raw = mne.io.read_raw_bdf(path)
    #     except (IOError, OSError) as err:
    #         ret_1 = ['0', '打开EEG文件无效', path]
    #         print(f"openEEGFile：except={err}")
    #     try:
    #         local_channels = local_raw.info['ch_names']
    #         local_index_channels = mne.pick_channels(local_channels, include=[])
    #         local_sampling_rate = int(local_raw.info['sfreq'])
    #         local_n_times = local_raw.n_times
    #         local_duration = int(local_n_times // local_sampling_rate)
    #         meas_date = local_raw.info['meas_date']
    #         if isinstance(meas_date, tuple):
    #             meas_date = datetime.datetime.fromtimestamp(meas_date[0])
    #         local_start_time = meas_date.strftime('%H:%M:%S')
    #         local_end_time = meas_date + datetime.timedelta(seconds=local_duration)
    #         local_end_time = local_end_time.strftime('%H:%M:%S')
    #
    #         ret_1 = ['1', local_raw, local_channels, local_index_channels,
    #                  local_sampling_rate, local_n_times, local_duration, meas_date, local_start_time,
    #                  local_end_time]
    #     except Exception as err:
    #         ret_1 = ['0', f'读EEG文件头异常:{err}']
    #         print(f"openEEGFile：读EEG文件头异常={err}")
    #
    #     # 读文件
    #     raw = ret_1[1]
    #     _index_channels = ret_1[3]
    #     try:
    #         raw_copy = raw.copy()
    #         if _t_min != -1:
    #             if _t_max == -1:
    #                 raw_copy.crop(tmin=_t_min, include_tmax=True)
    #             else:
    #                 raw_copy.crop(tmin=_t_min, tmax=_t_max)
    #         raw_copy.load_data()
    #         data, times = raw_copy[_index_channels, :]
    #         data = data * (pow(10, 4))
    #         # data = data * 1037
    #         ret = ['1', data, times]
    #         print(f"readEEGfile：ok:len(data)={len(data)}:{times}")
    #     except Exception as e:
    #         ret = ['0', f'读数据块raw_copy不成功:{e}.']
    #
    #     # 关闭文件
    #     raw.close()
    #     return ret

    # 写脑电文件功能
    def writeEEG(self, check_id, file_id, data):
        # 判断目录是否存在
        dirname = str(check_id).rjust(11, '0')
        path = os.path.join(self.root_path, 'data', 'formated_data', dirname)
        print("写入的脑电文件名称是：",path)
        filename = str(file_id).rjust(3, '0') + '.bdf'
        if not os.path.exists(path):
            os.makedirs(path)
        file_dir = os.path.join(path, filename)
        try:
            with open(file_dir, 'ab') as f:
                f.write(data)
                f.close()
                # block_id += 1
                # received_size += len(rdata)
        except Exception as e:
            print('writeEEG', e)

    # 这里写文件不能仅仅是追加，要能写入固定的块，不然会出问题
    # 写文件功能
    def writeByte(self, savePath, data, block_size, block_id):
        try:
            print(f'writeByte savePath: {savePath}, block_size: {block_size}, block_id: {block_id}')
            with open(savePath, 'r+b') as f:  # 使用 'r+b' 以支持随机读写
                write_position = (block_id - 1) * block_size
                f.seek(write_position)  # 移动到指定的块位置
                f.write(data)
        except FileNotFoundError:
            # 如果文件不存在，创建文件并写入
            with open(savePath, 'wb') as f:
                print(f'File not found, creating new file: {savePath}')
                f.write(data)
        except Exception as e:
            print('writeByte error:', e)

    # FIXME:思考将传入的过多默认参数改为**c这种传递方式
    # 打包文件读写返回消息
    def packageMsg(self, state='', block_id=None, check_id=None, file_name='', mac=''):
        filemsg = []
        if state == 'waiting':
            filemsg = [state, block_id]
        elif state == 'wrongSite' or state == 'unknownError' or state == 'cleaned' or state == 'wrongServer':
            filemsg = [state]
        elif state == 'wrongBlock':
            filemsg = [state, block_id]
        elif state == 'uploaded':
            filemsg = [state]
        elif state == 'recover':
            filemsg = [state, check_id, file_name, mac]
        else:
            filemsg = [state]
        return filemsg

    # 删除上传的脑电文件夹下所有文件,或者删除上传脑电文件夹的某一文件
    def removeFile(self, check_id=None, file_id=None, flag=''):
        if flag == '':
            dirname = str(check_id).rjust(11, '0')
            path = os.path.join(self.root_path, 'data', 'formated_data', dirname)
            print(path)
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    print("delfile", e)
                    return False
                return True
            else:
                return True
        else:
            dirname = str(check_id).rjust(11, '0')
            filename = str(file_id).rjust(3, '0') + '.bdf'
            filepath = os.path.join(self.root_path, 'data', 'formated_data', dirname, filename)
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    print(f"File {filepath} has been deleted successfully.")
                    return True
                else:
                    print(f"File {filepath} does not exist.")
                    return True
            except Exception as e:
                print(f"An error occurred: {e}")
                return False

    # 按字节读取文件
    def readByte(self, file_path, block_size, block_id):
        try:
            print(f'readFile file_path: {file_path}, block_size:{block_size}, block_id: {block_id}')
            with open(file_path, 'rb') as f:
                received_size = (block_id - 1) * block_size
                f.seek(received_size)
                data = f.read(block_size)
                if not data:
                    return
        except Exception as e:
            print('readFile', e)
        return data

    # 写文件功能
    def writeByteXXX(self, savePath, data):
        try:
            with open(savePath, 'ab') as f:
                f.write(data)
        except Exception as e:
            print('writeByte', e)

    # 获取文件的默认导联
    def getDefChannels(self, path):
        try:
            print(f'getDefChannels path: {path}')
            # 使用preload=False来避免加载整个数据集
            raw = mne.io.read_raw_bdf(path, preload=False)
            # 获取导联的名称
            channel_names = raw.ch_names
            return channel_names
        except Exception as e:
            print('getDefChannels', e)
            return []

    # 根据地址获取EEG数据
    def getEEGData(self, isDefault, fileName, channel_set=[], type='wave'):
        try:
            print(f'getEEGData fileName: {fileName}, channel_set: {channel_set}')
            # 读取BDF文件
            raw = mne.io.read_raw_bdf(fileName, preload=True)
            channel_names = raw.ch_names
            print(channel_names)

            # leads = ['Fp1', 'Fpz', 'Fp2', 'AF7', 'AF3', 'AFz', 'AF4', 'AF8', 'F9', 'F7', 'F5', 'F3', 'F1', 'Fz', 'F2',
            #          'F4', 'F6', 'F8', 'F10', 'FT9', 'FT7', 'FC5', 'FC3', 'FC1', 'FCz', 'FC2', 'FC4', 'FC6', 'FT8',
            #          'FT10', 'M1', 'M2', 'T7', 'C5', 'C3', 'C1', 'Cz', 'C2', 'C4', 'C6', 'T8', 'TP9', 'TP7', 'CP5',
            #          'CP3', 'CP1', 'CPz', 'CP2', 'CP4', 'CP6', 'TP8', 'TP10', 'P9', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2',
            #          'P4', 'P6', 'P8', 'P10', 'PO7', 'PO3', 'POz', 'PO4', 'PO8', 'O1', 'Oz', 'O2', 'CB1', 'CB2']
            # 创建一个正则表达式，匹配这些导联名后可能跟着的后缀
            # pattern = r'\b(' + '|'.join(leads) + r')(?:[-\s][\w]*)?'
            # matches = re.findall(pattern, example_input)

            if not isDefault and type == 'wave':
                new_channel_names = [name.replace('-REF', '').replace('EEG ', '') for name in channel_names]
                raw.rename_channels({old: new for old, new in zip(channel_names, new_channel_names)})
                print(f'channel_names: {raw.ch_names}')

                # 处理需要计算差值的导联
                for channel in channel_set:
                    ch1, ch2 = channel.split('-')
                    print(f'channel: {channel}, ch1: {ch1}, ch2: {ch2}')
                    raw = mne.set_bipolar_reference(raw, anode=ch1, cathode=ch2, ch_name=f'{channel}',
                                                    drop_refs=False)

                raw.load_data()
                raw.drop_channels(new_channel_names)

            print(f'channel_names2: {raw.ch_names}')
            # data = raw.get_data()
            # 打印数据形状
            # print("Data shape:", data.shape)
            return raw
        except Exception as e:
            print('getEEGData', e)
            return []

    def addAlgorithmFile(self, file_name, data):
        try:
            path = os.path.join(self.root_path,'classifier', 'algorithms\\')
            file_name = file_name + '.py'
            file_path = os.path.join(path, file_name)
            with open(file_path, 'ab') as f:
                f.write(data)
            return '1', file_name
        except (IOError, OSError) as err:
            print('addAlgorithmFile', err)
            return '0', err

    def delAlgorithmFile(self, train_name, test_name, predict_name):
        try:
            files_path = os.path.join(self.root_path, 'classifier', 'algorithms\\')
            files_list = os.listdir(files_path)
            for file in files_list:
                if file == train_name:
                    file_path = os.path.join(files_path, file)  # 获取文件的完整路径
                    os.remove(file_path)
                elif file == test_name:
                    file_path = os.path.join(files_path, file)  # 获取文件的完整路径
                    os.remove(file_path)
                elif file == predict_name:
                    file_path = os.path.join(files_path, file)  # 获取文件的完整路径
                    os.remove(file_path)
            return '1', 'True'
        except Exception as e:
            print('delAlgorithmFile', e)
            return '0', 'False'

    def recoverAlgorithmFile(self, file_name):
        try:
            files_path = os.path.join(self.root_path, 'classifier', 'algorithms\\')
            files_list = os.listdir(files_path)
            for file in files_list:
                if file == file_name:
                    file_path = os.path.join(files_path, file)  # 获取文件的完整路径
                    os.remove(file_path)
                    break
            return '1', 'True'
        except Exception as e:
            print('recoverAlgorithmFile', e)
            return '0', 'False'

    def get_set_file_type(self):
        with open("data/config.json", "r", encoding='utf8') as fp:
            json_data = json.load(fp)
            config_data = json_data.get('set_file_type')
            return config_data

        # 从source_dir目录下查找是否存在文件名（不含后缀）为filename的文件，并返回其文件名和文件后缀

    def GetFileNameAndExt_from_dir_byName(self, filename, source_dir):
        # 1.将指定A目录下的文件名取出,并将文件名文本和文件后缀拆分出来
        img = os.listdir(source_dir)  # 得到文件夹下所有文件名称
        s = []

        for fileNum in img:  # 遍历文件夹
            if not os.path.isdir(fileNum):  # 判断是否是文件夹,不是文件夹才打开
                # print(fileNum)  # 打印出文件名
                imgname = os.path.join(source_dir, fileNum)
                # print(imgname)  # 打印出文件路径
                (imgpath, tempimgname) = os.path.split(imgname)  # 将路径与文件名分开
                (shotname, extension) = os.path.splitext(tempimgname)  # 将文件名文本与文件后缀分开
                if shotname == filename:
                    # print(shotname, extension)
                    return shotname, extension

# if __name__ == '__main__':
#     a = appUtil()
#     print(a.root_path)







