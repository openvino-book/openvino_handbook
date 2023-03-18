<!-- TOC -->

- [.1. 简介](#1-%E7%AE%80%E4%BB%8B)
- [.2. 安装并配置Anaconda](#2-%E5%AE%89%E8%A3%85%E5%B9%B6%E9%85%8D%E7%BD%AEanaconda)
    - [.2.1. 下载并安装Anaconda](#21-%E4%B8%8B%E8%BD%BD%E5%B9%B6%E5%AE%89%E8%A3%85anaconda)
    - [.2.2. 配置Anaconda国内镜像源](#22-%E9%85%8D%E7%BD%AEanaconda%E5%9B%BD%E5%86%85%E9%95%9C%E5%83%8F%E6%BA%90)
    - [.2.3. 创建并激活虚拟环境ov_book](#23-%E5%88%9B%E5%BB%BA%E5%B9%B6%E6%BF%80%E6%B4%BB%E8%99%9A%E6%8B%9F%E7%8E%AF%E5%A2%83ov_book)
- [.3. 下载并安装Git](#3-%E4%B8%8B%E8%BD%BD%E5%B9%B6%E5%AE%89%E8%A3%85git)
- [.4. 克隆并安装YOLOv5](#4-%E5%85%8B%E9%9A%86%E5%B9%B6%E5%AE%89%E8%A3%85yolov5)
- [.5. 安装openvino-dev](#5-%E5%AE%89%E8%A3%85openvino-dev)
- [.6. 安装VS Code](#6-%E5%AE%89%E8%A3%85vs-code)

<!-- /TOC -->
### 简介
本文将从零开始详述在Windows10/11上搭建OpenVINO+YOLOv5开发环境。

###  安装并配置Anaconda
#### 下载并安装Anaconda
Anaconda([官方网站](https://www.anaconda.com/))是Python软件包(packages)和虚拟环境(virtual environment)的管理工具，让Python开发者能方便快捷地管理Python运行的虚拟环境和开发应用程序所依赖的各种软件包。

从[Anaconda官网](https://www.anaconda.com/)下载最新的Anaconda安装文件，双击安装。

所有安装选项页面均保持默认选择，除了在高级安装选项(Advanced Installation Options)页， 请勾选“Add Anaconda to my PATH environment variable”，让Anaconda成为Windows系统默认的Python运行版本。

![勾选“Add Anaconda to my PATH environment variable”](pic/anaconda_advanced_option.png)

#### 配置Anaconda国内镜像源
参考[Anaconda 镜像使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/)，完成Anaconda国内镜像源配置，这样可以极大的提高Python软件包的下载速度。

注意: Windows 用户无法直接创建名为 .condarc 的文件，可先执行 conda config --set show_channel_urls yes 生成该文件之后再修改

#### 创建并激活虚拟环境ov_book
打开**命令提示符** 窗口，输入命令更新当前conda
> conda update conda

输入命令创建名为“ov_book"的虚拟环境
> conda create -n ov_book python=3.9

![创建名为“ov_book"的虚拟环境](pic/conda_create.png)

激活ov_book虚拟环境
> activate ov_book

![激活ov_book虚拟环境](pic/activate.png)

设置pip[百度镜像源](https://www.jianshu.com/p/4b34840f79dd),提高使用pip工具下载Python软件包的速度

### 下载并安装Git
Git是一个开源免费的分布式版本控制系统，不管是小项目还是大项目，都可以高效的管理。本书主要用Git工具从GitHub克隆项目代码仓，例如：[YOLOv5代码仓](https://github.com/ultralytics/yolov5)。

从[Git官网](https://git-scm.com/downloads)下载Git安装文件，按默认选项安装即可。

### 克隆并安装YOLOv5
**第一步**，启动Git Bash，将YOLOv5代码仓克隆到本地
>git clone https://github.com/ultralytics/yolov5.git

![克隆YOLOv5代码仓到本地](pic/clone_yolov5.png)

**第二步**，打开*命令提示符*窗口，激活ov_book虚拟环境，进入yolov5文件夹，安装YOLOv5所需的依赖软件包。
>activate ov_book

>pip install -r requirements.txt

![安装YOLOv5所需的依赖软件包](pic/install_yolov5.png)

**第三步**，导出yolov5s-cls ONNX格式模型
> python export.py --weights yolov5s-cls.pt --include onnx --img 224

![导出yolov5s-cls ONNX格式模型](pic/export_yolov5s_cls.png)

### 安装openvino-dev

由于本书不涉及TensorFlow等框架，所以在安装时openvino-dev，增加一个onnx的选项，参考：https://pypi.org/project/openvino-dev/

>pip install openvino-dev[onnx]

![安装openvino-dev](pic/install_openvino.png)

### 安装VS Code
Visual Studio Code 是一款功能强大的代码编辑器，非常适合跟Anaconda和Git一起，作为Python程序的集成开发环境(IDE)。

从[VS Code官网](https://code.visualstudio.com/)下载安装文件，按照默认选项完成安装。

到此，**完成了在Windows10/11上搭建OpenVINO+YOLOv5开发环境**。



