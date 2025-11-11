"""
设施类定义模块
作者: 奇趣乐园团队
创建时间: 2024-01
功能: 定义Facility类，包含排队队列、运行逻辑
"""
import time
from typing import List, Dict, Optional
from data_structures import FacilityQueue


class Facility:
    """
    设施类，代表乐园中的一个设施
    """
    def __init__(self, name: str, capacity: int, run_time: int, x: int, y: int, 
                 facility_type: str = "默认", emoji: str = "🎪"):
        """
        初始化设施
        参数:
            name: 设施名称
            capacity: 设施容量（每次可容纳人数）
            run_time: 单次运行时长（秒）
            x: 设施在地图上的x坐标
            y: 设施在地图上的y坐标
            facility_type: 设施类型
            emoji: 设施的emoji表示
        """
        self.name = name
        self.capacity = capacity
        self.run_time = run_time
        self.x = x
        self.y = y
        self.type = facility_type
        self.emoji = emoji
        
        # 排队队列
        self.waiting_queue = FacilityQueue()
        
        # 状态信息
        self.is_running = False
        self.current_visitors = []  # 当前在设施中的游客
        self.run_start_time = 0  # 运行开始时间
        
        # 统计信息
        self.total_run_time = 0  # 总运行时间
        self.total_idle_time = 0  # 总空闲时间
        self.total_visitors_served = 0  # 总服务游客数
        self.last_status_change_time = time.time()  # 最后状态改变时间
        
        # 排队历史数据，用于图表显示
        self.queue_history = []  # [(timestamp, queue_length)]
        
    def update_status(self, current_time: float) -> None:
        """
        更新设施状态
        参数:
            current_time: 当前时间
        """
        # 更新统计信息
        time_passed = current_time - self.last_status_change_time
        if self.is_running:
            self.total_run_time += time_passed
        else:
            self.total_idle_time += time_passed
        # 更新最后状态改变时间，确保下次计算的是增量时间
        self.last_status_change_time = current_time
        
        # 记录排队历史
        self.queue_history.append((current_time, len(self.waiting_queue)))
        # 保留最近1000条记录
        if len(self.queue_history) > 1000:
            self.queue_history.pop(0)
        
        # 检查运行是否结束
        if self.is_running and current_time - self.run_start_time >= self.run_time:
            self._finish_run()
    
    def _finish_run(self) -> None:
        """
        结束当前运行，释放游客
        """
        self.is_running = False
        self.total_visitors_served += len(self.current_visitors)
        self.current_visitors.clear()
    
    def start_run(self, current_time: float) -> bool:
        """
        开始运行设施，从队列中取游客
        参数:
            current_time: 当前时间
        返回:
            是否成功启动
        """
        if self.is_running:
            return False
        
        # 从队列中取出最多capacity个游客
        self.current_visitors = []
        for _ in range(self.capacity):
            visitor = self.waiting_queue.pop()
            if visitor:
                self.current_visitors.append(visitor)
            else:
                break
        
        if self.current_visitors:
            self.is_running = True
            self.run_start_time = current_time
            return True
        return False
    
    def add_visitor(self, visitor) -> None:
        """
        添加游客到排队队列
        参数:
            visitor: 游客对象
        """
        self.waiting_queue.append(visitor)
    
    def get_queue_length(self) -> int:
        """
        获取当前排队长度
        返回:
            排队人数
        """
        return len(self.waiting_queue)
    
    def get_utilization(self) -> float:
        """
        计算设施利用率
        返回:
            利用率百分比
        """
        total_time = self.total_run_time + self.total_idle_time
        if total_time == 0:
            return 0.0
        return (self.total_run_time / total_time) * 100
    
    def get_avg_waiting_time(self) -> float:
        """
        估算平均等待时间
        返回:
            等待时间（秒）
        """
        queue_length = len(self.waiting_queue)
        if queue_length == 0:
            return 0.0
        
        # 简单估算：每批capacity个游客需要run_time秒
        batches = (queue_length + self.capacity - 1) // self.capacity
        return batches * self.run_time
    
    def move(self, x: int, y: int) -> None:
        """
        移动设施位置
        参数:
            x: 新的x坐标
            y: 新的y坐标
        """
        self.x = x
        self.y = y
    
    def to_dict(self) -> Dict[str, any]:
        """
        将设施信息转换为字典，用于保存到JSON
        返回:
            设施信息字典
        """
        return {
            "name": self.name,
            "capacity": self.capacity,
            "run_time": self.run_time,
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "emoji": self.emoji
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'Facility':
        """
        从字典创建设施对象
        参数:
            data: 设施信息字典
        返回:
            Facility对象
        """
        return cls(
            name=data["name"],
            capacity=data["capacity"],
            run_time=data["run_time"],
            x=data["x"],
            y=data["y"],
            facility_type=data.get("type", "默认"),
            emoji=data.get("emoji", "🎪")
        )


class FacilityFactory:
    """
    设施工厂类，用于创建不同类型的设施
    """
    # 设施类型配置
    FACILITY_TYPES = {
        "过山车": {"emoji": "🎢", "default_capacity": 20, "default_run_time": 120},
        "摩天轮": {"emoji": "🎡", "default_capacity": 36, "default_run_time": 180},
        "旋转木马": {"emoji": "🎠", "default_capacity": 16, "default_run_time": 90},
        "碰碰车": {"emoji": "🚗", "default_capacity": 8, "default_run_time": 100},
        "海盗船": {"emoji": "⛵", "default_capacity": 24, "default_run_time": 110}
    }
    
    @classmethod
    def create_facility(cls, name: str, facility_type: str, capacity: int, 
                        run_time: int, x: int, y: int) -> Facility:
        """
        创建设施
        参数:
            name: 设施名称
            facility_type: 设施类型
            capacity: 设施容量
            run_time: 运行时长
            x: x坐标
            y: y坐标
        返回:
            Facility对象
        """
        config = cls.FACILITY_TYPES.get(facility_type, {"emoji": "🎪"})
        emoji = config.get("emoji", "🎪")
        
        return Facility(
            name=name,
            capacity=capacity,
            run_time=run_time,
            x=x,
            y=y,
            facility_type=facility_type,
            emoji=emoji
        )
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """
        获取所有可用的设施类型
        返回:
            设施类型列表
        """
        return list(cls.FACILITY_TYPES.keys())
    
    @classmethod
    def get_type_info(cls, facility_type: str) -> Dict[str, any]:
        """
        获取指定设施类型的默认信息
        参数:
            facility_type: 设施类型
        返回:
            设施类型信息
        """
        return cls.FACILITY_TYPES.get(facility_type, {})