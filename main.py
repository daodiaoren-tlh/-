"""
奇趣乐园模拟器 - 主程序入口
作者: 奇趣乐园团队
创建时间: 2024-01
功能: 初始化并启动图形界面
"""
import tkinter as tk
from gui import ThemeParkGUI


def main():
    """
    主函数，启动模拟器
    """
    # 创建Tkinter根窗口
    root = tk.Tk()
    
    # 初始化GUI
    app = ThemeParkGUI(root)
    
    # 设置窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    
    # 启动主循环
    root.mainloop()


def on_closing(root):
    """
    处理窗口关闭事件
    参数:
        root: 根窗口
    """
    # 这里可以添加清理代码
    root.destroy()


if __name__ == "__main__":
    main()