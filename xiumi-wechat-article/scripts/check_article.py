#!/usr/bin/env python3
"""公众号推文质检：字数、外链、图片、敏感词、HTML 合规。

用法：
    python check_article.py article.md
    python check_article.py article.md --html article.html -o QA.md
"""
from __future__ import annotations

import argparse
import html as html_lib
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TITLE_MAX = 64
TITLE_TARGET = 24
SUMMARY_MAX = 120
SUMMARY_TARGET = 60
PARA_MAX = 220
EMOJI_MAX = 3

SENSITIVE = [
    "震惊", "必看", "速看", "深度好文", "爆款",
    "第一品牌", "国家级", "顶级", "100%", "永久", "根治", "治愈率", "包治",
    "稳赚", "保本", "保过", "零风险", "无风险",
    "转发到", "集赞", "助力解锁", "分享到3个群",
]

MANUAL = [
    "封面 2.35:1 裁切后主标题是否还在安全区（左右 8%、下 12%）",
    "首屏是否有「标题 + 一句价值 + 一张图」",
    "摘要脱离标题能否独立成立",
    "每屏是否至少一个视觉锚点（小标题/图/引用/卡片）",
    "手机预览三处断行是否难看（长英文、长数字、括号换行）",
    "引导（二维码/往期/关注）是否有效、是否过期",
    "原创声明、留言、合集是否按需勾选",
]


def split_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict[str, str] = {}
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                for raw in lines[1:idx]:
                    if ":" in raw:
                        key, value = raw.split(":", 1)
                        meta[key.strip()] = value.strip().strip('"').strip("'")
                return meta, "\n".join(lines[idx + 1:])
    return meta, "\n".join(lines)


def strip_markdown(body: str) -> str:
    out = []
    for line in body.split("\n"):
        s = line.strip()
        if not s or s.startswith(":::"):
            out.append("")
            continue
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"^#{1,6}\s*", "", s)
        s = re.sub(r"^>\s?", "", s)
        s = re.sub(r"^[-*+]\s+", "", s)
        s = re.sub(r"^\d+[.)]\s+", "", s)
        s = s.replace("**", "").replace("==", "")
        out.append(s)
    return "\n".join(out)


def strip_html(raw: str) -> str:
    """从生成的 HTML 里取纯文本，用于字数与敏感词检查。"""
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    s = re.sub(r"(?is)<br\s*/?>|</p>|</section>|</h[1-6]>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html_lib.unescape(s)
    lines = [re.sub(r"[ \t\u00a0]+", " ", ln).strip() for ln in s.splitlines()]
    return "\n\n".join(ln for ln in lines if ln)


def main() -> int:
    ap = argparse.ArgumentParser(description="WeChat article checker")
    ap.add_argument("source")
    ap.add_argument("--html", default=None, help="同时检查生成的 html")
    ap.add_argument("-o", "--output", default=None, help="把报告写到文件")
    args = ap.parse_args()

    path = Path(args.source)
    if not path.exists():
        raise SystemExit(f"file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    is_html_input = path.suffix.lower() in {".html", ".htm"}
    if is_html_input:
        meta = {}
        body = ""
        plain = strip_html(raw)
        if args.html is None:
            args.html = str(path)
    else:
        meta, body = split_frontmatter(raw)
        plain = strip_markdown(body)
    chars = len(re.sub(r"\s", "", plain))
    # HTML 输入时优先扫纯文本，避免把 style="width:100%" 之类的属性当成正文
    scan = plain if is_html_input else raw

    findings: list[tuple[str, str]] = []  # (level, message)

    def add(level: str, msg: str) -> None:
        findings.append((level, msg))

    # --- 标题 / 摘要 ---
    title = meta.get("title", "").strip()
    summary = meta.get("summary", "").strip()
    if is_html_input:
        add("INFO", "以 HTML 为输入：跳过 title/summary 检查，发布时在后台核对")
    elif not title:
        add("ERR", "frontmatter 缺少 title（公众号标题）")
    elif len(title) > TITLE_MAX:
        add("ERR", f"标题 {len(title)} 字，超过平台 {TITLE_MAX} 字上限")
    elif len(title) > TITLE_TARGET:
        add("WARN", f"标题 {len(title)} 字，列表页约 20 字截断，建议压到 {TITLE_TARGET} 字内")
    else:
        add("OK", f"标题 {len(title)} 字")

    if is_html_input:
        pass
    elif not summary:
        add("WARN", "没有 summary：微信会自动抓正文前几十字，通常很难看")
    elif len(summary) > SUMMARY_MAX:
        add("ERR", f"摘要 {len(summary)} 字，超过 {SUMMARY_MAX} 字上限")
    elif len(summary) > SUMMARY_TARGET:
        add("WARN", f"摘要 {len(summary)} 字，建议 ≤ {SUMMARY_TARGET} 字")
    else:
        add("OK", f"摘要 {len(summary)} 字")

    if summary and title and summary.startswith(title[:8]):
        add("WARN", "摘要开头与标题重复，摘要应补充信息而不是复述")

    if not meta.get("author"):
        add("INFO", "没有 author，发布时记得填（≤ 8 字）")

    # --- 正文 ---
    if chars < 300:
        add("WARN", f"正文只有 {chars} 字符，可能是占位稿")
    elif chars > 5000:
        add("WARN", f"正文 {chars} 字符偏长，考虑拆成两篇或加更多视觉锚点")

    if is_html_input:
        headings = len(re.findall(r"(?i)<h[23]\b", raw))
    else:
        headings = len(re.findall(r"^#{2,3}\s+", body, flags=re.M))
    if headings == 0:
        add("WARN", "没有任何小标题，长文会失去视觉锚点")
    elif headings > 8:
        add("WARN", f"{headings} 个小标题偏多，考虑合并")

    long_paras = []
    for para in re.split(r"\n\s*\n", plain):
        text = para.strip()
        if not text or text.startswith(":::") or text.startswith("·"):
            continue
        length = len(re.sub(r"\s", "", text))
        if length > PARA_MAX:
            long_paras.append(length)
    if long_paras:
        add("WARN", f"{len(long_paras)} 段超过 {PARA_MAX} 字（最长 {max(long_paras)}），手机上一段别超过 4 行")

    if "\u3000" in scan:
        add("WARN", "出现全角空格 U+3000，微信里会错位，删掉改用段距")

    emojis = re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", scan)
    if len(emojis) > EMOJI_MAX:
        add("WARN", f"{len(emojis)} 个 emoji，建议全篇 ≤ {EMOJI_MAX} 个")

    hits = [w for w in SENSITIVE if w in scan]
    if hits:
        add("WARN", f"命中风险词：{'、'.join(hits)}（广告法/诱导行为，确认语境）")

    # --- 外链 ---
    links = re.findall(r"\]\((https?://[^)\s]+)\)", body)
    bad_links = [u for u in links if "mp.weixin.qq.com" not in u and "weixin.qq.com" not in u]
    if bad_links:
        add("WARN", f"{len(bad_links)} 个外部链接，微信正文只放行公众号/视频号/小程序，其余会被去掉")

    # --- 图片 ---
    imgs = re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", body)
    remote = [s for s in imgs if s.startswith(("http://", "https://"))]
    local = [s for s in imgs if not s.startswith(("http://", "https://"))]
    if remote:
        add("WARN", f"{len(remote)} 张图是外链，粘贴后可能破图，建议本地图上传")

    try:
        from PIL import Image  # noqa: F401
        pil_ok = True
    except Exception:
        pil_ok = False

    for src in local:
        target = (path.parent / src).resolve()
        if not target.exists():
            add("ERR", f"图片不存在：{src}")
            continue
        size_mb = target.stat().st_size / 1024 / 1024
        if size_mb > 2:
            add("ERR", f"图片 {src} {size_mb:.1f}MB，超过 2MB 上限")
        elif size_mb > 0.5:
            add("WARN", f"图片 {src} {size_mb:.1f}MB，建议压到 500KB 以内")
        if pil_ok:
            try:
                from PIL import Image

                with Image.open(target) as im:
                    if im.width < 900:
                        add("WARN", f"图片 {src} 宽 {im.width}px，正文图建议 ≥ 900px")
            except Exception:
                pass

    cover = meta.get("cover")
    if cover and not cover.startswith(("http://", "https://")):
        cover_path = (path.parent / cover).resolve()
        if not cover_path.exists():
            add("ERR", f"封面不存在：{cover}")
        elif pil_ok:
            try:
                from PIL import Image

                with Image.open(cover_path) as im:
                    ratio = im.width / im.height
                    if abs(ratio - 2.35) > 0.12:
                        add("WARN", f"封面比例 {ratio:.2f}，公众号封面应为 2.35:1（用 prep_images.py 裁）")
            except Exception:
                pass
    if not cover:
        add("INFO", "frontmatter 没有 cover，发布时需在后台选封面（2.35:1 + 1:1）")

    # --- HTML ---
    if args.html:
        html_path = Path(args.html)
        if not html_path.exists():
            add("ERR", f"HTML 不存在：{args.html}")
        else:
            out = html_path.read_text(encoding="utf-8")
            if "<style" in out:
                add("ERR", "HTML 含 <style> 标签，微信会剥离")
            if "class=" in out:
                add("ERR", "HTML 含 class，微信会剥离")
            if "<script" in out:
                add("ERR", "HTML 含 <script>，会被删除且可能触发风控")
            if re.search(r"<(ul|li)\b", out):
                add("WARN", "HTML 用了 ul/li，符号可能被吃，改用带符号的 section")
            if re.search(r'<img[^>]+src="https?://', out):
                add("WARN", "HTML 里是外链图，粘贴后可能破图")
            if len(out) > 200_000:
                add("WARN", f"HTML {len(out)//1000}KB 偏大，粘贴可能卡")

    # --- 输出 ---
    errors = sum(1 for lv, _ in findings if lv == "ERR")
    warns = sum(1 for lv, _ in findings if lv == "WARN")
    oks = sum(1 for lv, _ in findings if lv == "OK")
    para_count = len([b for b in re.split(r"\n\s*\n", plain) if b.strip()])
    minutes = max(0.5, round(chars / 400, 1))

    lines = [
        "# 推文质检报告",
        "",
        f"- 文件：`{path.name}`",
        f"- 主题：`{meta.get('theme', 'paper')}`",
        f"- 正文字数：{chars}（约 {minutes} 分钟读完）",
        f"- 结构：{headings} 个小标题 / {len(imgs)} 张图 / {para_count} 段",
        f"- 结果：{errors} 个错误 / {warns} 个警告 / {oks} 项通过",
        "",
        "## 检查项",
        "",
    ]
    for level, msg in findings:
        mark = {"ERR": "❌", "WARN": "⚠️", "OK": "✅", "INFO": "ℹ️"}[level]
        lines.append(f"- {mark} **{level}** {msg}")

    lines += ["", "## 必须人工确认", ""]
    lines += [f"- [ ] {item}" for item in MANUAL]

    report = "\n".join(lines) + "\n"
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"[ok] report -> {args.output}")

    for level, msg in findings:
        print(f"[{level.lower()}] {msg}")
    print(f"[summary] errors={errors} warnings={warns} chars={chars}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
