from classifier.algorithms.alg import AlgorithmTemplate
import torch

class testAlgorithm(AlgorithmTemplate):

    def __init__(self, modelFileName, testingSetFilename):
        super().__init__(modelFileName)
        self.testingSetFilename = testingSetFilename
        self.test_performance = None
        self.test_set = None
        self.test_label = None

    # 虚函数重写
    def test(self):
        pass

    def load(self):
        self.model = torch.load(self.modelFileName, weights_only=False)

    def run(self):
        self.test_set, self.test_label = self.get_dataset(self.testingSetFilename)
        self.load()
        self.test()
        self.result = True
        print("test_performance:{}finish, result:{}finished".format(self.test_performance, self.result))