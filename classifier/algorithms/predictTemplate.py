import sys

from torch import nn

from predictAlg import predictAlgorithm

# 预测算法类
# 将 predictTemplate 修改为自己的类名
class predictTemplate(predictAlgorithm):
    def __init__(self, modelFileName, eegFileName, time_stride, scan_file_channel_list, sample_rate, sample_len,
                 unitFactor, model_trained_sample_rate, alg_type, set_temp):
        super().__init__(modelFileName, eegFileName, time_stride, scan_file_channel_list, sample_rate, sample_len,
                 unitFactor, model_trained_sample_rate, alg_type, set_temp)
        # 加载模型
        self.load()
        # 定义预测算法需要使用的参数


    # 主要实现预测算法的测试功能
    def predict(self, data, channel_list):
        # -------------------------------------------------------------------------
        # 以下为父类 predictAlgorithm 中已经定义的变量，直接使用即可
        # self.model  加载好的模型
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        # 主要步骤包含（部分非必要）

        # 特征提取
        # 归一化处理
        # 模型预测
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        # 必要代码
        predictions = 0.8   # 计算实际的准确率将其替换
        return predictions
        # -------------------------------------------------------------------------



# 自行定义该算法中使用到的模型,该模型必须与训练算法中的模型相同 如：
class EEGNet(nn.Module):
    def __init__(self):
        super(EEGNet).__init__()
        # 定义模型的激活函数

    def forward(self, x):
        # 神经网络层
        return x



#####   上传前必须切换到该入口函数   ####
# 上传到系统调用的入口函数
def run_main():
    print('start')
    args = sys.argv[1:]
    a = predictTemplate(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], args[9])
    a.run()
    print('finish')



# 用户测试调用的如何函数
# 控制台打印出 "test_acc:0.7“ 为有效
def dev_run():
    # 请将训练好的模型命名为 model 并放在与该文件的同一目录下
    modelFileName = 'model.pth'
    # 请将需要预测的脑电文件命名为 data 并放在与该文件的同一目录下
    eegFileName = 'data.bdf'
    # 请设置时间跨度
    time_stride = 1
    # 请设置扫描通道
    scan_file_channel_list = []
    # 请设置脑电文件样本频率
    sample_rate = 250
    # 请设置脑电文件总样本点
    sample_len = 25000
    # 请设置因素
    unitFactor = 0.1
    # 请设置训练样本频率
    model_trained_sample_rate = 250
    # 请设置预测类型
    alg_type = 'wave'
    # 请设置标签下标列表
    set_temp = []
    a = predictTemplate(modelFileName, eegFileName, time_stride, scan_file_channel_list, sample_rate, sample_len,
                 unitFactor, model_trained_sample_rate, alg_type, set_temp)
    a.run()



# 系统调用训练算法的入口函数
if __name__ == '__main__':
    #####   上传前必须切换到该入口函数   ####
    # run_main()

    # 请在上传前切换入口函数
    dev_run()