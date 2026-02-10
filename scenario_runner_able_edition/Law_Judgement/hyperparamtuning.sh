#!/usr/bin/env bash

source ~/miniconda3/etc/profile.d/conda.sh
conda activate gfn

for i in {1..81}; do
  python3 GFN_trainsurrogate_hyperparamtuning.py
  sleep 30
done
