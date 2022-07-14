import torch
def gflow2proxy(gflow, redun_list, redun_dict,batch_size,proxy_max_len):
  generated = torch.LongTensor(batch_size, proxy_max_len)
  generated.fill_(-1)
  filled = []
  for redun in redun_list:
    index, action_id = redun_dict[redun]
    generated[:,index] = action_id
    filled.append(index)
  gflow_index = 0
  for i in range(proxy_max_len):
    if i in filled:
      continue
    else:
      generated[:,i] = gflow[:,gflow_index]
      gflow_index = gflow_index + 1
  return generated

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self