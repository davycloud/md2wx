# md2wx

 Markdown 转 微信公众号

把 Markdown 文件一键转为 HTML 格式，但是添加了部分样式和 JavaScript，让它可以一键复制到微信公众号平台。

其它不支持直接上传 Markdown 内容的平台，例如知乎，也可以采用该工具的转换结果。

## 为什么要开发这个工具

目前网上流行的工具都要求把 Markdown 内容拷贝到编辑器里才能渲染出 HTML 结果，虽然很简单但是存在以下问题：

1. 需要访问网站才能使用
2. 如果发现有内容有错别字等需要修改的地方，要么修改原文件后再复制粘贴一遍，要么在浏览器改好再复制粘贴回原文件
3. 很难添加自定义的功能

md2wx 是如何解决的：

1. 使用命令行本地执行一条命令 `md2wx` 即可，自动在本地启动 HTTP 服务器展示 HTML 结果
2. 自动监控需要转换的 Markdown 文件，发现改动自动重新转换
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
usage: md2wx [-h] [--output OUTPUT] [--template TEMPLATE] [--static STATIC | --nostatic] 
             [--codestyle CODESTYLE] [--noserver] [--port PORT] [--quite] [--debug] 
             mdpath
                                                                                                                                                                      
Markdown 一键复制发布到微信公众号（或其它平台）。                                                                                                                     
                                                                                                                                                                      
positional arguments:                                                                                                                                                 
  mdpath                .md 文件或者是其所在文件夹路径，缺省是当前路径                                                                                                
                                                                                                                                                                      
optional arguments:                                                                                                                                                   
  -h, --help            show this help message and exit                                                                                                               
  --output OUTPUT, -o OUTPUT
                        输出文件夹路径，缺省是临时目录
  --template TEMPLATE   模板文件路径
  --static STATIC       静态文件路径
  --nostatic            不需要静态文件
  --codestyle CODESTYLE
                        代码样式名，缺省是 "github-dark"
  --noserver, --noserve
                        不启动HTTP服务器
  --port PORT           HTTP服务器端口，缺省是 8800
  --quite, -q           安静模式，不要打开浏览器
  --debug               开启Debug
```

举例：

转换当前目录下的所有 `.md` 文件：

```bash
md2wx .
```

转换某个 `.md` 文件：

```bash
md2wx my_post.md
```

