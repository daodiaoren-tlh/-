"""
游客类定义模块
作者: 奇趣乐园团队
创建时间: 2024-01
功能: 定义Visitor类，包含行程单栈、移动逻辑
"""
import time
from typing import Optional, Dict, List, Set
from data_structures import PlanStack


class Visitor:
    """
    游客类，代表乐园中的一个游客
    """
    def __init__(self, visitor_id: int, x: int, y: int, plan: List[str] = None):
        """
        初始化游客
        参数:
            visitor_id: 游客ID
            x: 初始x坐标
            y: 初始y坐标
            plan: 游玩计划（行程单）
        """
        self.id = visitor_id
        self.x = x
        self.y = y
        self.status = "自由"
        self.target_facility = None  # 当前目标设施
        self.waiting_start_time = 0  # 开始等待的时间
        self.ride_start_time = 0  # 开始游玩的时间
        self.total_waiting_time = 0  # 总等待时间
        self.total_ride_time = 0  # 总游玩时间
        self.visited_facilities = set()  # 已访问的设施集合
        self.emoji = "👤"  # 游客的emoji表示
        
        # 行程单栈
        self.plan_stack = PlanStack()
        if plan:
            # 将行程单逆序压入栈中，使第一个设施在栈顶
            for facility_name in reversed(plan):
                self.plan_stack.push(facility_name)
        
        # 更新目标设施为栈顶元素
        self._update_target()
    
    def _update_target(self) -> None:
        """
        更新目标设施为行程单栈顶
        """
        self.target_facility = self.plan_stack.peek()
    
    def get_next_destination(self) -> Optional[str]:
        """
        获取下一个目的地
        返回:
            下一个设施名称或None
        """
        return self.target_facility
    
    def move_towards(self, target_x: int, target_y: int) -> bool:
        """
        向目标位置移动一步
        参数:
            target_x: 目标x坐标
            target_y: 目标y坐标
        返回:
            是否已到达目标位置
        """
        # 简单的移动逻辑：先x方向，再y方向
        if self.x < target_x:
            self.x += 1
        elif self.x > target_x:
            self.x -= 1
        elif self.y < target_y:
            self.y += 1
        elif self.y > target_y:
            self.y -= 1
        else:
            return True  # 已到达
        
        return False
    
    def start_waiting(self) -> None:
        """
        开始等待
        """
        self.status = "等待"
        self.waiting_start_time = time.time()
    
    def end_waiting(self) -> float:
        """
        结束等待
        返回:
            等待时间（秒）
        """
        waiting_time = time.time() - self.waiting_start_time
        self.total_waiting_time += waiting_time
        return waiting_time
    
    def start_ride(self) -> None:
        """
        开始游玩
        """
        self.status = "游玩"
        self.ride_start_time = time.time()
    
    def end_ride(self) -> float:
        """
        结束游玩
        返回:
            游玩时间（秒）
        """
        ride_time = time.time() - self.ride_start_time
        self.total_ride_time += ride_time
        self.visited_facilities.add(self.target_facility)
        
        # 从行程单栈中弹出已完成的设施
        self.plan_stack.pop()
        
        # 更新目标设施
        self._update_target()
        
        # 如果没有下一个目标，设置状态为完成
        if not self.target_facility:
            self.status = "完成"
        else:
            self.status = "自由"
        
        return ride_time
    
    def get_status_text(self) -> str:
        """
        获取状态文本
        返回:
            状态文本
        """
        if self.status == "自由":
            if self.target_facility:
                return f"下一站：{self.target_facility}"
            else:
                return "行程结束"
        elif self.status == "等待":
            return f"等待：{self.target_facility}"
        elif self.status == "游玩":
            return f"游玩：{self.target_facility}"
        elif self.status == "完成":
            return "行程结束"
        return self.status
    
    def has_plan(self) -> bool:
        """
        检查是否还有行程安排
        返回:
            是否有行程
        """
        return not self.plan_stack.is_empty()
    
    def get_remaining_plan(self) -> List[str]:
        """
        获取剩余行程
        返回:
            剩余行程列表（从栈顶到栈底）
        """
        # 由于栈的特性，需要反转来得到正确的顺序
        return list(reversed(self.plan_stack.stack))
    
    def to_dict(self) -> Dict[str, any]:
        """
        将游客信息转换为字典
        返回:
            游客信息字典
        """
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "status": self.status,
            "target_facility": self.target_facility,
            "remaining_plan": self.get_remaining_plan(),
            "total_waiting_time": self.total_waiting_time,
            "total_ride_time": self.total_ride_time,
            "visited_facilities": list(self.visited_facilities)
        }
    
    def get_bubble_text(self) -> str:
        """
        获取显示在游客头顶的气泡文本
        返回:
            气泡文本
        """
        return self.get_status_text()


class VisitorGenerator:
    """
    游客生成器，用于批量创建游客
    """
    def __init__(self):
        self.next_id = 1
    
    def generate_visitor(self, x: int, y: int, plan: List[str] = None) -> Visitor:
        """
        生成一个游客
        参数:
            x: 初始x坐标
            y: 初始y坐标
            plan: 游玩计划
        返回:
            Visitor对象
        """
        visitor = Visitor(self.next_id, x, y, plan)
        self.next_id += 1
        return visitor
    
    def generate_batch(self, count: int, entry_x: int, entry_y: int, 
                      facility_names: List[str]) -> List[Visitor]:
        """
        批量生成游客
        参数:
            count: 游客数量
            entry_x: 入口x坐标
            entry_y: 入口y坐标
            facility_names: 可选设施列表
        返回:
            游客列表
        """
        import random
        visitors = []
        
        for _ in range(count):
            if facility_names:
                # 确保plan_length不超过可用设施数量
                max_plan_length = min(4, len(facility_names))
                min_plan_length = min(2, max_plan_length)
                plan_length = random.randint(min_plan_length, max_plan_length)
                plan = random.sample(facility_names, plan_length)
            else:
                plan = []
            
            visitor = self.generate_visitor(entry_x, entry_y, plan)
            visitors.append(visitor)
        
        return visitors