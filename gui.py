"""
图形界面核心逻辑模块
作者: 奇趣乐园团队
创建时间: 2024-01
功能: 实现地图绘制、按钮事件、图表渲染等GUI功能
"""
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time
from typing import List, Dict, Tuple, Optional, Any

from facility import Facility, FacilityFactory
from visitor import Visitor, VisitorGenerator
from data_structures import CommandStack, EventQueue
from utils import (
    save_layout, load_layout, export_to_excel, generate_random_position,
    calculate_distance, ensure_directory, get_available_colors,
    get_utilization_color, get_queue_color, create_default_facilities
)


class ThemeParkGUI:
    """
    奇趣乐园模拟器图形界面类
    """
    def __init__(self, root: tk.Tk):
        """
        初始化GUI
        参数:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.title("奇趣乐园模拟器")
        self.root.geometry("1400x800")
        
        # 设置中文字体
        self.set_fonts()
        
        # 数据初始化
        self.map_size = 16
        self.cell_size = 40
        self.facilities: Dict[str, Facility] = {}
        self.visitors: List[Visitor] = []
        self.visitor_generator = VisitorGenerator()
        self.command_stack = CommandStack(max_size=5)
        self.event_queue = EventQueue()
        
        # 历史数据
        self.queue_history: Dict[str, List] = {}
        self.utilization_history: Dict[str, List] = {}
        self.waiting_time_history: Dict[str, List] = {}
        self.start_time = time.time()
        
        # 拖拽相关
        self.dragging_facility = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_data = {}
        
        # 图表相关
        self.current_chart_facility = "所有设施"
        self.last_chart_update = 0
        self.chart_update_interval = 1000  # 图表更新间隔（毫秒）
        self.heatmap_update_interval = 300000  # 热力图更新间隔（5分钟）
        
        # 创建界面
        self.create_ui()
        
        # 加载布局或创建默认设施
        self.load_facilities()
        
        # 启动模拟
        self.simulation_running = False
        self.root.after(1000, self.update_simulation)
    
    def set_fonts(self):
        """
        设置支持中文的字体
        """
        # 设置matplotlib字体
        plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "sans-serif"]
        plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
        
        # 创建字体样式
        self.style = ttk.Style()
        # 设置全局字体
        self.style.configure(
            ".",
            font=('SimHei', 10),
            foreground="black"
        )
        # 设置标题字体
        self.style.configure(
            "TLabel",
            font=('SimHei', 10)
        )
        self.style.configure(
            "Title.TLabel",
            font=('SimHei', 12, 'bold')
        )
        self.style.configure(
            "TButton",
            font=('SimHei', 10)
        )
        # 设置Loading Frame样式
        self.style.configure(
            "Loading.TFrame",
            background="white"
        )
    
    def create_ui(self):
        """
        创建用户界面
        """
        # 显示加载屏幕
        self._show_loading_screen()
        
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧控制面板
        self.control_frame = ttk.LabelFrame(self.main_frame, text="控制面板", padding="10")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 设施管理
        self.create_facility_controls()
        
        # 游客管理
        self.create_visitor_controls()
        
        # 操作控制
        self.create_operation_controls()
        
        # 右侧内容区域
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 地图和图表区域分割
        self.map_chart_frame = ttk.Frame(self.content_frame)
        self.map_chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # 地图区域
        self.map_frame = ttk.LabelFrame(self.map_chart_frame, text="乐园地图", padding="10")
        self.map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建地图画布
        self.map_canvas = tk.Canvas(
            self.map_frame,
            width=self.map_size * self.cell_size,
            height=self.map_size * self.cell_size,
            bg="white",
            highlightthickness=1,
            highlightbackground="black"
        )
        self.map_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定拖拽事件
        self.map_canvas.bind("<Button-1>", self.on_map_click)
        self.map_canvas.bind("<B1-Motion>", self.on_map_drag)
        self.map_canvas.bind("<ButtonRelease-1>", self.on_map_release)
        
        # 图表区域
        self.chart_frame = ttk.LabelFrame(self.map_chart_frame, text="数据可视化", padding="10")
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建图表标签页
        self.chart_notebook = ttk.Notebook(self.chart_frame)
        self.chart_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 排队长度图表
        self.create_queue_chart()
        
        # 等待时间热力图
        self.create_heatmap_chart()
        
        # 设施利用率仪表盘
        self.create_utilization_gauge()
        
        # 隐藏加载屏幕
        self.root.after(1500, self._hide_loading_screen)
    
    def _show_loading_screen(self):
        """
        显示加载屏幕
        """
        # 创建一个覆盖整个窗口的加载框架
        self.loading_frame = ttk.Frame(self.root, style="Loading.TFrame")
        self.loading_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # 加载文字
        loading_label = ttk.Label(
            self.loading_frame,
            text="地图加载中...",
            font=('SimHei', 14)
        )
        loading_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def _hide_loading_screen(self):
        """
        隐藏加载屏幕
        """
        self.loading_frame.destroy()
    
    def create_facility_controls(self):
        """
        创建设施管理控制区域
        """
        facility_frame = ttk.LabelFrame(self.control_frame, text="设施管理", padding="10")
        facility_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 设施类型选择
        ttk.Label(facility_frame, text="设施类型:").pack(anchor="w", pady=2)
        self.facility_type_var = tk.StringVar(value="过山车")
        facility_type_frame = ttk.Frame(facility_frame)
        facility_type_frame.pack(fill=tk.X)
        
        for facility_type in FacilityFactory.get_available_types():
            ttk.Radiobutton(
                facility_type_frame,
                text=facility_type,
                variable=self.facility_type_var,
                value=facility_type
            ).pack(side=tk.LEFT, padx=5)
        
        # 新增设施按钮
        ttk.Button(
            facility_frame,
            text="新增设施",
            command=self.add_facility_dialog
        ).pack(fill=tk.X, pady=5)
        
        # 删除设施按钮
        ttk.Button(
            facility_frame,
            text="删除选中设施",
            command=self.delete_selected_facility
        ).pack(fill=tk.X, pady=2)
    
    def create_visitor_controls(self):
        """
        创建游客管理控制区域
        """
        self.visitor_frame = ttk.LabelFrame(self.control_frame, text="游客管理", padding="10")
        self.visitor_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 游客数量输入
        ttk.Label(self.visitor_frame, text="游客数量:").pack(anchor="w", pady=2)
        self.visitor_count_var = tk.StringVar(value="10")
        ttk.Entry(self.visitor_frame, textvariable=self.visitor_count_var, width=10).pack(fill=tk.X)
        
        # 生成游客按钮
        ttk.Button(
            self.visitor_frame,
            text="生成游客",
            command=self.generate_visitors
        ).pack(fill=tk.X, pady=5)
    
    def create_operation_controls(self):
        """
        创建操作控制区域
        """
        operation_frame = ttk.LabelFrame(self.control_frame, text="操作控制", padding="10")
        operation_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 模拟控制
        control_btn_frame = ttk.Frame(operation_frame)
        control_btn_frame.pack(fill=tk.X)
        
        self.simulate_btn = ttk.Button(
            control_btn_frame,
            text="开始模拟",
            command=self.toggle_simulation
        )
        self.simulate_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # 撤销/重做按钮
        self.undo_btn = ttk.Button(
            control_btn_frame,
            text="撤销",
            command=self.undo_operation,
            state=tk.DISABLED
        )
        self.undo_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        self.redo_btn = ttk.Button(
            control_btn_frame,
            text="重做",
            command=self.redo_operation,
            state=tk.DISABLED
        )
        self.redo_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # 导出数据按钮
        ttk.Button(
            operation_frame,
            text="导出Excel",
            command=self.export_data
        ).pack(fill=tk.X, pady=5)
        
        # 图表设施选择
        ttk.Label(operation_frame, text="图表设施:").pack(anchor="w", pady=2)
        self.chart_facility_var = tk.StringVar(value="所有设施")
        self.chart_facility_combo = ttk.Combobox(
            operation_frame,
            textvariable=self.chart_facility_var,
            state="readonly"
        )
        self.chart_facility_combo.pack(fill=tk.X)
        self.chart_facility_combo.bind("<<ComboboxSelected>>", self.on_chart_facility_change)
    
    def create_queue_chart(self):
        """
        创建排队长度折线图
        """
        queue_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(queue_frame, text="排队长度")
        
        # 创建图表
        self.queue_fig, self.queue_ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.queue_ax.set_title("实时排队长度折线图")
        self.queue_ax.set_xlabel("时间")
        self.queue_ax.set_ylabel("排队人数")
        self.queue_ax.grid(True)
        
        # 创建画布
        self.queue_canvas = FigureCanvasTkAgg(self.queue_fig, master=queue_frame)
        self.queue_canvas.draw()
        self.queue_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_heatmap_chart(self):
        """
        创建等待时间热力图
        """
        heatmap_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(heatmap_frame, text="等待时间热力图")
        
        # 创建图表
        self.heatmap_fig, self.heatmap_ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.heatmap_ax.set_title("游客平均等待时间热力图")
        
        # 创建画布
        self.heatmap_canvas = FigureCanvasTkAgg(self.heatmap_fig, master=heatmap_frame)
        self.heatmap_canvas.draw()
        self.heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_utilization_gauge(self):
        """
        创建设施利用率仪表盘
        """
        gauge_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(gauge_frame, text="设施利用率")
        
        # 创建仪表盘框架
        self.gauge_content_frame = ttk.Frame(gauge_frame)
        self.gauge_content_frame.pack(fill=tk.BOTH, expand=True)
    
    def load_facilities(self):
        """
        加载设施布局
        """
        layout_data = load_layout()
        
        if not layout_data:
            # 如果没有布局数据，创建默认设施
            default_facilities = create_default_facilities()
            for facility in default_facilities:
                self.add_facility(facility)
        else:
            # 从布局数据加载设施
            for name, data in layout_data.items():
                facility = Facility.from_dict(data)
                self.add_facility(facility)
    
    def add_facility_dialog(self):
        """
        显示新增设施对话框
        """
        facility_type = self.facility_type_var.get()
        type_info = FacilityFactory.get_type_info(facility_type)
        
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"新增{facility_type}")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 设施名称
        ttk.Label(dialog, text="设施名称:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        name_var = tk.StringVar(value=f"{facility_type}{len(self.facilities) + 1}")
        ttk.Entry(dialog, textvariable=name_var, width=20).grid(row=0, column=1, padx=10, pady=5)
        
        # 设施容量
        ttk.Label(dialog, text="设施容量:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        capacity_var = tk.StringVar(value=str(type_info.get("default_capacity", 20)))
        ttk.Entry(dialog, textvariable=capacity_var, width=20).grid(row=1, column=1, padx=10, pady=5)
        
        # 运行时长
        ttk.Label(dialog, text="运行时长(秒):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        run_time_var = tk.StringVar(value=str(type_info.get("default_run_time", 120)))
        ttk.Entry(dialog, textvariable=run_time_var, width=20).grid(row=2, column=1, padx=10, pady=5)
        
        def confirm():
            try:
                name = name_var.get().strip()
                if not name:
                    messagebox.showerror("错误", "设施名称不能为空")
                    return
                
                if name in self.facilities:
                    messagebox.showerror("错误", "设施名称已存在")
                    return
                
                capacity = int(capacity_var.get())
                if capacity < 1:
                    messagebox.showerror("错误", "设施容量必须大于0")
                    return
                
                run_time = int(run_time_var.get())
                if run_time < 10:
                    messagebox.showerror("错误", "运行时长必须大于等于10秒")
                    return
                
                # 生成随机位置
                existing_positions = [(f.x, f.y) for f in self.facilities.values()]
                x, y = generate_random_position(self.map_size, existing_positions)
                
                # 创建设施
                facility = FacilityFactory.create_facility(
                    name, facility_type, capacity, run_time, x, y
                )
                
                # 添加撤销操作
                def undo_add():
                    self.remove_facility(name)
                
                def redo_add():
                    self.add_facility(facility)
                
                self.command_stack.push(undo_add, redo_add)
                self.update_undo_redo_buttons()
                
                # 实际添加设施
                self.add_facility(facility)
                
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="确定", command=confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def add_facility(self, facility: Facility):
        """
        添加设施到地图
        参数:
            facility: 设施对象
        """
        self.facilities[facility.name] = facility
        self.queue_history[facility.name] = []
        self.utilization_history[facility.name] = []
        self.waiting_time_history[facility.name] = []
        self.update_chart_facility_combo()
        self.draw_map()
        save_layout(list(self.facilities.values()))
    
    def remove_facility(self, facility_name: str):
        """
        从地图移除设施
        参数:
            facility_name: 设施名称
        """
        if facility_name in self.facilities:
            del self.facilities[facility_name]
            self.update_chart_facility_combo()
            self.draw_map()
            save_layout(list(self.facilities.values()))
    
    def delete_selected_facility(self):
        """
        删除选中的设施
        """
        # 这里简化处理，实际应该有选中机制
        if not self.facilities:
            messagebox.showinfo("提示", "没有设施可以删除")
            return
        
        facility_names = list(self.facilities.keys())
        
        if len(facility_names) == 1:
            # 只有一个设施，直接删除
            facility_name = facility_names[0]
        else:
            # 多个设施，让用户选择
            facility_name = simpledialog.askstring(
                "删除设施",
                f"请输入要删除的设施名称\n可选: {', '.join(facility_names)}",
                parent=self.root
            )
            
            if not facility_name or facility_name not in self.facilities:
                messagebox.showinfo("提示", "无效的设施名称")
                return
        
        # 保存设施信息用于重做
        facility = self.facilities[facility_name]
        facility_info = facility.to_dict()
        
        # 添加撤销操作
        def undo_delete():
            self.add_facility(Facility.from_dict(facility_info))
        
        def redo_delete():
            self.remove_facility(facility_name)
        
        self.command_stack.push(undo_delete, redo_delete)
        self.update_undo_redo_buttons()
        
        # 实际删除设施
        self.remove_facility(facility_name)
    
    def generate_visitors(self):
        """
        生成游客
        """
        try:
            count = int(self.visitor_count_var.get())
            if count <= 0:
                messagebox.showerror("错误", "游客数量必须大于0")
                return
            
            # 在入口位置生成游客（假设在地图左上角）
            entry_x, entry_y = 0, 0
            
            # 获取可用的设施名称列表
            facility_names = list(self.facilities.keys())
            if not facility_names:
                messagebox.showinfo("提示", "请先添加设施")
                return
            
            # 生成游客
            new_visitors = self.visitor_generator.generate_batch(
                count, entry_x, entry_y, facility_names
            )
            
            self.visitors.extend(new_visitors)
            self.draw_map()
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def toggle_simulation(self):
        """
        切换模拟状态
        """
        if self.simulation_running:
            self.simulation_running = False
            self.simulate_btn.config(text="开始模拟")
        else:
            self.simulation_running = True
            self.simulate_btn.config(text="暂停模拟")
    
    def update_simulation(self):
        """
        更新模拟状态
        """
        current_time = time.time()
        
        if self.simulation_running:
            # 更新设施状态
            for facility in self.facilities.values():
                facility.update_status(current_time)
                
                # 如果设施空闲且有游客在排队，开始运行
                if not facility.is_running and facility.get_queue_length() > 0:
                    facility.start_run(current_time)
                
                # 更新历史数据
                self.queue_history[facility.name].append(
                    (current_time, facility.get_queue_length())
                )
                self.utilization_history[facility.name].append(
                    (current_time, facility.get_utilization())
                )
            
            # 更新游客状态
            for visitor in self.visitors:
                if visitor.status == "自由" and visitor.target_facility:
                    # 向目标设施移动
                    target_facility = self.facilities.get(visitor.target_facility)
                    if target_facility:
                        if visitor.move_towards(target_facility.x, target_facility.y):
                            # 到达设施，开始等待
                            visitor.start_waiting()
                            target_facility.add_visitor(visitor)
                elif visitor.status == "游玩":
                    # 检查是否游玩结束
                    # 这里简化处理，实际应该与设施运行同步
                    pass
            
            # 更新图表（每秒更新一次）
            if current_time - self.last_chart_update >= 1.0:
                self.update_charts()
                self.last_chart_update = current_time
        
        # 重绘地图（无论是否运行都需要绘制）
        self.draw_map()
        
        # 继续更新
        self.root.after(100, self.update_simulation)
    
    def draw_map(self):
        """
        绘制地图
        """
        self.map_canvas.delete("all")
        
        # 绘制网格
        for i in range(self.map_size + 1):
            x = i * self.cell_size
            y = i * self.cell_size
            self.map_canvas.create_line(x, 0, x, self.map_size * self.cell_size)
            self.map_canvas.create_line(0, y, self.map_size * self.cell_size, y)
        
        # 绘制设施
        for facility in self.facilities.values():
            x1 = facility.x * self.cell_size
            y1 = facility.y * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            
            # 设施背景
            fill_color = "lightblue" if facility.is_running else "lightgray"
            self.map_canvas.create_rectangle(
                x1, y1, x2, y2, fill=fill_color, outline="black"
            )
            
            # 设施图标
            self.map_canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2 - 10,
                text=facility.emoji,
                font=("SimHei", 16)
            )
            
            # 设施名称
            self.map_canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2 + 10,
                text=facility.name,
                font=("SimHei", 8)
            )
            
            # 排队人数
            queue_length = facility.get_queue_length()
            color = get_queue_color(queue_length)
            self.map_canvas.create_text(
                x1 + 10, y1 + 10,
                text=f"{queue_length}",
                fill=color,
                font=("SimHei", 10, "bold")
            )
            
            # 保存设施位置信息，用于拖拽
            self.map_canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="", outline="", tags=("facility", facility.name)
            )
        
        # 绘制游客
        for visitor in self.visitors:
            x = visitor.x * self.cell_size + self.cell_size / 2
            y = visitor.y * self.cell_size + self.cell_size / 2
            
            # 游客图标
            self.map_canvas.create_text(
                x, y,
                text=visitor.emoji,
                font=("SimHei", 14)
            )
            
            # 气泡文本
            bubble_text = visitor.get_bubble_text()
            bubble_width = len(bubble_text) * 8
            bubble_height = 20
            
            # 绘制气泡背景
            self.map_canvas.create_rectangle(
                x - bubble_width / 2 - 5,
                y - bubble_height - 15,
                x + bubble_width / 2 + 5,
                y - 15,
                fill="white",
                outline="black",
                width=1
            )
            
            # 绘制气泡文本
            self.map_canvas.create_text(
                x,
                y - bubble_height / 2 - 15,
                text=bubble_text,
                font=("SimHei", 8)
            )
    
    def on_map_click(self, event):
        """
        处理地图点击事件
        """
        # 获取点击位置的设施
        items = self.map_canvas.find_closest(event.x, event.y)
        if items:
            tags = self.map_canvas.gettags(items[0])
            if "facility" in tags and len(tags) > 1:
                facility_name = tags[1]
                if facility_name in self.facilities:
                    self.dragging_facility = facility_name
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y
                    self.drag_data = {
                        "x": self.facilities[facility_name].x,
                        "y": self.facilities[facility_name].y
                    }
    
    def on_map_drag(self, event):
        """
        处理地图拖拽事件
        """
        if self.dragging_facility:
            # 计算拖拽位置对应的网格坐标
            grid_x = min(max(0, event.x // self.cell_size), self.map_size - 1)
            grid_y = min(max(0, event.y // self.cell_size), self.map_size - 1)
            
            # 检查是否与其他设施位置冲突
            collision = False
            for name, facility in self.facilities.items():
                if name != self.dragging_facility and facility.x == grid_x and facility.y == grid_y:
                    collision = True
                    break
            
            if not collision:
                # 临时移动设施显示
                facility = self.facilities[self.dragging_facility]
                facility.x = grid_x
                facility.y = grid_y
                self.draw_map()
    
    def on_map_release(self, event):
        """
        处理地图释放事件
        """
        if self.dragging_facility:
            facility = self.facilities[self.dragging_facility]
            old_x = self.drag_data["x"]
            old_y = self.drag_data["y"]
            new_x = facility.x
            new_y = facility.y
            
            # 如果位置有变化，记录操作
            if old_x != new_x or old_y != new_y:
                # 添加撤销操作
                def undo_move():
                    facility.move(old_x, old_y)
                    save_layout(list(self.facilities.values()))
                
                def redo_move():
                    facility.move(new_x, new_y)
                    save_layout(list(self.facilities.values()))
                
                self.command_stack.push(undo_move, redo_move)
                self.update_undo_redo_buttons()
                
                # 保存新位置
                save_layout(list(self.facilities.values()))
            
            self.dragging_facility = None
            self.drag_data = {}
    
    def update_undo_redo_buttons(self):
        """
        更新撤销/重做按钮状态
        """
        self.undo_btn.config(state=tk.NORMAL if self.command_stack.can_undo() else tk.DISABLED)
        self.redo_btn.config(state=tk.NORMAL if self.command_stack.can_redo() else tk.DISABLED)
    
    def undo_operation(self):
        """
        执行撤销操作
        """
        if self.command_stack.undo():
            self.update_undo_redo_buttons()
    
    def redo_operation(self):
        """
        执行重做操作
        """
        if self.command_stack.redo():
            self.update_undo_redo_buttons()
    
    def update_chart_facility_combo(self):
        """
        更新图表设施选择下拉框
        """
        values = ["所有设施"] + list(self.facilities.keys())
        self.chart_facility_combo['values'] = values
    
    def on_chart_facility_change(self, event):
        """
        处理图表设施选择变化
        """
        self.current_chart_facility = self.chart_facility_var.get()
    
    def update_charts(self):
        """
        更新所有图表
        """
        self.update_queue_chart()
        self.update_heatmap_chart()
        self.update_utilization_gauge()
    
    def update_queue_chart(self):
        """
        更新排队长度折线图
        """
        self.queue_ax.clear()
        self.queue_ax.set_title("实时排队长度折线图")
        self.queue_ax.set_xlabel("时间")
        self.queue_ax.set_ylabel("排队人数")
        self.queue_ax.grid(True)
        
        colors = get_available_colors(len(self.facilities))
        current_time = time.time()
        
        if self.current_chart_facility == "所有设施":
            # 显示所有设施
            for i, (name, history) in enumerate(self.queue_history.items()):
                if len(history) > 0:
                    times = [(t - self.start_time) for t, _ in history]
                    values = [v for _, v in history]
                    self.queue_ax.plot(times, values, label=name, color=colors[i % len(colors)])
            self.queue_ax.legend()
        else:
            # 显示单个设施
            if self.current_chart_facility in self.queue_history:
                history = self.queue_history[self.current_chart_facility]
                if len(history) > 0:
                    times = [(t - self.start_time) for t, _ in history]
                    values = [v for _, v in history]
                    self.queue_ax.plot(times, values, label=self.current_chart_facility, color=colors[0])
                    self.queue_ax.legend()
        
        # 设置x轴标签格式
        import matplotlib.dates as mdates
        from datetime import datetime, timedelta
        
        # 转换时间显示格式
        def format_time(x, pos=None):
            seconds = int(x)
            mins, secs = divmod(seconds, 60)
            return f"{mins}:{secs:02d}"
        
        self.queue_ax.xaxis.set_major_formatter(format_time)
        
        # 只显示最近100个数据点的标签
        for label in self.queue_ax.get_xticklabels():
            label.set_fontsize(8)
        
        self.queue_fig.tight_layout()
        self.queue_canvas.draw()
    
    def update_heatmap_chart(self):
        """
        更新等待时间热力图
        """
        # 这里简化处理，实际应该计算不同时间段的平均等待时间
        self.heatmap_ax.clear()
        self.heatmap_ax.set_title("游客平均等待时间热力图")
        
        if not self.facilities:
            self.heatmap_canvas.draw()
            return
        
        # 生成示例数据
        facility_names = list(self.facilities.keys())
        time_slots = ["0-10分钟", "10-20分钟", "20-30分钟", "30-40分钟", "40-50分钟", "50-60分钟"]
        
        # 模拟等待时间数据
        import numpy as np
        data = np.random.randint(0, 60, size=(len(time_slots), len(facility_names))) / 10
        
        # 绘制热力图
        im = self.heatmap_ax.imshow(data, cmap="Reds")
        
        # 设置标签
        self.heatmap_ax.set_xticks(np.arange(len(facility_names)))
        self.heatmap_ax.set_yticks(np.arange(len(time_slots)))
        self.heatmap_ax.set_xticklabels(facility_names, rotation=45, ha="right", fontsize=8)
        self.heatmap_ax.set_yticklabels(time_slots, fontsize=8)
        
        # 添加颜色条
        cbar = self.heatmap_fig.colorbar(im, ax=self.heatmap_ax)
        cbar.set_label("平均等待时间(分钟)")
        
        # 在热力图上标注数值
        for i in range(len(time_slots)):
            for j in range(len(facility_names)):
                text = self.heatmap_ax.text(j, i, f"{data[i, j]:.1f}",
                                         ha="center", va="center", color="black", fontsize=6)
        
        self.heatmap_fig.tight_layout()
        self.heatmap_canvas.draw()
    
    def update_utilization_gauge(self):
        """
        更新设施利用率仪表盘
        """
        # 清空现有内容
        for widget in self.gauge_content_frame.winfo_children():
            widget.destroy()
        
        if not self.facilities:
            ttk.Label(self.gauge_content_frame, text="暂无设施数据").pack(pady=20)
            return
        
        # 创建一个网格布局
        max_cols = 3
        row = 0
        col = 0
        
        for facility in self.facilities.values():
            utilization = facility.get_utilization()
            color = get_utilization_color(utilization)
            
            # 创建设施利用率卡片
            gauge_card = ttk.LabelFrame(self.gauge_content_frame, text=facility.name, padding="10")
            gauge_card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # 利用率文本
            utilization_label = ttk.Label(
                gauge_card,
                text=f"{utilization:.1f}%",
                foreground=color,
                font=('SimHei', 16, 'bold')
            )
            utilization_label.pack(pady=10)
            
            # 更新网格位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 设置网格权重
        for i in range(row + 1):
            self.gauge_content_frame.rowconfigure(i, weight=1)
        for i in range(max_cols):
            self.gauge_content_frame.columnconfigure(i, weight=1)
    
    def export_data(self):
        """
        导出数据到Excel
        """
        if not self.facilities:
            messagebox.showinfo("提示", "暂无数据可导出")
            return
        
        # 导出数据
        filename = export_to_excel(
            list(self.facilities.values()),
            self.queue_history,
            self.utilization_history
        )
        
        if filename:
            messagebox.showinfo("成功", f"数据已导出到:\n{filename}")
        else:
            messagebox.showerror("错误", "数据导出失败")