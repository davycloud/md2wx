"""将 Markdown 转换为可以一键发布的 HTML
"""

import os
import io
import sys
import shlex
import time
import argparse
import tempfile
import shutil
import webbrowser
import threading
from typing import Optional, Union
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

STYLE_DIR = STATIC_DIR / 'css'

BUILTIN_STYLES = {css.stem: css for css in STYLE_DIR.glob('*.css')}
BUILTIN_STYLES.pop('_basic')
BASIC_STYLE_FILE = STYLE_DIR / '_basic.css'
DEFAULT_STYLE_NAME = 'cyan'

assert DEFAULT_STYLE_NAME in BUILTIN_STYLES

TEMPLATE_PATH = pkg_path / 'templates' / 'wx.html'

MAIN_SCRIPT_FILE = STATIC_DIR / 'js' / 'script.js'

CODE_STYLE = 'github-dark'

SERVER_PORT = 8800

DEBUG = False

assert STATIC_DIR.is_dir()
assert TEMPLATE_PATH.is_file()

# 环境变量传参
EV_ARGS = 'MD2WX_ARGS'


def validate_static_file(static_file: Optional[Union[str, Path]]):
    """校验静态文件参数

    允许 3 种情况：

    - None：直接返回，按缺省处理
    - 路径：必须是已经存在的文件
    - 字符串：必须是以 http:// 或 https:// 开头的链接形式，否则转为路径处理

    """
    if static_file is None:
        return static_file
    if isinstance(static_file, str):
        if static_file.startswith('http://') or static_file.startswith('https://'):
            return static_file
        static_file = Path(static_file)
    assert static_file.is_file(), f'指定的静态文件不存在：{static_file}'
    return static_file


def get_style(style_file: Optional[Union[str, Path]], default='') -> str:
    if style_file is None:
        return default
    elif isinstance(style_file, str):
        return style_file
    elif isinstance(style_file, Path):
        name = style_file.name
        return f'<link href="{name}" rel="stylesheet">'
    else:
        raise ValueError(f'样式文件参数不正确：{style_file}')


def get_custom_script(script_file: Optional[Union[str, Path]], default='') -> str:
    if script_file is None:
        return default
    elif isinstance(script_file, str):
        return script_file
    elif isinstance(script_file, Path):
        name = script_file.name
        return f'<script src="{name}"> </script>'
    else:
        raise ValueError(f'脚本文件参数不正确：{script_file}')


def markdown_to_html(markdown_text):
    return markdown.markdown(markdown_text,
                             extensions=['extra', 'toc', 'nl2br', 'sane_lists'])


def render_markdown(markdown_path: Path, template: Template, **kwargs):
    with open(markdown_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    metadata = post.metadata
    content = markdown_to_html(post.content)
    kwargs.update(metadata)
    if DEBUG:
        print(f'模板参数传入: {kwargs}')
    return template.substitute(content=content, **kwargs)


def run_server(directory='.', port=SERVER_PORT):
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

    Handler = partial(SimpleHTTPRequestHandler, directory=directory)  # noqa

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


def app(content_path: Path,
        template_path: Path,
        output_dir: Optional[Path] = None,
        style_path: Optional[Union[str, Path]] = None,
        custom_script_path: Optional[Union[str, Path]] = None,
        code_style: str = CODE_STYLE,
        copy_basic_static=True,
        start_server=False,
        server_port=SERVER_PORT,
        quite=False
        ):
    tmpl = Template(template_path.read_text(encoding='utf-8'))
    tmpl_ts = template_path.stat().st_mtime

    # 虽然命令行输入的参数已经校验过了，这里仍然需要校验以防直接调用出错
    style_path = validate_static_file(style_path)
    custom_script_path = validate_static_file(custom_script_path)
    to_copy = [f for f in (custom_script_path, style_path) if isinstance(f, Path)]
    if copy_basic_static:
        to_copy.append(MAIN_SCRIPT_FILE)
        to_copy.append(BASIC_STYLE_FILE)

    with ctx_output_dir(output_dir) as output_dir:
        print(f'输出文件路径：{output_dir}')
        for f in to_copy:
            if f.parent != output_dir:
                shutil.copy(f, output_dir)

        custom_style = get_style(style_path, default='')
        custom_script = get_custom_script(custom_script_path, default='')

        def render(all_render=False):
            nonlocal tmpl, tmpl_ts

            need_all_render = all_render
            # TODO: 不光模板，其它静态文件也要判断是否有更新
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
                html_text = render_markdown(md_file, template=tmpl,
                                            custom_style=custom_style,
                                            custom_script=custom_script,
                                            code_style=code_style)
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
            if server_started_ok:
                webbrowser.open(url)

        render(all_render=True)

        if start_server:
            threading.Thread(target=monitor, daemon=True).start()
            if not quite:
                threading.Thread(target=openurl).start()
            try:
                server_started_ok = True
                run_server(directory=str(output_dir), port=server_port)
            except OSError:
                print(f'启动 HTTP Server 失败，使用 --port 换其它端口试试。')
                server_started_ok = False
                raise



def _main(args):
    content_path = Path(args.mdpath)
    if not (content_path.is_dir() or content_path.is_file()):
        raise ValueError(f'Markdown路径不正确，请指定文件夹或文件：{content_path}')

    start_server = args.start_server
    if args.output:
        output_dir = Path(args.output)
        if output_dir.exists() and not output_dir.is_dir():
            raise ValueError(f'Output已存在且不是一个文件夹：{output_dir}')
    else:
        output_dir = None
        if not start_server:
            raise ValueError(
                f'没有指定输出目录，页面会输出到临时目录，此时如果不启动服务器，命令执行完毕后文件会自动清除而无法查看，所以至少需满足一项。')

    if args.template:
        template_path = Path(args.template)
    else:
        template_path = TEMPLATE_PATH
        if not args.copy_basic_static:
            raise ValueError(
                f'默认的模板需要JS才能正常运行，该选项只在指定了自定义模板的情况下才能使用。')

    assert template_path.is_file(), f'模板文件不正确： {template_path}'

    if args.css:
        style_file = validate_static_file(args.css)
    else:
        style_file = BUILTIN_STYLES.get(args.style, None)

    if args.script:
        script_file = validate_static_file(args.script)
    else:
        script_file = None

    code_stype = args.codestyle
    if code_stype not in code_styles:
        raise ValueError(f'codestyle 不支持，可选择的是：{code_styles}')

    if args.dryrun:
        exit(0)

    app(content_path, template_path,
        output_dir=output_dir,
        style_path=style_file,
        custom_script_path=script_file,
        copy_basic_static=args.copy_basic_static,
        start_server=start_server, server_port=args.port,
        code_style=code_stype, quite=args.quite
        )


def main():
    parser = ArgumentParser(prog='md2wx', description='Markdown 一键复制发布到微信公众号（或其它平台）。', epilog='')
    parser.add_argument('mdpath', help='.md 文件或者是其所在文件夹路径，缺省是当前路径')
    parser.add_argument('--output', '-o', help='输出文件夹路径，缺省是临时目录')
    parser.add_argument('--template', help='模板文件路径')

    parser.add_argument('--script', help='JavaScript 文件路径')

    style_group = parser.add_mutually_exclusive_group()
    style_group.add_argument('--style', choices=list(BUILTIN_STYLES.keys()), default=DEFAULT_STYLE_NAME,
                             help='内置的样式名')
    style_group.add_argument('--css', help='自定义样式的CSS文件')
    parser.add_argument('--codestyle', default=CODE_STYLE, help=f'代码样式名，缺省是 "{CODE_STYLE}"')
    parser.add_argument('--no-basic-static', dest='copy_basic_static', action='store_false',
                        help='不要复制基础静态文件(_basic.css 和 script.js)，当自定义模板不需要这些文件时使用该选项')
    parser.add_argument('--noserver', '--noserve', dest='start_server', action='store_false',
                        help='不启动HTTP服务器(只有在使用 --output 指定了输出目录时才能用)')
    parser.add_argument('--port', type=int, default=SERVER_PORT, help='HTTP服务器端口，缺省是 ' + str(SERVER_PORT))
    parser.add_argument('--quite', '-q', action='store_true', help='安静模式，不要打开浏览器')
    parser.add_argument('--debug', action='store_true', help='开启Debug')
    parser.add_argument('--dryrun', action='store_true',
                        help='不实际运行，解析参数后立即退出，配合 --debug 查看参数解析结果')

    global DEBUG
    args_ns = argparse.Namespace()
    if EV_ARGS in os.environ:
        env_args = shlex.split(os.environ.get(EV_ARGS))
        _sys_stderr = sys.stderr
        try:
            sys.stderr = io.StringIO()
            parser.parse_known_args(env_args, args_ns)
        except SystemExit:
            pass
        finally:
            sys.stderr = _sys_stderr

    args = parser.parse_args(namespace=args_ns)
    assert args is args_ns

    DEBUG = args.debug
    if DEBUG:
        print(args)

    try:
        _main(args)
    except Exception as err:
        print(f'Error: {err}')
        if DEBUG:
            raise


if __name__ == '__main__':
    main()
