import sys

from torch import nn

from trainAlg import trainAlgorithm

# 训练算法类
# 将 trainTemplate 修改为自己的类名
class trainTemplate(trainAlgorithm):
    def __init__(self, modelFileName, trainingSetFileName):
        super().__init__(modelFileName, trainingSetFileName)
        # 定义训练算法需要使用的参数 如：
        self.epochs = 50
        self.batch_size = 32


    # 主要实现训练算法的训练功能
    def train(self):
        # -------------------------------------------------------------------------
        # 以下为父类 trainAlgorithm 中已经定义的变量，直接使用即可
        # self.train_set            训练样本
        # self.train_label          训练标签
        # self.model                需要训练的模型
        # self.train_performance    记录训练的准确率
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        # 主要步骤包含（部分非必要）

        # 特征提取
        # 归一化处理
        self.model = EEGNet()    # 创建用户定义的模型将其替换
        # 设置优化器
        # 创建损失函数
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        # 必要代码
        for epoch in range(self.epochs):
            # 模型训练 如：
            # self.model.train()
            # self.model(train_X)

            self.train_performance = 0.9  # 计算实际的准确率将其替换
            avg_loss = 0.2  # 计算实际的损失率将其替换
            print("epoch{}：train_acc:{},loss:{}".format(epoch + 1, self.train_performance, avg_loss))

        # -------------------------------------------------------------------------



# 自行定义该算法中使用到的模型 如：
class EEGNet(nn.Module):
    def __init__(self):
        super(EEGNet).__init__()
        # 定义模型的激活函数

    def forward(self, x):
        # 神经网络层
        return x



#####   上传前必须切换到该入口函数   ####
# 上传到系统调用的入口函数
def run_main(args):
    print('start')
    a = trainTemplate(args[0], args[1])
    a.run()
    print('finish')



# 用户测试调用的如何函数
# 运行后文件所在目录下出现 model.pth 为有效
def dev_run():
    model_path = 'model.pth'
    # 请将数据集命名为 trainSet 且文件后缀为 .npz
    # 数据集以 "data" 为key的数据为 【样本】
    # 数据集以 “label” 为key的数据为 【标签】
    # 请将数据集放在与该文件的同一目录下
    train_set_path = 'trainSet.npz'
    a = trainTemplate(model_path, train_set_path)
    a.run()



# 系统调用训练算法的入口函数
if __name__ == '__main__':
    #####   上传前必须切换到该入口函数   ####
    # args = sys.argv[1:]
    # run_main(args)

    # 请在上传前切换入口函数
    dev_run()