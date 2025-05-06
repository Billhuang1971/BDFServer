import sys

from torch import nn

from testAlg import testAlgorithm

# 测试算法类
# 将 testTemplate 修改为自己的类名
class testTemplate(testAlgorithm):
    def __init__(self, modelFileName, testingSetFileName):
        super().__init__(modelFileName, testingSetFileName)
        # 加载模型
        self.load()
        # 定义测试算法需要使用的参数


    # 主要实现测试算法的测试功能
    def test(self):
        # -------------------------------------------------------------------------
        # 以下为父类 testAlgorithm 中已经定义的变量，直接使用即可
        # self.test_set    测试样本
        # self.test_label  测试标签
        # self.model_dict  加载好的模型
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        # 主要步骤包含（部分非必要）

        # 特征提取
        # 归一化处理
        # 模型测试
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        # 必要代码
        self.test_performance = 0.7    # 计算实际的准确率将其替换
        print("test_acc:{}".format(self.test_performance))
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
    a = testTemplate(args[0], args[1])
    a.run()
    print('finish')



# 用户测试调用的如何函数
# 控制台打印出 "test_acc:0.7“ 为有效
def dev_run():
    # 请将训练好的模型命名为 model 并放在与该文件的同一目录下
    model_path = 'model.pth'
    # 请将数据集命名为 trainSet 且文件后缀为 .npz
    # 数据集以 "data" 为key的数据为 【样本】
    # 数据集以 “label” 为key的数据为 【标签】
    # 请将数据集放在与该文件的同一目录下
    train_set_path = 'trainSet.npz'
    a = testTemplate(model_path, train_set_path)
    a.run()



# 系统调用训练算法的入口函数
if __name__ == '__main__':
    #####   上传前必须切换到该入口函数   ####
    # run_main()

    # 请在上传前切换入口函数
    dev_run()