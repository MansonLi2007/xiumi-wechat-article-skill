#!/usr/bin/env python3
"""Markdown -> 微信公众号兼容 HTML（单文件片段，全内联样式）。

输入约定（frontmatter 可选）：
    ---
    title: 文章标题
    summary: 摘要
    theme: paper | ink | mint
    cover: images/cover.jpg
    author: 作者
    ---

正文支持：
    # 大标题 / ## 小标题 / ### 三级标题
    普通段落（连续行为一段）
    **加粗**   ==高亮==   [文字](链接)
    > 引用（连续多行合并）
    - 无序列表 / 1. 有序列表
    --- 分割线
    ![图注](图片路径)
    指令块：:::lead  :::card 标题  :::quote  :::notice  :::end，以单独一行 ::: 结束

用法：
    python build_wechat.py article.md --theme paper -o article.html
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
THEMES_PATH = SKILL_ROOT / "assets" / "themes.json"

FONT_STACK = (
    "-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC',"
    "'Hiragino Sans GB','Microsoft YaHei',sans-serif"
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_themes() -> dict:
    with THEMES_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def split_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict[str, str] = {}
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        end = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                end = idx
                break
        if end is not None:
            for raw in lines[1:end]:
                if ":" in raw:
                    key, value = raw.split(":", 1)
                    meta[key.strip()] = value.strip().strip('"').strip("'")
            return meta, "\n".join(lines[end + 1:])
    return meta, "\n".join(lines)


class Renderer:
    def __init__(
        self,
        theme_name: str,
        themes: dict,
        placeholder_images: bool = False,
        image_base: Path | None = None,
    ):
        if theme_name not in themes:
            raise SystemExit(
                f"unknown theme {theme_name!r}; choose from {', '.join(sorted(themes))}"
            )
        theme = themes[theme_name]
        self.name = theme_name
        self.c = theme["colors"]
        self.f = theme["font"]
        self.r = theme["radius"]
        self.body2 = self.c.get("body2") or "#4A463F"
        self.quote_c = self.c.get("quote") or "#5A554E"
        self.placeholder_images = placeholder_images
        self.image_base = image_base
        self.img_seq = 0

    def resolve_src(self, src: str) -> str:
        """把相对图片路径转成 file:// 绝对地址，保证 HTML 放到任何目录都能预览。"""
        if self.image_base is None:
            return src
        if src.startswith(("http://", "https://", "data:", "file://", "/")):
            return src
        path = (self.image_base / src).resolve()
        return path.as_uri()

    # ---------- inline ----------
    def inline(self, text: str) -> str:
        out = html.escape(text, quote=False)
        out = re.sub(
            r"!\[([^\]]*)\]\(([^)\s]+)\)",
            lambda m: self.inline_image(m.group(1), m.group(2)),
            out,
        )
        out = re.sub(
            r"\[([^\]]+)\]\(([^)\s]+)\)",
            lambda m: (
                f'<a href="{m.group(2)}" style="color:{self.c["accent"]};'
                f'text-decoration:none;border-bottom:1px solid {self.c["accent_soft"]};">'
                f"{m.group(1)}</a>"
            ),
            out,
        )
        out = re.sub(
            r"\*\*(.+?)\*\*",
            lambda m: f'<strong style="font-weight:700;color:{self.c["text"]};">{m.group(1)}</strong>',
            out,
        )
        out = re.sub(
            r"==(.+?)==",
            lambda m: (
                f'<span style="background:{self.c["accent_soft"]};padding:0 2px;'
                f'border-radius:2px;">{m.group(1)}</span>'
            ),
            out,
        )
        return out

    # ---------- blocks ----------
    def image(self, caption: str, src: str, standalone: bool = False) -> str:
        cap = caption.strip()
        self.img_seq += 1
        if self.placeholder_images:
            label = f"图 {self.img_seq}"
            hint = cap or "在此插入图片"
            return (
                f'<section style="margin:24px 0;padding:44px 16px;background:{self.c["soft"]};'
                f'border:1px dashed {self.c["line"]};border-radius:{self.r}px;text-align:center;">'
                f'<p style="margin:0 0 8px;font-size:13px;line-height:1.6;'
                f'color:{self.c["sub"]};letter-spacing:1px;">{label}</p>'
                f'<p style="margin:0;font-size:14px;line-height:1.8;'
                f'color:{self.c["text"]};">{self.inline(hint)}</p>'
                f"</section>"
            )
        cap_html = ""
        if cap:
            cap_html = (
                f'<p style="margin:8px 0 0;font-size:{self.f["caption"]}px;line-height:1.6;'
                f'color:{self.c["sub"]};text-align:center;letter-spacing:0;">{self.inline(cap)}</p>'
            )
        return (
            f'<section style="margin:24px 0;">'
            f'<img src="{self.resolve_src(src)}" style="width:100%;display:block;'
            f'border-radius:{self.r}px;" alt="{html.escape(cap, quote=True)}"/>'
            f"{cap_html}</section>"
        )

    def inline_image(self, caption: str, src: str) -> str:
        """段落中间的图：只用行内元素，避免 <section> 嵌进 <p> 造成错位。"""
        cap = caption.strip()
        self.img_seq += 1
        if self.placeholder_images:
            return (
                f'<span style="display:inline-block;width:100%;padding:18px 10px;'
                f'background:{self.c["soft"]};border:1px dashed {self.c["line"]};'
                f'border-radius:{self.r}px;text-align:center;font-size:13px;'
                f'line-height:1.6;color:{self.c["sub"]};">图 {self.img_seq}：'
                f"{self.inline(cap or '在此插入图片')}</span>"
            )
        img = (
            f'<img src="{self.resolve_src(src)}" style="width:100%;vertical-align:middle;'
            f'margin:10px 0;border-radius:{self.r}px;" alt="{html.escape(cap, quote=True)}"/>'
        )
        if cap:
            img += (
                f'<br/><span style="font-size:{self.f["caption"]}px;line-height:1.6;'
                f'color:{self.c["sub"]};">{self.inline(cap)}</span>'
            )
        return img

    def profile(self, **overrides: object) -> dict:
        base = {
            "size": self.f["body"],
            "lh": self.f["lh"],
            "ls": self.f["ls"],
            "color": self.c["text"],
            "align": "justify",
            "margin": "0 0 1em",
        }
        base.update(overrides)
        return base

    def p(self, text: str, prof: dict | None = None) -> str:
        prof = prof or self.profile()
        return (
            f'<p style="margin:{prof["margin"]};font-size:{prof["size"]}px;'
            f'line-height:{prof["lh"]};letter-spacing:{prof["ls"]}px;'
            f'color:{prof["color"]};text-align:{prof["align"]};">{self.inline(text)}</p>'
        )

    def h1(self, text: str) -> str:
        return (
            f'<h1 style="margin:0 0 20px;font-size:22px;line-height:1.4;'
            f'color:{self.c["text"]};font-weight:700;text-align:center;">{self.inline(text)}</h1>'
        )

    def h2(self, text: str) -> str:
        return (
            '<section style="margin:36px 0 16px;">'
            f'<section style="width:32px;height:3px;background:{self.c["accent"]};'
            'margin:0 0 10px;"></section>'
            f'<h2 style="margin:0;font-size:{self.f["h2"]}px;line-height:1.5;'
            f'color:{self.c["text"]};font-weight:700;letter-spacing:0;">{self.inline(text)}</h2>'
            "</section>"
        )

    def h3(self, text: str) -> str:
        return (
            f'<h3 style="margin:24px 0 10px;font-size:{self.f["h3"]}px;line-height:1.5;'
            f'color:{self.c["text"]};font-weight:700;">{self.inline(text)}</h3>'
        )

    def hr(self) -> str:
        return (
            f'<section style="margin:32px 0;text-align:center;color:{self.c["line"]};'
            'font-size:13px;letter-spacing:8px;">· · ·</section>'
        )

    def quote(self, paras: list[str]) -> str:
        body = "".join(
            f'<p style="margin:0 0 8px;font-size:{self.f["body"]}px;line-height:1.9;'
            f'color:{self.c["sub"]};letter-spacing:{self.f["ls"]}px;">{self.inline(t)}</p>'
            for t in paras
        )
        return (
            f'<section style="margin:24px 0;padding:2px 0 2px 16px;'
            f'border-left:3px solid {self.c["accent"]};">{body}</section>'
        )

    def list_block(self, items: list[str], ordered: bool, prof: dict | None = None) -> str:
        prof = prof or self.profile()
        rows = []
        for idx, item in enumerate(items, 1):
            marker = f"{idx}." if ordered else "·"
            rows.append(
                f'<section style="margin:0 0 8px;font-size:{prof["size"]}px;'
                f'line-height:{prof["lh"]};letter-spacing:{prof["ls"]}px;'
                f'color:{prof["color"]};text-align:{prof["align"]};">'
                f'<span style="color:{self.c["accent"]};font-weight:700;'
                f'margin-right:8px;">{marker}</span>{self.inline(item)}</section>'
            )
        return '<section style="margin:12px 0 20px;">%s</section>' % "".join(rows)

    def container(self, kind: str, title: str, inner_blocks: list[tuple]) -> str:
        c, f = self.c, self.f
        margin = "0" if len(inner_blocks) == 1 else "0 0 8px"
        if kind == "lead":
            inner_html = self.render_blocks(inner_blocks, self.profile(size=f["lead"], color=self.body2, margin=margin))
            return (
                f'<section style="margin:8px 0 24px;padding:16px 18px;background:{c["soft"]};'
                f'border-radius:{self.r}px;">{inner_html}</section>'
            )
        if kind == "quote":
            inner_html = self.render_blocks(
                inner_blocks, self.profile(color=self.quote_c, lh=1.9, margin=margin)
            )
            return (
                f'<section style="margin:24px 0;padding:2px 0 2px 16px;'
                f'border-left:3px solid {c["accent"]};">{inner_html}</section>'
            )
        if kind == "notice":
            inner_html = self.render_blocks(inner_blocks, self.profile(size=15, color=self.body2, margin=margin))
            return (
                f'<section style="margin:20px 0;padding:14px 16px;background:{c["accent_soft"]};'
                f'border-left:3px solid {c["accent"]};'
                f'border-radius:0 8px 8px 0;">{inner_html}</section>'
            )
        if kind == "card":
            inner_html = self.render_blocks(inner_blocks, self.profile(size=15, color=self.body2, margin=margin))
            heading = ""
            if title:
                heading = (
                    f'<p style="margin:0 0 10px;font-size:17px;font-weight:700;'
                    f'color:{c["text"]};">{self.inline(title)}</p>'
                )
            return (
                f'<section style="margin:24px 0;padding:18px 16px;background:{c["card_bg"]};'
                f'border:1px solid {c["line"]};border-radius:{self.r}px;">'
                f"{heading}{inner_html}</section>"
            )
        if kind == "end":
            inner_html = self.render_blocks(
                inner_blocks, self.profile(size=14, color=c["sub"], lh=1.9, align="center", margin=margin)
            )
            return (
                f'<section style="margin:40px 0 8px;padding-top:24px;'
                f'border-top:1px dashed {c["line"]};text-align:center;">{inner_html}</section>'
            )
        return self.render_blocks(inner_blocks)

    # ---------- parse ----------
    def parse(self, lines: list[str]) -> list[tuple]:
        blocks: list[tuple] = []
        buf: list[str] = []

        def flush() -> None:
            if buf:
                blocks.append(("p", " ".join(x.strip() for x in buf)))
                buf.clear()

        i = 0
        while i < len(lines):
            raw = lines[i].rstrip()
            stripped = raw.strip()

            if not stripped:
                flush()
                i += 1
                continue

            if stripped.startswith(":::"):
                flush()
                match = re.match(r"^:::\s*([A-Za-z]+)\s*(.*)$", stripped)
                if match:
                    kind = match.group(1).lower()
                    title = match.group(2).strip()
                    if kind in {"lead", "quote", "notice", "end", "card"}:
                        inner: list[str] = []
                        j = i + 1
                        while j < len(lines) and lines[j].strip() != ":::":
                            inner.append(lines[j])
                            j += 1
                        blocks.append(("container", kind, title, self.parse(inner)))
                        i = j + 1
                        continue
                i += 1
                continue

            if stripped in {"---", "***", "___"}:
                flush()
                blocks.append(("hr",))
                i += 1
                continue

            if stripped.startswith("### "):
                flush()
                blocks.append(("h3", stripped[4:].strip()))
                i += 1
                continue
            if stripped.startswith("## "):
                flush()
                blocks.append(("h2", stripped[3:].strip()))
                i += 1
                continue
            if stripped.startswith("# "):
                flush()
                blocks.append(("h1", stripped[2:].strip()))
                i += 1
                continue

            img = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", stripped)
            if img:
                flush()
                blocks.append(("img", img.group(1), img.group(2)))
                i += 1
                continue

            if stripped.startswith(">"):
                flush()
                quote_lines = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    quote_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                    i += 1
                blocks.append(("quote", quote_lines))
                continue

            item = re.match(r"^[-*+]\s+(.*)$", stripped)
            if item:
                flush()
                items = []
                while i < len(lines):
                    m = re.match(r"^[-*+]\s+(.*)$", lines[i].strip())
                    if not m:
                        break
                    items.append(m.group(1))
                    i += 1
                blocks.append(("ul", items))
                continue

            item = re.match(r"^\d+[.)]\s+(.*)$", stripped)
            if item:
                flush()
                items = []
                while i < len(lines):
                    m = re.match(r"^\d+[.)]\s+(.*)$", lines[i].strip())
                    if not m:
                        break
                    items.append(m.group(1))
                    i += 1
                blocks.append(("ol", items))
                continue

            buf.append(raw)
            i += 1

        flush()
        return blocks

    # ---------- render ----------
    def render_blocks(self, blocks: list[tuple], prof: dict | None = None) -> str:
        parts = []
        for block in blocks:
            kind = block[0]
            if kind == "p":
                parts.append(self.p(block[1], prof))
            elif kind == "h1":
                parts.append(self.h1(block[1]))
            elif kind == "h2":
                parts.append(self.h2(block[1]))
            elif kind == "h3":
                parts.append(self.h3(block[1]))
            elif kind == "hr":
                parts.append(self.hr())
            elif kind == "img":
                parts.append(self.image(block[1], block[2]))
            elif kind == "quote":
                parts.append(self.quote(block[1]))
            elif kind == "ul":
                parts.append(self.list_block(block[1], ordered=False, prof=prof))
            elif kind == "ol":
                parts.append(self.list_block(block[1], ordered=True, prof=prof))
            elif kind == "container":
                _, sub, title, inner_blocks = block
                parts.append(self.container(sub, title, inner_blocks))
        return "\n".join(parts)

    def wrap(self, body: str) -> str:
        return (
            f'<section style="max-width:677px;margin:0 auto;padding:0;'
            f"font-size:{self.f['body']}px;line-height:{self.f['lh']};"
            f"letter-spacing:{self.f['ls']}px;color:{self.c['text']};"
            f'font-family:{FONT_STACK};word-break:break-word;">\n'
            f"{body}\n</section>"
        )

    def render(self, text: str) -> str:
        _, body = split_frontmatter(text)
        blocks = self.parse(body.split("\n"))
        return self.wrap(self.render_blocks(blocks))


def main() -> int:
    ap = argparse.ArgumentParser(description="Markdown -> WeChat-safe HTML fragment")
    ap.add_argument("source", help="markdown 文件")
    ap.add_argument("--theme", default=None, help="themes.json 里的主题名，默认取 frontmatter.theme 或 paper")
    ap.add_argument("-o", "--output", default=None, help="输出 html 路径，默认同名 .html")
    ap.add_argument(
        "--placeholder-images",
        action="store_true",
        help="不输出 <img>，改用带图注的虚线占位块（粘进微信/秀米后手动插图，避免破图）",
    )
    ap.add_argument(
        "--keep-relative",
        action="store_true",
        help="保留相对图片路径；默认转成 file:// 绝对地址，方便在任意目录预览",
    )
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"file not found: {src}")

    text = src.read_text(encoding="utf-8")
    meta, _ = split_frontmatter(text)
    themes = load_themes()
    theme = args.theme or meta.get("theme") or "paper"

    renderer = Renderer(
        theme,
        themes,
        placeholder_images=args.placeholder_images,
        image_base=None if args.keep_relative else src.resolve().parent,
    )
    out_html = renderer.render(text)

    for forbidden in ("<style", "<script", "class=", 'id="'):
        if forbidden in out_html:
            raise SystemExit(f"internal error: output contains {forbidden!r}")

    out = Path(args.output) if args.output else src.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(out_html + "\n", encoding="utf-8")

    print(f"[ok] theme={theme} blocks_html={out_html.count('<section')} -> {out}")
    print(f"[info] title={meta.get('title', '')!r} summary_len={len(meta.get('summary', ''))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
