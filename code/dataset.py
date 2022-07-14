import torch
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset,DataLoader
import re 
import json

import numpy as np
# deleted version only 14 states left 


class trafficSet(Dataset):
    def __init__(self,path,train,g_flag=False):
        with open(path,'r') as f:
              testset = json.load(f)
        actions_set = set()
        self.actions = []
        self.rewards = []
        self.data = []
        self.target = []
        self.redun_list = []
        self.redun_dict = {}
        self.states_list = []
        for tset in testset:
            self.actions.append(tset['actions'])
            self.rewards.append(tset['robustness'][0])
            for action in tset['actions']:
                    actions_set.add(action)
        if g_flag is False:
          if train is True:
              self.data = self.actions[:int(len(self.actions)*0.8)]
              self.target = self.rewards[:int(len(self.actions)*0.8)]
          else:
              self.data = self.actions[int(len(self.actions)*0.8):]
              self.target = self.rewards[int(len(self.actions)*0.8):]
        else:
          self.data = self.actions
          self.target = self.rewards
            
        self.actions_list = sorted(list(actions_set))
        self.proxy_actions_list = self.actions_list.copy() + [',','.']
        self.actions_to_index = {self.actions_list[i] : i  for i in range(len(self.actions_list))}
        self.actions_category = []
        self.actions_dict = {}
        self.actions_index = []
        i = 0
        action_string = re.sub(r'[0-9]+', '', self.actions_list[0])
        for action in self.actions_list:
            current_action =  action[:4] + re.sub(r'[0-9]+', '', action[4:])
            if current_action not in self.actions_category:
                self.actions_category = self.actions_category + [current_action]
                self.actions_index.append(i)
                self.actions_dict[current_action] = [action]
            else:
                self.actions_dict[current_action].append(action)
            i = i + 1
        
        self.proxy_actions_indexes= {}
        for i in range(len(self.actions_index)):
            if i != len(self.actions_index) -1 :
                self.proxy_actions_indexes[self.actions_category[i]] = [self.actions_index[i],self.actions_index[i+1]]
            else:
                self.proxy_actions_indexes[self.actions_category[i]] = [self.actions_index[i],len(self.actions_list)]
            i = i + 1
        index = 0
        self.actions_category = []
        for action in self.actions[0]:
          self.actions_category.append(action[:4] + re.sub(r'[0-9]+', '', action[4:]))
        remove_category = []
        remove_action = []
        for category in self.actions_category:
          sindex = self.proxy_actions_indexes[category][0]
          eindex = self.proxy_actions_indexes[category][1]
          if (eindex - sindex) == 1:
            self.redun_list.append(category)
            self.redun_dict[category] = [index ,sindex]
            remove_category.append(category)
            remove_action.append(self.actions_list[sindex])
          index = index + 1        
        for category in remove_category:
          self.actions_category.remove(category)
        for action in remove_action:
          self.actions_list.remove(action)
        self.actions_list = self.actions_list + [',','.'] # bos,eos(.) and pad(,) tokens
        temp_index = []
        temp_category = []
        self.actions_indexes = {}
        i = 0
        last_index = 0
        last_action =  self.actions_list[0][:4] + re.sub(r'[0-9]+', '', self.actions_list[0][:4])
        temp_category.append(last_action)
        for action in self.actions_list:
            current_action =  action[:4] + re.sub(r'[0-9]+', '', action[4:])
            if current_action not in temp_category:
                self.actions_indexes[last_action] = [last_index,i]
                last_action = current_action
                last_index = i

            else:
                continue
            i = i + 1
        self.pad_index = len(self.actions_list) - 2
        self.bos_index = len(self.actions_list) - 1
        self.max_len = len(self.actions_category) + 1

        # self.embeddings = Embedding(len(self.actions_list),emb_dim,self.actions_indexes[','][0])
    def __getitem__(self, index):
        state = self.actions[index]
        state_idx = []
        proxy_idx = []
        remove_idx = -1
        for action in state:
            state_idx.append(self.actions_to_index[action])
        proxy_idx = state_idx.copy()
        count = 0
        for redun in self.redun_list:
          #print(redun)
          state_idx[self.redun_dict[redun][0]] = remove_idx 
        while remove_idx in state_idx:
          state_idx.remove(remove_idx)
        # action = [self.actions_indexes['.'][0]] + action  # add <BOS> for every action
        state = torch.LongTensor(state_idx)
        proxy_state = torch.LongTensor(proxy_idx)
        reward = self.rewards[index]
        reward = np.exp(reward)
        # print(index)
        return proxy_state,state,reward
    def __len__(self):
        return len(self.data)