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
DEBUG_MODE = True  # 在正式打包时将其设置为 False
if DEBUG_MODE:
    # ———————————————————调试变量赋值——————————————————————————
    g_aux_dir = f'W:/01Work/01HZJC/2024/规范/自制小工具/2024工具/02属性赋值/示例/辅助'
    g_dbg_input = f"W:/09Temp/09/矢量/520000BH202403M.shp"
    random_number = random.randint(10, 99)
    g_dbg_output = f"W:/09Temp/09/26/T{random_number}.shp"

else:
    # 正式模式下，通常不会赋值调试变量
    g_aux_dir = ""
    g_dbg_input = ""
    g_dbg_output = ""
# ———————————————————辅助方法——————————————————————————

# ---------------------初始化---------------------------
# 拆分do_work函数为多个小函数
def read_files(p_shp_path, p_aux_path):
    KQ_path = os.path.join(p_aux_path, g_KQ_fn)
    XZQ_path = os.path.join(p_aux_path, g_XZQ_fn)
    BHQ_path = os.path.join(p_aux_path, g_BHQ_fn)
    ZDQ_path = os.path.join(p_aux_path, g_ZDQ_fn)
    rail_buf_path = os.path.join(p_aux_path, g_rail_buf_fn)
    dict_exl = os.path.join(p_aux_path, g_dict_fn)
    data_reg_path = os.path.join(p_aux_path, g_data_reg_fn)

    KQ_ply = gpd.read_file(KQ_path)
    XZQ_ply = gpd.read_file(XZQ_path)
    BHQ_ply = gpd.read_file(BHQ_path)
    ZDQ_ply = gpd.read_file(ZDQ_path)
    rail_buf_ply = gpd.read_file(rail_buf_path)
    data_reg_ply = gpd.read_file(data_reg_path)
    LKBH_dict = get_dict(dict_exl, "附表1-绿色矿山列表")

    KSJC_ply,encoding = read_file_with_encoding(p_shp_path)

    return KSJC_ply, KQ_ply, XZQ_ply, BHQ_ply, ZDQ_ply, rail_buf_ply, data_reg_ply, LKBH_dict,dict_exl,encoding


def spatial_join(target, join, fields, how='left', predicate='intersects'):
    joined = gpd.sjoin(target, join[fields], how=how, predicate=predicate)
    return joined.groupby('F_ID').first()


def assign_fields_from_joined(target_gdf, joined_gdf, fields, field_mapping=None):
    if field_mapping:
        for target_field, joined_field in field_mapping.items():
            target_gdf[target_field] = joined_gdf[joined_field]
    else:
        for field in fields:
            target_gdf[field] = joined_gdf[field]
    return target_gdf


def decimal_to_dms(decimal):
    """Convert decimal degree to DMS format with two decimal places."""
    degrees = int(decimal)
    minutes_full = (decimal - degrees) * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60
    dms = f"{degrees}°{minutes:02d}′{seconds:05.2f}″"
    return dms


# 读取代码表格中对应的sheet，存入字典对象
def get_dict(p_path, sht_name, header_row=0):
    # 读取字典Excel文件
    # dict_df = pd.read_excel(p_path, sheet_name=sht_name, usecols=[0, 1])
    dict_df = pd.read_excel(p_path, sheet_name=sht_name, header=header_row, usecols=[0, 1])
    return dict_df


def generate_KQJB(KMXKZ):
    """Generate KQJB based on KMXKZ value."""
    if pd.isna(KMXKZ):
        return None
    KMXKZ_str = str(KMXKZ)
    if len(KMXKZ_str) < 7:
        return None
    if KMXKZ_str[1:3] == '10':
        return 'A'
    elif KMXKZ_str[3:5] == '00':
        return 'B'
    elif KMXKZ_str[5:7] == '00':
        return 'C'
    else:
        return 'D'


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


# 判断是否存在 F_ID 字段
def create_F_ID(p_ply):
    if 'F_ID' not in p_ply.columns:
        print("字段 'F_ID' 不存在，正在创建...")
    else:
        print("字段 'F_ID' 已经存在，无需创建。")
        # 将当前索引重置为新列 'F_ID'
    p_ply = p_ply.reset_index(drop=True)  # 先重置索引
    p_ply['F_ID'] = p_ply.index  # 用重置后的索引赋值给 'F_ID'，从1开始
    return p_ply


# 删除过期字段
def del_old_filed(p_ply):
    # 筛选出以 "o_" 开头的字段（列）
    o_prefix_columns = [col for col in p_ply.columns if col.startswith('o_')]
    if o_prefix_columns:
        print(f"即将删除以下字段：{o_prefix_columns}")
        # 删除以 "o_" 开头的字段
        p_ply = p_ply.drop(columns=o_prefix_columns)
    return p_ply


def del_temp_filed(p_ply):
    # 删除 "index"和 F_ID 的辅助字段
    fields_to_delete = ["index", "F_ID"]

    for field in fields_to_delete:
        if field in p_ply.columns:
            print(f"删除辅助字段: {field}")
            p_ply.drop(columns=[field], inplace=True)
        else:
            print(f"字段 {field} 不存在，无需删除。")



def print_field_sample(gdf):
    """打印每个字段的前几行内容作为样本"""
    for column in gdf.columns:
        print(f"字段名: {column}")
        print(gdf[column].head(5))
        print(f"字段类型: {gdf[column].dtype}")


# # -----------------界面方法--------------------------
# 使窗口局屏幕中央
def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    root.geometry(f'{width}x{height}+{x}+{y}')


def sel_dbf_file():
    print("xx")


def sel_shp_file():
    path_ = askopenfilename(defaultextension=".shp", filetypes=[("shape文件", "*.shp")])
    shp_path.set(path_)


def sel_output_file(p_flag=1):
    path_ = asksaveasfilename(defaultextension=".shp", filetypes=[("Shapefile", "*.shp")])
    output_path.set(path_)


def sel_aux_directory():
    global g_aux_dir
    g_aux_dir = filedialog.askdirectory(title="选择辅助目录")
    aux_path.set(g_aux_dir)
    if g_aux_dir:
        print(f"选择的辅助目录: {g_aux_dir}")


# 使后面的layers 的crs和KSJC_ply 保持一致
def align_crs(KSJC_ply, *layers):
    for layer in layers:
        if KSJC_ply.crs != layer.crs:
            layer.to_crs(KSJC_ply.crs)


# 计算KSJC_ply 中的 X,Y，经纬度和面积
def get_geometry_params(KSJC_ply):
    KSJC_ply['centroid'] = KSJC_ply.geometry.centroid
    KSJC_ply['KMX'] = KSJC_ply['centroid'].x.round(6)
    KSJC_ply['KMY'] = KSJC_ply['centroid'].y.round(6)
    KSJC_ply['X2'] = KSJC_ply['KMX'].apply(decimal_to_dms)
    KSJC_ply['Y2'] = KSJC_ply['KMY'].apply(decimal_to_dms)
    projected_ply = KSJC_ply.to_crs(epsg=4508)
    KSJC_ply['KMZDMJ'] = projected_ply.geometry.area.round(2)
    KSJC_ply = KSJC_ply.drop(columns='centroid')
    return KSJC_ply


def join_KQ(KSJC_ply, KQ_ply):
    # 扩展 KQ_ply 的多边形
    KQ_ply['geometry'] = KQ_ply.geometry.buffer(0.0000001)
    KCFS_mapping = {
        "露天开采": "26001",
        "地下开采": "26002",
        "露天开采/地下开采": "26003"
    }
    KQ_ply['KCFS'] = KQ_ply['KCFS'].map(KCFS_mapping)

    KSJC_ply = create_F_ID(KSJC_ply)
    fields_to_transfer = ['XKZH', 'KSMC', 'JJLX', 'QTZKZ', 'KCFS', 'KCZKZ']
    KQ_ply_selected = KQ_ply[['geometry'] + fields_to_transfer]
    joined_KQ = gpd.sjoin(KSJC_ply, KQ_ply_selected, how='left', predicate='intersects')
    joined_unique = joined_KQ.groupby('F_ID').first()
    KSJC_ply['KMXKZ'] = joined_unique['XKZH']
    KSJC_ply['KMMC'] = joined_unique['KSMC']
    KSJC_ply['KMJJLX'] = joined_unique['JJLX']
    KSJC_ply['KMQTKZ'] = joined_unique['QTZKZ']
    KSJC_ply['KMKCFS'] = joined_unique['KCFS']
    KSJC_ply['KMLX'] = np.where(joined_unique['KCZKZ'].isnull(), KSJC_ply['KMLX'], joined_unique['KCZKZ'])
    KSJC_ply['KMLX'] = KSJC_ply['KMLX'].apply(lambda x: "" if x is None else x)
    # return KSJC_ply


def My_debug(p_path):
    print(f"debug{p_path}")


def do_work(p_shp_path, p_aux_path, p_output_path):
    try:
        KSJC_ply, KQ_ply, XZQ_ply, BHQ_ply, ZDQ_ply, rail_buf_ply, data_reg_ply, LKBH_dict,dict_exl,KSJC_encoding = read_files(p_shp_path, p_aux_path)

        # 确保所有文件使用相同的坐标参考系
        align_crs(KSJC_ply, KQ_ply, XZQ_ply, BHQ_ply, ZDQ_ply, rail_buf_ply)

        # ---------------开始计算X,Y,面积参数-------------------
        KSJC_ply = get_geometry_params(KSJC_ply)

        # 进行空间连接并赋值新字段
        # join_KQ(KSJC_ply, KQ_ply)
        # 扩展 KQ_ply 的多边形
        KQ_ply['geometry'] = KQ_ply.geometry.buffer(0.0000001)

        KCFS_mapping = {
            "露天开采": "26001",
            "地下开采": "26002",
            "露天开采/地下开采": "26003"
        }
        KQ_ply['KCFS'] = KQ_ply['KCFS'].map(KCFS_mapping)

        # 判断是否有"F_ID",如果没有则新建，并建立索引
        KSJC_ply = create_F_ID(KSJC_ply)

        # 选择要传递的字段
        KQ_fields = ['geometry', 'XKZH', 'KSMC', 'JJLX', 'QTZKZ', 'KCFS', 'KCZKZ']
        joined_KQ = spatial_join(KSJC_ply, KQ_ply, KQ_fields)

        # 使用映射字段赋值
        field_mapping = {
            'KMXKZ': 'XKZH',
            'KMMC': 'KSMC',
            'KMJJLX': 'JJLX',
            'KMQTKZ': 'QTZKZ',
            'KMKCFS': 'KCFS',
            'KMLX': 'KCZKZ'  # 这里根据你的逻辑调整
        }
        KSJC_ply = assign_fields_from_joined(KSJC_ply, joined_KQ, None,field_mapping)

        # # 仅在 KSJC_ply['KMLX'] 为空时赋值 joined_KQ['KCZKZ'] 的值
        KSJC_ply['KMLX'] = np.where(joined_KQ['KCZKZ'].isnull(), KSJC_ply['KMLX'], joined_KQ['KCZKZ'])
        KSJC_ply['KMLX'] = KSJC_ply['KMLX'].apply(lambda x: "" if x is None else x)

        # --------------------和行政区域文件相交，读取省、市、县和地址字段-------------------------
        # 重命名XZQ_ply中的字段以避免冲突
        XZQ_ply_renamed = XZQ_ply.rename(columns={
            'XIANDM': 'XZQ_XIANDM',
            'SHENGDM': 'XZQ_SHENGDM',
            'SHIDM': 'XZQ_SHIDM',
            'SHENG': 'XZQ_SHENG',
            'SHI': 'XZQ_SHI',
            'XIAN': 'XZQ_XIAN'
        })

        # 执行空间连接操作
        joined_XZQ = gpd.sjoin(KSJC_ply, XZQ_ply_renamed[
            ['geometry', 'XZQ_XIANDM', 'XZQ_SHENGDM', 'XZQ_SHIDM', 'XZQ_SHENG', 'XZQ_SHI', 'XZQ_XIAN', 'DIZHI']], how='left',
                               predicate='intersects')

        # 计算相交后的几何形状并添加为新列
        valid_joined_XZQ = joined_XZQ.dropna(subset=['index_right'])

        # 计算相交后的几何形状并添加为新列
        valid_joined_XZQ['intersection'] = valid_joined_XZQ.apply(
            lambda row: row.geometry.intersection(XZQ_ply_renamed.loc[row['index_right'], 'geometry']), axis=1)

        # 将结果合并回原 DataFrame，如果需要的话
        joined_XZQ = joined_XZQ.join(valid_joined_XZQ['intersection'], how='left')

        # 计算每个相交后多边形的面积并将其添加为新列
        joined_XZQ['area'] = joined_XZQ['intersection'].area

        # 按F_ID 和面积进行排序，并保留面积最大的记录
        joined_XZQ = joined_XZQ.sort_values(by=['F_ID', 'area'], ascending=[True, False])
        joined_XZQ = joined_XZQ.drop_duplicates(subset=['F_ID'])
        # 创建并赋值新字段
        # 复制F_ID列
        # KSJC_ply['F_ID_copy'] = KSJC_ply['F_ID']
        # KSJC_ply = KSJC_ply.set_index('F_ID')
        KSJC_ply['XIANDM'] = joined_XZQ.set_index('F_ID')['XZQ_XIANDM']
        KSJC_ply['SHENGDM'] = joined_XZQ.set_index('F_ID')['XZQ_SHENGDM']
        KSJC_ply['SHIDM'] = joined_XZQ.set_index('F_ID')['XZQ_SHIDM']
        KSJC_ply['SHENG'] = joined_XZQ.set_index('F_ID')['XZQ_SHENG']
        KSJC_ply['SHI'] = joined_XZQ.set_index('F_ID')['XZQ_SHI']
        KSJC_ply['XIAN'] = joined_XZQ.set_index('F_ID')['XZQ_XIAN']
        KSJC_ply['KMDZ'] = joined_XZQ.set_index('F_ID')['DIZHI']

        # 重置索引并处理字段
        KSJC_ply = KSJC_ply.reset_index()

        # --------------------和保护区文件相交，读取BHQMC代码-------------------------
        # 检查并删除重复的 level_0 列
        if 'level_0' in KSJC_ply.columns:
            KSJC_ply = KSJC_ply.drop(columns='level_0')
        if 'level_0' in BHQ_ply.columns:
            BHQ_ply = BHQ_ply.drop(columns='level_0')
        # 执行空间连接操作
        joined_BHQ = gpd.sjoin(KSJC_ply, BHQ_ply[['geometry', 'MC']], how='left', predicate='intersects')
        # 创建并赋值新字段
        joined_unique_BHQ = joined_BHQ.groupby('F_ID').first()
        KSJC_ply['BHQMC'] = joined_unique_BHQ['MC']

        # --------------------读取绿色矿山编码 LKBH-------------------------
        def assign_LKBH(row):
            if pd.notna(row['KMMC']):
                matching_row = LKBH_dict[LKBH_dict.iloc[:, 1] == row['KMMC']]
                if not matching_row.empty:
                    return matching_row.iloc[0, 0]
            return row['LKBH']

        KSJC_ply['LKBH'] = KSJC_ply.apply(assign_LKBH, axis=1)

        # --------------------和重点区（长江流域）文件相交，读取ZDQY代码-------------------------
        # 执行空间连接操作
        joined_ZDQ = gpd.sjoin(KSJC_ply, ZDQ_ply[['geometry', 'ZDQName']], how='left', predicate='intersects')
        joined_ZDQ_unique = joined_ZDQ.groupby('F_ID').first()
        # 创建并赋值新字段
        KSJC_ply['ZDQY'] = joined_ZDQ_unique['ZDQName']

        # -----------------更新ZDQY字段------------------------
        def update_ZDQY(row):
            if pd.notna(row['LKBH']):
                if pd.isna(row['ZDQY']):
                    return '绿色矿山'
                else:
                    return f"{row['ZDQY']}、绿色矿山"
            return row['ZDQY']

        KSJC_ply['ZDQY'] = KSJC_ply.apply(update_ZDQY, axis=1)

        # ------------------和rail_buf相交判断，赋值TL字段------------------------
        def check_rail_buf_intersection(row):
            intersecting = rail_buf_ply.intersects(row.geometry)
            return '是' if intersecting.any() else '否'

        KSJC_ply['TL'] = KSJC_ply.apply(check_rail_buf_intersection, axis=1)


        # ---------------KQJB矿权级别---------------------------
        # 根据KMXKZ字段生成KQJB字段
        KSJC_ply['KQJB'] = KSJC_ply['KMXKZ'].apply(generate_KQJB)

        # ---------------中文矿种ZWKZ---------------------------------
        # 读取“附表2-矿产术语代码” sheet
        dict_df = get_dict(dict_exl, "附表2-矿产术语代码")
        dict_df['矿产代码'] = dict_df['矿产代码'].astype(str)
        dict_df = dict_df.dropna(subset=['矿产代码'])  # 删除矿种代码为空的行
        kmlx_to_zwkz = dict_df.set_index('矿产代码')['矿产名称'].to_dict()
        # 给KSJC_ply的ZWKZ列赋值
        KSJC_ply['KMLX'] = KSJC_ply['KMLX'].astype(str)
        KSJC_ply['ZWKZ'] = KSJC_ply['KMLX'].map(kmlx_to_zwkz)
        # ---------------违法类型WFLX---------------------------------
        # 读取“附表4-其他代码” sheet
        dict_df = get_dict(dict_exl, "附表4-其他代码",60)
        # 只取第 1-12 行，并确保它们是字符串类型
        dict_df = dict_df.iloc[:12]
        dict_df['代码值'] = dict_df['代码值'].astype(str)
        dict_df = dict_df.dropna(subset=['存在问题'])  # 删除矿种代码为空的行
        KMCZWT_to_WFLX = dict_df.set_index('代码值')['存在问题'].to_dict()
        # 给KSJC_ply的WFLX列赋值
        KSJC_ply['KMCZWT'] = KSJC_ply['KMCZWT'].astype(str)
        KSJC_ply['WFLX'] = KSJC_ply['KMCZWT'].map(KMCZWT_to_WFLX)

        # ---------------本期数据源和时间 BQYX、BQSJ---------------------------------
        joined_BQYX = gpd.sjoin(KSJC_ply, data_reg_ply[['geometry', 'SATE', 'DATE']], how='left', predicate='intersects')
        joined_BQYX = joined_BQYX.drop_duplicates(subset=['F_ID'])
        # KSJC_ply = KSJC_ply.set_index('F_ID')
        # 创建并赋值新字段
        KSJC_ply['BQYX'] = joined_BQYX['SATE']
        # 如果 DATE 字段不是 datetime 类型，需要先转换
        joined_BQYX['DATE'] = pd.to_datetime(joined_BQYX['DATE'])
        KSJC_ply['BQSJ'] = joined_BQYX['DATE'].dt.strftime('%Y%m%d')

        # -----------------保存结果到新的shapefile-------------
        del_temp_filed(KSJC_ply)
        KSJC_ply = KSJC_ply.where(pd.notnull(KSJC_ply), None)
        KSJC_ply.to_file(p_output_path, encoding=KSJC_encoding)
        tkinter.messagebox.showinfo("完成", "处理完成！结果已保存到指定文件。")
    except Exception as e:
        print(f'错误，{e}')
        tkinter.messagebox.showerror("错误", f"处理失败：{e}")


# -------------------------遍历XZQ的多边形，找到其大部分面积所在的SSX多边形，并赋值SHENG、SHI、XIAN字段-----------------------------
def XZQ_XIAN_intract(p_SSX_path, p_XZQ_path, p_output_path):
    print(f"更新县、市、省到村shp文件上：{p_output_path}")
    try:
        # 读取对应的shapefile文件，尝试使用不同的编码格式
        SSX_ply = gpd.read_file(p_SSX_path, encoding='gb18030')
        XZQ_ply = gpd.read_file(p_XZQ_path, encoding='gb18030')
        # -------------调试-----------------------------
        # 打印字段内容样本进行调试
        print("调试信息：打印字段内容样本")
        print_field_sample(XZQ_ply)

        # 遍历XZQ的多边形，找到其大部分面积所在的SSX多边形，并赋值SHENG、SHI、XIAN字段
        for xzq_idx, xzq_row in XZQ_ply.iterrows():
            xzq_geometry = xzq_row.geometry
            max_intersection_area = 0
            matched_ssx_row = None

            for ssx_idx, ssx_row in SSX_ply.iterrows():
                ssx_geometry = ssx_row.geometry
                if xzq_geometry.intersects(ssx_geometry):
                    intersection_area = xzq_geometry.intersection(ssx_geometry).area
                    if intersection_area > max_intersection_area:
                        max_intersection_area = intersection_area
                        matched_ssx_row = ssx_row

            if matched_ssx_row is not None:
                XZQ_ply.at[xzq_idx, 'SHENG'] = matched_ssx_row['SHENG']
                XZQ_ply.at[xzq_idx, 'SHI'] = matched_ssx_row['SHI']
                XZQ_ply.at[xzq_idx, 'XIAN'] = matched_ssx_row['XIAN']
                XZQ_ply.at[xzq_idx, 'SHENGDM'] = matched_ssx_row['SHENGDM']
                XZQ_ply.at[xzq_idx, 'SHIDM'] = matched_ssx_row['SHIDM']
                XZQ_ply.at[xzq_idx, 'XIANDM'] = matched_ssx_row['XIANDM']

        # 保存更新后的XZQ结果到新的shapefile
        print("准备保存")

        # 确保所有字段的值都是Shapefile支持的类型
        # XZQ_ply = ensure_valid_field_types(XZQ_ply)

        XZQ_ply.to_file(p_output_path, encoding='gb18030')
        tkinter.messagebox.showinfo("完成", f"处理完成！结果已保存到{p_output_path}。")
    except Exception as e:
        print(f'错误，{e}')
        tkinter.messagebox.showerror("错误", f"处理失败：{e}")


if __name__ == '__main__':
    # 初始化Tk()
    root = Tk()

    # 设置标题
    root.title('图斑赋属性v1026')
    shp_path = StringVar()  # 图斑位置
    shp_KM_path = StringVar()  # 图斑位置
    aux_path = StringVar()  # 辅助信息目录
    output_path = StringVar()  # 输出文件

    row_index = 1
    Label(root, text="图斑文件路径:").grid(row=row_index, column=0)
    Entry(root, textvariable=shp_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5, pady=5)
    Button(root, text="选择图斑", width=11, command=sel_shp_file).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="辅助目录:").grid(row=row_index, column=0)
    Entry(root, textvariable=aux_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5)
    Button(root, text="选择目录", width=11, command=sel_aux_directory).grid(row=row_index, column=3, columnspan=2, sticky=E)

    row_index = row_index + 1
    Label(root, text="输出文件:").grid(row=row_index, column=0)
    Entry(root, textvariable=output_path, width=40).grid(row=row_index, column=1, columnspan=2, sticky=W, padx=5)
    Button(root, text="输出图斑", width=11, command=sel_output_file).grid(row=row_index, column=3, columnspan=2,
                                                                          sticky=E)

    row_index = row_index + 1
    Button(root, text='执行', width=20,
           command=lambda: do_work(shp_path.get(), aux_path.get(),output_path.get())).grid(row=row_index, columnspan=5)

    # ------------------------------调试------------------------------------------
    # # 生成随机的两位数
    # random_number = random.randint(10, 99)
    #
    shp_path.set(g_dbg_input)
    aux_path.set(g_aux_dir)
    output_path.set(g_dbg_output)
    #
    # row_index = row_index + 1
    # debug2_btn = Button(root, text='测试图斑建立FID字段', width=20,
    #                    command=lambda: My_debug(shp_path.get()))
    # debug2_btn.grid(row=row_index, columnspan=5)

    # 设置窗口的初始大小
    center_window(root, 470, 20 + row_index * 30)
    root.mainloop()
