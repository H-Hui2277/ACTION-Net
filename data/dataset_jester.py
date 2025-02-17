import os 
import sys
import pickle
import numpy as np
import pandas as pd
import random
import torch
import pdb
from torch.utils.data import Dataset, DataLoader,RandomSampler
import torchvision.transforms as transforms
from torchvision.utils import save_image
from PIL import Image
import matplotlib.pyplot as plt
from tqdm import tqdm, trange
import random
import skimage.util as ski_util
from sklearn.utils import shuffle
from copy import copy




# 加载图片路径

def load_video(annot_path, mode):
    """
    @annot_path 数据集路径
    @mode 数据集模式 train / test / val
    """
    # mode: train, val, test
    csv_file = os.path.join(annot_path, '{}.pkl'.format(mode))
    annot_df = pd.read_pickle(csv_file)
    rgb_samples = []
    depth_samples = []
    labels = []
    for frame_i in range(annot_df.shape[0]):
        # 路径是存放在一个 .pkl 文件里的，这里应该是加载了某一个样本的所有切片路径
        rgb_list = annot_df['frame'].iloc[frame_i] # convert string in dataframe to list
        rgb_samples.append(rgb_list)
        labels.append(annot_df['label'].iloc[frame_i])
    print('{}: {} videos have been loaded'.format(mode, len(rgb_samples)))
    return rgb_samples, labels


class dataset_video(Dataset):
    def __init__(self, root_path, mode, spatial_transform=None, temporal_transform=None):
        self.root_path = root_path
        # rgb_samples[list]:所有文件路径  labels[list]
        self.rgb_samples, self.labels = load_video(root_path, mode)
        self.sample_num = len(self.rgb_samples)
        # spatial temporal
        self.spatial_transform = spatial_transform
        self.temporal_transform = temporal_transform

    def __getitem__(self, idx):
        # rgb_name[list(string)] 该视频样本的所有切片路径
        rgb_name = self.rgb_samples[idx]
        label = self.labels[idx]
        indices = [i for i in range(len(rgb_name))]
        # TODO temporal_transform 是随机选取帧的方法
        selected_indice = self.temporal_transform(indices)
        clip_frames = []
        for i, frame_name_i in enumerate(selected_indice):
            rgb_cache = Image.open(rgb_name[frame_name_i]).convert("RGB")
            clip_frames.append(rgb_cache)
        # TODO spatial_transform 应该是对图像进行转换的方法 猜测是 list -> tensor
        clip_frames = self.spatial_transform(clip_frames)
        n, h, w = clip_frames.size()
        # 维度转换，应该是没有使用 toTensor()，手动进行的维度转换，猜测是 (h,w,c) -> (c,h,w)
        return clip_frames.view(-1, 3, h, w), int(label)
    def __len__(self):
        return int(self.sample_num)






class dataset_video_inference(Dataset):
    def __init__(self, root_path, mode, clip_num = 2, spatial_transform=None, temporal_transform=None):
        self.root_path = root_path
        self.clip_num = clip_num
        self.video_samples, self.labels = load_video(root_path, mode)
        self.mode = mode
        self.sample_num = len(self.video_samples)
        self.spatial_transform = spatial_transform
        self.temporal_transform = temporal_transform

    def __getitem__(self, idx):
        rgb_name = self.video_samples[idx]
        label = self.labels[idx]
        indices = [i for i in range(len(rgb_name))]
        # TODO 这个 clip_num 有待研究，好像是切片数量的意思，应该是分出两个切片，最后进行了 stack 操作
        video_clip = []
        for win_i in range(self.clip_num):
            clip_frames = []
            selected_indice = self.temporal_transform(copy(indices))
            for frame_name_i in selected_indice:
                rgb_cache = Image.open(rgb_name[frame_name_i]).convert("RGB")
                clip_frames.append(rgb_cache)
            clip_frames = self.spatial_transform(clip_frames)
            n, h, w = clip_frames.size()
            video_clip.append(clip_frames.view(-1, 3, h, w)) 
        video_clip = torch.stack(video_clip)
        return video_clip, int(label)

    def __len__(self):
        return int(self.sample_num)


