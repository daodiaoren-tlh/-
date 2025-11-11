"""
通用工具函数模块
作者: 奇趣乐园团队
创建时间: 2024-01
功能: 实现Excel导出、JSON保存/读取等通用工具函数
"""
import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from facility import Facility


def save_layout(facilities: List[Facility], filename: str = "layout.json") -> bool:
    """
    保存设施布局到JSON文件
    参数:
        facilities: 设施列表
        filename: 文件名
    返回:
        是否保存成功
    """
    try:
        layout_data = {}
        for facility in facilities:
            layout_data[facility.name] = {
                "name": facility.name,  # 添加name字段，与Facility.from_dict方法匹配
                "x": facility.x,
                "y": facility.y,
                "capacity": facility.capacity,
                "run_time": facility.run_time,
                "type": facility.type,
                "emoji": facility.emoji
            }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(layout_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"保存布局失败: {e}")
        return False


def load_layout(filename: str = "layout.json") -> Dict[str, Dict[str, Any]]:
    """
    从JSON文件加载设施布局
    参数:
        filename: 文件名
    返回:
        布局数据字典
    """
    if not os.path.exists(filename):
        return {}
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载布局失败: {e}")
        return {}


def export_to_excel(facilities: List[Facility], queue_history: Dict[str, List], 
                    utilization_data: Dict[str, List], 
                    output_dir: str = ".") -> str:
    """
    导出模拟数据到Excel文件
    参数:
        facilities: 设施列表
        queue_history: 排队历史数据
        utilization_data: 利用率数据
        output_dir: 输出目录
    返回:
        生成的Excel文件路径
    """
    try:
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"simulation_{timestamp}.xlsx")
        
        # 创建Excel写入器
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            # 工作表1：设施基础信息
            facility_data = []
            for facility in facilities:
                facility_data.append({
                    "设施名称": facility.name,
                    "设施类型": facility.type,
                    "容量": facility.capacity,
                    "单次运行时长": facility.run_time,
                    "X坐标": facility.x,
                    "Y坐标": facility.y,
                    "当前排队人数": facility.get_queue_length(),
                    "当前利用率": facility.get_utilization(),
                    "总服务游客数": facility.total_visitors_served
                })
            
            df_facilities = pd.DataFrame(facility_data)
            df_facilities.to_excel(writer, sheet_name="设施基础信息", index=False)
            
            # 工作表2：实时排队数据
            queue_data = []
            for facility_name, history in queue_history.items():
                for timestamp, queue_length in history:
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                    queue_data.append({
                        "时间": time_str,
                        "设施名称": facility_name,
                        "排队人数": queue_length
                    })
            
            df_queue = pd.DataFrame(queue_data)
            df_queue.to_excel(writer, sheet_name="实时排队数据", index=False)
            
            # 工作表3：设施利用率
            utilization_rows = []
            for facility in facilities:
                utilization_rows.append({
                    "设施名称": facility.name,
                    "总运行时间": facility.total_run_time,
                    "总空闲时间": facility.total_idle_time,
                    "利用率(%)": facility.get_utilization()
                })
            
            # 添加历史利用率数据
            for facility_name, history in utilization_data.items():
                for timestamp, utilization in history:
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                    utilization_rows.append({
                        "设施名称": facility_name,
                        "时间": time_str,
                        "利用率(%)": utilization
                    })
            
            df_utilization = pd.DataFrame(utilization_rows)
            df_utilization.to_excel(writer, sheet_name="设施利用率", index=False)
        
        return filename
    except Exception as e:
        print(f"导出Excel失败: {e}")
        return None


def generate_random_position(map_size: int = 16, 
                            existing_positions: List[tuple] = None) -> tuple:
    """
    生成随机位置，避开已存在的位置
    参数:
        map_size: 地图大小
        existing_positions: 已存在的位置列表
    返回:
        (x, y)坐标元组
    """
    import random
    
    if existing_positions is None:
        existing_positions = []
    
    max_attempts = 100
    for _ in range(max_attempts):
        x = random.randint(0, map_size - 1)
        y = random.randint(0, map_size - 1)
        if (x, y) not in existing_positions:
            return x, y
    
    # 如果尝试次数过多，返回第一个可用位置
    for x in range(map_size):
        for y in range(map_size):
            if (x, y) not in existing_positions:
                return x, y
    
    return 0, 0


def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """
    计算曼哈顿距离
    参数:
        x1, y1: 第一个点的坐标
        x2, y2: 第二个点的坐标
    返回:
        距离值
    """
    return abs(x1 - x2) + abs(y1 - y2)


def format_time(seconds: float) -> str:
    """
    格式化时间
    参数:
        seconds: 秒数
    返回:
        格式化的时间字符串
    """
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}时{minutes}分{seconds}秒"
    elif minutes > 0:
        return f"{minutes}分{seconds}秒"
    else:
        return f"{seconds}秒"


def ensure_directory(directory: str) -> None:
    """
    确保目录存在，如果不存在则创建
    参数:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_available_colors(count: int) -> List[str]:
    """
    获取可用的颜色列表，用于图表绘制
    参数:
        count: 需要的颜色数量
    返回:
        颜色字符串列表
    """
    # 预定义的颜色列表，确保颜色区分度高
    base_colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
    ]
    
    # 如果需要的颜色数量超过预定义列表，循环使用
    if count <= len(base_colors):
        return base_colors[:count]
    else:
        return (base_colors * (count // len(base_colors) + 1))[:count]


def get_utilization_color(utilization: float) -> str:
    """
    根据利用率获取颜色
    参数:
        utilization: 利用率百分比
    返回:
        颜色字符串
    """
    if utilization >= 80:
        return "green"  # 高利用率，绿色
    elif utilization >= 50:
        return "yellow"  # 中等利用率，黄色
    else:
        return "red"  # 低利用率，红色


def get_queue_color(queue_length: int) -> str:
    """
    根据排队长度获取颜色
    参数:
        queue_length: 排队人数
    返回:
        颜色字符串
    """
    if queue_length > 10:
        return "red"  # 排队人数超过10，红色
    else:
        return "black"  # 正常情况，黑色


def create_default_facilities() -> List[Facility]:
    """
    创建默认设施列表
    返回:
        设施列表
    """
    from facility import FacilityFactory
    
    default_facilities = [
        FacilityFactory.create_facility("极速过山车", "过山车", 20, 120, 3, 3),
        FacilityFactory.create_facility("幸福摩天轮", "摩天轮", 36, 180, 10, 3),
        FacilityFactory.create_facility("旋转木马", "旋转木马", 16, 90, 3, 10),
        FacilityFactory.create_facility("激情碰碰车", "碰碰车", 8, 100, 10, 10),
        FacilityFactory.create_facility("海盗船", "海盗船", 24, 110, 6, 6)
    ]
    
    return default_facilities