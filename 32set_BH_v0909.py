import geopandas as gpd
import pandas as pd
from tkinter import *
import random
import string
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import tkinter.messagebox
from tkinter import filedialog
import os
import numpy as np
# import openpyxl

# ———————————————————全局变量保存——————————————————————————
# 全局变量保存 GeoDatabase 文件路径和图层名称
g_aux_dir = ""
g_KQ_fn = "2024矿权.shp"
g_ZDQ_fn = "长江缓冲3K.shp"
g_BHQ_fn = "自然保护区.shp"
g_XZQ_fn = "行政区.shp"
g_rail_buf_fn = "铁路缓冲1K.shp"
g_dict_fn = "代码表2024测试.xlsx"
g_data_reg_fn = "当季度落图.shp"
g_year = '2024'
g_quarter = '3K'
# ———————————————————辅助方法——————————————————————————

# 读取代码表格中对应的sheet，存入字典对象
def get_dict(p_path, sht_name, header_row=0):
    # 读取字典Excel文件
    # dict_df = pd.read_excel(p_path, sheet_name=sht_name, usecols=[0, 1])
    dict_df = pd.read_excel(p_path, sheet_name=sht_name, header=header_row, usecols=[0, 1])
    return dict_df

def read_file_with_encoding(file_path, encodings=None):
    """尝试使用不同的编码格式读取文件，直到成功为止"""
    if encodings is None:
        encodings = ['utf-8', 'gb18030']
    for encoding in encodings:
        try:
            return gpd.read_file(file_path, encoding=encoding)
        except Exception as e:
            print(f"尝试使用编码 {encoding} 读取{file_path}文件失败：{e}")
    raise ValueError(f"无法使用提供的编码格式读取文件: {file_path}")


def ensure_valid_field_types(gdf):
    """确保所有字段的值都是Shapefile支持的类型"""
    for column in gdf.columns:
        print(f"字段：列 {column} 的类型为：{gdf[column].dtype}")
        if gdf[column].dtype == 'object':
            for idx, value in enumerate(gdf[column]):
                try:
                    if isinstance(value, bytes):
                        gdf.at[idx, column] = value.decode('utf-8')
                    elif not isinstance(value, str):
                        gdf.at[idx, column] = str(value)
                except Exception as e:
                    print(f"字段转换错误：列 {column} 的第 {idx} 行数据无法转换。错误：{e}")
                    raise
    return gdf


def print_field_sample(gdf):
    """打印每个字段的前几行内容作为样本"""
    for column in gdf.columns:
        print(f"字段名: {column}")
        print(gdf[column].head(5))
        print(f"字段类型: {gdf[column].dtype}")


# ---------------生成KCTBBH字段-------------------
def generate_kctbbh(xiandm, year, quarter, sequence, suffix=''):
    return f"{xiandm}{year}{quarter}{sequence:04d}{suffix}"


def assign_kctbbh(df, year, quarter):
    xiandm_groups = df.groupby('XIANDM')
    result = []

    for xiandm, group in xiandm_groups:
        sequence = 1
        kmxkz_dict = {}
        KMXKZ_cur_no = {}
        KMXKZ_seq = {}

        # 确定使用哪个字段
        if 'KMXKZ' in df.columns:
            kmxkz_field = 'KMXKZ'
        elif 'KDXKZ' in df.columns:
            kmxkz_field = 'KDXKZ'
        else:
            raise ValueError("Neither 'KMXKZ' nor 'KDXKZ' field found in the DataFrame.")
        # 第一次遍历，统计每个KMXKZ的出现次数
        for index, row in group.iterrows():
            kmxkz = row[kmxkz_field]
            if pd.isna(kmxkz) or kmxkz == '':
                continue
            if kmxkz in kmxkz_dict:
                kmxkz_dict[kmxkz] += 1
            else:
                kmxkz_dict[kmxkz] = 1
        # print(f": kmxkz_dict{kmxkz_dict}")
        # 第二次遍历，生成KCTBBH
        for index, row in group.iterrows():
            kmxkz = row[kmxkz_field]
            # Not_minus = True     # 标识 kmxkz_dict[kmxkz]的值是上次循环赋予的1，而不是递减减少到的1
            if pd.isna(kmxkz) or kmxkz == '':
                # KMXKZ为空，正常顺序编号
                kctbbh = generate_kctbbh(xiandm, year, quarter, sequence)
                sequence += 1
            else:
                # print(f"Processing index: {index}, KMXKZ: {kmxkz},出现次数：{kmxkz_dict[kmxkz]}")
                if kmxkz_dict[kmxkz] == 1:
                    # 只有一个KMXKZ，正常编号
                    kctbbh = generate_kctbbh(xiandm, year, quarter, sequence)
                    sequence += 1
                else:
                    if kmxkz not in KMXKZ_cur_no:    # 多个图斑属于一个矿权，但是遍历到了第一次。
                        KMXKZ_cur_no[kmxkz] = 1
                        KMXKZ_seq[kmxkz] = sequence  # 保存kmxkz对应的计数 比如0003A中的3
                        # 第一次出现的KMXKZ，编号为base_sequence + 'A'
                        kctbbh = generate_kctbbh(xiandm, year, quarter, sequence, 'A')
                        sequence += 1
                    else:                            # 多个图斑属于一个矿权，但是遍历到的次数大于1。
                        base_sequence = KMXKZ_seq[kmxkz]
                        suffix = string.ascii_uppercase[KMXKZ_cur_no[kmxkz]]
                        kctbbh = generate_kctbbh(xiandm, year, quarter, base_sequence, suffix)
                        KMXKZ_cur_no[kmxkz] += 1
            result.append((index, kctbbh))
    return result

# # -----------------界面方法--------------------------
# 使窗口局屏幕中央
def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    root.geometry(f'{width}x{height}+{x}+{y}')


def sel_shp_file():
    path_ = askopenfilename(defaultextension=".shp", filetypes=[("shape文件", "*.shp")])
    shp_path.set(path_)

def sel_KM_shp_file():
    path_ = askopenfilename(defaultextension=".shp", filetypes=[("shape文件", "*.shp")])
    shp_KM_path.set(path_)


def set_BH(p_path):
    print(f"测试：{p_path}")
    try:
        # 读取对应的shapefile文件
        KSJC_ply = read_file_with_encoding(p_path)     # gpd.read_file(p_path, encoding='utf-8')
        # 打印字段内容样本进行调试
        print("调试信息：打印字段内容样本")
        # print_field_sample(KSJC_ply)
        # ---------------生成KCTBBH字段-------------------
        # 假设 KSJC_ply 是你的 GeoDataFrame
        year = '2024'
        quarter = '3K'

        # 生成并分配 KCTBBH 编码
        kctbbh_assignments = assign_kctbbh(KSJC_ply, year, quarter)
        kctbbh_dict = dict(kctbbh_assignments)
        KSJC_ply['KCTBBH'] = KSJC_ply.index.map(kctbbh_dict)

        # ---------------生成ZBH字段-----------------------
        def assign_zbh(kctbbh):
            if pd.isna(kctbbh):  # 检查 kctbbh 是否为 NaN
                return ''  # 返回空字符串
            kctbbh = str(kctbbh)  # 将 kctbbh 转换为字符串
            if len(kctbbh) == 17:
                return kctbbh[-1]
            return ''
        KSJC_ply['ZBH'] = KSJC_ply['KCTBBH'].apply(assign_zbh)

        # 保存结果到新的shapefile
        KSJC_ply.to_file(p_path, encoding='gb18030')
        tkinter.messagebox.showinfo("完成", "处理完成！结果已保存到指定文件。")
    except Exception as e:
        print(f'错误，{e}')
        tkinter.messagebox.showerror("错误", f"处理失败：{e}")


def update_KMBH(p_path, p_km_path):
    print(f"更新图斑编号到：{p_path}")
    try:
        # 读取对应的shapefile文件，尝试使用不同的编码格式
        KSJC_ply = read_file_with_encoding(p_path)
        KM_ply = read_file_with_encoding(p_km_path)
        # ---------------------------------更新KM的图斑编号--------------------------------------
        # 1. 将KM的“KCTBBH”全部赋“空值”
        KM_ply['KCTBBH'] = ''

        # 2. 进行相交分析
        for ks_idx, ks_row in KSJC_ply.iterrows():
            # 获取KSJC的KCTBBH值
            ks_kctbbh = ks_row['KCTBBH']
            ks_geometry = ks_row.geometry

            for km_idx, km_row in KM_ply.iterrows():
                km_geometry = km_row.geometry

                # 检查是否相交
                if ks_geometry.intersects(km_geometry):
                    # 将KSJC的KCTBBH赋值给KM
                    KM_ply.at[km_idx, 'KCTBBH'] = ks_kctbbh

        # 3. 给余下的KM图斑编号顺序赋值
        unique_xiandm = KM_ply['XIANDM'].unique()

        # 遍历每个县行政代码
        for xiandm in unique_xiandm:
            # 过滤出当前县行政代码的图斑
            xiandm_km_ply = KM_ply[KM_ply['XIANDM'] == xiandm]

            # 提取已有编号中的数字部分（忽略字母等字符）
            existing_bh = xiandm_km_ply['KCTBBH'].dropna()
            numbers = existing_bh.str.extract(r'(\d{4}K(\d{4}))$')[1].dropna().astype(int)

            # 找出已有编号的最大值
            max_number = numbers.max() if not numbers.empty else 0

            # 开始编号
            start_number = max_number + 1
            prefix = f"{xiandm}20242K"

            # 遍历该县行政代码下的所有图斑，为空的编号依次赋值
            for idx, row in xiandm_km_ply.iterrows():
                if pd.isna(row['KCTBBH']) or row['KCTBBH'] == '':
                    new_bh = f"{prefix}{start_number:04d}"
                    KM_ply.at[idx, 'KCTBBH'] = new_bh
                    start_number += 1

        # 保存KM结果到原shapefile
        print("准备保存到原文件路径")
        KM_ply.to_file(p_km_path, encoding='gb18030')
        tkinter.messagebox.showinfo("完成", f"处理完成！结果已保存到{p_km_path}。")
    except Exception as e:
        print(f'错误，{e}')
        tkinter.messagebox.showerror("错误", f"处理失败：{e}")


if __name__ == '__main__':
    # 初始化Tk()
    root = Tk()

    # 设置标题
    root.title('图斑编号更新')
    shp_path = StringVar()  # 图斑位置
    shp_KM_path = StringVar()  # 图斑位置

    row_index = 1
    Label(root, text="图斑文件路径:").grid(row=row_index, column=0)
    Entry(root, textvariable=shp_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择图斑", width=11, command=sel_shp_file).grid(row=row_index, column=3, columnspan=2, sticky=E)

    # ------------------------------调试------------------------------------------
    ## 生成随机的两位数
    random_number = random.randint(10, 99)

    # shp_path.set(r'W:/09Temp/06/17属性赋值/Data/待赋值.shp')

    row_index = row_index + 1
    debug_btn = Button(root, text='①更新变化图斑编号', width=20, command=lambda: set_BH(shp_path.get()))
    debug_btn.grid(row=row_index, columnspan=5)

    row_index = row_index + 1
    Label(root, text="图斑文件路径:").grid(row=row_index, column=0)
    Entry(root, textvariable=shp_KM_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择图斑", width=11, command=sel_KM_shp_file).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    debug2_btn = Button(root, text='②更新开面图斑编号', width=20,
                       command=lambda: update_KMBH(shp_path.get(), shp_KM_path.get()))
    debug2_btn.grid(row=row_index, columnspan=5)


    # 设置窗口的初始大小
    center_window(root, 470, 20 + row_index * 30)
    root.mainloop()
