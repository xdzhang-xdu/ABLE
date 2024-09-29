import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint

def Embedding(num_embeddings, embedding_dim, padding_idx=None):
    m = nn.Embedding(num_embeddings, embedding_dim, padding_idx=padding_idx)
    nn.init.normal_(m.weight, mean=0, std=embedding_dim ** -0.5)
    if padding_idx is not None:
        nn.init.constant_(m.weight[padding_idx], 0)
    return m


class MLP(nn.Module):
    def __init__(self, num_tokens, num_outputs, num_hid,
                 num_layers, max_len=60, dropout=0.1,
                 partition_init=150.0, use_checkpoint=False):
        super(MLP, self).__init__()
        print("num_tokens:", num_tokens, "max_len:", max_len)
        self.input = nn.Linear(num_tokens * max_len, num_hid)

        hidden_layers = []
        for _ in range(num_layers):
            hidden_layers.append(nn.Dropout(dropout))
            hidden_layers.append(nn.ReLU())
            hidden_layers.append(nn.Linear(num_hid, num_hid))
        self.hidden = nn.Sequential(*hidden_layers)
        self.output = nn.Linear(num_hid, num_outputs)
        self.max_len = max_len
        self.num_tokens = num_tokens
        self.emb = Embedding(self.num_tokens, self.num_tokens)

        self.use_checkpoint = use_checkpoint

    def forward(self, x, return_all=False, lens=None):
        if not self.use_checkpoint:
            # print(x.shape)
            x = self.emb(x)
            # print(x.shape)
            x = x.reshape(x.size(0), -1)
            # print(x.shape)
            out = self.input(x)
            # print(out.shape)
            out = self.hidden(out)
            out = self.output(out)
            # print(out.shape)
            out = out.reshape(-1)
            return out
        else:
            x = self.emb(x)
            x = x.reshape(x.size(0), -1)
            out = checkpoint(self.input, x, use_reentrant=False)
            out = checkpoint(self.hidden, out, use_reentrant=False)
            out = checkpoint(self.output, out, use_reentrant=False)
            out = out.reshape(-1)
            return out
