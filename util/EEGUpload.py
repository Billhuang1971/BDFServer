import os
import threading


class EEGUpload(object):
    def __init__(self, dbUtil, appUtil):
        self.root_path = os.path.dirname(os.path.dirname(__file__))+'\\'
        # 用来保存文件每次传的块大小(5M)
        self.block_size = 5 * 1024 * 1024
        # 用来保存当前上传脑电文件的路径
        self.file_dir = None
        self.dbUtil = dbUtil
        self.appUtil = appUtil
        self.filename_mutex = threading.Lock()

    def makeFileName(self, REQmsg):
        account = REQmsg[3][0]
        try:
            check_number = REQmsg[3][2]
            self.filename_mutex.acquire()
            filename, file_id, check_id = self.appUtil.makeFilePath(check_number)
            self.filename_mutex.release()
        except Exception as e:
            print("makeFileName:", e)
        if filename:
            msgtip = [account, f'脑电文件名生成成功', '', '']
            ret = ['1', REQmsg[1], f'脑电文件名生成成功', [filename, file_id, check_id]]
            return msgtip, ret
        else:
            msgtip = [account, f'脑电文件名生成失败', '', '']
            ret = ['0', REQmsg[1], f'脑电文件名生成失败']
            return msgtip, ret

    def unPack(self, REQmsg):
        try:
            if REQmsg[3][1][0] == "EEGUpload":
                account = REQmsg[3][0]
                filemsg = REQmsg[3][1][1:]
                number = REQmsg[1]
                return account, filemsg, number
            else:
                print("无法处理客户端传送来的信息")
                # 返回默认值避免 None
                return None, None, None
        except Exception as e:
            print(f"unPack 出错: {e}")
            # 返回默认值避免 None
            return None, None, None

    def packMsg(self, state='', block_id=None, check_id=None, file_name='', mac=''):
        filemsg = []
        if state == 'waiting':
            filemsg = ['EEGUpload', state, block_id]
        elif state == 'wrongSite' or state == 'unknownError' or state == 'cleaned' or state == 'wrongServer':
            filemsg = ['EEGUpload', state]
        elif state == 'wrongBlock':
            filemsg = ['EEGUpload', state, block_id]
        elif state == 'uploaded':
            filemsg = ['EEGUpload', state]
        elif state == 'recover':
            filemsg = ['EEGUpload', state, check_id, file_name, mac]
        else:
            filemsg = ['EEGUpload', state]
        return filemsg

    def writeEEG(self, REQmsg):
        try:
            print("writeEEG里的REQmsg:", REQmsg)

            # 解包并检查返回值
            unpacked = self.unPack(REQmsg)
            if unpacked == (None, None, None):
                raise ValueError("unPack 返回无效值")

            account, filemsg, number = unpacked

            state = filemsg[0]
            check_id = filemsg[1]
            file_id = filemsg[2]

            # 根据状态调用处理函数
            if state == 'start':
                return self._handle_start(account, filemsg, check_id, file_id, number)
            elif state == 'uploading':
                return self._handle_uploading(account, filemsg, check_id, file_id, number)
            elif state == 'uploaded':
                return self._handle_uploaded(account, filemsg, check_id, file_id, number)
            elif state == 'clean':
                return self._handle_clean(account, filemsg, check_id, file_id, number)
            elif state == 'continue':
                return self._handle_continue(account, filemsg, check_id, file_id, number)
            else:
                return self._handle_unknown_state(account, filemsg, number)

        except Exception as e:
            print(f"writeEEG 出错: {e}")
            account = REQmsg[3][0] if REQmsg and len(REQmsg) > 3 else "Unknown"
            return self._error_response(account, f"脑电文件上传出错: {e}",number ,filemsg)

    # 各种状态处理
    def _handle_start(self, account, filemsg, check_id, file_id, number):
        rf, result = self.dbUtil.get_fileInfo('check_id', check_id, 'file_id', file_id)
        # 数据库中存在这条记录
        if result:
            s_mac = result[0][6]
            c_mac = filemsg[3]
            if s_mac == c_mac:
                # 更新这条记录
                self.dbUtil.update_fileInfo(filemsg,'notUploaded', 0)
                self.dbUtil.update_checkInfo([check_id, 'uploading'], flag='1')
                filemsg = self.packMsg('waiting', 1)
                return self._success_response(account, "发送脑电传输请求成功，并更新数据库脑电数据成功！", number,filemsg)
            else:
                filemsg = self.packMsg('wrongSite')
                return self._success_response(account, "文件上传地址和数据库内mac地址不符", filemsg)
        # 数据库中不存在这条记录
        else:
            # 新增这条记录
            if self.dbUtil.add_fileInfo(filemsg):
                self.dbUtil.update_checkInfo([check_id, 'uploading'])
                filemsg = self.packMsg('waiting', 1)
                return self._success_response(account, "发送脑电传输请求成功，并向数据库添加记录成功！", number, filemsg)
            else:
                return self._error_response(account, "向数据库添加脑电数据记录失败", number, filemsg)

    def makeFile(self,check_id,file_id):
        # 判断目录是否存在
        dirname = str(check_id).rjust(11, '0')
        path = os.path.join(self.root_path, 'data', 'formated_data', dirname)
        print("写入的脑电文件名称是：", path)
        filename = str(file_id).rjust(3, '0') + '.bdf'
        # 如果目录不存在，创建目录
        if not os.path.exists(path):
            os.makedirs(path)
        file_dir = os.path.join(path, filename)
        # 如果存在脑电文件，对他进行删除
        if os.path.exists(file_dir):
            # 删除文件
            os.remove(file_dir)
            print(f"文件已成功删除: {file_dir}")
        return file_dir

    def _handle_uploading(self, account, filemsg, check_id, file_id, number):
        data = filemsg[5]
        rf, result = self.dbUtil.get_fileInfo('check_id', check_id, 'file_id', file_id)
        # 数据库的d3存在以check_id, file_name为关键字的记录
        if result:
            s_mac = result[0][6]
            c_mac = filemsg[3]
            sblock_id = result[0][5]
            cblock_id = filemsg[4]
            # mac地址验证通过
            if s_mac == c_mac:
                # 块号验证通过
                if cblock_id == sblock_id + 1:
                    if cblock_id == 1:
                        self.file_dir = self.makeFile(check_id,file_id)
                        # 成功打开
                        if self.file_dir:
                            self.appUtil.writeByte(self.file_dir, data, self.block_size, cblock_id)
                            self.dbUtil.update_fileInfo(filemsg, 'uploading', sblock_id + 1)
                            filemsg = self.packMsg('waiting', sblock_id + 2)
                            return self._success_response(account, "上传并更新脑电数据成功", number, filemsg)
                        else:
                            # 删除文件
                            self.appUtil.removeFile(check_id=check_id, file_id=file_id, flag='1')
                            self.dbUtil.del_fileInfo(check_id=check_id, file_id=file_id, state='', flag='')
                            filemsg = self.packMsg('wrongServer')
                            return self._success_response(account, "服务端不存在该条脑电数据记录", number, filemsg)
                    else:
                        # 打开脑电文件成功
                        if self.file_dir:
                            self.appUtil.writeByte(self.file_dir, data, self.block_size, cblock_id)
                            self.dbUtil.update_fileInfo(filemsg, 'uploading', sblock_id + 1)
                            filemsg = self.packMsg('waiting', sblock_id + 2)
                            return self._success_response(account, "上传并更新脑电数据成功", number, filemsg)
                        # 未能打开脑电文件
                        else:
                            # 删除文件
                            self.appUtil.removeFile(check_id=check_id, file_id=file_id, flag='1')
                            self.dbUtil.del_fileInfo(check_id=check_id, file_id=file_id, state='', flag='')
                            filemsg = self.packMsg('wrongServer')
                            return self._success_response(account, "服务端不存在该条脑电数据记录", number, filemsg)
                # 块号验证不通过
                else:
                    filemsg = self.packMsg('wrongBlock',sblock_id + 1)
                    return self._success_response(account, "上传数据块与服务端需要的数据块不一致", number, filemsg)
            # mac地址验证不通过
            else:
                filemsg = self.packMsg('wrongSite')
                return self._success_response(account, "文件上传地址和数据库内mac地址不符", number, filemsg)
        # 数据库的d3不存在以check_id, file_name为关键字的记录
        else:
            filemsg = self.packMsg('wrongServer')
            return self._success_response(account, "服务端不存在该条脑电数据记录", number, filemsg)

    def _handle_uploaded(self, account, filemsg, check_id, file_id, number):
        # 先取出以check_id,file_id为关键字的记录
        rf, result = self.dbUtil.get_fileInfo('check_id', check_id, 'file_id', file_id)
        if result:
            s_mac = result[0][6]
            c_mac = filemsg[3]
            sblock_id = result[0][5]
            # mac地址验证通过
            if s_mac == c_mac:
                self.dbUtil.update_fileInfo(filemsg, 'uploaded', sblock_id)
                filemsg = self.packMsg('uploaded')
                return self._success_response(account, "脑电数据传送完成", number, filemsg)
            else:
                filemsg = self.packMsg('wrongSite')
                return self._success_response(account, "文件上传地址和数据库内mac地址不符", number, filemsg)

    def _handle_clean(self, account, filemsg, check_id, file_id, number):
        rf, result = self.dbUtil.get_fileInfo('check_id', check_id, 'file_id', file_id)
        # 数据库中存在这条记录
        if result:
            s_mac = result[0][5]
            c_mac = filemsg[3]
            state = result[0][3]
            if s_mac == c_mac and state == 'notUploaded':
                self.appUtil.removeFile(check_id=check_id, file_id=file_id, flag='1')
                self.dbUtil.del_fileInfo(check_id, file_id, state='notUploaded', flag='1')
                filemsg = self.packMsg('cleaned')
                return self._success_response(account, "清除相关脑电数据成功", number, filemsg)
            elif s_mac == c_mac and state == 'uploading':
                filemsg = self.packMsg('recover')
                return self._success_response(account,"脑电数据需复原后重新上传", number, filemsg)
            elif s_mac == c_mac and state == 'uploaded':
                filemsg = self.packMsg('uploaded')
                return self._success_response(account, "已有上传完成的脑电数据", number, filemsg)
            else:
                filemsg = self.packMsg('unknownError')
                return self._success_response(account, "发送脑电数据时发生未知错误", number, filemsg)
        # 数据库中不存在这条记录
        else:
            filemsg = self.packMsg('wrongServer')
            return self._success_response(account, "服务端不存在该条脑电数据记录", number, filemsg)

    def _handle_continue(self, account, filemsg, check_id, file_id, number):
        rf, result = self.dbUtil.get_fileInfo('check_id', check_id, 'file_id', file_id)
        # 数据库中存在这条记录
        if result:
            s_mac = result[0][6]
            c_mac = filemsg[3]
            sblock_id = result[0][5]
            # mac地址验证通过
            if s_mac == c_mac:
                cblock_id = sblock_id + 1
                filemsg = self.packMsg('waiting', cblock_id)
                return self._success_response(account, "发送脑电传输续传请求成功", number, filemsg)
            else:
                filemsg = self.packMsg('wrongSite')
                return self._success_response(account, "文件上传地址和数据库内mac地址不符", number, filemsg)
        else:
            filemsg = self.packMsg('wrongServer')
            return self._success_response(account, "服务端不存在该条脑电数据记录", number, filemsg)

    def _handle_unknown_state(self, account, filemsg, number):
        return self._success_response(account, "服务端无法处理该脑电上传状态", number, filemsg)

    # 辅助方法，用于生成成功或失败的响应
    def _success_response(self, account, message, number, filemsg):
        msgtip = [account, message, '', '']
        ret = ['1', number, message, filemsg]
        return msgtip, ret

    def _error_response(self, account, message, number,filemsg):
        msgtip = [account, message, '', '']
        ret = ['0', number, message, filemsg]
        return msgtip, ret
