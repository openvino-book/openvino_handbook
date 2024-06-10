## <center>搭建OpenVINO™ JavaScript 开发环境</center>
- [搭建OpenVINO™ JavaScript开发环境](#在windows上搭建openvino-JavaScript开发环境)
  - [:tent:简介](#tent简介)
  - [:factory:安装Nodejs](#factory安装Nodejs)
  - [:stars:下载并安装Git](#stars下载并安装git)
  - [:whale:安装VS Code](#whale安装vs-code)
  - [🎨创建并配置JavaScript项目](#🎨创建并配置JavaScript项目)
    - [第一步：创建OpenVINO™C#项目](#第一步：创建OpenVINO™JavaScript项目)
    - [第二步：添加项目依赖:rocket:安装OpenVINO™ 开发套件](#第二步：:rocket:安装OpenVINO™ 开发套件)
  - [🎁测试OpenVINO™JavaScript项目](#🎁测试OpenVINO™JavaScript项目)
  - [🎯总结](#🎯总结)

### :tent:简介
本文将从零开始详述如何搭建OpenVINO™ JavaScript开发环境。

###  :factory:安装Nodejs

Node.js 是一个基于Chrome V8 引擎的JavaScript 运行环境。安装Nodejs可以使用brew或者去官网地址下载，[en官网](https://nodejs.org/en/download/package-manager) ,选择对应系统安装Nodejs，openvino 需要20以上的版本
已经安装了Nodejs的可以使用 `n`, 或者 `nvm` 来管理node包版本
[中文安装地址](https://nodejs.cn/)
![image](https://github.com/txl1123/openvino_handbook/assets/9738404/9d633e2f-5edd-412a-b2a6-c43f51d0416f)

安装完成后，输入以下命令查看是否安装成功，并且确认node版本`>=20`
![image](https://github.com/txl1123/openvino_handbook/assets/9738404/f4d18afe-1a20-4135-861f-5da161140fd5)


### :stars:下载并安装Git

Git是一个开源免费的分布式版本控制系统，不管是小项目还是大项目，都可以高效的管理。主要用Git工具从GitHub克隆项目代码仓。

从[Git官网](https://git-scm.com/downloads)下载Git安装文件，按默认选项安装即可。

### :whale:安装VS Code

Visual Studio Code（简称“VS Code”） 是一款功能强大的代码编辑器，在前端开发的过程中必不可少，vscode作为代码编辑器，开源、免费、颜值高。更关键的是，丰富的插件，能够提高开发效率。

从[VS Code官网](https://code.visualstudio.com/)下载安装文件，按照默认选项完成安装。


### 🎨创建并配置JavaScript项目

#### 第一步：创建OpenVINO™JavaScript项目

新建一个项目目录，用vscode 打开，在`TERMINAL` 输入`init` 来初始化项目
```shell
npm init
```
#### 第二步：:rocket:安装OpenVINO™ 开发套件

OpenVINO™ 工具套件包含：OpenVINO Core，OpenVINO Model Wrap和Tensor 等，使用命令安装**OpenVINO™ 工具套件**：
```
npm install openvino-node
```
验证是否安装成功，在`index.js`文件里编写如下：
```
const { addon: ov } = require('openvino-node');
console.log(ov);
```
执行`index.js`的代码：
```shell
node index
```
如果打印出的效果如下，那就说明安装运行成功
![image](https://github.com/txl1123/openvino_handbook/assets/9738404/fb5d041f-3d27-4338-9640-0af716cb5c5a)


<!-- ### 🎁测试OpenVINO™JavaScript项目

从运行一个简单的 开始, 官方提供了Nodejs的官方demo -->

### 🎯总结

至此，我们就完成了在MacOS上搭建OpenVINO™C#开发环境，欢迎大家使用，如需要更多信息，可以参考一下内容：
- [openvino-node Api文档](https://docs.openvino.ai/2024/api/nodejs_api/nodejs_api.html)
- [openvino-node 官方Demo](https://github.com/openvinotoolkit/openvino/blob/master/samples/js/node/README.md)
- [openvino model zoo](https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/intel/index.md)
