import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
from pathlib import Path

class ExcelRankerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel名次填充工具 (Tk版)")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        # 数据变量
        self.file_path = ""
        self.df = None
        self.start_row_num = 1  # 记录实际起始行号
        self.original_df = None  # 保存原始DataFrame用于显示原始数据
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 文件选择
        ttk.Label(main_frame, text="Excel文件:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.file_label = ttk.Label(main_frame, text="未选择", foreground="gray", width=40)
        self.file_label.grid(row=0, column=1, sticky=tk.W, padx=(10,0))
        ttk.Button(main_frame, text="选择文件", command=self.select_file).grid(row=0, column=2, padx=(10,0))
        
        # 起始行设置
        ttk.Label(main_frame, text="数据起始行:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.start_row_var = tk.StringVar(value="1")
        start_row_entry = ttk.Entry(main_frame, textvariable=self.start_row_var, width=10)
        start_row_entry.grid(row=1, column=1, sticky=tk.W, padx=(10,0))
        ttk.Label(main_frame, text="(Excel行号，跳过标题行)").grid(row=1, column=2, sticky=tk.W, padx=(10,0))
        
        # 列选择区域
        ttk.Label(main_frame, text="列选择:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(15,8))
        
        # 排名依据列
        ttk.Label(main_frame, text="排名依据列:").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.data_col_combo = ttk.Combobox(main_frame, state="readonly", width=35)
        self.data_col_combo.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=(10,0))
        
        # 班级列
        ttk.Label(main_frame, text="班级列 (可选):").grid(row=4, column=0, sticky=tk.W, pady=8)
        self.class_col_combo = ttk.Combobox(main_frame, state="readonly", width=35)
        self.class_col_combo.grid(row=4, column=1, columnspan=2, sticky=tk.W, padx=(10,0))
        self.class_col_combo.set("无")  # 默认值
        
        # 结果列名
        ttk.Label(main_frame, text="结果列名设置:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, pady=(15,8))
        
        ttk.Label(main_frame, text="总排名列名:").grid(row=6, column=0, sticky=tk.W, pady=8)
        self.rank_name_var = tk.StringVar(value="总排名")
        ttk.Entry(main_frame, textvariable=self.rank_name_var, width=20).grid(row=6, column=1, sticky=tk.W, padx=(10,0))
        
        ttk.Label(main_frame, text="班级排名列名:").grid(row=7, column=0, sticky=tk.W, pady=8)
        self.class_rank_name_var = tk.StringVar(value="班级排名")
        ttk.Entry(main_frame, textvariable=self.class_rank_name_var, width=20).grid(row=7, column=1, sticky=tk.W, padx=(10,0))
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=3, pady=(20,15))
        
        self.process_btn = ttk.Button(button_frame, text="开始计算", 
                                    command=self.start_processing, state="disabled")
        self.process_btn.pack(side=tk.LEFT, padx=8)
        
        self.save_btn = ttk.Button(button_frame, text="保存结果", 
                                 command=self.save_results, state="disabled")
        self.save_btn.pack(side=tk.LEFT, padx=8)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=450)
        self.progress.grid(row=9, column=0, columnspan=3, pady=15)
        
        # 状态栏
        self.status_var = tk.StringVar(value="请选择Excel文件")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10,0))
    
    def select_file(self):
        """选择Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls")]
        )
        
        if not file_path:
            return
            
        self.file_path = file_path
        self.file_label.config(text=Path(file_path).name)
        self.status_var.set("正在读取文件...")
        
        try:
            # 获取起始行
            start_row = int(self.start_row_var.get())
            if start_row < 1:
                raise ValueError("起始行必须大于0")
            self.start_row_num = start_row  # 保存起始行号
                
            # 读取Excel（跳过起始行之前的所有行）
            self.original_df = pd.read_excel(file_path)  # 保存完整原始数据
            self.df = pd.read_excel(file_path, skiprows=start_row-1)  # 跳过起始行
            
            # 更新列下拉框
            columns = ["无"] + list(self.df.columns)
            self.data_col_combo['values'] = self.df.columns.tolist()
            self.class_col_combo['values'] = columns
            
            # 设置默认选择
            if len(self.df.columns) > 0:
                self.data_col_combo.set(self.df.columns[0])
                self.class_col_combo.set("无")
            
            self.status_var.set(f"读取成功: {len(self.df)}行数据 (跳过前{start_row-1}行)")
            self.process_btn['state'] = 'normal'
            self.progress['value'] = 0
            
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取文件:\n{str(e)}")
            self.status_var.set("读取失败")
    
    def start_processing(self):
        """开始处理"""
        if self.df is None or self.original_df is None:
            messagebox.showwarning("警告", "请先选择并读取文件")
            return
            
        try:
            # 获取参数
            data_col = self.data_col_combo.get()
            class_col = self.class_col_combo.get()
            rank_name = self.rank_name_var.get().strip() or "总排名"
            class_rank_name = self.class_rank_name_var.get().strip() or "班级排名"
            
            if not data_col:
                messagebox.showwarning("警告", "请选择排名依据列")
                return
                
            if data_col not in self.df.columns:
                messagebox.showerror("错误", f"列'{data_col}'不存在")
                return
                
            self.status_var.set("正在计算排名...")
            self.progress['value'] = 30
            
            # 处理数据
            df = self.df.copy()
            
            # 转换为数值
            if not pd.api.types.is_numeric_dtype(df[data_col]):
                df[data_col] = pd.to_numeric(df[data_col], errors='coerce')
                na_mask = df[data_col].isna()
                na_count = na_mask.sum()
                
                if na_count > 0:
                    # 获取无效数据的详细信息（使用原始DataFrame显示真实数据）
                    na_indices = df[na_mask].index.tolist()
                    excel_rows = [self.start_row_num + idx for idx in na_indices]
                    
                    # 从原始DataFrame获取真实原始数据（注意索引对应关系）
                    invalid_details = []
                    for i, (df_idx, excel_row) in enumerate(zip(na_indices[:5], excel_rows[:5])):
                        # 注意：df_idx是处理后的DataFrame索引，需要映射回原始DataFrame
                        original_idx = df_idx  # 因为跳过了起始行，索引是对应的
                        if original_idx < len(self.original_df):
                            original_value = str(self.original_df.iloc[original_idx][data_col])
                            invalid_details.append(f"Excel第{excel_row}行: '{original_value}'")
                    
                    details_text = "\n".join(invalid_details)
                    if na_count > 5:
                        details_text += f"\n... 还有{na_count-5}行类似数据"
                    
                    # 显示详细提示
                    if messagebox.askyesno("发现无效数据", 
                                         f"在'{data_col}'列中发现{na_count}个非数值数据:\n\n"
                                         f"{details_text}\n\n"
                                         f"是否跳过这些行继续处理？"):
                        df = df.dropna(subset=[data_col]).reset_index(drop=True)
                        self.status_var.set(f"已跳过{na_count}行无效数据")
                    else:
                        self.status_var.set("用户取消操作")
                        return
                        
            # 计算总排名
            rank_series = df[data_col].rank(ascending=False, method='min')
            df[rank_name] = rank_series.fillna(0).astype(int)
            self.progress['value'] = 60
            
            # 计算班级排名
            if class_col and class_col != "无":
                if class_col in df.columns:
                    class_rank_series = df.groupby(class_col)[data_col].rank(ascending=False, method='min')
                    df[class_rank_name] = class_rank_series.fillna(0).astype(int)
                    # df[class_rank_name] = df.groupby(class_col)[data_col].rank(
                    #     ascending=False, method='min').astype(int)
                    self.progress['value'] = 80
                else:
                    messagebox.showwarning("警告", f"班级列'{class_col}'不存在")
            
            # 完成
            self.df = df
            self.progress['value'] = 100
            
            # 生成统计信息
            msg = f"计算完成！\n总数据: {len(self.df)}行"
            if class_col != "无" and class_col in df.columns:
                msg += f"\n班级数: {df[class_col].nunique()}"
            self.status_var.set(msg)
            self.save_btn['state'] = 'normal'
            
        except Exception as e:
            messagebox.showerror("处理失败", f"计算过程中出错:\n{str(e)}")
            self.status_var.set("处理失败")
            self.progress['value'] = 0
    
    def save_results(self):
        """保存结果"""
        if self.df is None:
            messagebox.showwarning("警告", "没有可保存的数据")
            return
            
        save_path = filedialog.asksaveasfilename(
            title="保存结果",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")]
        )
        
        if not save_path:
            return
            
        try:
            self.df.to_excel(save_path, index=False)
            messagebox.showinfo("保存成功", f"结果已保存至:\n{save_path}")
            self.status_var.set(f"已保存: {Path(save_path).name}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存文件失败:\n{str(e)}")

def main():
    root = tk.Tk()
    app = ExcelRankerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()