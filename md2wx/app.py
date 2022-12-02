"""将 Markdown 转换为可以一键发布的 HTML
"""
import time
import tempfile
import shutil
import webbrowser
import threading
from typing import Optional
from contextlib import contextmanager
from pathlib import Path
from string import Template
from functools import partial
from argparse import ArgumentParser

import markdown
import frontmatter

from md2wx.styles import code_styles


pkg_path = Path(__file__).parent

STATIC_DIR = pkg_path / 'static'

TEMPLATE_PATH = pkg_path / 'templates' / 'wx.html'

CODE_STYLE = 'github-dark'

SERVER_PORT = 8800

DEBUG = False

assert STATIC_DIR.is_dir()
assert TEMPLATE_PATH.is_file()


def markdown_to_html(markdown_text):
    return markdown.markdown(markdown_text,
                             extensions=['extra'])


def render_markdown(markdown_path: Path, template: Template, **kwargs):
    with open(markdown_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    metadata = post.metadata
    content = markdown_to_html(post.content)
    kwargs.update(metadata)
    return template.substitute(content=content, **kwargs)


def run_server(directory='.', port=SERVER_PORT):
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

    Handler = partial(SimpleHTTPRequestHandler, directory=directory)

    with ThreadingHTTPServer(("", port), Handler) as httpd:
        print("serving at port", port)
        print("按下 Ctrl + c 停止运行")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.shutdown()


def iter_md_files(content_path: Path):
    if content_path.is_file():
        yield content_path
    elif content_path.is_dir():
        for p in content_path.glob('*.md'):
            if p.is_file():
                yield p
    else:
        raise ValueError()


@contextmanager
def ctx_output_dir(output_dir: Optional[Path]):
    tmp_dir = None
    if not output_dir:
        tmp_dir = tempfile.TemporaryDirectory()
        output_dir = Path(tmp_dir.name)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    try:
        yield output_dir
    finally:
        if tmp_dir:
            tmp_dir.cleanup()


def app(content_path,
        template_path,
        output_dir=None,
        static_path=None,
        code_style=CODE_STYLE,
        start_server=False,
        server_port=SERVER_PORT,
        ):
    tmpl = Template(template_path.read_text(encoding='utf-8'))
    tmpl_ts = template_path.stat().st_mtime

    with ctx_output_dir(output_dir) as output_dir:

        def render():
            nonlocal tmpl, tmpl_ts

            need_all_render = False
            if template_path.stat().st_mtime > tmpl_ts:
                # reload template
                need_all_render = True
                tmpl = Template(template_path.read_text(encoding='utf-8'))
                tmpl_ts = template_path.stat().st_mtime

            for md_file in iter_md_files(content_path):
                html_file = output_dir.joinpath(f'{md_file.stem}.html')
                if not need_all_render and html_file.is_file() \
                        and html_file.stat().st_mtime > md_file.stat().st_mtime:
                    continue
                html_text = render_markdown(md_file, tmpl, code_style=code_style)
                html_file.write_text(html_text, encoding='utf-8')

        def monitor():
            while True:
                time.sleep(2)
                render()

        def openurl():
            time.sleep(1)
            url = f'http://localhost:{server_port}/'
            if content_path.is_file():
                url += content_path.stem + '.html'
            webbrowser.open(url)

        print(f'输出文件路径：{output_dir}')
        if static_path:
            shutil.copytree(static_path, output_dir, dirs_exist_ok=True)

        render()

        if start_server:
            threading.Thread(target=monitor, daemon=True).start()
            threading.Thread(target=openurl).start()
            run_server(directory=str(output_dir), port=server_port)


def _main(args):
    content_path = Path(args.mdpath)
    if not (content_path.is_dir() or content_path.is_file()):
        raise ValueError(f'Markdown路径不正确，请指定文件夹或文件：{content_path}')

    start_server = args.start_server
    copy_static = args.copy_static
    if args.output:
        output_dir = Path(args.output)
        if output_dir.exists() and not output_dir.is_dir():
            raise ValueError(f'Output已存在且不是一个文件夹：{output_dir}')
    else:
        output_dir = None
        if not copy_static:
            print(f'提示：没有指定输出目录并且选择不拷贝静态文件，如果模板需要本地静态文件，页面将无法正常显示。')
        if not start_server:
            raise ValueError(f'没有指定输出目录，页面会输出到临时目录，此时如果不启动服务器，命令执行完毕后文件会自动清除而无法查看，所以至少需满足一项。')

    if args.template:
        template_path = Path(args.template)
    else:
        template_path = TEMPLATE_PATH

    assert template_path.is_file(), f'模板文件不正确： {template_path}'

    if not copy_static:
        static_path = None
    elif args.static:
        static_path = Path(args.static)
        assert static_path.is_dir(), f'静态文件路径不正确: {static_path}'
    else:
        static_path = STATIC_DIR

    code_stype = args.codestyle
    if code_stype not in code_styles:
        raise ValueError(f'codestyle 不支持，可选择的是：{code_styles}')

    app(content_path, template_path,
        output_dir=output_dir, static_path=static_path,
        start_server=start_server, server_port=args.port,
        code_style=code_stype
        )


def main():
    parser = ArgumentParser(prog='md2wx', description='Markdown 一键复制发布到微信公众号（或其它平台）。', epilog='')
    parser.add_argument('mdpath', help='.md 文件或者是其所在文件夹路径，缺省是当前路径')
    parser.add_argument('--output', '-o', help='输出文件夹路径，缺省是临时目录')
    parser.add_argument('--template', help='模板文件路径')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--static', help='静态文件路径')
    group.add_argument('--nostatic', dest='copy_static', action='store_false', help='不需要静态文件')
    parser.add_argument('--codestyle', default='github-dark', help='代码样式名')
    parser.add_argument('--noserver', '--noserve', dest='start_server', action='store_false', help='不启动HTTP服务器')
    parser.add_argument('--port', type=int, default=SERVER_PORT, help='HTTP服务器端口')
    parser.add_argument('--openurl', action='store_true', help='打开浏览器并访问HTTP服务器')
    parser.add_argument('--debug', action='store_true', help='开启Debug')

    global DEBUG

    args = parser.parse_args()
    DEBUG = args.debug
    if DEBUG:
        print(parser.format_help())
        print(args)
    try:
        _main(args)
    except Exception as err:
        print(f'Error: {err}')


if __name__ == '__main__':
    main()
