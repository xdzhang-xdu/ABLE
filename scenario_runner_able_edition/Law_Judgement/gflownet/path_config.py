class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
path_args = AttrDict(
    {
        # testing result data
        "test_result_direct": "/home/xdzhang/data/apollo7/active+max/{}",
        "debug_result_direct": "/home/xdzhang/data/apollo7/debug/{}",
        "spec_path": "rawdata/specs/spec_data.json",
        # data for training
        "train_data_path": "gflownet/generator/data/testset/a_testset_for_{}.json",
        # template for generating scenarios quickly
        "template_path": "gflownet/generator/data/templates/template_for_{}.json",
        # GFlownet model path
        "ckpt": "gflownet/generator/ckpt/{}_gfn.pkl",
        # proxy path
        "proxy_path": "gflownet/generator/proxy/model/{}",
        # result path from gfl model
        "in_process_dataset_path": "gflownet/generator/result/action_sequence_{}.json",
        "new_batch_path": "gflownet/generator/result/new_action_sequence_{}.json",
        "space_path": "gflownet/generator/data/action_space/space_for_{}.json"
    }
)