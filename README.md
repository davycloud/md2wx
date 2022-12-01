# md2wx


 Markdown 转 微信公众号

## 安装

```bash
pip install md2wx
```

## 如何使用

查看帮助：

```bash
> md2wx -h
usage: md2wx [-h] [--output OUTPUT] [--template TEMPLATE] [--static STATIC] [--codestyle CODESTYLE] [--noserver]
             [--port PORT] [--openurl] [--debug]
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
  --codestyle CODESTYLE
                        代码样式名
  --noserver, --noserve
                        不启动HTTP服务器
  --port PORT           HTTP服务器端口
  --openurl             打开浏览器并访问HTTP服务器
  --debug               开启Debug
```
