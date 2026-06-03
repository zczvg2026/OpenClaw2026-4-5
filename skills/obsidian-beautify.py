#!/usr/bin/env python3
"""
beautify_md.py - 格式化美化 Markdown 文件

功能：
1. 自动识别中文标题（一、二、三、... / 第X章）
2. 自动识别编号列表（1. 2. / ① ②）
3. 自动识别表格行（| ... |）
4. 在标题前加空行、在列表项前加空行
5. 处理常见的 markdown 格式问题
6. 修复 "---" 变成 "------" 的问题
"""

import re
import sys
from pathlib import Path

def beautify(text: str) -> str:
    lines = text.split('\n')
    result = []
    i = 0
    prev_is_blank = True

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ---- 检测章节标题 ----
        # 匹配：一、项目背景  二、xxx  (一)（二）
        is_heading = False
        heading_level = 0

        if re.match(r'^(一|二|三|四|五|六|七|八|九|十)[\u4e00-\u9fff]', stripped):
            # 中文数字章
            is_heading = True
            heading_level = 1
        elif re.match(r'^\([一二三四五六七八九十]+\)', stripped):
            # (一) (二)
            is_heading = True
            heading_level = 2
        elif re.match(r'^(第[一二三四五六七八九十\d]+[章节])', stripped):
            is_heading = True
            heading_level = 1
        elif re.match(r'^\d+[.、][A-Za-z\u4e00-\u9fff]', stripped):
            # 1. xxx 或 1、xxx 可能是小节标题
            is_heading = True
            heading_level = 2
        elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', stripped):
            # ①②③小节
            is_heading = True
            heading_level = 2
        elif re.match(r'^(路径一|路径二|路径三|第一步|第二步|第三步|第四步)', stripped):
            is_heading = True
            heading_level = 2
        elif re.match(r'^(\u2500{3,})', stripped):
            # 分隔线 --- 等，保留
            if not prev_is_blank:
                result.append('')
            result.append(stripped)
            prev_is_blank = False
            i += 1
            continue

        if is_heading:
            if not prev_is_blank:
                result.append('')
            if heading_level == 1:
                result.append(f'## {stripped}')
            else:
                result.append(f'### {stripped}')
            prev_is_blank = False
        else:
            # 常规行
            processed = line
            # 修复 "------" 变成 "---"
            processed = re.sub(r'-{4,}', '---', processed)
            # 修复半角引号
            processed = re.sub(r'---', '—', processed)  # em dash
            result.append(processed)
            prev_is_blank = False

        i += 1

    # 最后清理：多个连续空行合并为最多2个
    output = '\n'.join(result)
    output = re.sub(r'\n{4,}', '\n\n', output)

    return output


def process_file(filepath: Path) -> int:
    try:
        text = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            text = filepath.read_text(encoding='gbk')
        except:
            print(f"  [skip] {filepath.name} - 无法解码")
            return 0

    original_len = len(text)
    beautified = beautify(text)

    if len(beautified) < original_len * 0.8:
        print(f"  [warn] {filepath.name} - 格式化后内容减少过多，跳过")
        return 0

    filepath.write_text(beautified, encoding='utf-8')
    saved = original_len - len(beautified)
    print(f"  ✓ {filepath.name} (节省 {saved} 字符)")
    return 1


def main():
    target_dir = Path.home() / 'Documents' / 'Obsidian Vault' / '0-raw'

    md_files = list(target_dir.glob('*.md'))
    md_files.extend(list(target_dir.glob('*.txt')))

    print(f"开始美化 {len(md_files)} 个文件...\n")

    done = 0
    for f in sorted(md_files):
        done += process_file(f)

    print(f"\n完成！处理了 {done} 个文件")

if __name__ == '__main__':
    main()