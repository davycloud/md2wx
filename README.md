# md2wx

 Markdown 转 微信公众号

把 Markdown 文件一键转为 HTML 格式，但是添加了部分样式和 JavaScript，让它可以一键复制到微信公众号平台。

其它不支持直接上传 Markdown 内容的平台，例如知乎，也可以采用该工具的转换结果。

## 为什么要开发这个工具

目前网上的工具都要求把 Markdown 内容拷贝到编辑器里才能渲染出 HTML 结果，虽然很简单但是存在以下问题：

1. 需要访问网站才能使用
2. 如果发现有内容有错别字等需要修改的地方，要么修改原文件后再复制粘贴一遍，要么在浏览器改好再复制粘贴回原文件
3. 很难添加自定义的功能

md2wx 是如何解决的：

1. 使用命令行本地执行一条命令 `md2wx` 即可，自动在本地启动 HTTP 服务器展示 HTML 页面
2. 启动后在后台自动监控 Markdown 文件，发现改动自动重新转换
3. 项目结构超级简单：
    - 1 个 python 文件，处理参数和 markdown 解析
    - 1 个 HTML 模板文件，决定 HTML 的整体结构
    - 1 个 CSS 样式文件，决定显示效果
    - 1 个 JS 脚本文件，处理一些前端操作
   
Python 代码的处理过程非常简单，模板文件和静态文件用户完全可以按需自定义。


## 安装

```bash
pip install md2wx
```

## 如何使用

查看帮助：

```bash
> md2wx -h
usage: md2wx [-h] [--output OUTPUT] [--template TEMPLATE] [--script SCRIPT]
             [--style {blue,cyan,rose} | --css CSS] [--codestyle CODESTYLE]
             [--no-basic-static] [--noserver] [--port PORT] [--quite] [--debug] [--dryrun]
             mdpath

Markdown 一键复制发布到微信公众号（或其它平台）。

positional arguments:
  mdpath                .md 文件或者是其所在文件夹路径，缺省是当前路径

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        输出文件夹路径，缺省是临时目录
  --template TEMPLATE   模板文件路径
  --script SCRIPT       JavaScript 文件路径
  --style {blue,cyan,rose}
                        内置的样式名
  --css CSS             自定义样式的CSS文件
  --codestyle CODESTYLE
                        代码样式名，缺省是 "github-dark"
  --no-basic-static     不要复制基础静态文件(_basic.css 和 script.js)，当自定义模板不需要这些 文件时使用该选项
  --noserver, --noserve
                        不启动HTTP服务器(只有在使用 --output 指定了输出目录时才能用)
  --port PORT           HTTP服务器端口，缺省是 8800
  --quite, -q           安静模式，不要打开浏览器
  --debug               开启Debug
  --dryrun              不实际运行，解析参数后立即退出，配合 --debug 查看参数解析结果
```

### 必填参数：`mdpath`

唯一必填的位置参数，可以是一个 `.md` 文件，也可以是一个包含了 `.md` 文件的文件夹。

举例：

转换当前目录下的所有 `.md` 文件：

```bash
md2wx .
```

转换某个 `.md` 文件：

```bash
md2wx my_post.md
```

### 选项说明

- `--output OUTPUT`：指定输出路径，缺省情况下转换结果是保存在临时目录中的，运行完毕自动删除。如果想保留结果，就使用该选项指定一个文件夹。
- `--noserver`：缺省情况下，会自动启动一个 HTTP 服务器来查看 HTML 文件。在使用了 `--output` 的前提下，如果不需要启动服务器，可以使用该选项。
- `--port PORT`：指定 HTTP 服务器的端口。
- `--quite`：在启动 HTTP 服务器后，为了方便还将自动打开浏览器访问，如果已经打开了，可以使用该选项。

以下 2 个选项是和样式有关的：

- `--style STYLE_NAME`：选择内置的样式名
- `--codestyle CODESTYLE`：选择代码样式名，都是 `highlight.js` 支持的样式名，总共有 200 多个，想要知道有哪些可用的，可以随便指定一个值，例如 `--codestyle xx`， 这样报错信息里会提示有哪些可用。

由于本工具主要是一个 Python 项目，主要目的不是为了解决前端问题，且本人也不擅长前端，所以内置的样式只提供了最最基础的样式。

如果对结果不满意，可以使用如下选项来进行自定义：

- `--css`：指定一个 CSS 样式文件，可以是本地也可以是网络链接
- `--script SCRIPT`：指定一个 JavaScript 脚本文件，可以是本地也可以是网络链接
- `--template TEMPLATE`：指定一个 HTML 模板文件

如果只是自定义样式，使用 `--css` 指定一个 `.css` 文件即可。

如果需要操作内容，可以使用 `--script` 指定一个 JavaScript 脚本，理论上，该脚本可以对结果 HTML 页面做任意改动。

指定的样式文件和 JS 脚本文件，如果是本地文件，都会被拷贝到输出目录下，和最终的 HTML 文件在同一级目录下。
同时被拷贝的还有两个基础的静态文件，一个是 `_basic.css`，提供最基础的样式，一个是 `script.js` 提供最基础的操作。

如果想要彻底的自定义，或者不想用 JavaScript 来操作页面内容，也可以 `--template` 来指定一个自定义的模板。

当使用了自定义模板时，其中的一切内容都是可以自定义的，包括用到什么样式文件和脚本。此时如果不再依赖基础静态文件，使用 `--no-basic-static` 选项。

如果所有选项都无法满足，可以直接修改代码。

下面两个选项用于调试和定位问题：

- `--debug`：使用后可以打印更多信息
- `--dryrun`：不实际运行，解析参数后立即退出，配合 `--debug` 查看参数解析结果

### 环境变量

由于参数较多，如果不想每次都输入，可以通过环境变量保存。

环境变量的名字是 `MD2WX_ARGS`，值是要输入的任何选项，例如 `--output my_wx_output --css mystyle.css`。

命令行输入的参数优先级更高。

## 变更日志


- 0.1.0: 完成基本功能，首次发布。
