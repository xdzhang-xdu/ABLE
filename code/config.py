import sys
from proxy.proxy_config import *

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
args = AttrDict(
    {
    # 训练的数据位置
    "train_data_path":'data/a_testset_for_double_direction.json',
    # proxy神经网络本身层数,fix
    "proxy_num_layers":proxy_args.num_layers,
    # hidden_layers的神经元数量,fix
    "proxy_num_hid":proxy_args.num_hid,
    # proxy model的存放位置
    "proxy_path":"proxy/model/proxy/best_w.pth",
    # gflownet ckpt存放位置
    "save_ckpt_path":'ckpt/gflownet.pkl',
    # batch_size 大小这个数字越大越好
    "batch_size":128,
    # emb_dim emdding vector的维度
    "emb_dim":512,
    # n_layers hidden layers数量 2,4,8选择
    "n_layers":2,
    # hidden neuron数量,越大越好
    "n_hid":256,
    # n_train_steps 训练本身epoch数量,越大越好
    "n_train_steps":5000,
    # generated_path 生成文件位置
    "generated_path": "result/generated.json",
    # generated_number 生成的数量需要乘以batch_size,才是真正生成的数量
    "generated_number": 500,
}
)