"""把思维导图清洗成可公开版本，并放入网站。

清洗项（只删这三类，不动知识内容）：
  1. 个人信息：姓名、学校名、"学生："、同步基准日期
  2. src 字段：35 条指向本机磁盘的路径（公开无意义，还泄漏目录结构）
  3. 关于"材料缺失/无 OCR"的元信息（观感问题，且暗示老师材料的获取情况）

保留：全部 529 个知识节点、时间线、交互功能（搜索/展开/折叠/时间线/侧栏）。

方法：以文本方式定位 DATA 与 TIMELINE 两个字面量，做定向替换，其余代码原样保留。
"""

import os
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

data = import_module("site-data")

SRC = Path(os.environ.get("AUSMAT_MINDMAP")
           or (Path(__file__).resolve().parent / "corpus" / "mindmap.html"))   # 原始导图 HTML
OUT = Path(os.environ.get("AUSMAT_SITE")
           or (Path(__file__).resolve().parent / "my-site")) / "notes" / "mindmap.html"
D = Path(__file__).resolve().parent      # 脚本所在目录，用于调子脚本

# 导图在 notes/ 下，且只有一份（不随语言分文件），所以站内链接固定用这一层前缀。
# 英文切换时由注入的 JS 把 href 换成 data-href-en。
LINK_PREFIX = "../"

# DATA 里做过的节点名更正。定义必须放在文件前部 —— 后面有两处要用它，
# 而 Python 是顺序执行，放晚了就是 NameError（这次会话已经栽过三次同类问题：
# NAME = BRAND、themeVar 位置、以及这一处）。
#   * 说明的键要同步（子代理读的是源文件，用的是原名）
#   * i18n 词典的键与正文也要同步（否则该节点英文退回中文）
# **必须同样作用于这两处**，否则键对不上：
# 实际踩到：MAM 的键写 `lim(aʰ−1)/h`，产物里已改成 `lim(h→0)(aʰ−1)/h`，46 条全挂不上。
NAME_FIXES = [
    ("lim(aʰ−1)/h", "lim(h→0)(aʰ−1)/h"),
    ("R_E = 6.38×10⁶ m", "R_E = 6.37×10⁶ m"),
    # 节点名写「平均电动势 ε_avg = −4BANf」，但同一节点的说明写的是 ε_avg=4BANf。
    # 半周期（正弦）的平均值量值就是 2ε_max/π = 4BANf，负号属于方向约定、
    # 由楞次定律单独判断（节点名后半句正是在讲这个），不该写进量值式。
    # 高分学生走查发现这处自相矛盾。
    # 用**语言中立**的模式：中文名与英文名（Average emf ε_avg = −4BANf）都要覆盖，
    # 否则英文侧会留着负号。
    ("平均电动势 ε_avg = −4BANf", "平均电动势 ε_avg = 4BANf"),
    ("ε_avg = −4BANf", "ε_avg = 4BANf"),
]
# i18n 里的英文名也要跟着改（词典里那条的 name 带着旧写法）
ROOT_NAME = "AUSMAT May 2026 学习资料"

# 只生成一份、住在中文树 notes/ 下的页面 —— 与 site-build.py 的规则一致。
# 这些页面的"英文目标"不能写成 en/notes/...，那里根本没有文件：
#   mindmap.html            导图只有一份（双语在一个文件里，靠页内 JS 切）
#   advising/index.html     升学自检中英是两个文件，但都在 notes/advising/ 下
#   advising/en.html
# 不这么分，英文导航里这两项就是 404（踩过）。
SAME_FILE_BOTH_LANGS = {"mindmap.html"}
CROSS_TREE = {"mindmap.html", "advising/index.html", "advising/en.html"}

# ── 站点外壳 ────────────────────────────────────────────────────────────
#
# 2026-10 重做：导图原来是一个自带蓝色配色、height:100vh 全屏独占的独立应用，
# 跟站点其他页没有任何共同结构 —— 没有站点页头、没有页脚、不引站点样式表、
# 深色模式不支持。观感上跟其他页完全割裂。
#
# 现在改成与站点同构：套 header.site + main/.wrap + .note-head + footer.site，
# 配色全部走 assets/style.css 的变量（所以深色模式自动跟随），画布收进一张卡片，
# 原来的右侧详情栏移到画布下方（站点内容宽度是 780px，左右并排放不下）。
#
# 一个功能都没删：缩放、平移、点节点展开收起、搜索高亮、全部展开/收起、适应窗口、
# 考试时间线浮层、详情栏、图例、中英切换、节点计数。脚本里引用的 14 个 DOM id
# 全部保留原名，脚本因此一行都不用改。

MM_CSS = """
/* 知识导图 · 全部配色取自站点 assets/style.css 的变量，深色模式自动生效。
   这里只放导图独有的东西，通用排版（页头/页脚/标题/表格）交给站点样式表。 */
#app { display: block; }
.mm-toolbar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 0 0 14px;
}
.mm-toolbar input {
  font: inherit; font-size: .9rem; padding: 7px 12px; width: 210px; outline: none;
  border: 1px solid var(--line); border-radius: 8px;
  background: var(--bg); color: var(--text);
}
.mm-toolbar input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-bg); }
.mm-toolbar button {
  font: inherit; font-size: .87rem; padding: 7px 14px; cursor: pointer;
  border: 1px solid var(--line); border-radius: 8px;
  background: var(--bg); color: var(--text-soft);
  transition: background .15s, border-color .15s, color .15s;
}
.mm-toolbar button:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-bg); }
.mm-toolbar button.active { background: var(--accent); border-color: var(--accent); color: #fff; }
.mm-toolbar .spacer { flex: 1; }

/* 「适应窗口」缩到下限仍放不下时的提示条 */
.mm-hint {
  margin: 8px 0 0; padding: 7px 12px; border-radius: 6px;
  font-size: .82rem; color: var(--warn); background: var(--warn-bg);
}

/* ── 打印 ────────────────────────────────────────────────────────
   学生真实需求是「打出来背」（高分学生走查原话）。

   ⚠ 第一版这里只写了 `#canvasWrap svg { height: 70vh }`，**是坏的**：
   SVG 没有 viewBox、transform 也没重置，打印出来只截当前视口那一块。
   两位走查各自实测：全部展开后打印成 PDF，470 个知识点名命中 0 个。

   而把整棵树缩到一页宽同样不可读（1156px → 180mm 时 12.5px 的字只剩 1.9px）。
   所以打印改成输出**文本大纲**（#printOutline，由 buildPrintOutline 在
   beforeprint 时填充）：缩进反映层级、节点带说明，可读且能自然分页。
   画布本身在打印时隐藏，不再假装「导图能打印」。 */
.print-only { display: none; }

@media print {
  .mm-toolbar, #fitHint, #legend, #timeline, #canvasWrap,
  .site-nav, footer.site, .back, .lang-switch, nav,
  /* 页面标题区与详情栏：不隐藏的话每份 PDF 会印两遍标题，
     末尾还多出一段空详情栏（走查实测）。 */
  .note-head, #side { display: none !important; }
  .print-only { display: block !important; }
  #app, .wrap, main { max-width: none !important; width: 100% !important; }
  body { background: #fff !important; color: #000 !important; }
  .note-head h1, #sideTitle, #sideBody { color: #000 !important; }
  #printOutline .po-h1 { font-size: 15pt; font-weight: 700; margin: 0 0 2pt; }
  #printOutline .po-meta { font-size: 9pt; color: #555; margin: 0 0 10pt; }
  #printOutline .po-l { font-size: 10pt; line-height: 1.45; white-space: pre-wrap; }
  #printOutline .po-n { font-size: 8.5pt; line-height: 1.4; color: #333;
                        white-space: pre-wrap; margin: 0 0 3pt; }
  #printOutline .po-d0 { font-weight: 700; margin-top: 8pt; }
  #printOutline .po-d1 { font-weight: 600; margin-top: 5pt; }
  #printOutline .po-d2 { margin-left: 10pt; }
  #printOutline .po-d3 { margin-left: 20pt; }
  #printOutline .po-d4 { margin-left: 30pt; }
  @page { margin: 14mm; }
}

/* 画布卡片。高度用 vh 夹住，太高会把页脚顶到屏幕外，太矮看不清树。 */
#canvasWrap {
  position: relative; overflow: hidden; cursor: grab;
  height: clamp(340px, 56vh, 600px);
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--bg-soft);
}
#canvasWrap.dragging { cursor: grabbing; }
#canvasWrap svg { display: block; width: 100%; height: 100%; }
.node-rect { stroke-width: 1.5; cursor: pointer; }
.node-label { font-size: 12.5px; pointer-events: none; dominant-baseline: middle; }
.badge { font-size: 11px; pointer-events: none; dominant-baseline: middle; font-weight: 700; }
.link { fill: none; stroke-width: 1.8; opacity: .55; }
.node-g { cursor: pointer; }
.node-g:hover .node-rect { filter: brightness(.96); }
.dim { opacity: .15; transition: opacity .2s; }
.hit { opacity: 1; }

/* 提示条压在画布左下角 */
#canvasWrap .tip {
  position: absolute; left: 12px; bottom: 10px; pointer-events: none;
  font-size: 11.5px; color: var(--text-soft); opacity: .85;
  background: var(--bg); border: 1px solid var(--line); border-radius: 6px; padding: 3px 9px;
}

/* 详情栏：移到画布下方，跟文档流一致 */
#side {
  margin-top: 22px; padding: 16px 20px;
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--bg-soft);
}
#side h2 {
  font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
  color: var(--text-soft); margin: 0 0 10px;
}
#sideTitle { font-size: 1.05rem; font-weight: 700; margin: 0 0 10px; line-height: 1.5; }
#sideBody { font-size: .94rem; line-height: 1.85; white-space: pre-wrap; }
#sideSrc {
  margin-top: 14px; padding: 9px 11px; font-size: .8rem; line-height: 1.6;
  color: var(--text-soft); background: var(--bg);
  border: 1px solid var(--line); border-radius: 8px; word-break: break-all;
}

.legend { margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--line); }
.legend h2 {
  font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
  color: var(--text-soft); margin: 0 0 8px;
}
.legend div {
  display: flex; align-items: center; gap: 8px; font-size: .87rem;
  padding: 4px 0; cursor: pointer; border-radius: 6px;
}
.legend div:hover { color: var(--accent); }
.legend i { width: 12px; height: 12px; border-radius: 4px; display: inline-block; flex-shrink: 0; }

/* 考试时间线：盖在画布上的一张可滚动表 */
#timeline {
  position: absolute; inset: 0; display: none; overflow-y: auto;
  padding: 24px 28px 40px; background: var(--bg);
}
#timeline.show { display: block; }
#timeline h2 { margin: 0 0 4px; font-size: 1.15rem; }
#timeline p.sub { margin: 0 0 18px; color: var(--text-soft); font-size: .84rem; line-height: 1.7; }
#timeline table { width: 100%; margin: 0; font-size: .84rem; }
#timeline th, #timeline td { padding: 8px 11px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
#timeline th { background: var(--accent-bg); color: var(--text); font-weight: 600; white-space: nowrap; }
#timeline td.date { white-space: nowrap; font-weight: 600; }
#timeline tr:last-child td { border-bottom: none; }

/* 窄屏：这张表三列加起来 399px，面板只有 344px，「考核内容」整列被裁在面板外
   又没法滚（这张表是 buildTimeline 在 JS 里拼的，套不了站点的 .tw 容器）。
   让面板自己横滚。 */
@media (max-width: 700px) {
  #timeline { overflow-x: auto; }
}
#timeline .tag {
  display: inline-block; padding: 1px 7px; border-radius: 20px;
  font-size: .72rem; font-weight: 600; color: #fff; white-space: nowrap;
}

@media print {
  .mm-toolbar, #canvasWrap .tip { display: none; }
  #canvasWrap { height: auto; page-break-inside: avoid; }
}
"""


def nav_html() -> str:
    """站点导航，与 site-build.py 同源（data.NAV）。

    导图只有一份文件、中英靠页内 JS 切换，所以每个链接同时带中文标签
    (data-i18n，注入器据此换字) 与英文目标 (data-href-en，applyLang 据此换 href)。
    """
    out = []
    for entry in data.NAV:
        name, zh_lbl, en_lbl = entry[0], entry[1], entry[2]
        en_name = entry[3] if len(entry) > 3 else name
        zh_href = LINK_PREFIX + ("index.html" if name == "index.html" else f"notes/{name}")
        if en_name in CROSS_TREE:
            # 跨树：文件在中文树里，英文站也指同一份
            en_href = LINK_PREFIX + ("index.html" if en_name == "index.html" else f"notes/{en_name}")
        else:
            en_href = LINK_PREFIX + ("en/index.html" if en_name == "index.html"
                                     else f"en/notes/{en_name}")
        on = ' class="on"' if name == "mindmap.html" else ""
        # 导图自己这一项也带语言：否则在英文模式下点「Mind Map」会退回上次记住的
        # 语言（甚至中文）。点击自身等于一次「带语言刷新」。
        if name == "mindmap.html":
            zh_href += "?lang=zh"
            en_href += "?lang=en"
        out.append(f'<a href="{zh_href}" data-href-en="{en_href}" '
                   f'data-i18n="{zh_lbl}"{on}>{zh_lbl}</a>')
    return "\n      ".join(out)


def site_header() -> str:
    return ('<header class="site">\n  <div class="wrap">\n'
            f'    <a class="brand" href="{LINK_PREFIX}index.html">{data.BRAND_ZH}</a>\n'
            f'    <nav>{nav_html()}</nav>\n'
            '    <div class="lang-switch">'
            '<button id="btnLang" class="lang-link" type="button" '
            'title="切换语言 / Switch language">EN</button></div>\n'
            '  </div>\n</header>')


# 删掉 src 字段后，这几处界面文案就过时了（还在说"桌面上的资料位置"）
UI_FIXES = [
    ("这里会显示该知识点的具体内容，以及它在桌面上对应的资料文件位置。",
     "这里会显示该知识点的具体内容。"),
    ("点击节点可展开/收起，右侧面板会显示该知识点的说明与它在桌面上的资料位置。",
     "点击节点可展开/收起，右侧面板会显示该知识点的说明。"),
    ("点击节点可展开/收起，右侧面板显示该知识点的说明。",
     "点击节点可展开/收起，右侧面板显示该知识点的说明。"),
    ("<h2>内容详情</h2>", "<h2>内容详情</h2>"),
]

t = SRC.read_text(encoding="utf-8", errors="replace")
orig_len = len(t)


def find_literal(text: str, start_marker: str, open_ch: str, close_ch: str) -> tuple[int, int]:
    """返回 [起, 止) 区间，覆盖从 start_marker 开始的整个字面量。"""
    i = text.index(start_marker)
    j = text.index(open_ch, i)
    depth = 0
    k = j
    while k < len(text):
        c = text[k]
        if c == '"':                       # 跳过字符串，避免把字符串里的括号当结构
            k += 1
            while k < len(text) and text[k] != '"':
                if text[k] == "\\":
                    k += 1
                k += 1
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i, k + 1
        k += 1
    raise ValueError(f"未找到 {start_marker} 的结束位置")


def clean(text: str) -> tuple[str, list[str]]:
    report = []

    # ── 1. 个人信息 ──────────────────────────────────────────────
    # DATA 的顶层 note：整段重写，避免留下「学生：」这种残迹
    old_note = re.search(r'(const DATA = \{[\s\S]*?note: ")([\s\S]*?)(",)', text)
    if old_note:
        new_note = ("AUSMAT May 2026（西澳 WACE / ATAR 课程）五科学习内容总览。\\n\\n"
                    "点击节点可展开/收起，右侧面板显示该知识点的说明。")
        text = text[:old_note.start(2)] + new_note + text[old_note.end(2):]
        report.append("顶层说明已重写（移除姓名/学校/同步日期）")

    # 时间线里的学校地点与点名信息
    before = text
    text = re.sub(r"·\s*Sunway 大学[^\"\\]*", "", text)
    text = re.sub(r"【强制出席】", "", text)
    if text != before:
        report.append("时间线中的学校地点与点名信息已移除")

    # 兜底：任何残留的姓名/学校
    for pat, label in ((r"WEN\s*CHENGZHI", "姓名"), (r"Sunway", "学校名"), (r"学生：", "学生标记")):
        n = len(re.findall(pat, text, re.I))
        if n:
            text = re.sub(pat, "", text, flags=re.I)
            report.append(f"兜底清理 {label} × {n}")

    # ── 2. 删除 src 字段 ─────────────────────────────────────────
    n_src = len(re.findall(r'src:\s*"(?:[^"\\]|\\.)*"\s*,?', text))
    text = re.sub(r'\s*src:\s*"(?:[^"\\]|\\.)*"\s*,?', "", text)
    report.append(f"删除 src 本地路径字段 × {n_src}")

    # ── 3. 材料缺失类说明 ────────────────────────────────────────
    repl = [
        (r"（课程大纲要求；讲义文件缺失，见 REVISION）", "（课程大纲要求）"),
        (r"（原讲义 PDF 无 OCR 文本，可参考课程大纲与 EA REVISION）", "（参考课程大纲与 EA REVISION）"),
    ]
    n_meta = 0
    for pat, rep in repl:
        c = len(re.findall(pat, text))
        text = re.sub(pat, rep, text)
        n_meta += c
    report.append(f"清理材料缺失类说明 × {n_meta}")

    return text, report


# 只处理 DATA 与 TIMELINE 两个字面量，保留全部交互代码
data_start, data_end = find_literal(t, "const DATA", "{", "}")
tl_start, tl_end = find_literal(t, "TIMELINE", "[", "]")
print(f"DATA 字面量   : {data_end - data_start} 字符")
print(f"TIMELINE 字面量: {tl_end - tl_start} 字符")

new_data, rep1 = clean(t[data_start:data_end])
new_tl, rep2 = clean(t[tl_start:tl_end])

out = t[:data_start] + new_data + t[data_end:tl_start] + new_tl + t[tl_end:]

# ── 4. 修过时的界面文案（src 字段已删，不能再提「桌面上的资料位置」）──
n_ui = 0
for old, new in UI_FIXES:
    if old in out and old != new:
        out = out.replace(old, new)
        n_ui += 1
report_ui = [f"更新过时界面文案 × {n_ui}"]

# ── 5. 套上站点外壳 ──────────────────────────────────────────────
# 用锚点替换，不做全文重排：脚本那 150KB 一行都不动。
MM_TITLE = "知识导图"
MM_META = "五科知识点总览 · 可搜索、可缩放、可展开"

site_css = ('<link rel="stylesheet" href="../assets/style.css">\n'
            '<meta name="description" content="AUSMAT 五科知识点总览：'
            'MAM 数学方法、HBY 人体生物学、PHY 物理、ELD 英语、CSC 计算机科学的知识节点与中文说明，'
            '可搜索、可缩放、可展开，另附考试时间线。">')
# 锚在 </head> 上而不是 <title> 上：标题是在本步骤之后才被改写的，
# 用 <title> 做锚点会匹配不到（踩过一次）。
if "</head>" in out:
    out = out.replace("</head>", site_css + "\n</head>", 1)
    report_ui.append("引入站点样式表 assets/style.css")
else:
    report_ui.append("⚠ 未找到 </head> 锚点，站点样式表未引入")

# 它自己那套蓝色全屏样式整块换掉
if re.search(r"(?s)<style>.*?</style>", out):
    out = re.sub(r"(?s)<style>.*?</style>", "<style>" + MM_CSS + "</style>", out, count=1)
    report_ui.append("替换自有样式为站点配色（深色模式随之生效）")
else:
    report_ui.append("⚠ 未找到 <style> 块")

# ── 5a. body 开头：插入站点页头、标题区与工具栏 ──────────────────
BODY_TOP = f"""<body>
{site_header()}
<main><div class="wrap">
<div class="note-head">
  <a class="back" href="{LINK_PREFIX}index.html" data-href-en="{LINK_PREFIX}en/index.html" data-i18n="首页">← 首页</a>
  <h1 id="mmTitle" data-i18n="AUSMAT 学习资料思维导图">AUSMAT 学习资料思维导图<small id="stat"></small></h1>
  <div class="meta" data-i18n="{MM_META}">{MM_META}</div>
</div>
<div id="app">
  <div class="mm-toolbar">
    <input id="search" type="search" placeholder="搜索知识点…" aria-label="搜索知识点"
           data-ph-zh="搜索知识点…" data-ph-en="Search topics…"
           data-al-zh="搜索知识点" data-al-en="Search topics">
    <button id="btnExpand" data-i18n="全部展开">全部展开</button>
    <button id="btnCollapse" data-i18n="全部收起">全部收起</button>
    <button id="btnFit" data-i18n="适应窗口">适应窗口</button>
    <button id="btnTimeline" data-i18n="考试时间线">考试时间线</button>
  </div>
  <div id="fitHint" class="mm-hint" style="display:none" data-i18n="已缩到最小可读比例，再小就看不清了；其余部分请拖动查看">已缩到最小可读比例，再小就看不清了；其余部分请拖动查看</div>
  <div id="printOutline" class="print-only"></div>
  """

m_top = re.search(r"<body>.*?(?=<div id=\"main\">)", out, re.S)
if m_top:
    out = out[:m_top.start()] + BODY_TOP + out[m_top.end():]
    report_ui.append("套上站点页头 + 标题区 + 工具栏")
else:
    report_ui.append("⚠ 未找到 body 开头锚点，站点页头未插入")

# ── 5b. body 结尾：补页脚，闭合新增的容器 ────────────────────────
BODY_END = ('</aside>\n  </div>\n</div>\n</div></main>\n'
            '<footer class="site"><div class="wrap">' + data.FOOTER_ZH + '</div></footer>\n\n')

m_end = re.search(r"</aside>\s*</div>\s*</div>\s*(?=<script)", out, re.S)
if m_end:
    out = out[:m_end.start()] + BODY_END + out[m_end.end():]
    report_ui.append("补上站点页脚并闭合容器")
else:
    report_ui.append("⚠ 未找到 body 结尾锚点，页脚未加入")

# ── 5e. 详情栏的兜底文案 ─────────────────────────────────────────
# 三个问题一起修：
#   1. 叶子节点（529 个里的 470 个）没有 note，点开只显示「（具体知识点）」。
#      但 name 本身就是完整知识点（例："指数函数求导：e 的引入 …"），标题已经
#      显示了它，正文再说一句废话纯属噪音 —— 直接留空。
#   2. 这两句兜底文案是 JS 字符串，不走 data-i18n 机制，所以**永远不翻译**，
#      切到英文仍显示中文。改成按 LANG 取。
#   3. 切语言时 applyLang 会把详情栏重置成初始提示，已选中的节点内容丢失。
#      改成记住最后选中的节点，切语言后按新语言重渲染。
# 注意锚点用的是**长版本**文案：把长版截短的是原步骤 6，而它在本步骤之后才跑，
# 所以这里必须锚长版（最初锚短版，结果一直匹配不上，白改一轮）。本步骤已经完整
# 接管了这件事，步骤 6 因此退休。
OLD_DETAIL = ('  sideBody.textContent = n.note || ((n.children && n.children.length) '
              '? "（分类目录节点，展开可查看下属知识点）" '
              ': "（具体知识点。相关讲义、练习与真题见桌面 Ausmart 文件夹内对应科目目录）");')
NEW_DETAIL = ('  LAST_DETAIL = n;\n'
              '  // 有 note 就用；没有则给出它在树里的位置（由现有结构推导，不编内容）。\n'
              '  // 原来这里对 470 个叶子节点显示「（具体知识点）」，毫无信息量。\n'
              '  if (n.note){ sideBody.textContent = n.note; }\n'
              '  else {\n'
              '    const chain = pathOf(DATA, n);\n'
              '    const up = chain.slice(0, -1).map(function(x){ return x.name; });\n'
              '    const sibs = chain.length > 1\n'
              '      ? (chain[chain.length-2].children || []).filter(function(k){ return k !== n; })\n'
              '      : [];\n'
              '    const L = [];\n'
              '    if (up.length) L.push((LANG === "en" ? "Path: " : "位置：") + up.join(" › "));\n'
              '    if (sibs.length) L.push((LANG === "en" ? "Alongside " + sibs.length + " other topics here: "\n'
              '                                           : "同级还有 " + sibs.length + " 条：")\n'
              '      + sibs.slice(0, 6).map(function(k){ return k.name; }).join("、")\n'
              '      + (sibs.length > 6 ? (LANG === "en" ? ", and more" : " 等") : ""));\n'
              '    sideBody.textContent = L.join("\\n");\n'
              '  }')
if OLD_DETAIL in out:
    out = out.replace(OLD_DETAIL, NEW_DETAIL, 1)
    report_ui.append("详情栏：叶子节点不再显示占位句，分类提示改为随语言切换")
else:
    report_ui.append("⚠ 未找到详情栏兜底文案锚点")

# 变量必须声明在函数**外**，否则每次调用都被重置，applyLang 也看不见它。
# 锚点是单行的 —— 多行锚点在这套构建里匹配不上（文件是 CRLF，且两行之间的
# 空白难以精确复现），下面那条同理。
FUNC_OLD = "function showDetail(n){"
FUNC_NEW = ("let LAST_DETAIL = null;   // 记住最后选中的节点，切语言后按新语言重渲染\n"
            "// 从树上找出某个节点的祖先链（含它自己）。529 个节点，点一次遍历一遍完全够用，\n"
            "// 好过在每个节点上挂 _parent 指针。\n"
            "function pathOf(root, target){\n"
            "  let found = null;\n"
            "  (function walk(n, chain){\n"
            "    if (found) return;\n"
            "    const c = chain.concat([n]);\n"
            "    if (n === target){ found = c; return; }\n"
            "    if (n.children) n.children.forEach(function(k){ walk(k, c); });\n"
            "  })(root, []);\n"
            "  return found || [];\n"
            "}\n"
            "function showDetail(n){")
if FUNC_OLD in out:
    out = out.replace(FUNC_OLD, FUNC_NEW, 1)
    report_ui.append("LAST_DETAIL 声明在函数外（切语言才读得到）")
else:
    report_ui.append("⚠ 未找到 showDetail 函数头")

OLD_RESET = ('    if (sb) sb.textContent = lang === "en" '
             '? "Details of the selected topic appear here." : "这里会显示该知识点的具体内容。";')
NEW_RESET = ('    if (LAST_DETAIL) showDetail(LAST_DETAIL);\n'
             '    else if (sb) sb.textContent = lang === "en" '
             '? "Details of the selected topic appear here." : "这里会显示该知识点的具体内容。";')
# 这一条**不能**在这里做：那段 applyLang 代码是第 7 步由注入器加进来的，
# 此刻文件里还没有它，锚点必然匹配不到（这一版先踩了步骤顺序，白改一轮）。
# 实际替换放在注入之后。详见文件末尾「8. 注入后再修 applyLang」。

# ── 5d. 启动视图改成按实际画布自适应 ─────────────────────────────
# 原来启动调 initialView()，它把 k=0.85 / x=46 / y=28 写死 —— 那是按旧的
# height:100vh 整屏画布定的。画布收进 736px 宽的卡片后，树仍按旧尺寸摆放，
# 结果偏在右边、左侧大片空白（截图才发现）。
# 改调 fit(0.5)：读 getBoundingClientRect() 按真实尺寸缩放并左对齐。
# 再挂一个 resize 监听 —— 原来没有，窗口一变尺寸树就不跟着动。
INIT_OLD = "render(); initialView();"
INIT_NEW = ('render(); fit(0.5);\n'
            '  // 画布尺寸随窗口变化，重新适配一次（原来没有这个监听）\n'
            '  let _rzT = null;\n'
            '  window.addEventListener("resize", function(){ clearTimeout(_rzT); '
            '_rzT = setTimeout(function(){ fit(0.5); }, 150); });')
if INIT_OLD in out:
    out = out.replace(INIT_OLD, INIT_NEW, 1)
    report_ui.append("启动视图改为自适应（fit），并加上窗口 resize 重适配")
else:
    report_ui.append("⚠ 未找到启动视图锚点，视图仍按旧尺寸摆放")

# ── 5c. 断言脚本依赖的 DOM id 一个都没丢 ─────────────────────────
REQUIRED_IDS = ["btnCollapse", "btnExpand", "btnFit", "btnLang", "btnTimeline",
                "canvasWrap", "legend", "search", "sideBody", "sideSrc",
                "sideTitle", "stat", "timeline", "viewport", "svg", "main", "app"]
missing = [i for i in REQUIRED_IDS if f'id="{i}"' not in out]
if missing:
    report_ui.append("⚠ 外壳改造后缺失 DOM id：" + ", ".join(missing))
else:
    report_ui.append(f"外壳改造后 {len(REQUIRED_IDS)} 个 DOM id 全部保留")


# ── 6. 侧栏兜底文案 ──────────────────────────────────────────────
# 已由上面的详情栏步骤完整接管（它替换的就是整条 sideBody 赋值语句，
# 把那句指向「桌面 Ausmart 文件夹」的过时文案一并去掉了）。这里只留说明。
report_ui.append("侧栏兜底文案由详情栏步骤统一处理（原步骤 6 已并入）")

# ── 6b. 节点改名的同步（必须在第 7 步注入之前）────────────────────
# i18n 词典按节点**路径**索引。上面任何一处 NAME_FIXES 改了节点名，词典里那条就
# 永远查不到 —— 表现是该节点在英文视图里退回中文。
#
# 这一步**必须排在注入之前**：注入会把词典内容嵌进 HTML，之后再改名，HTML 里
# 嵌的仍是旧键。（第一版就放错了顺序，产物里那两处旧键始终不消失。）
I18N_FILE = OUT.parent.parent / "_i18n" / "mindmap-i18n.json"
if I18N_FILE.exists():
    try:
        _tr = json.loads(I18N_FILE.read_text(encoding="utf-8"))
    except Exception as _e:
        _tr = None
        report_ui.append(f"⚠ i18n 词典解析失败，改名后的键未同步：{_e}")
    if _tr is not None:
        _renamed = _vals = 0
        for _k in list(_tr.keys()):
            _nk = _k
            for _a, _b in NAME_FIXES:
                _nk = _nk.replace(_a, _b)
            if _nk != _k:
                _tr[_nk] = _tr.pop(_k)
                _renamed += 1
        for _v in _tr.values():
            for _fld in ("name", "note"):
                if isinstance(_v.get(_fld), str):
                    _o = _v[_fld]
                    for _a, _b in NAME_FIXES:
                        _v[_fld] = _v[_fld].replace(_a, _b)
                    if _v[_fld] != _o:
                        _vals += 1
        if _renamed or _vals:
            I18N_FILE.write_text(json.dumps(_tr, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
            report_ui.append(f"i18n 词典同步改名：{_renamed} 个键、{_vals} 处正文")

        # 节点说明的英文版并进词典的 note 字段 —— swapLang 本来就是从
        # I18N[path].note 取英文说明的，所以走这条路不用改渲染逻辑。
        # 键同样要补根名前缀并套用 NAME_FIXES（与中文说明一致的处理）。
        _en_added = _en_orphan = 0
        for _s in ("MAM", "PHY", "HBY", "ELD", "CSC"):
            _ef = D / "_sp" / f"notes-en-{_s}.json"
            if not _ef.exists():
                continue
            try:
                _ed = json.loads(_ef.read_text(encoding="utf-8"))
            except Exception as _e:
                report_ui.append(f"⚠ notes-en-{_s}.json 解析失败：{_e}")
                continue
            for _k, _v in _ed.items():
                if not (isinstance(_v, str) and _v.strip()):
                    continue
                _k = _k.strip()
                for _a, _b in NAME_FIXES:
                    _k = _k.replace(_a, _b)
                if not _k.startswith(ROOT_NAME + "/"):
                    _k = f"{ROOT_NAME}/{_k}"
                if _k in _tr:
                    _tr[_k]["note"] = _v.strip()
                    _en_added += 1
                else:
                    _en_orphan += 1
            report_ui.append(f"合并 notes-en-{_s}.json（{len(_ed)} 条）")
        if _en_added or _en_orphan:
            I18N_FILE.write_text(json.dumps(_tr, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
            _msg = f"英文说明并入词典 {_en_added} 条"
            if _en_orphan:
                _msg += f"（{_en_orphan} 条在词典里找不到对应路径，已跳过）"
            report_ui.append(_msg)

# ── 7. 注入中英双语支持（需要 _i18n/mindmap-i18n.json）──────────
# 关键：注入脚本只接收文件内容并**返回**注入后的内容，不自己写盘。
# 之前让它写盘，结果被本脚本后面的 write_text 用内存里未注入的版本覆盖，
# 表面上「注入成功」，实际文件里什么都没有。
I18N = OUT.parent.parent / "_i18n" / "mindmap-i18n.json"
if I18N.exists():
    # 用临时文件传，不用 stdin/stdout 管道：218KB 走管道会让父子进程双双卡死
    # （实测两个进程 0% CPU 挂十几分钟）。文件方式还能在中途直接查看内容。
    with tempfile.TemporaryDirectory() as td:
        fin = Path(td) / "in.html"
        fout = Path(td) / "out.html"
        fin.write_text(out, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(D / "mindmap-inject-i18n.py"), "--in", str(fin), "--out", str(fout)],
            cwd=str(D), capture_output=True, text=True, encoding="utf-8")
        got = fout.read_text(encoding="utf-8") if fout.exists() else ""
    # 只有「退出码 0 + 输出非空 + 输出确实变长了 + 含注入标记」才采用，
    # 否则保留未注入的原样内容 —— 注入失败绝不能把页面写坏或写空。
    if r.returncode == 0 and "btnLang" in got and len(got) > len(out):
        out = got
        report_ui.append("注入双语支持")
        for l in [x for x in (r.stderr or "").splitlines() if x.strip()][-3:]:
            print("    " + l)
    else:
        report_ui.append("⚠ 双语注入失败，已保留中文版（未覆盖）")
        print(f"    ⚠ 注入未采用：rc={r.returncode} 输出 {len(got)} 字符（原 {len(out)}）")
        for l in [x for x in (r.stderr or "").splitlines() if x.strip()][-4:]:
            print("      " + l)
else:
    report_ui.append("⚠ 未找到翻译文件，跳过双语注入（仅中文）")

# ── 7a. 数据更正：ELD 权重写错了 ─────────────────────────────────
# 导图源里两处说 ELD「校本 50% + 外部笔试 50%」，但学校官方
# 《004_Assessment Outline_May 2026》写得很清楚：
#   Task 1 书面 10 / Task 2A 探究 5 / Task 3 COAT 10 / Task 4 阅读 7 /
#   Task 5 阅读 8 / Task 6 书面 10 / Task 7 口语 10 / Task 2B 探究 10 / Task 8 期末 30
#   合计 100 —— 即校本 70% + 外部笔试 30%，不是 50/50。
# 其余四科的导图权重与官方大纲逐条一致（MAM 40/40/20、HBY、PHY、CSC 全部核对过），
# 只有 ELD 这一处错。英文侧同步改在 _i18n/mindmap-i18n.json。
ELD_WEIGHT_FIXES = [
    ("ELD 科目说明里的外部笔试占比",
     "另含 WACE 毕业必需的 OLNA 读写与算术测试。外部笔试占 50%。",
     "另含 WACE 毕业必需的 OLNA 读写与算术测试。外部笔试（Task 8）占 30%，校本 8 项任务合计 70%。"),
    ("ELD 考核任务节点的权重",
     "校本 8 项任务共 100 分（占总成绩 50%）+ WACE 外部笔试 50%",
     "校本 8 项任务合计 70% + WACE 外部笔试（Task 8）30%（依官方 Assessment Outline）"),
]
for label, old, new in ELD_WEIGHT_FIXES:
    if old in out:
        out = out.replace(old, new, 1)
        report_ui.append("更正：" + label)
    else:
        report_ui.append("⚠ ELD 权重锚点未命中：" + label)


# ⚠ 顺序：这一段必须在 7c 之前 —— 7c 拼 var TIMELINE_EN 时要用
# mm_timeline_en。放晚了就是 NameError（刚踩过）。
# ── 7d. 时间线面板的英文（走查报的：整个面板硬编码中文，EN 下切不过来）──
# 数据在 _sp/timeline-en.json，与源 TIMELINE 同序同长。
# **接进来之前已做与中文侧相同的清洗** —— 源里那条含 Sunway 大学 / JC2 /
# 一楼 / 点名，中文侧被剥掉了，英文侧不剥就等于把删过的信息放回去。
_TL_EN = D / "_sp" / "timeline-en.json"
mm_timeline_en = []
if _TL_EN.exists():
    try:
        mm_timeline_en = json.loads(_TL_EN.read_text(encoding="utf-8"))
        report_ui.append(f"读入 timeline-en.json（{len(mm_timeline_en)} 条）")
    except Exception as _e:
        report_ui.append(f"⚠ timeline-en.json 解析失败：{_e}")
else:
    report_ui.append("⚠ 缺 timeline-en.json，时间线面板英文不可用")



# ── 7c. 注入子代理写的节点说明 ────────────────────────────────────
# 语料里挖出来的说明放在 _sp/notes-<科目>.json，键是节点路径。
#
# 两条注意（都是实际踩到的）：
#   1. 子代理写的键**不含根节点前缀**。真实路径是「AUSMAT May 2026 学习资料/…」，
#      它们从科目节点开始写。所以要统一补上根名前缀 —— 不补则 0 命中。
#   2. 不改 DATA 字面量（那是 150KB 的 JS，字符串手术风险高），改为在 DATA 之后
#      注入一段运行时 patch 挂到节点上。
SUBI = ["MAM", "PHY", "HBY", "ELD", "CSC"]

mm_notes = {}
for _s in SUBI:
    _f = D / "_sp" / f"notes-{_s}.json"
    if not _f.exists():
        report_ui.append(f"⚠ 缺 notes-{_s}.json（该科说明未注入）")
        continue
    try:
        _d = json.loads(_f.read_text(encoding="utf-8"))
    except Exception as _e:
        report_ui.append(f"⚠ notes-{_s}.json 解析失败：{_e}")
        continue
    for _k, _v in _d.items():
        if not (isinstance(_v, str) and _v.strip()):
            continue
        _k = _k.strip()
        for _a, _b in NAME_FIXES:
            _k = _k.replace(_a, _b)
        # 有的子代理已经带了根前缀，有的没有 —— 不判断就会拼成
        # 「AUSMAT…/AUSMAT…/ELD 英语/…」而全部落空。
        if not _k.startswith(ROOT_NAME + "/"):
            _k = f"{ROOT_NAME}/{_k}"
        mm_notes[_k] = _v.strip()
    report_ui.append(f"读入 notes-{_s}.json（{len(_d)} 条）")

if mm_notes:
    # 只保留真能挂上的键，并算出覆盖率 —— 挂不上的静默丢弃会让「补了 500 条」
    # 变成一句空话，必须报出真实数字。
    _all_paths = set(re.findall(r'name:\s*"((?:[^"\\]|\\.)*)"', out))
    _tl_js = ("\n// ==== 时间线面板的英文（构建时注入，已做与中文侧相同的清洗）====\n"
              "var TIMELINE_EN = "
              + json.dumps(mm_timeline_en, ensure_ascii=False) + ";\n")
    _js = _tl_js + ("\n// ==== 节点说明（由构建脚本从语料提炼后注入）====\n"
           "var MM_NOTES = " + json.dumps(mm_notes, ensure_ascii=False) + ";\n"
           "(function(){\n"
           "  var hit = 0, miss = [];\n"
           "  (function w(n, p){\n"
           "    var q = p ? p + \"/\" + n.name : n.name;\n"
           "    if (MM_NOTES[q]){ if (!n.note) { n.note = MM_NOTES[q]; n._noteZh = true; } hit++; }\n"
           "    if (n.children) n.children.forEach(function(c){ w(c, q); });\n"
           "  })(DATA, \"\");\n"
           "  window.__MM_NOTES_STAT = { hit: hit, total: Object.keys(MM_NOTES).length };\n"
           "})();\n")
    _anchor = out.find("/* ============ 交互：平移与缩放 ============ */")
    if _anchor > 0:
        out = out[:_anchor] + _js + out[_anchor:]
        report_ui.append(f"注入节点说明 {len(mm_notes)} 条")
    else:
        report_ui.append("⚠ 未找到注入锚点，节点说明未注入")



# ── 7b. 导图自身的几处缺陷（高分学生走查发现的）────────────────────
JS_FIXES = [
    # 悬停预览在「面板在右侧」时很顺手，但面板移到画布下方之后，
    # 鼠标划过画布就会冲掉正在读的内容 —— 布局一变，同一个交互从便利变成打扰。
    # 去掉悬停绑定，只保留点击；悬停仍有 CSS 的 .node-g:hover 高亮反馈。
    ("去掉悬停覆盖详情栏",
     'g.addEventListener("mouseenter", function(){ showDetail(n); });',
     '// 悬停不再覆盖详情栏（面板在画布下方，划过就冲掉正在读的内容）。\n'
     '    // 悬停仍有 CSS 的 .node-g:hover 高亮，点节点才更新详情。'),

    # 详情栏已移到画布下方，但提示条与根节点说明还写「右侧」——
    # 「右侧」是上一版全屏布局的遗留（低分学生走查逐条比对才发现）。
    ("提示条里的「右侧」改为「下方」",
     "滚轮缩放 · 拖拽平移 · 点击节点展开/收起 · 点击右侧科目名展开整科",
     "滚轮缩放 · 拖拽平移 · 点击节点展开/收起 · 点击下方科目名展开整科"),

    ("根节点说明里的「右侧面板」改为「下方详情栏」",
     "点击节点可展开/收起，右侧面板显示该知识点的说明。",
     "点击节点可展开/收起，下方详情栏显示该知识点的说明。"),

    ("代码注释里的「右侧详情面板」",
     "/* ============ 右侧详情面板 ============ */",
     "/* ============ 详情面板（在画布下方）============ */"),

    # 时间线副标题里的校内渠道（9/20 Teams 通知、9/21 说明会）已经由
    # 「时间线面板跟随语言」那条整体替换掉了 —— 新 buildTimeline 里的副标题
    # 就是清洗后的版本。所以这里不再单列补丁：留着它会先改文本，
    # 让后一条的锚点对不上（实际踩到过）。


    # ── 导图可用性四坑（三位走查都提到，高分与低分各报了其中两处）──

    # 坑 1：节点名被静默截断。wrapText 结尾直接 slice(0,3)，
    # 多出来的字**不留痕迹**，约 53 个节点名看不全，最长的一个被砍掉一半。
    # 截断本身可以接受（盒子宽度有限），但必须让人知道被截了。
    ("截断的节点名补省略号",
     "  if (cur.trim()) lines.push(cur.trim());\n  return lines.slice(0, 3);",
     "  if (cur.trim()) lines.push(cur.trim());\n"
     "  // 超出 3 行必须留痕：原来是静默丢弃，学生以为节点名就那么长。\n"
     "  if (lines.length <= 3) return lines;\n"
     "  const kept = lines.slice(0, 3);\n"
     "  kept[2] = kept[2].replace(/[\\s、,，]+$/, \"\") + \"…\";\n"
     "  return kept;"),

    # 坑 2：默认只展开根节点 —— 529 个节点里只露 6 个，要看单元层得点 5 次。
    # 默认开到第 2 层（科目 → 单元，59 个节点），一进来就能看到整门课的结构。
    ("默认展开到单元层",
     "  normalize(DATA, 0, \"#2f6fed\");\n  DATA._open = true;",
     "  normalize(DATA, 0, \"#2f6fed\");\n"
     "  // 默认开到第 2 层（科目 → 单元）。原来只开根节点，一进来只看到 6 个节点，\n"
     "  // 要连着点 5 次才见到单元，低分学生走查说「不知道从哪看起」。\n"
     "  (function openTo(n, d){\n"
     "    n._open = d < 2;\n"
     "    if (n.children) n.children.forEach(function(c){ openTo(c, d + 1); });\n"
     "  })(DATA, 0);"),

    # 坑 3：适应窗口的下限。fit() 原来最大只缩到 floorK（多数调用传 0.5），
    # 而 529 个节点全展开约 1.8 万 px，塞进 600px 高的画布后字号只剩几像素，
    # 「适应窗口」这个名字与结果不符。改成：缩到**可读下限**就停，
    # 放不下时居中到根节点并提示用户拖动，而不是把字缩到看不见。
    ("适应窗口缩到可读下限即停",
     "  const k = Math.min((rect.width - pad*2)/b.width, (rect.height - pad*2)/b.height, 1.15);\n"
     "  view.k = Math.max(k, floorK || 0.1);\n"
     "  view.x = pad;\n"
     "  view.y = Math.max(20, (rect.height - b.height*view.k)/2);\n"
     "  applyTransform();",
     "  const k = Math.min((rect.width - pad*2)/b.width, (rect.height - pad*2)/b.height, 1.15);\n"
     "  const floor = floorK || MIN_READABLE_K;\n"
     "  view.k = Math.max(k, floor);\n"
     "  // 缩到下限仍放不下：不要把字继续缩小（那样等于看不见），\n"
     "  // 改为横向居中、纵向回到顶部，并提示可以拖动。\n"
     "  const overflow = k < floor - 1e-6;\n"
     "  view.x = pad;\n"
     "  view.y = overflow ? pad\n"
     "                    : Math.max(20, (rect.height - b.height*view.k)/2);\n"
     "  applyTransform();\n"
     "  const hint = document.getElementById(\"fitHint\");\n"
     "  if (hint) hint.style.display = overflow ? \"block\" : \"none\";"),

    # 可读下限常量。字号 12.5px，k=0.3 时约 3.8px —— 已经是能认出轮廓的极限。
    # 可读下限。字号 12.5px：
    #   0.3 → 3.75px，只是一团灰（第一版取的就是 0.3，注释却写着「低于这个值
    #         就只是一团灰」—— 自相矛盾，低分学生走查实测点出）
    #   0.45 → 5.6px，还能看出结构
    #   0.6  → 7.5px，中文勉强可读
    # 取 0.45：既不假装能读，也不至于完全看不清。
    ("加入可读下限常量",
     "let UID = 0;\nfunction normalize(n, d, color){",
     "// 画布最小缩放。低于这个值文字就只是一团灰，不如让用户自己拖。\n"
     "// 0.45 × 12.5px ≈ 5.6px —— 能看出结构，读字要靠放大。\n"
     "const MIN_READABLE_K = 0.45;\n"
     "let UID = 0;\nfunction normalize(n, d, color){"),

    # 初始视图改为「按可读比例显示顶部」，不再强行把整棵树塞进画布。
    # 59 行节点要塞进约 500px 高的画布，字只能剩不到 4px —— 几何上无解，
    # 强行「适应」的代价是整棵树变成一团灰。改成可读比例 + 拖动查看，
    # 「适应窗口」按钮仍保留强行适配的能力（缩到下限并提示）。
    #
    # 锚点必须用 buildLegend 那一行：上面的「默认展开到单元层」补丁已经把
    # DATA._open = true; 换成了 openTo 循环，用旧写法匹配不到（顺序坑，踩过多次）。
    ("初始视图按可读比例显示",
     "  buildLegend(); buildTimeline(); render(); fit(0.5);",
     "  buildLegend(); buildTimeline(); render();\n"
     "  // 可读比例，从根节点往下看；拖动查看其余。\n"
     "  initialView();"),

    # 窗口缩放时不再强行重新适配 —— 那会把用户当前的缩放级别冲掉。
    # 只重新应用一次变换，保持他正在看的地方。
    ("窗口缩放不再冲掉缩放级别",
     "_rzT = setTimeout(function(){ fit(0.5); }, 150);",
     "_rzT = setTimeout(function(){ applyTransform(); }, 150);"),

    # 打印：把「当前展开的树」导成缩进大纲再打印。
    #
    # 第一版只写了 `#canvasWrap svg { height: 70vh }`，注释还自称支持打印 ——
    # 实际毫无效果：SVG 没有 viewBox、transform 也没重置，打印出来只截当前视口。
    # 两位走查各自实测：全部展开后打印，470 个知识点名在 PDF 里命中 0 个。
    #
    # 把整棵树缩到一页宽同样没用：1156px 缩到 180mm，12.5px 的字只剩 1.9px。
    # 所以改成**文本大纲**（缩进反映层级、节点带说明），既能读又能自然分页。
    ("打印改为输出文本大纲",
     "  window.addEventListener(\"resize\", function(){",
     "  // 打印前把当前展开的树导成缩进大纲 —— SVG 缩放打印不可读（见构建脚本注释）\n"
     "  function countNodes(){ var n = 0;\n    (function w(x){ if (x._visible) n++; if (x.children) x.children.forEach(w); })(DATA);\n    return n; }\n  function buildPrintOutline(){\n"
     "    const box = document.getElementById(\"printOutline\");\n"
     "    if (!box) return;\n"
     "    const out = [];\n"
     "    (function walk(n, d){\n"
     "      if (!n._visible) return;\n"
     "      const pad = \"  \".repeat(d);\n"
     "      const bullet = (n.children && n.children.length) ? \"\" : \"· \";\n"
     "      out.push(\"<div class=\\\"po-l po-d\" + Math.min(d, 4) + \"\\\">\" + pad\n"
     "        + bullet + esc(n.name) + \"</div>\");\n"
     "      if (n.note) out.push(\"<div class=\\\"po-n po-d\" + Math.min(d, 4) + \"\\\">\"\n"
     "        + pad + esc(n.note) + \"</div>\");\n"
     "      if (n._open && n.children) n.children.forEach(function(c){ walk(c, d + 1); });\n"
     "    })(DATA, 0);\n"
     "    box.innerHTML = \"<div class=\\\"po-h1\\\">\" + esc(DATA.name) + \"</div>\"\n"
     "      + \"<p class=\\\"po-meta\\\">\" + (LANG === \"en\"\n"
     "          ? (\"Expanded topics only (\" + countNodes() + \" nodes). \"\n"
     "             + \"To print the whole map, press Expand all first.\")\n"
     "          : (\"只含当前展开的部分（\" + countNodes() + \" 个节点）。\"\n"
     "             + \"想打印全部，请先点「全部展开」。\")) + \"</p>\" + out.join(\"\");\n"
     "  }\n"
     "  window.addEventListener(\"beforeprint\", buildPrintOutline);\n"
     "  if (window.matchMedia) {\n"
     "    try { window.matchMedia(\"print\").addEventListener(\"change\", function(e){\n"
     "      if (e.matches) buildPrintOutline(); }); } catch (err) {}\n"
     "  }\n\n"
     "  window.addEventListener(\"resize\", function(){"),

    # 打印大纲要转义节点名与说明（里面有 < > & 与公式符号）。原文没有这个函数。
    ("加入打印大纲的转义函数",
     "let UID = 0;\nfunction normalize(n, d, color){",
     "function esc(s){\n"
     "  return String(s).replace(/&/g, \"&amp;\").replace(/</g, \"&lt;\")\n"
     "                  .replace(/>/g, \"&gt;\").replace(/\"/g, \"&quot;\");\n"
     "}\n"
     "let UID = 0;\nfunction normalize(n, d, color){"),

    # ── 外壳里三处漏翻译的元素 ──────────────────────────────────────
    # applyLang 只处理带 data-i18n 的元素；这三处没标，所以英文模式下一直是中文。
    # 是修好导航「术语表」之后用浏览器逐页扫出来的同类问题。
    # 翻译在 mindmap-inject-i18n.py 的 UI 里，这里只把标记加上。
    # 品牌名与页脚**不需要在这里打标** —— 实测它们本来就有 data-i18n，
    # 加这两条只会报「锚点未命中」并中断构建。真正需要的是下面这条图例提示。
    # （验证方式：把三条一起删掉重建，品牌名/页脚的 data-i18n 仍在，图例的没了。）
    ("图例提示标注可翻译",
     '<div class="tip">滚轮缩放 · 拖拽平移 · 点击节点展开/收起 · 点击下方科目名展开整科</div>',
     '<div class="tip" data-i18n="滚轮缩放 · 拖拽平移 · 点击节点展开/收起 · 点击下方科目名展开整科">'
     '滚轮缩放 · 拖拽平移 · 点击节点展开/收起 · 点击下方科目名展开整科</div>'),

    # ── 高分/游客走查报的三条（导图侧）──────────────────────────────

    # 标签页标题的补丁在 mindmap-inject-i18n.py 里 —— applyLang 是那边生成的，
    # 在这里打补丁会因「UI_EN 还没注入」而必然落空。
    # 触屏支持。原来只绑 mousedown/mousemove/mouseup/wheel，
    # 手机上既拖不动也缩不了，而画布左下还写着「滚轮缩放 · 拖拽平移」。
    ("加上触屏拖动与双指缩放",
     "  window.addEventListener(\"resize\", function(){",
     "  // ── 触屏：单指拖动、双指捏合缩放 ──────────────────────────\n"
     "  // 原来只有鼠标事件，手机上是死画布（高分与游客走查都提到）。\n"
     "  (function(){\n"
     "    let drag = null, pinch = null;\n"
     "    const svg = document.getElementById(\"svg\");\n"
     "    if (!svg) return;\n"
     "    const dist = function(t){ const dx = t[0].clientX - t[1].clientX,\n"
     "                              dy = t[0].clientY - t[1].clientY;\n"
     "                           return Math.hypot(dx, dy); };\n"
     "    svg.addEventListener(\"touchstart\", function(e){\n"
     "      if (e.touches.length === 1) {\n"
     "        drag = { x: e.touches[0].clientX - view.x, y: e.touches[0].clientY - view.y };\n"
     "        pinch = null;\n"
     "      } else if (e.touches.length === 2) {\n"
     "        pinch = { d: dist(e.touches), k: view.k }; drag = null;\n"
     "      }\n"
     "    }, { passive: true });\n"
     "    svg.addEventListener(\"touchmove\", function(e){\n"
     "      if (e.touches.length === 1 && drag) {\n"
     "        view.x = e.touches[0].clientX - drag.x;\n"
     "        view.y = e.touches[0].clientY - drag.y;\n"
     "        applyTransform();\n"
     "        e.preventDefault();\n"
     "      } else if (e.touches.length === 2 && pinch) {\n"
     "        const k = Math.max(MIN_READABLE_K,\n"
     "                           Math.min(1.15, pinch.k * (dist(e.touches) / pinch.d)));\n"
     "        const r = svg.getBoundingClientRect();\n"
     "        const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2 - r.left;\n"
     "        const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2 - r.top;\n"
     "        const rk = k / view.k;\n"
     "        view.x = cx - (cx - view.x) * rk;\n"
     "        view.y = cy - (cy - view.y) * rk;\n"
     "        view.k = k;\n"
     "        applyTransform();\n"
     "        e.preventDefault();\n"
     "      }\n"
     "    }, { passive: false });\n"
     "    svg.addEventListener(\"touchend\", function(){ drag = null; pinch = null; });\n"
     "    // 触屏上「滚轮缩放」这句话不成立，换成「双指缩放」。\n"
     "    if (\"ontouchstart\" in window) {\n"
     "      const tip = document.querySelector(\".tip\");\n"
     "      if (tip) tip.setAttribute(\"data-i18n\",\n"
     "        \"双指缩放 · 拖动平移 · 点击节点展开/收起 · 点击下方科目名展开整科\");\n"
     "    }\n"
     "  })();\n\n"
     "  window.addEventListener(\"resize\", function(){"),

    # ── 时间线面板的语言支持 ────────────────────────────────────────
    # 面板的表头与 35 行全是硬编码中文，applyLang 也从不重调它 ——
    # EN 模式下按钮变成 "Exam timeline"，点开却是一整张中文表。
    #
    # ⚠ 锚点必须是**整个原函数**。前两版只拿 `function buildTimeline(){`
    # 当锚点，新函数插进去之后原函数体还留在后面，拼出重复代码 →
    # 整个 <script> 语法错误、导图全挂。这个坑踩了两次。
    # 补丁写完必须 node --check 验一遍产出的 JS。
    ("时间线面板跟随语言",
     r'''function buildTimeline(){
  const box = document.getElementById("timeline");
  let html = '<h2>AUSMAT May 2026 · 五科考核日程</h2>' +
    '<p class="sub">整理自五科 OneNote 笔记本内的官方 Assessment Outline / Course Outline、9/20 Teams 通知及 9/21 说明会发放的全院官方考试时间表。<br>10/27–11/13 考试季每科两份卷：上午 ACCT（60 分钟）+ 下午 EE（95 分钟）。</p>' +
    '<table><thead><tr><th>日期</th><th>科目</th><th>考核内容与权重</th></tr></thead><tbody>';
  TIMELINE.forEach(function(r){
    let color = "#8896a8";
    DATA.children.forEach(function(c){ if (c.name.indexOf(r.subject) >= 0) color = c._color; });
    html += '<tr><td class="date">' + r.date + '</td><td><span class="tag" style="background:' + color + '">' + r.subject + '</span></td><td>' + r.detail + '</td></tr>';
  });
  html += "</tbody></table>";
  box.innerHTML = html;
}''',
     r'''function buildTimeline(){
  const box = document.getElementById("timeline");
  // 面板原来整块硬编码中文，applyLang 也从不重调它 —— EN 模式下按钮变成
  // "Exam timeline"，点开却是一整张中文表（三位走查都报了这条）。
  // 数据用构建时注入的 TIMELINE_EN（已做与中文侧相同的清洗）。
  const EN = (typeof LANG !== "undefined" && LANG === "en");
  const rows = (EN && typeof TIMELINE_EN !== "undefined" && TIMELINE_EN.length)
    ? TIMELINE_EN : TIMELINE;
  const head = EN
    ? '<h2>AUSMAT May 2026 · assessment schedule</h2>'
      + '<p class="sub">Compiled from the five course outlines and the exam schedule '
      + 'published by the school.<br>In the 10/27–11/13 examination season each subject '
      + 'sits two papers: ACCT (60 min) in the morning, EE (95 min) in the afternoon.</p>'
      + '<table><thead><tr><th>Date</th><th>Subject</th><th>Assessment and weighting</th>'
      + '</tr></thead><tbody>'
    : '<h2>AUSMAT May 2026 · 五科考核日程</h2>'
      + '<p class="sub">整理自五科课程大纲与校内公布的考试安排。<br>'
      + '10/27–11/13 考试季每科两份卷：上午 ACCT（60 分钟）+ 下午 EE（95 分钟）。</p>'
      + '<table><thead><tr><th>日期</th><th>科目</th><th>考核内容与权重</th></tr></thead><tbody>';
  let html = head;
  rows.forEach(function(r){
    let color = "#8896a8";
    DATA.children.forEach(function(c){ if (c.name.indexOf(r.subject) >= 0) color = c._color; });
    html += '<tr><td class="date">' + r.date + '</td>'
          + '<td><span class="tag" style="background:' + color + '">' + r.subject + '</span></td>'
          + '<td>' + r.detail + '</td></tr>';
  });
  html += "</tbody></table>";
  box.innerHTML = html;
}'''),

    # 补上极限的趋近条件。在讲极限的地方漏掉 lim 的下标，
    # 正是基础薄弱的人会被带偏的地方（低分学生走查提出）。
    ("补上极限的趋近条件",
     "lim(aʰ−1)/h",
     "lim(h→0)(aʰ−1)/h"),

    # 地球半径。导图写 6.38×10⁶ m，但学校发的公式与数据册、以及 2014–2023 真题的
    # 解答里一致用 6.37×10⁶ m（地球实际半径 6.371×10⁶ m，官方取 6.37）。
    # 用错值代入万有引力与卫星题会系统性偏一点，属于会真扣分的错。
    ("更正地球半径的取值",
     "R_E = 6.38×10⁶ m",
     "R_E = 6.37×10⁶ m"),

    # 节点名与它自己的说明打架：名字写 ε_avg = −4BANf，说明写 ε_avg=4BANf。
    # 半周期平均值量值是 2ε_max/π = 4BANf；负号是方向约定，由楞次定律单独判断。
    # 注意这条**只改说明以外的地方**——DATA 与词典正文都改，说明键由 NAME_FIXES 管。
    ("平均电动势去掉多余的负号（量值）",
     "ε_avg = −4BANf",
     "ε_avg = 4BANf"),

    # 时间线按钮有「打开/关闭」两种文案，原来写死中文。
    # 而且 applyLang 的 data-i18n 循环只写回基础文案，会把已打开的状态标签覆盖掉。
    ("时间线按钮文案跟随语言",
     'e.target.textContent = box.classList.contains("show") ? "返回导图" : "考试日程";',
     'e.target.textContent = box.classList.contains("show")\n'
     '      ? (LANG === "en" ? "Back to map" : "返回导图")\n'
     '      : (LANG === "en" ? "Exam timeline" : "考试时间线");'),

    ("根节点切回英文时翻译失效",
     'const p = path ? path + "/" + (n._zh ? n._zh.name : n.name) : n.name;',
     # 非根节点用 _zh.name（保存的中文原名）查表，根节点却直接用 n.name——
     # 第一次切换后 n.name 变成英文，再也查不到表，根节点就卡在英文或中文。
     'const p = path ? path + "/" + (n._zh ? n._zh.name : n.name) : (n._zh ? n._zh.name : n.name);'),

    # 深层节点恒定纯白底。原本无所谓，但站点其他页都跟随系统深色模式，
    # 深色下这些白方块很刺眼。改成读站点的 --bg / --text。
    ("深层节点底色改为跟随主题",
     'else { r.setAttribute("fill", "#ffffff"); r.setAttribute("stroke", n._color); }',
     'else { r.setAttribute("fill", themeVar("--bg", "#ffffff")); r.setAttribute("stroke", n._color); }'),

    ("深层节点文字色改为跟随主题",
     't.setAttribute("fill", dark ? "#ffffff" : "#1f2733");',
     't.setAttribute("fill", dark ? "#ffffff" : themeVar("--text", "#1f2733"));'),

    # 搜索无结果时什么都不发生，用户不知道是没匹配还是坏了。给输入框加个红边。
    ("搜索无结果时给出提示",
     'if (!matched.length) return;',
     'if (!matched.length) { document.getElementById("search").classList.add("mm-nohit"); return; }\n'
     '  document.getElementById("search").classList.remove("mm-nohit");'),

    # src 字段在清洗阶段已全部删除（528 个节点里带 src 的是 0 个），
    # 这个分支永远不会执行，而且里面的路径早就失效了。删掉。
    ("删除永不执行的 src 分支",
     '  if (n.src){ sideSrc.style.display = "block"; sideSrc.textContent = "📁 桌面资料位置：Ausmart\\\\" + n.src; }\n'
     '  else sideSrc.style.display = "none";',
     '  sideSrc.style.display = "none";   // src 字段已在清洗阶段删除，这里不再有可显示的内容'),
]

for label, old, new in JS_FIXES:
    if old in out:
        out = out.replace(old, new, 1)
        report_ui.append("修：" + label)
    else:
        report_ui.append("⚠ 锚点未命中：" + label)

# themeVar 辅助函数 + 系统主题变化时重绘
THEME_HELPER = ('function themeVar(name, fallback){\n'
                '  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();\n'
                '  return v || fallback;\n'
                '}\n'
                'function render(){')
if "function render(){" in out:
    out = out.replace("function render(){", THEME_HELPER, 1)
    report_ui.append("加入 themeVar（节点配色读站点变量）")
else:
    report_ui.append("⚠ 未找到 render 函数头，themeVar 未加入")

# 系统切换深色/浅色时重绘一次，否则节点底色要刷新页面才更新
THEME_WATCH = ('\n// 系统主题变化时重绘：节点底色读的是 CSS 变量，不会自动跟着变。\n'
               'try {\n'
               '  const mq = window.matchMedia("(prefers-color-scheme: dark)");\n'
               '  (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))\n'
               '    (function(){ render(); });\n'
               '} catch(e) {}\n')
if "\n// 启动完成后按记忆的语言再应用一次。" in out:
    out = out.replace("\n// 启动完成后按记忆的语言再应用一次。",
                      THEME_WATCH + "\n// 启动完成后按记忆的语言再应用一次。", 1)
    report_ui.append("跟随系统主题变化重绘")
else:
    report_ui.append("⚠ 未找到启动注释锚点，主题监听未加入")

# CSS 里补两处：搜索无结果的样式，以及更正我自己那条夸大的注释
CSS_FIX_OLD = "/* 知识导图 · 全部配色取自站点 assets/style.css 的变量，深色模式自动生效。\n   这里只放导图独有的东西，通用排版（页头/页脚/标题/表格）交给站点样式表。 */"
CSS_FIX_NEW = ("/* 知识导图 · 外壳配色取自站点 assets/style.css 的变量，深色模式自动生效。\n"
               "   注意：**节点方块的颜色不走这里** —— 它们由脚本内联设置，深层节点读的是\n"
               "   themeVar(\"--bg\") / themeVar(\"--text\")，同样跟随主题。\n"
               "   这里只放导图独有的东西，通用排版（页头/页脚/标题/表格）交给站点样式表。 */")
if CSS_FIX_OLD in out:
    out = out.replace(CSS_FIX_OLD, CSS_FIX_NEW, 1)
    report_ui.append("更正 CSS 顶部那条夸大的注释")

if ".mm-toolbar input:focus" in out:
    out = out.replace(
        ".mm-toolbar input:focus",
        ".mm-toolbar input.mm-nohit { border-color: var(--warn); background: var(--warn-bg); }\n"
        ".mm-toolbar input:focus", 1)
    report_ui.append("加入搜索无结果时的输入框样式")


# ── 8. 注入之后再修 applyLang ────────────────────────────────────# 这一步必须在第 7 步之后：applyLang 整个函数都是注入器加的，之前文件里没有它。
if OLD_RESET in out:
    out = out.replace(OLD_RESET, NEW_RESET, 1)
    report_ui.append("切语言时保留已选节点的详情（原来会被重置成初始提示）")
else:
    report_ui.append("⚠ 未找到详情栏重置锚点（applyLang 未注入？）")

# applyLang 的 data-i18n 循环只写回「基础文案」，会把时间线按钮已经变成
# 「返回导图」的状态标签覆盖掉。循环之后按当前状态重新同步一次。
TL_SYNC_ANCHOR = '    document.querySelectorAll("[data-href-en]").forEach(function(a){'
TL_SYNC = ('    // 时间线按钮有两种状态文案，上面那个 data-i18n 循环只会写回基础文案，\n'
           '    // 会把「已打开」的标签覆盖掉。按当前状态重新同步。\n'
           '    (function(){\n'
           '      const b = document.getElementById("btnTimeline");\n'
           '      const box = document.getElementById("timeline");\n'
           '      if (b && box) b.textContent = box.classList.contains("show")\n'
           '        ? (lang === "en" ? "Back to map" : "返回导图")\n'
           '        : (lang === "en" ? "Exam timeline" : "考试时间线");\n'
           '    })();\n')
if TL_SYNC_ANCHOR in out:
    out = out.replace(TL_SYNC_ANCHOR, TL_SYNC + TL_SYNC_ANCHOR, 1)
    report_ui.append("切语言后按当前状态同步时间线按钮文案")
else:
    report_ui.append("⚠ 未找到导航换目标锚点，时间线按钮同步未加入")

# ── 9. 英文词典外置：中文读者不该为 360KB 的翻译付费 ──────────────
# 导图页 686KB，其中 359KB 是 I18N（每个节点的英文名 + 英文说明），而中文读者
# 一次都用不到。实测中文首屏 252KB(gzip)，这份词典约占 100KB。
# 改成：页面里只留 `var I18N = null`，点「EN」时才取同目录的 mindmap-i18n.js；
# 取不到就停在中文并提示一句 —— 绝不能让 swapLang 读到 null 抛错。
I18N_OUT = OUT.parent / "mindmap-i18n.js"
BSLASH = chr(92)      # 反斜杠。写成字符码，免得这一行本身被转义搞乱


def _balanced_end(text: str, open_idx: int) -> int:
    """open_idx 指向 '{'，返回与之配对的 '}' 之后一位；认得字符串与转义。"""
    depth, i, in_str, esc = 0, open_idx, False, False
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == BSLASH:
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    raise ValueError("I18N 花括号不配对")


if "var I18N = {" in out:
    _i0 = out.index("var I18N = {")
    _b0 = out.index("{", _i0)
    _b1 = _balanced_end(out, _b0)
    _obj = out[_b0:_b1]
    if len(_obj.encode("utf-8")) < 20000:
        report_ui.append(f"⚠ I18N 只 {len(_obj)} 字节，疑似不完整，未外置")
    else:
        I18N_OUT.write_text(
            "/* 导图英文词典（构建产物，由 clean-mindmap.py 从页面里外置而来）。\n"
            "   页面只在切到英文时才加载它：中文读者不必为这 ~360KB 付费。 */\n"
            "var I18N = " + _obj + ";\n", encoding="utf-8")
        _tail = _b1 + 1 if out[_b1:_b1 + 1] == ";" else _b1
        out = out[:_i0] + "var I18N = null;" + out[_tail:]
        report_ui.append("英文词典外置 → notes/mindmap-i18n.js"
                         f"（{len(_obj.encode('utf-8')) // 1024}KB）")
else:
    report_ui.append("⚠ 未找到 I18N 字面量，英文词典未外置")

I18N_LOADER = """// 英文词典按需加载：它在同目录的 mindmap-i18n.js 里，中文读者不下载它。
var I18N_WAIT = [];
function i18nFailed(){
  var b = document.getElementById("btnLang");
  if (b) b.textContent = "EN";
  var sb = document.getElementById("sideBody");
  if (sb) sb.textContent = "英文版加载失败，请检查网络后重试 / English version failed to load.";
  // 词典没到就别留一张空画布：中文照常可看（首屏本来就没画）。
  try { render(); fit(0.5); } catch(e) {}
}
function loadI18N(cb){
  if (I18N) { cb(); return; }
  I18N_WAIT.push(cb);
  if (I18N_WAIT.length > 1) return;          // 已经有人在取了
  var settled = false;
  var timer = setTimeout(function(){         // 网络卡住时的兜底，别让画布一直空着
    if (settled) return;
    settled = true; I18N_WAIT = []; i18nFailed();
  }, 10000);
  var s = document.createElement("script");
  s.src = "mindmap-i18n.js";
  s.onload = function(){
    settled = true; clearTimeout(timer);
    var q = I18N_WAIT; I18N_WAIT = [];
    if (!I18N) { i18nFailed(); return; }
    q.forEach(function(f){ try { f(); } catch(e){} });
  };
  s.onerror = function(){
    settled = true; clearTimeout(timer);
    I18N_WAIT = []; i18nFailed();
  };
  document.head.appendChild(s);
}

// 切语言后把 ?lang= 同步到地址栏：刷新、收藏、后退都保持当前语言。
// file:// 下 history.replaceState 可能抛错，所以整段包在 try 里。
function setLangUrl(lang){
  try {
    var u = new URL(location.href);
    u.searchParams.set("lang", lang);
    history.replaceState(null, "", u);
  } catch(e) {}
}

"""
if "function swapLang(" in out and "function loadI18N(" not in out:
    out = out.replace("function swapLang(", I18N_LOADER + "function swapLang(", 1)
    report_ui.append("加入英文词典按需加载器")
else:
    report_ui.append("⚠ 未找到 swapLang 锚点，加载器未加入")

BTN_OLD = ('document.getElementById("btnLang").onclick = function()'
           '{ applyLang(LANG === "en" ? "zh" : "en", true); };')
BTN_NEW = ('document.getElementById("btnLang").onclick = function(){\n'
           '  if (LANG === "en"){ applyLang("zh", true); setLangUrl("zh"); return; }\n'
           '  loadI18N(function(){ applyLang("en", true); setLangUrl("en"); });\n'
           '};')
if BTN_OLD in out:
    out = out.replace(BTN_OLD, BTN_NEW, 1)
    report_ui.append("语言按钮改为「词典就绪后再切」")
else:
    report_ui.append("⚠ 未找到语言按钮锚点，按需加载不会生效")

BOOT_OLD = "if (LANG === 'en') applyLang('en', true);"
BOOT_NEW = "if (LANG === 'en') loadI18N(function(){ applyLang('en', true); });"
if BOOT_OLD in out:
    out = out.replace(BOOT_OLD, BOOT_NEW, 1)
    report_ui.append("记住的英文偏好改为加载后再应用")
else:
    report_ui.append("⚠ 未找到启动语言锚点（上次选过英文的访客会停在中文）")

# ── 10. 语言改由 URL 决定（?lang=en / ?lang=zh）──────────────────
# 导图只有一份文件，中英两棵目录树都指向它。以前只能从 localStorage 猜，于是
# 两个方向都会错（都实测到过）：
#   英文站点点「Mind Map」→ 落到中文；
#   在导图里切过英文、再回中文站点进来 → 落到英文。
# 现在链接显式带 ?lang=，页面优先用它；页内切换再把 URL 同步回去。
LANG_OLD = ('// 记住当前语言\n'
            'let LANG = "zh";\n'
            'try { const s = localStorage.getItem("mm-lang"); if (s) LANG = s; } catch(e) {}')
LANG_NEW = ('// 语言优先级：URL 的 ?lang= > 上次记住的 > 中文。\n'
            '// 导图只有一份文件，中英两棵目录树都指向它，只靠猜必定错一个方向。\n'
            'let LANG = "zh";\n'
            'try {\n'
            '  const _q = new URLSearchParams(location.search).get("lang");\n'
            '  if (_q === "en" || _q === "zh") {\n'
            '    LANG = _q;\n'
            '    localStorage.setItem("mm-lang", _q);\n'
            '  } else {\n'
            '    const s = localStorage.getItem("mm-lang");\n'
            '    if (s === "en" || s === "zh") LANG = s;\n'
            '  }\n'
            '} catch(e) {}')
if LANG_OLD in out:
    out = out.replace(LANG_OLD, LANG_NEW, 1)
    report_ui.append("语言改由 URL 的 ?lang= 决定")
else:
    report_ui.append("⚠ 未找到 LANG 初始化锚点，链接带语言不会生效")

# 页面标题也标注来源站点
out = out.replace("<title>AUSMAT 学习资料思维导图</title>",
                  "<title>知识导图 · AUSMAT 学习资料</title>")

# 页面标题也确认一下（不含个人信息即可）
print(f"\n总长度: {orig_len} -> {len(out)} 字符  (减少 {orig_len - len(out)})")
print("\n=== 清洗动作 ===")
for r in rep1 + rep2 + report_ui:
    print("  •", r)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(out, encoding="utf-8")
print(f"\n已写出: {OUT}")

# ── 校验 ──────────────────────────────────────────────────────
chk = OUT.read_text(encoding="utf-8")
print("\n=== 清洗后校验 ===")
for label, pat in (("姓名", r"WEN\s*CHENGZHI|Wenchengzhi"),
                   ("学校名", r"Sunway"),
                   ("学生标记", r"学生："),
                   ("src 字段", r"src:\s*\""),
                   ("本地路径", r"_Content Library|_Attachments|_Collaboration")):
    n = len(re.findall(pat, chk, re.I))
    print(f"  {label:<10} {n} 处  {'✓' if n == 0 else '✗ 仍有残留'}")

n_nodes = len(re.findall(r'name:\s*"', chk))
print(f"  知识节点数  {n_nodes}  (清洗前 529)")

