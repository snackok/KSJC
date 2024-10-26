import geopandas as gpd
import pandas as pd
from tkinter import *
import random
import string
from tkinter.filedialog import askopenfilename, asksaveasfilename
import tkinter.messagebox
from tkinter import filedialog
import os
import numpy as np
# import openpyxl

# ———————————————————全局变量保存——————————————————————————
# 全局变量保存 GeoDatabase 文件路径和图层名称
g_KQ_fn = "2024矿权.shp"
g_ZDQ_fn = "长江缓冲3K.shp"
g_BHQ_fn = "自然保护区.shp"
g_XZQ_fn = "行政区.shp"
g_rail_buf_fn = "铁路缓冲1K.shp"
g_dict_fn = "代码表2024测试.xlsx"
g_data_reg_fn = "当季度落图.shp"
g_year = '2024'
g_quarter = '3K'

# 定义调试模式标志
DEBUG_MODE = False  # 在正式打包时将其设置为 False
if DEBUG_MODE:
    # ———————————————————调试变量赋值——————————————————————————
    g_exl_input = f'W:/09Temp/10/B/贵州YXY/52贵州省.xlsx'
    g_TB_input = f"W:/09Temp/10/B/贵州YXY/贵州YXY/52贵州省-露天矿山-开发占地-KF.shp"
    g_KQ_input = f"W:/01Work/01HZJC/2024/Data/D01_矿权/202403矿权/520000CK202401.shp"
    g_LT_input = f"W:/09Temp/10/B/贵州YXY/贵州YXY/2023至2024落图范围.shp"
    random_number = random.randint(10, 99)
    g_dbg_output = f"W:/09Temp/10/B/贵州YXY/贵州YXY/T{random_number}.xlsx"

else:
    # 正式模式下，通常不会赋值调试变量
    g_exl_input = ""
    g_TB_input = ""
    g_KQ_input = ""
    g_LT_input = ""
    g_dbg_output = ""
# ———————————————————辅助方法——————————————————————————

# ---------------------初始化---------------------------

def read_file_with_encoding(file_path, encodings=None):
    """尝试使用不同的编码格式读取文件，直到成功为止，返回文件编码"""
    if encodings is None:
        encodings = ['utf-8', 'gb18030']

    for encoding in encodings:
        try:
            # 读取文件
            data = gpd.read_file(file_path, encoding=encoding)
            # 返回读取的数据和编码
            return data, encoding
        except Exception as e:
            print(f"尝试使用编码 {encoding} 读取 {file_path} 文件失败：{e}")

    raise ValueError(f"无法使用提供的编码格式读取文件: {file_path}")

# # -----------------界面方法--------------------------
# 使窗口局屏幕中央
def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f'{width}x{height}+{x}+{y}')


def sel_exl_file():
    print("xx")
    path_ = askopenfilename(defaultextension=".xlsx", filetypes=[("Excel文件", "*.xlsx")])
    exl_path.set(path_)


def sel_shp_file(target_path_var):
    path_ = askopenfilename(defaultextension=".shp", filetypes=[("shape文件", "*.shp")])
    target_path_var.set(path_)  # 动态设置路径变量


def sel_output_file(p_flag=1):
    path_ = asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
    output_path.set(path_)


def My_debug(p_path):
    print(f"debug{p_path}")


def do_excel(p_excel, p_TB_shp, p_KQ_shp, p_LT_shp, p_output_path):
    try:
        print(f"更新 {p_excel}, {p_TB_shp}, {p_KQ_shp}, {p_output_path}")

        # 读取图斑和矿权 shapefile
        TB_ply, TB_encoding = read_file_with_encoding(p_TB_shp)
        KQ_ply, KQ_encoding = read_file_with_encoding(p_KQ_shp)
        LT_ply, LT_encoding = read_file_with_encoding(p_LT_shp)
        # 读取 Excel 文件到 DataFrame
        df_exl = pd.read_excel(p_excel)

        # 初始化 "1_是否疑似越界" 列为 "否"
        df_exl["1_是否疑似越界"] = "否"

        # 遍历 DataFrame 中的每个许可证号
        for index, row in df_exl.iterrows():
            license_number = row["许可证号"]
            # 查找与许可证号匹配的矿权记录
            kq_records = KQ_ply[KQ_ply['XKZH'] == license_number]
            if not kq_records.empty:
                # 遍历所有匹配的矿权记录
                for _, kq_row in kq_records.iterrows():
                    # 获取当前矿权的边界
                    kq_boundary = kq_row.geometry
                    # 查找与该矿权记录相交的图斑
                    intersects = TB_ply[TB_ply.geometry.intersects(kq_boundary) & (TB_ply['KFZDFS'] == "10")]
                    # 检查图斑是否超出矿权边界
                    if not intersects.empty:
                        # 检查是否有图斑超出矿权边界
                        for _, tb_row in intersects.iterrows():
                            if not tb_row.geometry.within(kq_boundary):
                                df_exl.at[index, "1_是否疑似越界"] = "是"
                                break  # 一旦找到超出边界的情况，停止检查
                    if df_exl.at[index, "1_是否疑似越界"] == "是":
                        break  # 如果已判定为超出，停止遍历矿权记录

                    # 查找与该矿权记录相交的落图记录
                    intersects2 = LT_ply[LT_ply.geometry.intersects(kq_boundary)]
                    if not intersects2.empty:
                        # 提取交叉的落图记录中的“DATE”字段，并选取最新的日期
                        max_date = pd.to_datetime(intersects2['DATE']).max()

                        # 更新 Excel 中 "3_遥感影像时相" 列为最新的日期
                        df_exl.at[index, "3_遥感影像时相"] = max_date.strftime("%Y%m%d")

        # 将更新结果输出为新的 Excel 文件
        df_exl.to_excel(p_output_path, index=False)
        tkinter.messagebox.showinfo("完成", f"更新结果已保存到 {p_output_path}")
        print(f"更新结果已保存到 {p_output_path}")
    except Exception as e:
        print(f'错误，{e}')
        tkinter.messagebox.showerror("错误", f"处理失败：{e}")


if __name__ == '__main__':
    # 初始化Tk()
    root = Tk()

    # 设置标题
    root.title('露天矿山更新属性')
    exl_path = StringVar()  # excel位置
    TB_path = StringVar()  # 图斑位置 = StringVar()  # 图斑shp位置
    KQ_path = StringVar()  # 矿权shp位置
    LT_path = StringVar()  # 落图shp位置
    output_path = StringVar()  # 输出文件

    row_index = 1
    Label(root, text="Excel统计文件:").grid(row=row_index, column=0)
    Entry(root, textvariable=exl_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择文件", width=11, command=sel_exl_file).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="图斑文件路径:").grid(row=row_index, column=0)
    Entry(root, textvariable=TB_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择图斑", width=11, command=lambda: sel_shp_file(TB_path)).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="矿权文件路径:").grid(row=row_index, column=0)
    Entry(root, textvariable=KQ_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择矿权", width=11, command=lambda: sel_shp_file(KQ_path)).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="落图文件路径:").grid(row=row_index, column=0)
    Entry(root, textvariable=LT_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择落图数据", width=11, command=lambda: sel_shp_file(LT_path)).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="输出文件:").grid(row=row_index, column=0)
    Entry(root, textvariable=output_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5)
    Button(root, text="输出图斑", width=11, command=sel_output_file).grid(row=row_index, column=3, columnspan=2,
                                                                          sticky=E)

    row_index = row_index + 1
    Button(root, text='执行', width=20,
           command=lambda: do_excel(exl_path.get(), TB_path.get(),KQ_path.get(),LT_path.get(),output_path.get())).grid(row=row_index, columnspan=5)
    # ------------------------------调试------------------------------------------

    exl_path.set(g_exl_input)
    TB_path.set(g_TB_input)
    KQ_path.set(g_KQ_input)
    LT_path.set(g_LT_input)
    output_path.set(g_dbg_output)

    # 设置窗口的初始大小
    center_window(root, 470, 20 + row_index * 30)
    root.mainloop()
