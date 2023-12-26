## 🏅为 《OpenVINO权威指南》 做贡献

&emsp;   欢迎大家对我们提出宝贵意见🥰！我们期待大家为 《OpenVINO权威指南》 做出贡献，可以通过以下方式：

- **⁉报告错误/问题**

  如果您在阅读 《OpenVINO权威指南》 或运行范例时遇到错误行为，您可以在 GitHub Issues中[Create New Issue](https://github.com/openvino-book/openvino_handbook/issues)。

- **🔖提出新的产品和功能**

  如果你对 《OpenVINO权威指南》有相关建议或想分享您的想法，您可以打开一个[New Discussion](https://github.com/openvino-book/openvino_handbook/discussions)。 如果您的想法已经明确定义，您还可以创建一个功能请求问题，在这两种情况下，请提供详细说明，包括用例、优势和潜在挑战。

- 🎯**修复代码错误或开发新功能**

  如果您发现仓库中有代码错误或则其他内容错误，以及有新的功能或者应用案例开发，可以通过创建 [Pull requests](https://github.com/openvino-book/openvino_handbook/pulls)实现，再提交时，请注意代码风格以及文档风格与代码仓保持一致。


## ⭕提交拉取请求 (PR)



#### 1. fork开源项目

&emsp;   找到要提交PR的项目，先将该项目fork自己的代码仓。

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/Fork.png" height=500/></span></div>

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/Create_fork.png" height=500/></span></div>

####  2. 克隆开源项目

  将需要提交PR的项目克隆到本地。

```
//打开CMD或者打开Git Bash Here
git clone https://github.com/dlod-openvino/openvino_handbook.git
```

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/clone.png" height=300/></span></div>

#### 3.创建新的分支

&emsp;   提交PR时需要.为了防止在主分支上修改影响主分支代码，此处创建一个分支用于代码的修改。

```
cd openvino_handbook // 切换到项目路径
git checkout -b temp //创建名为temp的分支
git branch //查看已经创建的分支 如图有temph和main两个分支
git checkout temp // 切换到分支
```

&emsp;   切换好分支后就可以直接根据自己需求修改项目,如上图所示。

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/clone_temp.png" height=300/></span></div>



#### 4. 修改提交项目代码

&emsp;   将代码修改后，执行`git status` 命令查看修改了哪些文件，接着使用`git add 修改的文件名`添加到暂存区，最后使用`git commit -m "日志信息" 文件名`提交到本地库。

```
git status // 查看库状态
git add 文件名 // 将修改的文件存放到暂存区
git commit -m "日志信息" 文件名 // 将修改的文件提交到本地库
```

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/git_push.png" height=300/></span></div>

&emsp;   最后将本地项目代码提交到远程GitHub上

```
git push --set-upstream origin temp
```

&emsp;   切换到**主分支**，将分支temp代码合并到主分支，查看是否可以与主分支合并成功。

```
git checkout main // 切换到主分支
git merge temp  // 合并派生分支到主分支
```

&emsp;   合并成功后，将主分支推送到代码仓。

```
git add .  // 将修改的文件存放到暂存区
git commit -m "日志信息" // 将修改的文件提交到本地库
git push origin main // 推送到远程仓库
```
<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/push_main.png" height=500/></span></div>
&emsp;   在GitHub切换到main主分支，查看是否合并成功

#### 4.提交pr请求

&emsp;   进入自己`fork`的项目中，点击“xx commit ahead of”。

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/commit_ahead_of.png" height=500/></span></div>

&emsp;   点击`Create pull requests`

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/Create_pr.png" height=500/></span></div>

&emsp;   最后点击`Create pull request`，提交后开源人将会收到你的合并请求。

<div align=center><span><img src="https://github.com/openvino-book/openvino_handbook/blob/main/pic/create_pull_request.png" height=500/></span></div>

到此，PR提交完毕！

## ⭕编码规范

&emsp;   为保证项目编码风格一致，在提交PR时，要遵守该项目编码规范。

##### 🔻代码样式

&emsp;   我们的所有代码遵循Google 开源项目风格指南，包括Python, C/C++, C#

&emsp;   🔸C++ 风格指南：[English](https://google.github.io/styleguide/cppguide.html)

&emsp;   🔸Python 风格指南：[English](https://peps.python.org/pep-0008/)

## ⭕许可证

&emsp;   您所提交的贡献，默认您同意采用[MIT license](https://github.com/openvino-book/openvino_handbook/blob/main/LICENSE).