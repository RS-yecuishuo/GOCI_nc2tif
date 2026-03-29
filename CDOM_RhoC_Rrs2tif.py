import os
import tkinter as tk
from tkinter import filedialog, messagebox
from osgeo import gdal

# ===== 核心转换函数 =====
def convert_nc_to_single_band_tifs(nc_file, output_root, group_name):
    file_name = os.path.basename(nc_file)

    parts = file_name.split("_")
    date_str = parts[3]
    year = date_str[0:4]
    month = date_str[4:6]
    day = date_str[6:8]
    slot = parts[6]

    output_dir = os.path.join(output_root, year, month, day, slot, group_name)
    os.makedirs(output_dir, exist_ok=True)

    bands = [
        "380", "412", "443", "490",
        "510", "555", "620", "660",
        "680", "709", "745", "865"
    ]

    output_files = []

    for wl in bands:
        band_name = f"{group_name}_{wl}"

        output_tif = os.path.join(
            output_dir,
            file_name.replace(".nc", f"_{band_name}.tif")
        )

        vrt_file = output_tif.replace(".tif", ".vrt")

        # ===== 单波段VRT =====
        vrt_content = f"""<VRTDataset rasterXSize="2780" rasterYSize="2780">
  <Metadata domain="GEOLOCATION">
    <MDI key="LINE_OFFSET">0</MDI>
    <MDI key="LINE_STEP">1</MDI>
    <MDI key="PIXEL_OFFSET">0</MDI>
    <MDI key="PIXEL_STEP">1</MDI>
    <MDI key="SRS">EPSG:4326</MDI>
    <MDI key="X_BAND">1</MDI>
    <MDI key="X_DATASET">HDF5:"{nc_file}"://navigation_data/longitude</MDI>
    <MDI key="Y_BAND">1</MDI>
    <MDI key="Y_DATASET">HDF5:"{nc_file}"://navigation_data/latitude</MDI>
  </Metadata>

  <VRTRasterBand dataType="Float32" band="1">
    <NoDataValue>-999.0</NoDataValue>
    <SimpleSource>
      <SourceFilename relativeToVRT="0">HDF5:"{nc_file}"://geophysical_data/{group_name}/{band_name}</SourceFilename>
      <SourceBand>1</SourceBand>
    </SimpleSource>
  </VRTRasterBand>

</VRTDataset>
"""

        with open(vrt_file, "w") as f:
            f.write(vrt_content)

        # 转换
        gdal.Warp(
            output_tif,
            vrt_file,
            dstSRS='EPSG:32651',
            xRes=250,
            yRes=250,
            format='GTiff'
        )

        os.remove(vrt_file)

        print(f"已生成：{output_tif}")
        output_files.append(output_tif)

    return output_files


# ===== GUI部分 =====
def browse_nc():
    path = filedialog.askopenfilename(filetypes=[("NetCDF files", "*.nc")])
    entry_nc.delete(0, tk.END)
    entry_nc.insert(0, path)

def browse_output():
    path = filedialog.askdirectory()
    entry_out.delete(0, tk.END)
    entry_out.insert(0, path)

def run_conversion():
    nc_file = entry_nc.get()
    out_dir = entry_out.get()

    if not os.path.exists(nc_file):
        messagebox.showerror("错误", "NC文件不存在")
        return

    if not os.path.exists(out_dir):
        messagebox.showerror("错误", "输出路径不存在")
        return

    try:
        rrs_files = convert_nc_to_single_band_tifs(nc_file, out_dir, "Rrs")
        rhoc_files = convert_nc_to_single_band_tifs(nc_file, out_dir, "RhoC")

        messagebox.showinfo(
            "成功",
            f"转换完成！\nRrs数量: {len(rrs_files)}\nRhoC数量: {len(rhoc_files)}"
        )

    except Exception as e:
        messagebox.showerror("错误", str(e))


# ===== 主窗口 =====
root = tk.Tk()
root.title("GOCI-II Rrs 转 GeoTIFF 工具")
root.geometry("600x200")

# NC文件
tk.Label(root, text="NC文件路径:").pack()
entry_nc = tk.Entry(root, width=70)
entry_nc.pack()
tk.Button(root, text="选择NC文件", command=browse_nc).pack()

# 输出路径
tk.Label(root, text="输出文件夹:").pack()
entry_out = tk.Entry(root, width=70)
entry_out.pack()
tk.Button(root, text="选择输出文件夹", command=browse_output).pack()

# 运行按钮
tk.Button(root, text="开始转换", command=run_conversion, bg="green", fg="white").pack(pady=10)

root.mainloop()