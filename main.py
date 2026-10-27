"""
游戏主入口模块
负责初始化 pygame 并启动游戏主循环
"""

import pygame
import os
import sys
from game import Game


def main():
    """
    游戏主入口函数
    初始化 pygame 库并创建游戏实例，然后启动游戏循环
    """
    # 初始化 pygame 库
    pygame.init()
    
    # 创建游戏实例
    game = Game()
    
    # 启动游戏主循环
    game.run()


def resource_path(relative_path):
    """
    获取资源文件的绝对路径
    
    此函数用于处理打包后的资源路径问题：
    - 当使用 PyInstaller 打包时，sys._MEIPASS 指向临时文件夹
    - 开发环境下使用当前工作目录
    
    Args:
        relative_path: 资源文件的相对路径
        
    Returns:
        资源文件的绝对路径
    """
    try:
        # PyInstaller 创建临时文件夹时，_MEIPASS 指向临时文件夹
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境下使用当前工作目录
        base_path = os.path.abspath(".")
    
    # 处理路径分隔符，确保跨平台兼容性
    return os.path.join(base_path, relative_path.replace("/", os.sep))


# 程序入口
if __name__ == "__main__":
    main()