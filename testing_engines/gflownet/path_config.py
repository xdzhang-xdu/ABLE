class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
path_args = AttrDict(
    {
        # testing result data
        "test_result_direct": "/data/xdzhang/",
        "spec_path": "rawdata/specs/spec_data.json",
        # data for training
        "train_data_path": "generator/data/a_testset_for_{}.json",
        # template for generating scenarios quickly
        "template_path": "generator/data/template_for_{}.json",
        # GFlownet model path
        "ckpt": "generator/ckpt/{}_gfn.pkl",
        # proxy path
        "proxy_path": "generator/proxy/model/{}",
        # result path from gfl model
        "result_path": "generator/result/action_sequence_{}.json"
    }
)