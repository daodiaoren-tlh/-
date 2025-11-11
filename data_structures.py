"""
数据结构工具模块
作者: 奇趣乐园团队
创建时间: 2024-01
功能: 实现队列和栈的数据结构
"""
import collections
import heapq
from typing import Any, Callable, List, Tuple, Dict


class FacilityQueue:
    """
    设施排队队列
    使用collections.deque实现，支持快速的append和pop操作
    """
    def __init__(self):
        self.queue = collections.deque()
    
    def append(self, item: Any) -> None:
        """添加元素到队列尾部"""
        self.queue.append(item)
    
    def pop(self) -> Any:
        """从队列头部移除并返回元素"""
        if not self.queue:
            return None
        return self.queue.popleft()
    
    def __len__(self) -> int:
        """返回队列长度"""
        return len(self.queue)
    
    def __iter__(self):
        """返回队列迭代器"""
        return iter(self.queue)


class EventQueue:
    """
    事件优先级队列
    使用heapq实现，按事件时间排序
    """
    def __init__(self):
        self.events = []
        self.event_id = 0  # 用于确保事件时间相同时的稳定排序
    
    def push(self, time: float, event_type: str, data: Dict[str, Any]) -> None:
        """
        添加事件到优先级队列
        参数:
            time: 事件发生时间
            event_type: 事件类型
            data: 事件数据
        """
        # 使用(event_id, time, event_type, data)作为堆元素，确保相同时间的事件按添加顺序排序
        heapq.heappush(self.events, (time, self.event_id, event_type, data))
        self.event_id += 1
    
    def pop(self) -> Tuple[float, str, Dict[str, Any]]:
        """
        移除并返回最早发生的事件
        返回:
            (time, event_type, data)元组
        """
        if not self.events:
            return None
        time, _, event_type, data = heapq.heappop(self.events)
        return time, event_type, data
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return len(self.events) == 0
    
    def __len__(self) -> int:
        """返回队列中的事件数量"""
        return len(self.events)


class PlanStack:
    """
    游客行程单栈
    使用list实现，支持append和pop操作
    """
    def __init__(self):
        self.stack = []
    
    def push(self, item: str) -> None:
        """添加元素到栈顶"""
        self.stack.append(item)
    
    def pop(self) -> str:
        """从栈顶移除并返回元素"""
        if not self.stack:
            return None
        return self.stack.pop()
    
    def peek(self) -> str:
        """查看栈顶元素但不移除"""
        if not self.stack:
            return None
        return self.stack[-1]
    
    def is_empty(self) -> bool:
        """检查栈是否为空"""
        return len(self.stack) == 0
    
    def __len__(self) -> int:
        """返回栈的长度"""
        return len(self.stack)


class CommandStack:
    """
    命令栈，用于撤销/重做操作
    """
    def __init__(self, max_size: int = 5):
        self.undo_stack = []  # 撤销栈
        self.redo_stack = []  # 重做栈
        self.max_size = max_size  # 最大历史记录数
    
    def push(self, undo_func: Callable, redo_func: Callable) -> None:
        """
        添加操作到撤销栈
        参数:
            undo_func: 撤销函数
            redo_func: 重做函数
        """
        self.undo_stack.append((undo_func, redo_func))
        # 限制撤销栈大小
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        # 清空重做栈
        self.redo_stack.clear()
    
    def undo(self) -> bool:
        """
        执行撤销操作
        返回:
            是否成功撤销
        """
        if not self.undo_stack:
            return False
        undo_func, redo_func = self.undo_stack.pop()
        undo_func()
        self.redo_stack.append((undo_func, redo_func))
        return True
    
    def redo(self) -> bool:
        """
        执行重做操作
        返回:
            是否成功重做
        """
        if not self.redo_stack:
            return False
        undo_func, redo_func = self.redo_stack.pop()
        redo_func()
        self.undo_stack.append((undo_func, redo_func))
        return True
    
    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """检查是否可以重做"""
        return len(self.redo_stack) > 0