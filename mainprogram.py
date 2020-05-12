from PIL import Image
from showNDVI import *
from ExcelManage import *


class GetCode(object):

    def __init__(self):

        #定义一些参数
        self.root = tk.Tk(screenName="select")
        self.root.title("Main")
        # 设置整个顶层GUI页面长宽可拉伸
        self.root.resizable(width=True, height=True)
        self.path = tk.StringVar()
        self.path1 = tk.StringVar()
        self.year = tk.StringVar()

        #部署主界面
        #添加一个Label
        tk.Label(self.root, text="选择红光波段:").grid(row=0, column=0)
        # 输入、输出框存放选择路径
        # 添加一个输入框
        tk.Entry(self.root, textvariable=self.path, width=113).grid(row=0, column=1)
        # 添加一个按钮，绑定selectPath4功能
        tk.Button(self.root, text="选择红光波段", command=self.selectPath4).grid(row=0, column=2)

        tk.Label(self.root, text="选择近红外波段:").grid(row=1, column=0)
        # 输入、输出框存放选择路径
        tk.Entry(self.root, textvariable=self.path1, width=113).grid(row=1, column=1)
        # 绑定selectPath5功能
        tk.Button(self.root, text="选择近红外波段", command=self.selectPath5).grid(row=1, column=2)

        # 输入、输出框存放识别后生成文件路径
        tk.Label(self.root, text="输入年份").grid(row=2, column=0)
        tk.Entry(self.root, textvariable=self.year, width=100).grid(row=2, column=1)
        tk.Button(self.root, text="计算NDVI", command=self.calculate).grid(row=2, column=2)
        self.root.mainloop()

    def return_code(self):
        self.root.destroy()  # 关闭窗体

    def selectPath4(self):
        #选择图片路径
        path_ = fd.askopenfilename()
        self.path.set(path_)
        # 选路径之后进行图片展示
        self.showPhoto(self.path.get(), 1)

    def selectPath5(self):
        # 选择图片路径
        path_ = fd.askopenfilename()
        self.path1.set(path_)
        # 选路径之后进行图片展示
        self.showPhoto(self.path1.get(), 2)

    def calculate(self):
        #计算NDVI
        year = self.year.get()
        print(year)
        if year=="":
            year='2010'
        #读取波段4 和波段4 的图像
        im4 = self.path.get()
        im5 = self.path1.get()
        g = gdal.Open(im4)
        #获得红外波段的值
        red = g.ReadAsArray()
        g = gdal.Open(im5)
        #获得近红外波段的值
        nir = g.ReadAsArray()
        geo = g.GetGeoTransform()
        #获得投影坐标
        proj = g.GetProjection()
        # 为节约内存资源，删除g
        del g
        gc.collect()

        # 计算公式 (nir-red)/(nir+red)
        red = np.maximum(array(red, dtype=int), 1)
        nir = np.maximum(array(nir, dtype=int), 1)
        minus = np.subtract(nir, red)  # 计算公式 (nir-red)
        plus = np.add(nir, red)  #  计算公式(nir+red)

        del red, nir
        gc.collect()
        # 计算前一半的NDVI值，用(nir-red)/(nir+red)
        ndvil = np.floor_divide(minus[:, 0:2047] * 100, plus[:, 0:2047])
        #当NDVI值大于0.6时我们认为是绿地，计入面积area
        area = sum(ndvil > 60)
        # 计算后一半的NDVI值，用(nir-red)/(nir+red)
        ndvir = np.floor_divide(minus[:, 2047:] * 100, plus[:, 2047:])
        area += sum(ndvir > 60)
        print("vegetable has area(km2)", area * 9 / 10000)
        #换算area的单位
        writefile(year, area * 9 / 10000)
        #回收内存空间
        del minus, plus
        gc.collect()

        # 整合两半图像
        ndvi = np.hstack((ndvil, ndvir))
        # 二值化
        ndvi[ndvi <= 60] = 0
        ndvi[ndvi > 60] = 255
        # 保存图像
        shape = ndvi.shape
        driver = gdal.GetDriverByName("GTiff")
        dst_ds = driver.Create('ndvi' + year + '.tif', shape[1], shape[0], 1, gdal.GDT_Int16)
        dst_ds.SetGeoTransform(geo)
        dst_ds.SetProjection(proj)
        dst_ds.GetRasterBand(1).WriteArray(ndvi)
        dst_ds.FlushCache()  # write to disk
        dst_ds = None

        # 选测路径之后进行图片展示
        self.showPhoto('ndvi' + year + '.tif', 3)

        del dst_ds, ndvi, ndvil, ndvir
        gc.collect()
        # self.showPhoto("ndvi2013_2.tiff", 4)
        # path = "D:\\Others\\Program1\\image\\LC081210382013051401T1-SC20181105062955\\NDVI133.tif"

    # 重置图片（按要求缩放）
    def resize(self, w_box, h_box, pil_image):  # 参数是：要适应的窗口宽、高、Image.open后的图片
        w, h = pil_image.size  # 获取图像的原始大小
        # 计算图像缩放后的长和宽
        f1 = 0.5 * w_box / w
        f2 = 0.5 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        #返回缩放后的图像
        return pil_image.resize((width, height), PIL.Image.ANTIALIAS)
        # open_path为选择图片的路径

    #显示图片
    def showPhoto(self, open_path, state):
        # 期望图像显示的大小
        w_box = 600
        h_box = 600
        # get the size of the image
        # 根据选择的路径显示图片
        im = PIL.Image.open(open_path)

        # resize the image so it retains its aspect ration
        # but fits into the specified display box
        # 缩放图像让它保持比例，同时限制在一个矩形框范围内
        im_resize = self.resize(w_box, h_box, im)

        img = ImageTk.PhotoImage(im_resize)
        #如果state==1 说明为red波段图像，则画入主界面第三行，第一列
        if state == 1:
            tk.Label(self.root, image=img).grid(row=3, column=1)  # 布局控件
        # 如果state==2 说明为近红外波段图像，则画入主界面第三行，第二列
        elif state == 2:
            tk.Label(self.root, image=img).grid(row=3, column=2)  # 布局控件
        # 如果state==3 说明为NDVI结果，画入主界面第四行
        elif state == 3:
            tk.Label(self.root, text="结果").grid(row=4, column=0)
            tk.Label(self.root, image=img).grid(row=4, column=1)  # 布局控件
        # 其他情况
        else:
            tk.Label(self.root, image=img).grid(row=4, column=1)  # 布局控件

        self.root.mainloop()  # 显示图片
        del img, im
        gc.collect()


if __name__ == '__main__':
    GetCode()
