# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# MIT License
# Copyright (c) 2026 渐行渐远
# Licensed under the MIT License. See full terms at project root.
# ---------------------------------------------------------------------------
"""Substance 3D Designer 无头流水线（不打开 GUI）。

用法::

    # 1) 从 Designer 建好的 .sbs 生成"可无头运行"的 .sbsar
    python sbs_cli.py cook  G:/PBR/work/designer/build_ns_graph.sbs

    # 2) 查看 .sbsar 里有哪些图 / 输入 / 输出
    python sbs_cli.py info  out/build_ns_graph.sbsar

    # 3) 渲染
    python sbs_cli.py render out/build_ns_graph.sbsar --graph pkg://alchemical_chest_pbr \\
        --outdir out/ --size 9,9

    # 4) 一步到位（cook + render），并可选替换 .sbs 里的资源路径
    python sbs_cli.py run G:/PBR/work/designer/build_ns_graph.sbs \\
        --graph pkg://alchemical_chest_pbr --outdir out/ --map res=my_input.png

设计要点
--------
* ``.sbs`` 是**纯 XML 文本**（``<?xml ...?><package>...``），可以直接用文本工具
  读写；``<resource>`` 的 ``<filepath>`` 是相对 ``.sbs`` 所在目录的路径。
* 图输出必须经 ``<compOutputBridge>`` 接到 ``<graphOutputs>``，**不能**用图级
  ``<connections>``（写错会 cook 报 ``Unknown filter entry UID`` 并渲染全黑）。
* 命令行工具随 Designer 一起安装，无需额外装 SAT。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---- 默认的 Designer 安装位置（可用环境变量 DESIGNER_HOME 覆盖）----
DEFAULT_HOME_CANDIDATES = [
    Path(r"D:\Substance 3D Designer\Adobe Substance 3D Designer"),
    Path(r"C:\Program Files\Adobe\Adobe Substance 3D Designer"),
    Path(r"C:\Program Files\Allegorithmic\Substance Designer"),
]


def find_designer_home() -> Path:
    env = os.environ.get("DESIGNER_HOME")
    if env:
        p = Path(env)
        if (p / "sbsrender.exe").exists():
            return p
        raise SystemExit(f"DESIGNER_HOME 指向的目录里没有 sbsrender.exe: {p}")
    for p in DEFAULT_HOME_CANDIDATES:
        if (p / "sbsrender.exe").exists():
            return p
    raise SystemExit(
        "找不到 Substance 3D Designer 安装目录。\n"
        "请设置环境变量 DESIGNER_HOME，例如：\n"
        r'  set DESIGNER_HOME=D:\Substance 3D Designer\Adobe Substance 3D Designer'
    )


def run_tool(exe: Path, args: list[str]) -> int:
    """运行命令行工具并实时输出。"""
    print(f"[cmd] {exe.name} {' '.join(args)}", flush=True)
    proc = subprocess.run([str(exe), *args])
    return proc.returncode


# --------------------------------------------------------------------------
# .sbs 文本处理
# --------------------------------------------------------------------------
IDENT_RE = re.compile(r'<identifier v="([^"]+)"/>')
FILEPATH_RE = re.compile(r'<filepath v="[^"]*"/>')
PKGREF_RE = re.compile(r"pkg:///([A-Za-z0-9_./-]+)\?")


def sbs_resources(sbs: Path) -> list[str]:
    """列出 .sbs 里定义的所有资源名。"""
    text = sbs.read_text(encoding="utf-8")
    return IDENT_RE.findall(text[text.find("<content>"):]) and [
        m.group(1)
        for m in re.finditer(r'<resource><identifier v="([^"]+)"/>', text)
    ]


def sbs_graphs(sbs: Path) -> list[str]:
    """列出 .sbs 里所有图的名字。"""
    text = sbs.read_text(encoding="utf-8")
    return re.findall(r'<graph><identifier v="([^"]+)"/>', text)


def retarget_resources(sbs: Path, out_sbs: Path, mapping: dict[str, str]) -> dict:
    """把 .sbs 里指定资源的 filepath 换掉，输出成新 .sbs。

    mapping: {资源名: 新文件路径}；路径若是绝对路径会转成相对 out_sbs 的相对路径。
    """
    text = sbs.read_text(encoding="utf-8")
    base = out_sbs.parent
    report = {}

    def repl(m):
        block_start = text.rfind("<resource>", 0, m.start())
        block = text[block_start:m.end() + 30]
        name_m = re.search(r'<identifier v="([^"]+)"/>', block)
        if not name_m or name_m.group(1) not in mapping:
            return m.group(0)
        new_path = Path(mapping[name_m.group(1)])
        if new_path.is_absolute():
            try:
                new_path = new_path.relative_to(base)
            except ValueError:
                pass  # 跨盘符就只能绝对路径
        new_path = str(new_path).replace("\\", "/")
        report[name_m.group(1)] = new_path
        return f'<filepath v="{new_path}"/>'

    new_text = FILEPATH_RE.sub(repl, text)
    out_sbs.parent.mkdir(parents=True, exist_ok=True)
    out_sbs.write_text(new_text, encoding="utf-8")
    return report


# --------------------------------------------------------------------------
# 子命令
# --------------------------------------------------------------------------
def cmd_cook(args, home: Path) -> int:
    sbs = Path(args.sbs)
    outdir = Path(args.outdir) if args.outdir else sbs.parent
    outdir.mkdir(parents=True, exist_ok=True)
    name = args.name or sbs.stem
    return run_tool(home / "sbscooker.exe", [
        "--inputs", str(sbs).replace("\\", "/"),
        "--output-path", str(outdir).replace("\\", "/"),
        "--output-name", name,
    ])


def cmd_info(args, home: Path) -> int:
    return run_tool(home / "sbsrender.exe", [
        "info", "--input", str(Path(args.sbsar)).replace("\\", "/"),
    ])


def cmd_render(args, home: Path) -> int:
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = ["render", "--input", str(Path(args.sbsar)).replace("\\", "/")]
    if args.graph:
        cmd += ["--input-graph", args.graph]
    if args.output_node:
        cmd += ["--input-graph-output", args.output_node]
    cmd += ["--output-path", str(outdir).replace("\\", "/")]
    if args.pattern:
        cmd += ["--output-name", args.pattern]
    if args.size:
        cmd += ["--set-value", f"$outputsize@{args.size}"]
    for kv in (args.set or []):
        cmd += ["--set-value", kv]
    return run_tool(home / "sbsrender.exe", cmd)


def cmd_run(args, home: Path) -> int:
    """一步到位：可选换资源 → cook → render。"""
    src = Path(args.sbs)
    work = Path(args.workdir) if args.workdir else src.parent
    work.mkdir(parents=True, exist_ok=True)

    mapping = {}
    for item in (args.map or []):
        if "=" not in item:
            raise SystemExit(f"--map 需要 名字=路径 的形式，收到: {item}")
        k, v = item.split("=", 1)
        mapping[k] = v

    if mapping:
        target = work / (src.stem + "_cli.sbs")
        rep = retarget_resources(src, target, mapping)
        print("[map] 资源重定向:")
        for k, v in rep.items():
            print(f"        {k} -> {v}")
        src = target

    rc = cmd_cook(argparse.Namespace(sbs=str(src), outdir=str(work), name=args.name), home)
    if rc != 0:
        print("[ERROR] cook 失败", file=sys.stderr)
        return rc

    sbsar = work / ((args.name or src.stem) + ".sbsar")
    ns = argparse.Namespace(
        sbsar=str(sbsar), graph=args.graph, output_node=args.output_node,
        outdir=str(Path(args.outdir) if args.outdir else work / "out"),
        pattern=args.pattern, size=args.size, set=args.set,
    )
    return cmd_render(ns, home)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Substance 3D Designer 无头流水线（不打开 GUI）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--designer-home", help="Designer 安装目录（默认自动探测或读 DESIGNER_HOME）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("cook", help=".sbs → .sbsar")
    p.add_argument("sbs")
    p.add_argument("--outdir")
    p.add_argument("--name")

    p = sub.add_parser("info", help="查看 .sbsar 的图/输入/输出")
    p.add_argument("sbsar")

    p = sub.add_parser("render", help="渲染 .sbsar")
    p.add_argument("sbsar")
    p.add_argument("--graph", help='只渲染某张图，如 pkg://alchemical_chest_pbr')
    p.add_argument("--output-node", help="只渲染某个输出节点")
    p.add_argument("--outdir", default="out")
    p.add_argument("--pattern", help='输出文件名模板，如 "{inputGraphUrl}_{outputNodeName}"')
    p.add_argument("--size", help="输出尺寸指数，如 9,9 表示 512x512（2^9）")
    p.add_argument("--set", action="append", help="其他 --set-value，可重复")

    p = sub.add_parser("run", help="cook + render 一步到位")
    p.add_argument("sbs")
    p.add_argument("--graph")
    p.add_argument("--output-node")
    p.add_argument("--outdir")
    p.add_argument("--workdir")
    p.add_argument("--name")
    p.add_argument("--pattern")
    p.add_argument("--size")
    p.add_argument("--set", action="append")
    p.add_argument("--map", action="append",
                   help="替换 .sbs 里的资源路径：资源名=图片路径（可重复）")

    args = ap.parse_args(argv)
    home = Path(args.designer_home) if args.designer_home else find_designer_home()
    print(f"[env] Designer: {home}")
    return getattr(sys.modules[__name__], f"cmd_{args.cmd}")(args, home)


if __name__ == "__main__":
    sys.exit(main())
