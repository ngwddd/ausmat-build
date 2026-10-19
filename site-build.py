"""生成双语学习站（面向公众的干净版本）。

本版修正三个问题：
  1. 隐私：不公开信息来源文件、不公开版本迭代记录、不出现任何内部路径
  2. 可用性：语言切换改成「普通链接指向另一语言版本」，不再依赖 JavaScript
     —— 之前用 JS 改 data-lang 再由 CSS 隐藏，禁用 JS 就完全无法切换
  3. 结构：每种语言生成一套独立页面（/ = 中文，/en/ = 英文），任何静态服务器都能服务

内容红线：只发布自己整理的事实与自己的讲解；不含学校/SCSA 材料与任何个人信息。
"""

import os
import datetime
import json
import re
import shutil
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

data = import_module("site-data")

OUT = Path(os.environ.get("AUSMAT_SITE")
           or (Path(__file__).resolve().parent / "my-site"))            # 站点输出目录


def _site_base() -> str:
    """站点在 GitHub Pages 上的路径前缀，形如 /ausmat-guide/。

    404 页必须用站点根绝对路径（Pages 会在任意深度返回它，相对路径会指错），
    所以得知道仓库名。以前这个值是手写死的，2026-09 仓库从 course-notes 改名成
    ausmat-guide 之后，404 页整页掉样式、链接全指错 —— 只能靠人记得来改。
    现在从 git remote 反推，改名不用改代码。
    """
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=str(OUT),
                             capture_output=True, text=True, encoding="utf-8",
                             timeout=10).stdout.strip()
    except Exception:
        url = ""
    m = re.search(r"/([^/]+?)(?:\.git)?/?$", url)
    return f"/{m.group(1)}/" if m else "/ausmat-guide/"


SITE_BASE = _site_base()

# 品牌名从 site-data.py 读。注意必须写成 data.XXX —— 文件后半段那个 BRAND
# 字典此时还没定义，直接写 NAME = BRAND 会 NameError（踩过一次）。
NAME = {"zh": data.BRAND_ZH, "en": data.BRAND_EN}

# ── 页面骨架（单语言，无内容依赖 JS）──────────────────────────────────────

SHELL = """<!doctype html>
<html lang="__HTMLANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<!-- hreflang 指的是目标页的语言，不是当前页的。
     原来这里用了当前页的语言去描述另一语言的地址，等于反着说。
     自指那一条（hreflang 指向本页）Google 只是建议、不是必须，就不加了 ——
     少一处会算错的地方。（注释里也不要写星号：它会被输出到每个页面上。） -->
<link rel="alternate" hreflang="__OTHERHREFLANG__" href="__OTHER__">
<link rel="stylesheet" href="__UP__assets/style.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <a class="brand" href="__BRAND_LINK__">__BRAND__</a>
    <nav>__NAV__</nav>
    <div class="lang-switch">
      __LANG_SWITCH__
    </div>
  </div>
</header>
<main><div class="wrap">
__BODY__
</div></main>
<footer class="site"><div class="wrap">__FOOTER__</div></footer>
</body>
</html>
"""

# 导航从 site-data.py 读，不再在这里定义 —— 导图页（clean-mindmap.py 生成）
# 也要用同一份，两处各写一份迟早会不一致。格式说明见 site-data.NAV 的注释。
NAV = data.NAV
BRAND = {"zh": data.BRAND_ZH, "en": data.BRAND_EN}
FOOT = {"zh": data.FOOTER_ZH, "en": data.FOOTER_EN}


# 页面在两套语言树中的实际路径
#   中文： index.html          notes/timetable.html   …
#   英文： en/index.html       en/notes/timetable.html …
# 关键：导航链接必须带上 notes/ 前缀——首页在根层，子页在 notes/ 层下。
# 原来这里还有一个 ROOT_PAGES 常量，列了 5 个根层页面（还漏了 glossary/papers），
# 但从定义到删除一次都没被读过 —— 留着只会让人以为它管着什么。2026-10 删除。

# 只生成一份的页面（不随语言切换）。知识导图是双语混排的交互应用，
# 中英两版没有意义，也会让那份 50KB 的文件重复两份。
ENGLISH_ONLY: set[str] = {"mindmap.html"}

# 只生成一份、且住在中文树 notes/ 下的页面。从别处指过去时，链接要多退一层
# 语言目录，否则 /en/ 下的页面会解析成 /en/notes/... 而 404。
#   导图       notes/mindmap.html
#   升学自检   notes/advising/{index,en}.html —— 它自己带语言文件，
#              所以不放进 ENGLISH_ONLY（那会让 out_path 误判），只在这里声明。
# 2026-10 补：升学自检此前漏了这一条，英文站的导航与首页卡片全部指向
# /en/notes/advising/en.html，点进去就是 404。
CROSS_TREE: set[str] = {"mindmap.html", "advising/index.html", "advising/en.html"}


def out_path(lang: str, name: str) -> str:
    """某页面在指定语言树中的站点相对路径（用于生成文件与计算链接）。"""
    if name in ENGLISH_ONLY:
        return f"notes/{name}"          # 只有中文树一份，两个语言都指向它
    en = lang == "en"
    if name == "index.html":
        return "en/index.html" if en else "index.html"
    return f"en/notes/{name}" if en else f"notes/{name}"


# 每页一句真正的 description。
# 原来调用方把 title 传了两次，于是 <meta name="description"> 就是 title 的复读
# （「首页 · 学习笔记」），分享出去没有任何摘要（游客走查提出）。
PAGE_DESCS = {
    "index.html": (
        "AUSMAT（西澳 WACE 课程）2026 年 5 月入学的学习笔记：五科考核日程与权重、"
        "知识点导图、术语表、升学自检。中英双语，可打印。",
        "Study notes for AUSMAT (WA WACE) starting May 2026: assessment schedule and "
        "weightings for five subjects, a topic mind map, a glossary and an ATAR self-check.",
    ),
    "timetable.html": (
        "AUSMAT 五科全年各场考核的日期、类型与权重，含每场的时间、时长与允许携带，附 WACE 外部考试标注与倒计时。",
        "Dates, types and weightings for every AUSMAT assessment, with the timing and "
        "duration of each one, WACE external examinations marked, and a countdown.",
    ),
    "timeline.html": (
        "AUSMAT 一学年的 37 周节奏：假期、三次密集考核期与期末冲刺，按周次列出每个阶段在学什么、考什么。",
        "The 37-week rhythm of the AUSMAT year: the breaks, three crunch periods and the "
        "run-in to finals, week by week, with what is taught and examined in each stretch.",
    ),
    "subjects.html": (
        "AUSMAT 五科（MAM / HBY / PHY / ELD / CSC）的考核构成与考试范围。",
        "Assessment structure and examination scope for the five AUSMAT subjects "
        "(MAM / HBY / PHY / ELD / CSC).",
    ),
    "papers.html": (
        "历年 WACE 真题从哪找：SCSA 官方页面与社区库各覆盖哪些年份，以及五科考官报告里反复点名的常见失分点。",
        "Where to find past WACE papers: which years the SCSA pages and the community vault "
        "cover, plus the mistakes the examiner reports keep flagging in each subject.",
    ),
    "glossary.html": (
        "AUSMAT 与 WACE 术语表：AT 课程、ATAR、TEA、TISC、五科缩写等。",
        "AUSMAT and WACE glossary: AT courses, ATAR, TEA, TISC and the five subject codes.",
    ),
    "about.html": (
        "这个站包含什么、不包含什么，内容从哪来、按什么原则取舍，以及为什么不收录学校发放的材料。",
        "What this site does and does not contain, where the content comes from, the rules "
        "used to choose it, and why school-issued material is left out.",
    ),
}


def build_page(lang: str, rel: str, title: str, desc: str, body_fn) -> str:
    """组装单语言页面。

    rel 是站点根相对路径，如 'notes/timetable.html'。
    body_fn(lang, link) 由本函数调用——因为只有这里知道当前页的深度，
    正文里的内部链接必须先经过 link() 才拿到正确的 ../ 前缀。
    """
    en = lang == "en"
    stem = Path(rel).stem
    fname = "index.html" if stem == "index" else f"{stem}.html"

    # 路径分三部分，弄混是本项目最容易出错的地方（已经错过四次）：
    #
    #   langdir    —— 语言目录："en" 或 ""（英文页的 URL 前缀）
    #   subdirs    —— 语言根以下的子目录，如 "notes" 或 ""
    #   up_lang    —— 从本页目录回到「本语言根」的 ../ 前缀
    #
    # 页面链接 = up_lang + (langdir + "/" if langdir else "") + inner
    # 静态资源 = up_lang + inner        （assets/vendor 在站点根，不在语言树里）
    #
    # 曾经用 d[len("en/"):] 去算子目录，但 d 是 "en" 而不是 "en/"，
    # 切片什么也没切掉，于是 en/index.html 生成出 en/en/index.html。
    d = str(Path(rel).parent).replace("\\", "/")     # "en"、"en/notes"、"notes"、""
    langdir = "en" if en else ""
    parts = [x for x in d.split("/") if x and x != "."]
    if langdir and parts and parts[0] == langdir:
        parts = parts[1:]
    subdirs = "/".join(parts)                        # "" 或 "notes"
    up_lang = "../" * (len(parts))                   # 回语言根

    # 静态资源在站点根，所以用「页面在站点里的总层数」推前缀。
    # 之前用「语言根深度 + 语言目录」拼，结果 en/notes/ 变成 ../../assets/（超出站点根），
    # 因为 parts 已经不含语言目录，等于把 en/ 那层算了两遍。
    #
    #   index.html        0 层 -> ""      notes/x.html       1 层 -> "../"
    #   en/index.html     1 层 -> "../"   en/notes/x.html    2 层 -> "../../"
    total_depth = len(parts) + (1 if langdir else 0)
    up_assets = "../" * total_depth

    prefix = (langdir + "/") if langdir else ""

    def link(name: str) -> str:
        # 同语言链接必须是「相对」的：从本页目录出发，不重复语言目录。
        # 例外是只生成一份、住在中文树里的页面（导图、升学自检），
        # 它们要跨树指过去，得先退回语言根再退掉语言目录那一层。
        if name in ENGLISH_ONLY or name in CROSS_TREE:
            inner = f"notes/{name}"
            up_cross = "../" * (len(parts) + (1 if langdir else 0))
            url = up_cross + inner
            # 导图只有一份文件，中英两棵树都指向它，落地页只能自己判断该显示哪种
            # 语言。不把语言带上它就只能猜（URL 没有、只剩 localStorage）——实测：
            # 从英文站点进来会停在中文，从中文站点进来又可能停在英文。
            if name == "mindmap.html":
                url += "?lang=en" if en else "?lang=zh"
            return url
        inner = "index.html" if name == "index.html" else f"notes/{name}"
        return up_lang + inner

    def other_lang_link(other: str) -> str:
        # 跨语言要「多退一层」：目标在另一棵语言树里，
        # 还要再退掉当前的语言目录（en/）。
        #   从 /en/index.html          -> "index.html"              退 0 + 1 层
        #   从 /en/notes/timetable.html -> "../../notes/timetable.html"  退 1 + 1 层
        #   从 /notes/timetable.html    -> "../en/notes/timetable.html"  退 1 + 0 层
        od = "en/" if other == "en" else ""
        inner = "index.html" if fname == "index.html" else f"notes/{fname}"
        up_cross = "../" * (len(parts) + (1 if langdir else 0))
        return up_cross + od + inner

    body = body_fn(lang, link)

    items = []
    # 导航名是「相对 notes/ 或站点根」的写法（index.html / timetable.html /
    # advising/index.html），而 rel 是「相对站点根」且英文页多一层 en/。
    # 把 rel 折成同一套坐标系再比，才不会两头都命中：
    # 早先的写法是「parent == '.' 或 parent in rel」，当 fname 是 index.html 时
    # 根导航那一项恒为真 —— 嵌套的 index 页会把「首页」和自己同时点亮。
    _nav_space = rel
    for _pref in ("en/", "notes/"):
        if _nav_space.startswith(_pref):
            _nav_space = _nav_space[len(_pref):]
    for entry in NAV:
        name, zh_lbl, en_lbl = entry[0], entry[1], entry[2]
        en_name = entry[3] if len(entry) > 3 else name
        target = en_name if en else name
        cur = (_nav_space == name)
        items.append(f'<a href="{link(target)}"{" class=\"on\"" if cur else ""}>'
                     f'{en_lbl if en else zh_lbl}</a>')

    # 同一页面的另一语言版本
    other = other_lang_link("en" if not en else "zh")

    # 只生成一份的页面（导图）没有另一语言版本，切换链接会指向自己，所以留空。
    if fname in ENGLISH_ONLY:
        lang_switch_html = ""
    else:
        other_code = "zh" if en else "en"
        label = "中文" if en else "EN"
        lang_switch_html = (f'<a class="lang-link" href="{other}" hreflang="{other_code}" '
                            f'lang="{other_code}">{label}</a>')

    return (SHELL
            .replace("__HTMLANG__", "en" if en else "zh-CN")
            .replace("__TITLE__", title)
            .replace("__DESC__", desc)
            .replace("__LANG_SWITCH__", lang_switch_html)
            .replace("__ALT_OTHER__", other)
            .replace("__UP__", up_assets)
            # 品牌链接必须走 link()，不能写 __UP__index.html：
            # 在 /en/index.html 上前者会生成 /en/en/index.html，后者会跳出英文树。
            .replace("__BRAND_LINK__", link("index.html"))
            .replace("__BRAND__", NAME["en"] if en else NAME["zh"])
            .replace("__NAV__", "\n      ".join(items))
            # 语言切换是一个普通链接，指向同一页面的另一语言版本。
            # 英文页面上显示「中文」，中文页面上显示「EN」——不做当前语言的高亮，
            # 因为一个链接没有「选中」状态可言。
            .replace("__OTHERLANG__", "zh" if en else "en")
        .replace("__OTHERHREFLANG__", "zh-CN" if en else "en")
            .replace("__OTHERLABEL__", "中文" if en else "EN")
            .replace("__OTHER__", other)
            .replace("__FOOTER__",
                     FOOT["en"] if en else FOOT["zh"])
            .replace("__BODY__", body))


# ── 内容（单语言直出，不再双写）────────────────────────────────────────────

def md_inline(t):
    """把 `**粗体**` 转成 <strong>。

    本站不做 Markdown 解析，文案里的 `**` 会**原样显示成星号**。
    这个坑已经踩过两次：首页的「索引」和真题页的说明，两处都漏出过字面 `**`。
    凡是带 `**` 的文案，输出前一律过这里。
    """
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)


def fmt(iso, lang):
    if not iso:
        return "—"
    y, m, d = iso.split("-")
    return f"{y}-{int(m):02d}-{int(d):02d}" if lang == "en" else f"{y}/{int(m)}/{int(d)}"


def rng(a, b, lang):
    if not a:
        return "—"
    if not b or a == b:
        return fmt(a, lang)
    return f"{fmt(a, lang)} – {fmt(b, lang)}"


def rows(lang):
    out = []
    # 按**到期日**排，不是起始日。倒计时徽标锚的是区间右端，按起始日排会让
    # 徽标列不单调（例：CSC Task 6 算到 1/21 却排在 ELD Task 7（算到 1/8）前面）。
    # 徽标是行动依据，列该跟着它单调。走查提出。
    for t in sorted(data.TASKS,
                    key=lambda x: (x.get("end") or x["date"] or "9999", x["subj"])):
        w = f'{t["weight"]}%' if t["weight"] else "—"
        note = t[f"note_{lang}"]
        # 形式细节（几点考、考多久、多少分、允许带什么）并进同一行的备注里，
        # 不另开页面 —— 每场考试的日期本来就在这一行，拆到别处反而要来回翻。
        _fmt = data.ASSESS_FMT.get((t["subj"], t["task"], t["date"]))
        if _fmt:
            _extra = _fmt[0] if lang == "zh" else _fmt[1]
            note = f"{note}；{_extra}" if note else _extra
        note_html = f"<br><small>{note}</small>" if note else ""
        # data-due 给倒计时脚本用。
        # **必须取区间的右端**：范围型任务（如 MAM Final 2027/2/1 – 2/12）的
        # 「还剩几天」应当算到 2/12，锚在起点会少算 11 天，排复习计划直接误判。
        # 走查实测：原来锚 2/1 显示「还剩 117 天」，而实际考试可落在 2/12（128 天），
        # 同类 5 行（CSC Task 6 / ELD Task 8 / HBY 与 PHY Final / MAM Final）。
        #
        # 也**刻意不在服务端算天数** —— 构建日期会被冻进页面，过几天就全错。
        # 日期原样输出，由浏览器按当天算。
        due_iso = t.get("end") or t["date"]
        due = f' data-due="{due_iso}"' if due_iso else ""
        span = ' data-span="1"' if (t.get("end") and t["end"] != t["date"]) else ""
        # WACE 外部考试加个标记 —— 低分走查说「我最怕的就是不知道外考是哪几天」，
        # 而这一页原来全文没有「外部考试」字样。
        # 注意：h 是 page_timetable 的局部 lambda，rows() 里没有，直接用 lang 判断。
        _zh = (lang == "zh")
        ext = (f'<span class="ext" title="'
               f'{"WACE 外部考试（SCSA 命题）" if _zh else "WACE external examination (set by SCSA)"}">'
               f'{"外考" if _zh else "EXT"}</span> ') if t.get("external") else ""
        out.append(f'<tr{due}{span}><td>{t["subj"]}</td><td>{ext}{t["task"]}</td><td>{t["type"]}</td>'
                   f'<td>{w}</td><td>{rng(t["date"], t["end"], lang)}{note_html}'
                   f'<span class="due"></span></td></tr>')
    return "\n".join(out)


# 倒计时脚本。渐进增强：没有 JS 时页面照常（只是不显示剩余天数），
# 有 JS 时按**访问当天**计算，所以页面不会随构建时间过期。
COUNTDOWN_JS = """
<script>
(function(){
  var rows = document.querySelectorAll('[data-due]');
  if (!rows.length) return;
  var today = new Date(); today.setHours(0,0,0,0);
  var ZH = document.documentElement.lang !== 'en';
  rows.forEach(function(tr){
    var iso = tr.getAttribute('data-due');
    var parts = iso.split('-');
    var d = new Date(+parts[0], +parts[1]-1, +parts[2]);
    var days = Math.round((d - today) / 86400000);
    var slot = tr.querySelector('.due');
    if (!slot) return;
    // 「已过」有歧义：读起来像「你错过了」。改成「已结束」，只陈述事实。
    // 过期行也不再整行降透明度（36 行里 15 行已过，全灰像页面坏了）。
    // 范围型任务（有起止日期）在提示里说明这个数字算到哪一天，
    // 否则「还剩 117 天」看不出是算到 2/1 还是 2/12。
    var isSpan = tr.hasAttribute('data-span');
    function tail(days) {
      if (!isSpan) return '';
      return ZH ? '（算到 ' + (parts[1] * 1) + '/' + (parts[2] * 1) + '）'
                : ' (to ' + (parts[1] * 1) + '/' + (parts[2] * 1) + ')';
    }
    if (days < 0)   { slot.textContent = ZH ? '已结束' : 'past'; slot.className = 'due past'; }
    else if (days === 0) { slot.textContent = (ZH ? '就是今天' : 'today') + tail(days); slot.className = 'due soon'; }
    else if (days <= 14) { slot.textContent = (ZH ? '还剩 ' : 'in ') + days + (ZH ? ' 天' : 'd') + tail(days);
                           slot.className = 'due soon'; }
    else            { slot.textContent = (ZH ? '还剩 ' : 'in ') + days + (ZH ? ' 天' : 'd') + tail(days);
                      slot.className = 'due'; }
    if (days < 0) tr.classList.add('is-past');
  });
})();
</script>
"""


def weights(lang):
    zh = lang == "zh"
    out = []
    for subj, ws in data.WEIGHTS.items():
        name = data.SUBJECT_NAMES[subj][0 if zh else 1]
        if ws:
            total = sum(w for _, w in ws)
            b = ("<table><thead><tr><th>考核类型</th><th>权重</th></tr></thead><tbody>"
                 if zh else
                 "<table><thead><tr><th>Assessment type</th><th>Weighting</th></tr></thead><tbody>")
            for n, w in ws:
                b += f"<tr><td>{n}</td><td>{w}%</td></tr>"
            b += (f'<tr><td><strong>合计</strong></td><td><strong>{total}%</strong></td></tr>'
                  if zh else
                  f'<tr><td><strong>Total</strong></td><td><strong>{total}%</strong></td></tr>')
            b += "</tbody></table>"
        else:
            b = ('<div class="notice"><p>本页不列出该科权重——没有可核实的来源，宁可不写。</p></div>'
                 if zh else
                 '<div class="notice"><p>Weightings are not listed for this subject: no verifiable source, '
                 'so nothing is stated.</p></div>')
        out.append(f'<h3>{subj} · {name}</h3>{b}')
    return "\n".join(out)


def page_home(lang, link):
    """link() 由调用方注入，负责补正确的 ../ 前缀。

    卡片链接必须走 link()，不能写死 'notes/timetable.html'——
    英文页在 /en/ 下，写死会解析成 /en/timetable.html 而 404。
    """
    zh = lang == "zh"
    t, tl, s, ab = link("timetable.html"), link("timeline.html"), link("subjects.html"), link("about.html")
    mm = link("mindmap.html")
    pp = link("papers.html")
    pp_glossary = link("glossary.html")
    # 升学自检中英分两个文件，不能共用一个名字
    adv = link("advising/en.html" if lang == "en" else "advising/index.html")
    # 卡片描述必须与目标页实际内容一致：
    # 曾经写「复习建议」，但五科页后来改成了「考核构成 + 内容范围」，复习建议已移除。
    n_tasks = len(data.TASKS)
    n_rules = data.ADVISING_RULE_COUNT
    if zh:
        return f"""
<div class="hero"><h1>AUSMAT 学习笔记</h1>
<p>完整学期的考核日程、五科权重构成与内容范围。中英双语，可打印。</p>
<p class="hero-note">AUSMAT 是西澳 <strong>WACE / ATAR</strong> 体系的大学预科课程（Australian Matriculation），
在马来西亚授课、考西澳的课程与考试。本站记录的是这个体系里一届学生的五门 AT 科目：
<strong>数学方法 MAM</strong>、<strong>人体生物学 HBY</strong>、<strong>物理 PHY</strong>、
<strong>英语 ELD</strong>、<strong>计算机科学 CSC</strong>。
不明白的缩写见<a href="{pp_glossary}">术语表</a>。</p></div>
<div class="sec-title">快速入口</div>
<ul class="cards">
<li><a href="{t}"><span class="t">考试日程表</span><span class="d">共 {n_tasks} 项考核任务的日期与权重 · 2026/05 → 2027/02</span></a></li>
<li><a href="{adv}"><span class="t">升学自检</span><span class="d">填一份情况，按规则库汇总出适用的升学建议 · {n_rules} 条规则可逐条查看</span></a></li>
<li><a href="{mm}"><span class="t">知识导图</span><span class="d">五科知识点全览，可搜索、可展开</span></a></li>
<li><a href="{tl}"><span class="t">学期时间线</span><span class="d">37 周（末周 4 天）的节奏、假期与三次密集期</span></a></li>
<li><a href="{s}"><span class="t">五科要点</span><span class="d">各科权重构成，以及每项考核覆盖哪些内容</span></a></li>
<li><a href="{pp}"><span class="t">真题与资料</span><span class="d">五科历年 WACE 试卷的官方与社区入口</span></a></li>
<li><a href="{ab}"><span class="t">关于本站</span><span class="d">内容说明</span></a></li>
</ul>
<div class="notice"><p>本站只包含个人整理的通用信息与原创讲解，不含学校发放的讲义、练习卷、试卷及其答案，也不含任何个人信息。知识导图里会提到某些资料的名称与页数——那是对我手头材料的 <strong>索引</strong>，不是资料本身。升学自检工具是个例外：它确实要填学生资料，但完全在你自己浏览器里运行，不上传、不保存到服务器，关掉页面即消失。</p></div>
"""
    return f"""
<div class="hero"><h1>AUSMAT Study Notes</h1>
<p>A full-course assessment timetable, subject weightings and content covered. Bilingual, printable.</p>
<p class="hero-note">AUSMAT is the Australian Matriculation programme: a pre-university year taught in
Malaysia that sits the Western Australian <strong>WACE / ATAR</strong>. This site documents one intake of
it, covering five AT subjects: <strong>Mathematics Methods (MAM)</strong>, <strong>Human Biology (HBY)</strong>,
<strong>Physics (PHY)</strong>, <strong>English EAL/D (ELD)</strong> and <strong>Computer Science (CSC)</strong>.
Unfamiliar abbreviations are defined in the <a href="{pp_glossary}">glossary</a>.</p></div>
<div class="sec-title">Quick links</div>
<ul class="cards">
<li><a href="{t}"><span class="t">Assessment Timetable</span><span class="d">{n_tasks} tasks with their dates and weightings · May 2026 – Feb 2027</span></a></li>
<li><a href="{adv}"><span class="t">Advising self-check</span><span class="d">Fill in one record and get the advice that applies · {n_rules} rules, readable one by one</span></a></li>
<li><a href="{mm}"><span class="t">Mind Map</span><span class="d">Every topic across five subjects · searchable</span></a></li>
<li><a href="{tl}"><span class="t">Semester Timeline</span><span class="d">37 weeks (the last one 4 days), the breaks, and three crunch periods</span></a></li>
<li><a href="{s}"><span class="t">Five Subjects</span><span class="d">Weightings, and what each assessment covers</span></a></li>
<li><a href="{pp}"><span class="t">Past Papers</span><span class="d">Official and community sources for all five subjects</span></a></li>
<li><a href="{ab}"><span class="t">About</span><span class="d">What this site does and does not contain</span></a></li>
</ul>
<div class="notice"><p>This site contains only general information I compiled and explanations I wrote. It does not include school-issued handouts, worksheets, exam papers or their solutions. It holds no personal information, with one exception: the advising tool does ask for a student record, but it runs entirely in your own browser, uploads nothing and stores nothing on a server. The mind map does name some course materials and their page counts — that is an <strong>index</strong> of what I have, not the materials themselves.</p></div>
"""


def page_timetable(lang, link):
    zh = lang == "zh"
    h = (lambda z, e: z if zh else e)
    return f"""
<div class="note-head"><a class="back" href="{link('index.html')}">← {h('首页', 'Home')}</a>
<h1>{h('考试日程表', 'Assessment Timetable')}</h1>
<div class="meta">{h('AUSMAT May 2026 Intake · 2026 年 5 月 → 2027 年 2 月', 'AUSMAT May 2026 Intake · May 2026 – Feb 2027')}</div></div>

<h2>{h('全部考核任务（按日期）', 'All assessment tasks (chronological)')}</h2>
<p>{h(f'共 {len(data.TASKS)} 项。标「—」的是未给日期或未给权重。每场考试的时间、时长、允许携带什么，写在日期下面那行小字里。', f'{len(data.TASKS)} tasks. A dash means no date or no weighting is stated. Timing, duration and what you may bring appear in the small print under each date.')}</p>
<table><thead><tr>
<th>{h('科目', 'Subj')}</th><th>{h('任务', 'Task')}</th><th>{h('类型', 'Type')}</th>
<th>{h('权重', 'Wt')}</th><th>{h('日期', 'Date')}</th>
</tr></thead><tbody>
{rows(lang)}
</tbody></table>

<div class="notice"><p>{h('标了「外考」的是 <strong>WACE 外部考试</strong>：由 SCSA 命题、全州统一，占分见权重列。其余为校本考核。',
     'Rows marked <strong>EXT</strong> are <strong>WACE external examinations</strong>: set by SCSA and sat statewide. Everything else is school-based assessment.')}</p>
<p>{h('这个区分本站只能核到一部分：MAM 期末（40%）与 ELD Task 8（30%）有直接凭据，其余三科的期末是按它们落在结课考试期（1/25–2/13）判断的。以学校通知为准。',
     'This site can only confirm part of that split: MAM\'s final (40%) and ELD Task 8 (30%) are directly evidenced; the other three are inferred from falling inside the final examination period (25 Jan – 13 Feb). Check with the school.')}</p></div>

<h2>{h('学期结构', 'Course structure')}</h2>
<table><thead><tr><th>{h('项目', 'Item')}</th><th>{h('日期', 'Dates')}</th></tr></thead><tbody>
<tr><td>{h('开课', 'Course starts')}</td><td>{fmt(data.SEMESTER['start'], lang)}</td></tr>
<tr><td>{h('最后教学日', 'Last teaching day')}</td><td>{fmt(data.SEMESTER['end'], lang)}</td></tr>
<tr><td>{h('全部考核结束', 'All assessments end')}</td><td>{fmt(data.SEMESTER['last_exam'], lang)}</td></tr>
""" + "".join(
        f'<tr class="hot"><td>{h("假期", "Break")}</td><td>{fmt(a, lang)} – {fmt(b, lang)}</td></tr>'
        for a, b, _ in data.SEMESTER["breaks"]) + "".join(
        f'<tr><td>{h("考试窗口", "Examination window")}</td><td>{fmt(a, lang)} – {fmt(b, lang)}</td></tr>'
        for a, b, _ in data.SEMESTER["exam_windows"]) + f"""
</tbody></table>

<h2>{h('各科权重构成', 'Weighting by subject')}</h2>
{weights(lang)}

<div class="notice"><p>{h('表里的科目用课程代码缩写：<strong>MAM</strong> 数学方法、<strong>HBY</strong> 人体生物学、<strong>PHY</strong> 物理、<strong>ELD</strong> 英语（EAL/D）、<strong>CSC</strong> 计算机科学。含义都列在<a href="' + link('glossary.html') + '">术语表</a>。各科大纲均注明日期为暂定（tentative, subject to change）。本页为个人整理，以学校与 SCSA 的官方文件为准。另外，计算机的结课考试日期与本站标注的结课考试期不重合——这一处来自大纲本身的表述差异，未能核对，同样以学校通知为准。',
  'The subject column uses course codes: <strong>MAM</strong> Mathematics Methods, <strong>HBY</strong> Human Biology, <strong>PHY</strong> Physics, <strong>ELD</strong> English (EAL/D), <strong>CSC</strong> Computer Science — all defined in the <a href="' + link('glossary.html') + '">glossary</a>. Every outline marks its dates as tentative and subject to change. This page is a personal summary; the official school and SCSA documents take precedence. One inconsistency could not be reconciled: the Computer Science final exam falls outside the final-evaluation window shown above, which comes from wording differences in the outline itself. Check with the school.')}</p></div>
{COUNTDOWN_JS}"""


def page_timeline(lang, link):
    zh = lang == "zh"
    h = (lambda z, e: z if zh else e)

    # 周次桶：(周次, 起, 止, 阶段说明)
    # 阶段说明是编辑内容（哪些周在讲什么）；**考核项一律从 data.TASKS 自动生成**。
    # 2026-10 改成这样：原先整行描述都是手写的，改数据时不同步，结果整页漏掉了
    # PHY 与 HBY 的全部考核（含 PHY Task 3 的 20%、HBY EE 的 20%、TT2 的 15%），
    # 照它判断节奏会漏掉近三成分数。手写描述必然与数据漂移，所以只留不可推导的部分。
    BUCKETS = [
        ("1–3", "2026-05-25", "2026-06-12", ("开课、Unit 3 导入", "Course start, Unit 3 introduction")),
        ("4–7", "2026-06-15", "2026-07-10", ("编程基础", "Programming fundamentals")),
        ("8–10", "2026-07-13", "2026-07-31", ("面向对象", "Object-oriented programming")),
        ("11–13", "2026-08-03", "2026-08-21", ("最密集的一段", "The busiest stretch")),
        ("14–17", "2026-08-24", "2026-09-18", ("网络通信", "Networking")),
        ("18–19", "2026-09-21", "2026-10-02", ("安全框架", "Security frameworks")),
        ("20", "2026-10-05", "2026-10-09", ("假期", "Break")),
        ("21–23", "2026-10-12", "2026-10-30", ("密码学、数据管理", "Cryptography, data management")),
        ("24–26", "2026-11-02", "2026-11-20", ("考试周", "Examination weeks")),
        ("27–30", "2026-11-23", "2026-12-18", ("数据库项目", "Database project")),
        ("31–32", "2026-12-21", "2027-01-01", ("假期", "Break")),
        ("33–35", "2027-01-04", "2027-01-21", ("期末冲刺", "Run-up to the finals")),
        # 末桶的**右端必须到 2/13**（最后一门考完），不能停在最后教学日 2/4。
        # 原来写 2/4，而列在这个桶里的四门期末（MAM 2/1–2/12、ELD 与 HBY 至 2/12、
        # PHY 至 2/13）全都考到桶外 —— 桶说「结课考试」却把考试截止日切掉了。
        # 教学周与考试期是两回事：教学到 2/4 结束，考试到 2/13 结束。
        ("36–37+", "2027-01-25", "2027-02-13", ("结课考试期", "Final examination period")),
    ]

    def _d(s):
        y, m, dd = map(int, s.split("-"))
        return datetime.date(y, m, dd)

    rows = []
    for lbl, a, b, phase in BUCKETS:
        A, B = _d(a), _d(b)
        hits = []
        spanning = []      # 与 hits 平行：这一项是否跨出了本桶
        for t in data.TASKS:
            if not t["date"]:
                continue
            td = _d(t["date"])
            te = _d(t["end"]) if t.get("end") else td
            # 起止范围与本周次桶相交就算（跨周的长期项目会出现在多个桶里，
            # 这正是想让人看到的）
            if td <= B and te >= A:
                w = (f' {t["weight"]}%') if t.get("weight") else ""
                # 任务名本身是语言中立的（Task 1 / Topic Test 2 / Final Examination），
                # 所以两种语言共用，不需要 task_en 字段。
                _span = (td < A or te > B)     # 起止越出本桶
                spanning.append(_span)
                _mark = "*" if _span else ""
                hits.append(f'{t["subj"]} {t["task"]}{w}{_mark}')
        _is_break = phase[0] in ("假期",)
        desc = h(phase[0], phase[1])
        if hits:
            if _is_break:
                # 假期行里出现项目是因为它们**跨过**假期，不是要在假期交付。
                # 原来直接列出来，读着像「假期也得交 20%」（走查提出）。
                desc += h("（下列项目横跨这段时间，并不在假期内交付）：",
                          " (the items below span this break; nothing is due during it): ")
                desc += h("、", ", ").join(hits)
            else:
                desc += h("：", ": ") + h("、", ", ").join(hits)
            # 跨阶段的任务会在多个桶里出现（如 CSC 的长期项目），说明一句，
            # 否则读起来像同一个考核被排了两次（走查提出）。
            if any(spanning):
                desc += h("（带 * 的跨多个阶段）", " (* spans more than one phase)")
        hot = "hot" if (A <= _d("2026-08-21") and B >= _d("2026-08-03")) or \
                       (A <= _d("2026-11-20") and B >= _d("2026-11-02")) or \
                       (A <= _d("2027-02-04") and B >= _d("2027-01-25")) else ""
        rows.append((lbl, rng(a, b, lang), desc, hot))

    body = "".join(f'<tr{" class=\"hot\"" if c else ""}><td>{w}</td><td>{d}</td><td>{t}</td></tr>'
                   for w, d, t, c in rows)
    return f"""
<div class="note-head"><a class="back" href="{link('index.html')}">← {h('首页', 'Home')}</a>
<h1>{h('学期时间线', 'Semester Timeline')}</h1>
<div class="meta">{h('2026 年 5 月 → 2027 年 2 月', 'May 2026 – February 2027')}</div></div>
<p>{h('把整个课程摊在一条时间线上，便于看节奏：哪几周密集、哪些是假期、考试集中在什么时候。',
      'The whole course on one timeline, to show the rhythm: which weeks are dense, where the breaks fall, and when assessments cluster.')}</p>
<table><thead><tr><th>{h('周次', 'Weeks')}</th><th>{h('日期', 'Dates')}</th><th>{h('阶段', 'Phase')}</th></tr></thead>
<tbody>{body}</tbody></table>
<div class="notice"><p>{h(
  f'表里的缩写第一次出现时已在括号里展开；其余名词（ATAR、TEA、OLNA、COAT 等）见<a href="{link("glossary.html")}">术语表</a>。',
  f'Abbreviations are expanded in brackets the first time they appear; the rest (ATAR, TEA, OLNA, COAT and others) are defined in the <a href="{link("glossary.html")}">glossary</a>.')}</p></div>
<div class="callout"><p>{h('节奏上有三处要提前准备：8 月中上旬三科作业叠在一起；11 月中下旬考试周与两项任务重叠；12 月中 CSC 项目与 MAM Topic Test 3 同期。',
  'Three pinch points to plan for: early-to-mid August (three subjects overlap), mid-to-late November (examination weeks overlap with two tasks), and mid December (CSC project coincides with MAM Topic Test 3).')}</p></div>
"""


def scope_table(subj: str, lang: str) -> str:
    """把「哪项考核 → 覆盖哪些内容」列成表。

    这一版取代了之前的通用公式块。那几条微积分公式和考核任务、和学生实际
    要掌握的内容都不搭，放在评估页面里显得突兀。评估页面该回答的是
    「考什么、怎么算分」，不是贴公式表。
    """
    rows = data.SCOPE.get(subj) or []
    zh = lang == "zh"
    if not rows:
        return ('<div class="notice"><p>本页不列出该科考核范围——没有可核实的来源，宁可不写。</p></div>'
                if zh else
                '<div class="notice"><p>No scope is listed for this subject: no verifiable source, '
                'so nothing is stated.</p></div>')
    h = (lambda z, e: z if zh else e)
    body = "".join(f'<tr><td><strong>{a}</strong></td><td>{c if zh else b}</td></tr>'
                   for a, b, c in rows)
    return (f'<table><thead><tr><th>{h("考核", "Assessment")}</th>'
            f'<th>{h("内容范围", "Content covered")}</th></tr></thead><tbody>{body}</tbody></table>')


def page_subjects(lang, link):
    zh = lang == "zh"
    h = (lambda z, e: z if zh else e)

    def block(subj, tip_zh="", tip_en=""):
        name = data.SUBJECT_NAMES[subj][0 if zh else 1]
        ws = data.WEIGHTS.get(subj) or []
        scope = data.SCOPE.get(subj) or []

        # 完全没有可核实数据的科目：只说一次。
        # 之前拆成「没权重」「没范围」「没找到来源」三句，说的其实是同一件事，
        # 页面上连着重复三遍很难看。
        if not ws and not scope:
            msg = ("没有找到这一科可核实的考核数据，因此本页<strong>不列出权重与范围</strong>"
                   "——宁可留空，也不填猜测的数字。" if zh else
                   "No verifiable assessment data was found for this subject, so <strong>neither "
                   "weightings nor scope are listed</strong> — better to leave a gap than to fill it "
                   "with guesswork.")
            return f'<h2>{subj} · {name}</h2>\n<div class="notice"><p>{msg}</p></div>'

        if ws:
            total = sum(w for _, w in ws)
            wt = " + ".join(f"{n} {w}%" for n, w in ws)
            wsum = (f'<p><strong>权重构成</strong>：{wt} = {total}%</p>' if zh
                    else f'<p><strong>Weighting</strong>: {wt} = {total}%</p>')
        else:
            wsum = ('<p>没有可核实的权重数据。</p>' if zh
                    else '<p>No verifiable weighting data.</p>')
        tip = ""
        if tip_zh or tip_en:
            tip = f'<div class="callout"><p>{tip_zh if zh else tip_en}</p></div>'
        return (f'<h2>{subj} · {name}</h2>\n'
                f'<div class="box">{wsum}</div>\n'
                f'{scope_table(subj, lang)}\n{tip}')

    blocks = [
        block("MAM",
              "注意 <strong>Topic Test 2 单项占 20%</strong>——比两次 Investigation 中的任何一次都重，"
              "是期末的一半，而且落在 11 月考试周内。"
              "<strong>别按小测准备：它之前的空档只有 10/5–10/9 那一周假期，那周开始过范围才来得及。</strong>",
              "Note that <strong>Topic Test 2 alone is worth 20%</strong> — more than either "
              "Investigation, half of what the final exam is worth, and it falls inside the November "
              "examination window. <strong>Do not treat it as a routine test: the only clear gap before "
              "it is the 5–9 October break, so that is when to start working through the content.</strong>"),
        block("PHY",
              "注意 <strong>Topic Test 两项合计 28%</strong>，只比期末的 30% 少一点。只盯期末会把将近三成的分数放掉。"
              "10 月底的 Evaluation Exam 还紧接 11 月中的考试周。",
              "Note that the <strong>two Topic Tests total 28%</strong>, not much less than the 30% "
              "final. Focusing only on the final leaves nearly a third of the marks exposed. The "
              "Evaluation Exam at the end of October also runs straight into the mid-November "
              "examination weeks."),
        block("CSC",
              "两个 Project 合计 40%，与两次考试总分相等，而且都跨数周——最需要提前动手。",
              "The two projects total 40%, equal to the two examinations combined, and each runs over "
              "several weeks. These most reward starting early."),
        block("ELD",
              # 任务数从数据算 —— 原先写死「8 项」，但 timetable 里 ELD 实际有 9 行
              # （Task 2A/2B 分行），高分学生走查对出来的。
              f'共 {len([t for t in data.TASKS if t["subj"] == "ELD"])} 项任务，是五科中最多的一科；'
              "口语类任务合计超过 20%。"
              "建议录音自听——多数人察觉不到自己语速过快或停顿过多。",
              f'{len([t for t in data.TASKS if t["subj"] == "ELD"])} tasks, the most of any subject. '
              "Spoken tasks exceed 20% combined. Recording "
              "yourself and listening back helps: most people cannot hear their own pace or filler "
              "pauses while speaking."),
        block("HBY",
              "注意 <strong>两次 Extended Response 合计 15%</strong>、Lab Assessment 单项 10%——"
              "这两类没有期末那种压迫感，最容易在平时被放掉。",
              "Note that the <strong>two Extended Responses total 15%</strong> and the Lab Assessment "
              "is 10% on its own. Neither feels urgent the way a final does, which is exactly why "
              "they get neglected."),
    ]

    return f"""
<div class="note-head"><a class="back" href="{link('index.html')}">← {h('首页', 'Home')}</a>
<h1>{h('五科要点', 'Five Subjects')}</h1>
<div class="meta">{h('考核构成与内容范围', 'Assessment structure and content covered')}</div></div>

<p>{h('下面每科给出两部分：<strong>分数怎么构成</strong>，以及<strong>每项考核覆盖哪些内容</strong>。',
     'For each subject below: <strong>how the marks are made up</strong>, and <strong>what content each assessment covers</strong>.')}</p>

{"".join(blocks)}

<div class="callout">
<p>{h('复习时优先看「内容范围」那一列——它直接告诉你每项考核会考到哪些主题，比笼统地把课本过一遍省时间。',
     'When revising, start with the content-covered column: it tells you which topics each assessment draws on, which is more efficient than re-reading the whole course.')}</p>
</div>

<div class="notice">
<p>{h('本页为个人整理，不复述学校或 SCSA 大纲的任务描述原文；具体表述与要求以官方文件为准。',
     'This page is a personal summary and does not reproduce task descriptions from the school or SCSA outlines; the official documents govern the detail and requirements.')}</p>
</div>
"""


def page_about(lang, link):
    zh = lang == "zh"
    h = (lambda z, e: z if zh else e)
    return f"""
<div class="note-head"><a class="back" href="{link('index.html')}">← {h('首页', 'Home')}</a>
<h1>{h('关于本站', 'About')}</h1>
<div class="meta">{h('内容说明', 'What this site contains')}</div></div>

<h2>{h('包含什么', 'What it contains')}</h2>
<div class="box">
<ul>
<li>{h('个人整理的考核日期与权重（事实性信息）', 'Assessment dates and weightings I compiled (factual information)')}</li>
<li>{h('个人撰写的学科讲解、公式与复习建议', 'Subject explanations, formulas and revision advice written by me')}</li>
</ul>
</div>

<h2>{h('不包含什么', 'What it does not contain')}</h2>
<div class="box">
<ul>
<li>{h('学校发放的讲义、练习卷、试卷及其答案', 'School-issued handouts, worksheets, exam papers or their solutions')}</li>
<li>{h('任何个人信息，包括姓名、学号、联系方式', 'Any personal information: names, student numbers, contact details')}</li>
<li>{h('无法核实的数据', 'Anything that cannot be verified')}</li>
</ul>
</div>

<h2>{h('技术说明', 'Technical notes')}</h2>
<ul>
<li>{h('纯静态页面：没有框架、没有构建步骤', 'Pure static pages: no framework, no build step')}</li>
<li>{h('公式排版所需的字体与脚本随本站提供，不依赖外部服务', 'The fonts and scripts needed for maths typesetting are served from this site; no external services are used')}</li>
<li>{h('中英文各有独立页面，通过页面上方的链接切换，不需要 JavaScript；<strong>知识导图是唯一的例外</strong>：它只有一份文件，中英切换靠页内的按钮完成', 'Chinese and English have separate pages, switched with the links at the top — no JavaScript required')}</li>
<li>{h('配色跟随系统深色模式；可用浏览器打印功能输出 PDF', 'Follows system dark mode; the browser print function can produce a PDF')}</li>
</ul>
"""


def page_papers(lang, link):
    """真题与资料 —— 只指路，不托管试卷文件。理由印在页面上。"""
    zh = lang == "zh"
    h = (lambda z, e: z if zh else e)

    rows = []
    for subj, p in data.PAPERS.items():
        name = data.SUBJECT_NAMES[subj][0 if zh else 1]
        scsa = data.SCSA_PAPERS_BASE + p["scsa"]
        rows.append(
            f'<tr><td><strong>{subj}</strong> · {name}</td>'
            f'<td><a href="{scsa}" rel="noopener">SCSA</a></td>'
            f'<td><a href="{p["vault"]}" rel="noopener">WACE Vault</a></td></tr>')
    table = (f'<table><thead><tr><th>{h("科目", "Subject")}</th>'
             f'<th>{h("官方真题（SCSA）", "Official papers (SCSA)")}</th>'
             f'<th>{h("社区题库", "Community vault")}</th></tr></thead>'
             f'<tbody>{"".join(rows)}</tbody></table>')

    mirrors = "".join(
        f'<li><a href="{m["url"]}" rel="noopener"><span class="t">{m["name"]}</span>'
        f'<span class="d">{m["zh"] if zh else m["en"]}</span></a></li>'
        for m in data.PAPER_MIRRORS)

    # 逐年覆盖表。官方五科年份一致、社区库逐科不同，所以按科目一行行列出来，
    # 让人一眼看出「我要的那一年该去哪个源拿」。
    heads = data.COVERAGE_HEAD_ZH if zh else data.COVERAGE_HEAD_EN
    crows = []
    for subj, scsa_y, vault_y in data.PAPER_COVERAGE:
        name = data.SUBJECT_NAMES[subj][0 if zh else 1]
        crows.append(f'<tr><td><strong>{subj}</strong> · {name}</td>'
                     f'<td>{scsa_y}</td><td>{vault_y}</td></tr>')
    coverage = (f'<table><thead><tr>' +
                "".join(f"<th>{x}</th>" for x in heads) +
                f'</tr></thead><tbody>{"".join(crows)}</tbody></table>')

    # 考官报告的失分点。**粗体** 标记要在服务端转成 <strong>：
    # 页面其余部分不做 Markdown 解析，直接输出会露出字面星号（首页那次就是这样）。

    # 考官报告的失分点。`**粗体**` 要在服务端转成 <strong>：
    # 页面其余部分不做 Markdown 解析，直接输出会露出字面星号。
    # 「所以怎么办」列。对策由 _sp/findings-fixes.json 提供，与 EXAMINER_FINDINGS
    # 同序同长；文件还没写好时自动退化成两列，不阻断构建。
    # 低分走查的原话：「它是一张纯罪名清单：六条失分点、零条对策。」
    _fixes = None
    _fx = Path(__file__).parent / "_sp" / "findings-fixes.json"
    if _fx.exists():
        try:
            _raw = json.loads(_fx.read_text(encoding="utf-8"))
            if (len(_raw) == len(data.EXAMINER_FINDINGS)
                    and all(len(a) == len(b[2]) for a, b in zip(_raw, data.EXAMINER_FINDINGS))):
                _fixes = _raw
            else:
                print("  ⚠ findings-fixes.json 与失分点条数不匹配，本次不加对策列")
        except Exception as _e:
            print(f"  ⚠ findings-fixes.json 解析失败：{_e}")

    frows = []
    for _si, (subj, yr, items) in enumerate(data.EXAMINER_FINDINGS):
        sname = data.SUBJECT_NAMES[subj][0 if zh else 1]
        if _fixes:
            rows = []
            for _ii, (a, b) in enumerate(items):
                fx = _fixes[_si][_ii]
                rows.append(f'<li>{md_inline(a if zh else b)}'
                            f'<div class="fix">{h("怎么办", "Do this")}：'
                            f'{md_inline(fx[0] if zh else fx[1])}</div></li>')
            lis = "".join(rows)
        else:
            lis = "".join(f"<li>{md_inline(a if zh else b)}</li>" for a, b in items)
        frows.append(f'<tr><td><strong>{subj}</strong> · {sname}'
                     f'<br><small class="muted">{yr}</small></td>'
                     f'<td><ul class="tight">{lis}</ul></td></tr>')
    _fixhead = (f'<th>{h("普遍失分点 / 所以怎么办", "Commonly lost marks / what to do")}</th>'
                if _fixes else f'<th>{h("普遍失分点", "Commonly lost marks")}</th>')
    findings = (f'<table><thead><tr><th>{h("科目（报告年份）", "Subject (report year)")}</th>'
                f'{_fixhead}</tr></thead>'
                f'<tbody>{"".join(frows)}</tbody></table>')

    return f"""
<div class="note-head"><a class="back" href="{link('index.html')}">← {h('首页', 'Home')}</a>
<h1>{h('真题与资料', 'Past Papers')}</h1>
<div class="meta">{h('五科历年 WACE 试卷与资料的入口', 'Where to find past WACE papers for the five subjects')}</div></div>

<p>{h('下面两条主线覆盖五科：<strong>SCSA 官方真题</strong>（免费、含评分标准与公式手册）与 <strong>WACE Vault</strong>（社区整理，年份更长）。',
     'Two sources cover all five subjects: <strong>the official SCSA pages</strong> (free, with marking keys and formula sheets) and <strong>WACE Vault</strong> (community-run, with a longer run of years).')}</p>

{table}

<div class="callout"><p>{md_inline(h(data.COVERAGE_NOTE_ZH, data.COVERAGE_NOTE_EN))}</p></div>

<h2>{h('考官报告：五科常见失分点', 'Examiner reports: where marks are commonly lost')}</h2>
<p>{h('每年考完，SCSA 会随真题一起发布一份考官报告，写明当年考生普遍在哪些地方丢分。下面按科目整理，只转述现象，不含题目原文。',
     'Each year SCSA publishes an examiner report alongside the paper, setting out where candidates commonly lost marks. Categorised by subject below — the patterns only, no question text.')}</p>
{findings}

<div class="notice"><p>{md_inline(h(data.EXAMINER_NOTE_ZH, data.EXAMINER_NOTE_EN))}</p></div>

<div class="notice"><p>{md_inline(h(data.VAULT_CAVEAT_ZH, data.VAULT_CAVEAT_EN))}</p></div>

<h2>{h('逐年覆盖', 'Year by year')}</h2>
{coverage}
<p>{h(data.VAULT_EXTRA_ZH, data.VAULT_EXTRA_EN)}</p>

<h2>{h('可整目录下载', 'Downloadable in bulk')}</h2>
<p>{h('上面两个入口都是逐个文件点取。想一次拿到一批做离线库，用下面这个 Git 仓库。',
     'Both sources above are one file at a time. For an offline library, this Git repository is easier.')}</p>
<ul class="cards">{mirrors}</ul>

<div class="notice">
<p>{h(data.PAPERS_STANCE_ZH, data.PAPERS_STANCE_EN)}</p>
</div>

<div class="notice">
<p>{h('提示：SCSA 的域名是 <code>scsa.wa.edu.au</code>。网上不少资料写成 <code>scsa.wa.gov.au</code>，那个域名并不存在。',
     'Note: the SCSA domain is <code>scsa.wa.edu.au</code>. Plenty of material online writes <code>scsa.wa.gov.au</code>, which does not exist.')}</p>
</div>
"""


def page_glossary(lang, link):
    """术语表 —— 解释站内反复出现却没展开的名词与缩写。"""
    zh = lang == "zh"
    h = (lambda z, e: z if zh else e)

    sections = []
    for si, (title_zh, title_en, items) in enumerate(data.GLOSSARY):
        rows = []
        for gi, it in enumerate(items):
            src = it["src"] if zh else it["srcEn"]
            body = it["zh"] if zh else it["en"]
            # 词条名与全称都要分语言：有几条的中文名本身就是中文
            # （标准分 / AT 课程 / 数学加分），只写一份会漏进英文页。
            term = it["t"] if zh else it.get("tEn", it["t"])
            full = it["full"] if zh else it.get("fullEn", it["full"])
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
            body = re.sub(r"`(.+?)`", r"<code>\1</code>", body)
            head = f'<strong>{term}</strong>'
            if full and full != "—":
                head += f'<br><span class="gl-full">{full}</span>'
            # 锚点 id 必须全局唯一：早先按「每节从 1 开始」编号，三节各出一个 g-1，
            # HTML 非法（低分学生走查发现）。改成 节号-条号。
            body_html = (f'{body}<div class="gl-src">{h("来源", "Source")}'
                         f'{":" if zh else ": "}{src}</div>')
            extra = it.get("note_zh" if zh else "note_en")
            if extra:
                # 注意：这一段替换**必须放在 f-string 之外**。
                # 写在 f-string 的花括号表达式里时，`\\*` 会被当成「反斜杠 + 任意字符」，
                # 结果把整段替换成字面量 `\1\1\1…`（实际踩到过）。
                extra_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", extra)
                # 英文用半角冒号 —— 全角「：」在英文里很显眼
                body_html += (f'<div class="gl-note">{h("注意", "Note")}'
                              f'{":" if zh else ": "}{extra_html}</div>')
            rows.append(f'<tr id="g-{si + 1}-{gi + 1}"><td>{head}</td><td>{body_html}</td></tr>')
        sections.append(f'<h2>{h(title_zh, title_en)}</h2>'
                        f'<table class="glossary"><tbody>{"".join(rows)}</tbody></table>')

    return f"""
<div class="note-head"><a class="back" href="{link('index.html')}">← {h('首页', 'Home')}</a>
<h1>{h('术语表', 'Glossary')}</h1>
<div class="meta">{h('站内反复出现、但之前没有展开解释的名词与缩写', 'Terms and abbreviations used across this site, previously left unexplained')}</div></div>

<div class="callout"><p>{h(data.GLOSSARY_NOTE_ZH, data.GLOSSARY_NOTE_EN)}</p></div>

{"".join(sections)}
"""


# 标题按语言分两套 —— 之前是单一字符串，英文页会显示「首页 · Home」这种中英混排。
# (中文标题, 英文标题) → 页面函数。原来源表里还带第三个字段 depth，但从来没被读过
# （路径层数由 build_page 从 rel 自己算），2026-10 去掉。
PAGES = {
    "index.html": (("首页 · 学习笔记", "Home · Study Notes"), page_home),
    "timetable.html": (("考试日程表 · 学习笔记", "Assessment Timetable · Study Notes"), page_timetable),
    "timeline.html": (("学期时间线 · 学习笔记", "Semester Timeline · Study Notes"), page_timeline),
    "subjects.html": (("五科要点 · 学习笔记", "Five Subjects · Study Notes"), page_subjects),
    "papers.html": (("真题与资料 · 学习笔记", "Past Papers · Study Notes"), page_papers),
    "glossary.html": (("术语表 · 学习笔记", "Glossary · Study Notes"), page_glossary),
    "about.html": (("关于 · 学习笔记", "About · Study Notes"), page_about),
}



def page_404(lang, link):
    """自定义 404：无 JS 也能用，中英双语。

    GitHub Pages 对未匹配路径返回仓库根目录的这个文件，任意深度都用它。
    实测下面这些「手输或旧链接会走」的路径原本都是 Pages 的通用 404：
        /notes/  /en/notes/  /notes/index.html  /glossary.html

    ⚠ 链接与 CSS 必须用**站点根绝对路径**。第一版写成相对路径、再靠 JS 按
    location.pathname 重算，结果**禁用 JS 时全部指错**（在 /notes/ 深度下点「首页」
    落到 /notes/index.html，又一个 404），CSS 也加载失败、整页无样式（游客实测）。

    唯一的一小段 JS 只做一件事：在 file:// 下把绝对路径换回相对路径，
    方便本地预览。没有它，本地打开会没样式，但线上完全正常。
    """
    items = [
        ("index.html", "首页", "Home"),
        ("notes/timetable.html", "考试日程", "Timetable"),
        ("notes/subjects.html", "五科要点", "Subjects"),
        ("notes/mindmap.html", "知识导图", "Mind Map"),
        ("notes/advising/index.html", "升学自检", "Advising"),
        ("notes/glossary.html", "术语表", "Glossary"),
        ("notes/timeline.html", "学期时间线", "Timeline"),
        ("notes/papers.html", "真题与资料", "Past Papers"),
        ("notes/about.html", "关于", "About"),
    ]
    lis = "".join(
        f'<li><a href="{SITE_BASE}{u}" data-p="{u}">'
        f'<span class="t">{z}</span><span class="d">{e}</span></a></li>'
        for u, z, e in items)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>找不到这个页面 / Page not found · 学习笔记</title>
<meta name="description" content="这个地址下没有内容，页面可能已经挪走。这里有本站全部页面的入口。">
<link rel="stylesheet" href="{SITE_BASE}assets/style.css" data-css="1">
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="{SITE_BASE}index.html" data-p="index.html">学习笔记 · Study Notes</a>
</div></header>
<main><div class="wrap">

<h1>找不到这个页面</h1>
<p>这个地址下没有内容。可能是链接打错了，或者页面已经挪走了。下面是站点里的全部页面。</p>

<ul class="cards">{lis}</ul>

<hr>

<h2>Page not found</h2>
<p>There is nothing at this address. The link may be mistyped, or the page may have moved.
Every page on the site is listed above.</p>

<p><small>404</small></p>
</div></main>
<footer class="site"><div class="wrap">
<p>AUSMAT May 2026 · 个人学习笔记 / personal study notes</p>
</div></footer>
<script>
/* 唯一的用途：本地用 file:// 打开预览时，把站点根绝对路径换回相对路径。
   线上（GitHub Pages）走不到这里 —— 绝对路径本来就对，禁用 JS 也照样能用。 */
(function () {{
  if (location.protocol !== 'file:') return;
  document.querySelectorAll('[data-p]').forEach(function (el) {{
    el.setAttribute('href', './' + el.getAttribute('data-p'));
  }});
  var css = document.querySelector('[data-css]');
  if (css) css.setAttribute('href', './assets/style.css');
}})();
</script>
</body>
</html>
"""


def main():
    # 清掉旧的（保留 vendor / assets / node_modules）
    for d in ("notes", "en"):
        p = OUT / d
        if p.exists():
            shutil.rmtree(p)
    old = OUT / "index.html"
    if old.exists():
        old.unlink()

    n = 0
    errors = []
    for lang in ("zh", "en"):
        for rel, ((title_zh, title_en), fn) in PAGES.items():
            title = title_zh if lang == "zh" else title_en
            target = out_path(lang, rel)
            f = OUT / target
            f.parent.mkdir(parents=True, exist_ok=True)
            _d = PAGE_DESCS.get(rel, (title, title))
            page = build_page(lang, target, title, _d[0] if lang == "zh" else _d[1], fn)
            f.write_text(page, encoding="utf-8")
            print(f"  {target:<32} {len(page):>7} 字节")

            # 生成后自检。
            # 有两处 '../en/' 是合法的跨语言引用，不算错，先剥掉再查：
            #   1. <link rel="alternate" hreflang>  给搜索引擎的语言版本声明
            #   2. <a class="lang-link">            页面上给用户的语言切换链接
            # 只有「同语言链接里出现跨语言前缀」才是 bug。
            probe = re.sub(r'<link rel="alternate"[^>]*>', "", page)
            probe = re.sub(r'<a class="lang-link".*?</a>', "", probe, flags=re.S)
            for bad, why in (
                ("__", "未替换的占位符"),
                ("../en/", "同语言链接里出现跨语言前缀"),
                ("en/notes/notes/", "重复的 notes/ 前缀"),
                ("/en/notes/en/", "重复的语言前缀"),
                ('href="en/index.html"', "根层页面用了带语言前缀的相对链接"),
            ):
                if bad in probe:
                    errors.append(f"{target}: 含 {bad!r}（{why}）")
            n += 1

    print(f"\n生成 {n} 个页面（{n // 2} 页 × 中英两套）-> {OUT}")

    # 自定义 404。GitHub Pages 对未匹配路径会用仓库根目录的这个文件，
    # 任意深度都生效 —— 一次覆盖 /notes/、/en/notes/、/glossary.html 这类
    # 手输或旧链接会走的路径（实测它们原本都是 Pages 的通用 404）。
    f404 = OUT / "404.html"
    f404.write_text(page_404("zh", None), encoding="utf-8")
    print(f"  {'404.html':<32} {f404.stat().st_size:>7} 字节")

    if errors:
        print("\n⚠ 自检发现问题：")
        for e in errors:
            print("   " + e)
        return 1
    print("自检通过：无悬空占位符或错误前缀")
    return 0


if __name__ == "__main__":
    # 以前这里只写 main()，自检报了问题退出码仍是 0 —— 单独跑这个脚本时
    # CI / 批处理看不出失败（走 build-site.py 还能靠输出里的 ⚠ 拦住）。
    sys.exit(main())




