import os.path
import numpy as np

dir_block = "./"
dir_topK = "./"

def load_block(subvector, i, j):
    filename = f"block_{i}_{j}.npy"
    filepath = os.path.join(dir_block, filename)
    if not os.path.exists(filepath):
        print(f"File {filepath} not found")
        return None
    return np.load(filepath)

def save_block(subvector, i, j):
    if not os.path.exists(dir_block):
        os.makedirs(dir_block)
    filename = f"block_{i}_{j}.npy" #用i、j标识; 也可以维护一个数据记录表
    filepath = os.path.join(dir_block, filename)
    np.save(filepath, subvector)
    return None

"""
topKs: 列表，其中每个元素是一个字典？？？
"""
def save_topK(topKs):
    if not os.path.exists(dir_topK):
        os.makedirs(dir_topK)
    filename = f"      .npy"  # 该用什么作标识？
    filepath = os.path.join(dir_topK, filename)
    np.save(filepath, topKs)
    return None
