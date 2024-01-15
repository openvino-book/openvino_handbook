## Install LabVIEW OpenVINO Toolkit

- [Install LabVIEW OpenVINO Toolkit](#install-labview-openvino-toolkit)
  - [1 简介](#1-简介)
  - [2 软件安装](#2-软件安装)
    - [2.1 环境搭建](#21-环境搭建)
    - [2.2 准备工作](#22-准备工作)
      - [2.2.1 安装LabVIEW 2018(64位)或更高版本](#221-安装labview-201864位或更高版本)
      - [2.2.2 LabVIEW AI视觉工具包安装说明](#222-labview-ai视觉工具包安装说明)
    - [2.3 LabVIEW OpenVINO工具包安装说明](#23-labview-openvino工具包安装说明)
      - [2.3.1 设置LabVIEW程序默认以管理员身份运行](#231-设置labview程序默认以管理员身份运行)
      - [2.3.2 工具包安装步骤](#232-工具包安装步骤)
      - [2.3.3工具包成功安装测试](#233工具包成功安装测试)
      - [2.3.4 常见报错解决办法](#234-常见报错解决办法)
  - [3 联系我们](#3-联系我们)
  - [4 总结](#4-总结)



### 1 简介


**LabVIEW OpenVINO**工具包是我们（VIRobotics团队）开发的一款AI推理加速工具包，整个工具包作为**LabVIEW**的插件，旨在帮助用户提高工作效率和推理速度。使用者可以在**LabVIEW**中直接使用**OpenVINO**实现在**CPU、GPU(intel)、FPGA、VPU**等硬件上的部署和推理。

本文将从零开始详述在Windows10/11上搭建OpenVINO™ LabVIEW开发环境，并对 **OpenVINO™ LabVIEW**环境进行简单测试。



### 2 软件安装
#### 2.1 环境搭建

- 操作系统：**Windows系统**
- **LabVIEW**：2018及以上 64位版本
- **VIPM** ：2021及以上版本
- **AI视觉工具包**（techforce_lib_opencv_cpu）：1.0.1.16及以上版本

#### 2.2 准备工作
##### 2.2.1 安装LabVIEW 2018(64位)或更高版本
本司的所有视觉相关的工具包，均支持2018或更高版本64位LabVIEW,如果您电脑已经安装了2018 或更高版本64位LabVIEW，则可跳过本步骤，无需重复安装。若还未安装，请从https://www.ni.com/zh-cn/support/downloads/software-products/download.labview.html ，下载**LabVIEW**安装文件。需要注意的是：请选择2018及以上的**LabVIEW 64位**版本，并勾选**Vision Development**模块和**NI-IMAQdx**。

<div align=center><img src="../pic/图片1.png" width=600></div>

##### 2.2.2 LabVIEW AI视觉工具包安装说明
1、在下载链接：https://pan.baidu.com/s/1nCprtMkbBW9nBrtTyMEXGA?pwd=yiku 中，下载文件 “LabVIEW AI视觉工具包”，文件中包含工具包安装包和测试范例。
2、双击安装包【techforce_lib_opencv_cpu-xxx.vip】，进入VIPM安装环境，点击Install开始安装； 
<div align=center><img src="../pic/图片2.png" width=600></div>
3、默认勾选内容，点击continue；
<div align=center><img src="../pic/图片3.png" width=600></div>
4、点击Yes，I accept……；
<div align=center><img src="../pic/图片4.png" width=600></div>
5、如下图所示，均显示为No Errors即成功安装，点击Finish即可；
<div align=center><img src="../pic/图片5.png" width=600></div>

6、成功安装后打开**LabVIEW**并新建**VI**，在程序框图面板 (记得是程序框图面板，不是前面板哦)中鼠标右键-->点击**Addons**-->可以看到附加工具包**Addons**中多了一项"**VIRobotics**"-->点击**VIRobotics**-->点击函数选版**opencv_yiku**，可以找到我们刚刚安装好的工具包中所有的机器视觉相关函数，至此**LabVIEW AI视觉工具包CPU版安装完成**。
<div align=center><img src="../pic/图片6.png" width=600></div>

#### 2.3 LabVIEW OpenVINO工具包安装说明
##### 2.3.1 设置LabVIEW程序默认以管理员身份运行
1、转到…\ National Instruments \ LabVIEW 2018路径, 右键点击LabVIEW.exe，选择属性； 
<div align=center><img src="../pic/图片7.png" width=600></div>
2、单击兼容性，选择以管理员身份运行，然后点击应用，此时LabVIEW.exe程序已获得默认管理员权限运行；
<div align=center><img src="../pic/图片8.png" width=600></div>
*注意：安装完所需工具包之后一定要记得去除默认以管理员身份运行此程序。}

##### 2.3.2 工具包安装步骤
1、在下载链接：链接：https://pan.baidu.com/s/1OeGLzQcGRPCBvM35TNI5SA?pwd=yiku  中下载文件 “LabVIEW OpenVINO工具包”，文件中包含工具包安装包和测试范例。
2、以管理员身份打开VIPM，双击安装包【virobotics_lib_openvino-xxx.vip】，进入VIPM安装环境，点击Install开始安装；
<div align=center><img src="../pic/图片9.png" width=600></div>
3、安装需要几分钟，等待一会，出现如下界面，均显示为No Errors即成功安装，点击Finish即可。
<div align=center><img src="../pic/图片10.png" width=600></div>

##### 2.3.3工具包成功安装测试
1、在“\ LabVIEW OpenVINO工具包\LabVIEW OpenVINO工具包测试范例”中，将test_openvino文件夹放到不包含中文的路径下；
2、双击test_openvino.vi，点击运行，能够出现成功运行界面，即OpenVINO成功安装并可正常使用，若无法使用，请查看下一页解决方法。
<div align=center><img src="../pic/图片11.png" width=600></div>


##### 2.3.4 常见报错解决办法
1、VIPM安装界面显示一直在连接LabVIEW，打开LabVIEW之后看到环境变量添加失败提示。
<div align=center><img src="../pic/图片12.png" width=300></div>

解决办法：点击OK，继续安装工具包，安装完成之后，手动将以下路径添加到系统环境变量Path中。
C:\ProgramData\VIRobotics\driver\OpenVINO\bin\intel64\Release
C:\ProgramData\VIRobotics\driver\OpenVINO\3rdparty\tbb\bin
<div align=center><img src="../pic/图片13.png" width=600></div>
<div align=center><img src="../pic/图片14.png" width=600></div>


2、范例测试报错
解决办法：
- 确保test_openvino文件夹放到了不包含中文的路径下；
- 确保已经安装openvino工具包，如未安装，请先安装；
- 查看是否有如下文件路径： C:\ProgramData\VIRobotics\driver\OpenVINO；
- 如有以上路径，请先完全关闭labview，然后将以下两个路径添加到系统环境变量中：
  C:\ProgramData\VIRobotics\driver\OpenVINO\bin\intel64\Release C:\ProgramData\VIRobotics\driver\OpenVINO\3rdparty\tbb\bin
- 重新运行范例，即可成功。


### 3 联系我们

如有任何需求帮助，可根据以下方式联系我们。

**上海仪酷智能科技有限公司（VIRobotics）**

**公司创始人：王立奇**

微信号：wangstoudamire

**添加微信请备注**：intel_openvino

**微信公众号**：VIRobotics

**官网**：https://www.virobotics.net/

**邮箱**：info@virobotics.net

如您想要探讨更多关于LabVIEW与人工智能技术，欢迎加入我们的技术交流群：705637299。进群请备注：intel_openvino


### 4 总结
至此，我们就完成了在Windows上搭建OpenVINO™C#开发环境，欢迎大家使用，如需要更多信息，可以参考一下内容：


-  [LabVIEW AI开发者福音：LabVIEW OpenVINO AI加速工具包，不来看看？](https://mp.weixin.qq.com/s/G1mw_yawlQ96JG5g14pSRg)

- [AI for Science：OpenVINO™ + 英特尔显卡解薛定谔方程｜开发者实战](https://mp.weixin.qq.com/s/yKHx260O2y4Q10KYx9UNHA)
