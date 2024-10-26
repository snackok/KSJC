import geopandas as gpd
import pandas as pd
from tkinter import *
import random
import os
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import tkinter.messagebox

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


def sel_model_file():
    path_ = askopenfilename(defaultextension=".shp", filetypes=[("shape文件", "*.shp")])
    model_path.set(path_)


def sel_output_file(p_flag=1):
    path_ = asksaveasfilename(defaultextension=".shp", filetypes=[("Shapefile", "*.shp")])
    output_path.set(path_)


def do_work(p_shp_path, p_model_path, p_output_path):
    try:
        # 读取老shp文件
        old_ply = gpd.read_file(p_shp_path)
        # 读取新shp模板文件
        new_ply = gpd.read_file(p_model_path)  # r"W:/09Temp/06/新老图斑转化/new_shape_KM.shp"

        # 新shp文件的字段
        new_fields = new_ply.columns.tolist()

        # 字段名称映射
        field_mapping = {
            "Area": "KMZDMJ",
            "XZQDM": "XIANDM",
            "备注": "KMBZ",
            "TLYX_1km_": "TL",
            "TBZBH": "ZBH",
            "SQSJHQSJ": "SQSJ",
            "SJHQSJ": "BQSJ",
            "WXSJY": "BQYX",
            "KCKZ": "ZWKZ",   #   "": "",
            "X": "X2",
            "Y": "Y2",
            "LXWFTBSQBH": "SQKCTBBH",
            "SFCXWF": "SFLXBH",
            "批次": "SSJD",
            "省": "SHENG",
            "市": "SHI",
            "县": "XIAN",
            "CJLY": "ZDQY"
        }

        # 创建新DataFrame并初始化新字段
        result_df = pd.DataFrame(index=old_ply.index,columns=new_fields)

        # 确保几何列
        result_gdf = gpd.GeoDataFrame(result_df, geometry=new_ply.geometry)

        # 保留新字段，并添加老字段（以o_为前缀）
        for old_field in old_ply.columns:
            if old_field in field_mapping:
                result_gdf[field_mapping[old_field]] = old_ply[old_field]
            elif old_field in new_fields:  # 如果老字段在新字段中，则直接复制
                result_gdf[old_field] = old_ply[old_field]
            elif old_field != old_ply.geometry.name:  # 避免重复添加几何列
                result_gdf["o_" + old_field] = old_ply[old_field]

        # 设置几何列
        result_gdf.set_geometry(new_ply.geometry.name, inplace=True)

        # 提取省、市编码
        if 'XIANDM' in result_gdf.columns and result_gdf['XIANDM'].notna().any():
            result_gdf['SHENGDM'] = result_gdf['XIANDM'].apply(lambda x: f"{str(x)[:2]}0000")
            result_gdf['SHIDM'] = result_gdf['XIANDM'].apply(lambda x: f"{str(x)[:4]}00")

        # 保存结果到新的shapefile
        result_gdf.to_file(p_output_path, encoding='gb18030')
        tkinter.messagebox.showinfo("完成", "处理完成！结果已保存到指定文件。")
    except Exception as e:
        print(f'错误，{e}')
        # tkinter.messagebox.showerror("错误", f"处理失败：{e}")


if __name__ == '__main__':
    # 初始化Tk()
    root = Tk()

    # 设置标题
    root.title('新老图斑转换 by WW.WCGS')
    shp_path = StringVar()       # 图斑位置
    model_path = StringVar()
    output_path = StringVar()    # 输出文件


    row_index = 1
    Label(root, text="老图斑路径:").grid(row=row_index, column=0)
    Entry(root, textvariable=shp_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择图斑", width=11, command=sel_shp_file).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="变化图斑模板:").grid(row=row_index, column=0)
    Entry(root, textvariable=model_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5)
    Button(root, text="选择变化图斑", width=11, command=sel_model_file).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="输出文件:").grid(row=row_index, column=0)
    Entry(root, textvariable=output_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5)
    Button(root, text="输出图斑", width=11, command=sel_output_file).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Button(root, text='执行', width=20,
           command=lambda: do_work(shp_path.get(), model_path.get(), output_path.get())).grid(row=row_index, columnspan=5)

    # 设置窗口的初始大小
    # root.geometry("350x100")
    center_window(root, 470, 20+row_index*30)

    # ------------------------------调试------------------------------------------
    # 生成随机的两位数
    # random_number = random.randint(10, 99)

    # shp_path.set(r'W:/09Temp/06/新老图斑转化/老图斑/old2.shp')
    # output_path.set(r"W:/09Temp/06/新老图斑转化/老图斑/" + f"A{random_number}.shp")

    # debug_btn = Button(root, text='调试', width=20, command=lambda: My_debug(dbf_path.get()))
    # debug_btn.grid(row=5, columnspan=5)
    # debug_btn.pack_forget()
    root.mainloop()