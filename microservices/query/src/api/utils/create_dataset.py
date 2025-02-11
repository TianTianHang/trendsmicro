import numpy as np


def create_sliding_window(data, window_size):
    """
    创建滑动窗口数据
    :param data: 时间序列数据列表
    :param window_size: 滑动窗口的大小
    :return: X (输入特征) 和 y (目标值)
    """
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])  # 当前窗口的前 window_size 个值作为输入特征
        y.append(data[i + window_size])    # 当前窗口的第 window_size + 1 个值作为目标值
    return np.array(X), np.array(y).reshape((-1,1))