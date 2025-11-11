"""
核心功能测试脚本
作者: 奇趣乐园团队
创建时间: 2024-01
功能: 测试模拟器的核心功能
"""
import unittest
import time
from facility import Facility, FacilityFactory
from visitor import Visitor
from data_structures import FacilityQueue, PlanStack, CommandStack, EventQueue


class TestDataStructures(unittest.TestCase):
    """
    测试数据结构
    """
    def test_facility_queue(self):
        """
        测试设施队列功能
        """
        queue = FacilityQueue()
        self.assertEqual(len(queue), 0)
        
        # 测试添加元素
        queue.append("游客1")
        queue.append("游客2")
        self.assertEqual(len(queue), 2)
        
        # 测试弹出元素
        self.assertEqual(queue.pop(), "游客1")
        self.assertEqual(queue.pop(), "游客2")
        self.assertEqual(len(queue), 0)
        
        # 测试空队列弹出
        self.assertIsNone(queue.pop())
    
    def test_plan_stack(self):
        """
        测试行程单栈功能
        """
        stack = PlanStack()
        self.assertTrue(stack.is_empty())
        
        # 测试压入元素
        stack.push("过山车")
        stack.push("摩天轮")
        self.assertEqual(len(stack), 2)
        self.assertEqual(stack.peek(), "摩天轮")
        
        # 测试弹出元素
        self.assertEqual(stack.pop(), "摩天轮")
        self.assertEqual(stack.pop(), "过山车")
        self.assertTrue(stack.is_empty())
        
        # 测试空栈操作
        self.assertIsNone(stack.pop())
        self.assertIsNone(stack.peek())
    
    def test_command_stack(self):
        """
        测试命令栈功能
        """
        stack = CommandStack(max_size=3)
        self.assertFalse(stack.can_undo())
        self.assertFalse(stack.can_redo())
        
        # 测试添加命令
        value = [1]
        
        def add_value():
            value.append(2)
        
        def remove_value():
            if len(value) > 1:
                value.pop()
        
        stack.push(remove_value, add_value)
        self.assertTrue(stack.can_undo())
        self.assertFalse(stack.can_redo())
        
        # 测试撤销和重做
        add_value()
        self.assertEqual(value, [1, 2])
        
        stack.undo()
        self.assertEqual(value, [1])
        self.assertFalse(stack.can_undo())
        self.assertTrue(stack.can_redo())
        
        stack.redo()
        self.assertEqual(value, [1, 2])
        self.assertTrue(stack.can_undo())
        self.assertFalse(stack.can_redo())
    
    def test_event_queue(self):
        """
        测试事件队列功能
        """
        queue = EventQueue()
        self.assertTrue(queue.is_empty())
        
        # 测试添加事件
        queue.push(10, "游客到达", {"id": 1})
        queue.push(5, "设施完成", {"name": "过山车"})
        queue.push(10, "游客到达", {"id": 2})
        self.assertEqual(len(queue), 3)
        
        # 测试弹出事件（按时间排序）
        time1, type1, data1 = queue.pop()
        self.assertEqual(time1, 5)
        self.assertEqual(type1, "设施完成")
        
        time2, type2, data2 = queue.pop()
        self.assertEqual(time2, 10)
        self.assertEqual(data2["id"], 1)  # 时间相同，按添加顺序
        
        time3, type3, data3 = queue.pop()
        self.assertEqual(time3, 10)
        self.assertEqual(data3["id"], 2)
        
        self.assertTrue(queue.is_empty())


class TestSimulationCore(unittest.TestCase):
    """
    测试模拟核心功能
    """
    def test_facility_creation(self):
        """
        测试设施创建
        """
        facility = Facility("过山车", 20, 120, 0, 0)
        self.assertEqual(facility.name, "过山车")
        self.assertEqual(facility.capacity, 20)
        self.assertEqual(facility.run_time, 120)
        self.assertEqual(facility.x, 0)
        self.assertEqual(facility.y, 0)
        
        # 测试工厂方法
        factory_facility = FacilityFactory.create_facility(
            "摩天轮", "摩天轮", 36, 180, 1, 1
        )
        self.assertEqual(factory_facility.name, "摩天轮")
        self.assertEqual(factory_facility.type, "摩天轮")
        self.assertEqual(factory_facility.emoji, "🎡")
    
    def test_visitor_plan(self):
        """
        测试游客行程
        """
        plan = ["过山车", "摩天轮", "旋转木马"]
        visitor = Visitor(1, 0, 0, plan)
        
        # 测试行程栈初始化
        self.assertEqual(visitor.get_next_destination(), "过山车")
        
        # 测试完成一个设施后更新行程
        visitor.end_ride()
        self.assertEqual(visitor.get_next_destination(), "摩天轮")
        self.assertEqual(len(visitor.plan_stack), 2)
        
        visitor.end_ride()
        self.assertEqual(visitor.get_next_destination(), "旋转木马")
        
        visitor.end_ride()
        self.assertIsNone(visitor.get_next_destination())
        self.assertEqual(visitor.status, "完成")
    
    def test_facility_queue_management(self):
        """
        测试设施队列管理
        """
        facility = Facility("过山车", 2, 10, 0, 0)  # 容量为2
        
        # 创建游客并添加到队列
        visitor1 = Visitor(1, 0, 0)
        visitor2 = Visitor(2, 0, 0)
        visitor3 = Visitor(3, 0, 0)
        
        facility.add_visitor(visitor1)
        facility.add_visitor(visitor2)
        facility.add_visitor(visitor3)
        
        # 检查队列长度
        self.assertEqual(facility.get_queue_length(), 3)
        
        # 开始运行，应该能容纳2个游客
        current_time = time.time()
        facility.start_run(current_time)
        
        # 队列中应该剩下1个游客
        self.assertEqual(facility.get_queue_length(), 1)
        self.assertEqual(len(facility.current_visitors), 2)
        
        # 模拟运行结束
        facility._finish_run()
        self.assertEqual(len(facility.current_visitors), 0)
        self.assertEqual(facility.total_visitors_served, 2)


class TestStatistics(unittest.TestCase):
    """
    测试统计功能
    """
    def test_utilization_calculation(self):
        """
        测试利用率计算
        """
        facility = Facility("过山车", 20, 120, 0, 0)
        
        # 初始利用率为0
        self.assertEqual(facility.get_utilization(), 0.0)
        
        # 设置运行和空闲时间
        facility.total_run_time = 60  # 1分钟运行
        facility.total_idle_time = 30  # 30秒空闲
        
        # 利用率应该是 60/(60+30) = 66.666%
        self.assertAlmostEqual(facility.get_utilization(), 66.667, places=3)
    
    def test_avg_waiting_time(self):
        """
        测试平均等待时间估算
        """
        facility = Facility("过山车", 5, 10, 0, 0)  # 容量5，运行时间10秒
        
        # 没有排队时等待时间为0
        self.assertEqual(facility.get_avg_waiting_time(), 0.0)
        
        # 添加6个游客，应该需要2批，等待时间为20秒
        for i in range(6):
            facility.add_visitor(Visitor(i, 0, 0))
        
        self.assertEqual(facility.get_avg_waiting_time(), 20.0)


def run_all_tests():
    """
    运行所有测试
    """
    print("开始测试数据结构...")
    data_structure_suite = unittest.TestLoader().loadTestsFromTestCase(TestDataStructures)
    data_structure_result = unittest.TextTestRunner(verbosity=2).run(data_structure_suite)
    
    print("\n开始测试模拟核心功能...")
    simulation_suite = unittest.TestLoader().loadTestsFromTestCase(TestSimulationCore)
    simulation_result = unittest.TextTestRunner(verbosity=2).run(simulation_suite)
    
    print("\n开始测试统计功能...")
    statistics_suite = unittest.TestLoader().loadTestsFromTestCase(TestStatistics)
    statistics_result = unittest.TextTestRunner(verbosity=2).run(statistics_suite)
    
    # 检查是否所有测试都通过
    all_passed = (data_structure_result.wasSuccessful() and
                 simulation_result.wasSuccessful() and
                 statistics_result.wasSuccessful())
    
    if all_passed:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 有测试失败！")
    
    return all_passed


if __name__ == "__main__":
    run_all_tests()