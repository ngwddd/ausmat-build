"""给导图注入中英双语支持。

设计要点（读完原脚本后定的）：
  * 原脚本只在 normalize() 里读 name 并算尺寸（_lines/_w/_h），其余代码都读 _lines。
    所以只需在切换语言时：换掉 name → 重算 _lines/_w/_h → render()。
  * 不能直接重跑 normalize()：它内含 `n._open = d < 2`，会把用户已展开/收起的
    状态全部重置。因此单独写 refreshDims()，只更新尺寸，保留 _open。
  * 界面文案（按钮、提示、侧栏）另用 UI 表替换。
  * 导图自身的顶栏语言按钮与站点风格一致，并记住选择（localStorage）。

翻译数据来源：_i18n/mindmap-i18n.json（由子代理翻译后合并），
结构 { "<path>": {"name": "...", "note": "..."} }。
"""

import os
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(os.environ.get("AUSMAT_SITE")
            or (Path(__file__).resolve().parent / "my-site"))
MM = SITE / "notes" / "mindmap.html"
I18N = SITE / "_i18n" / "mindmap-i18n.json"

# 界面文案：中文 → 英文
#
# 2026-10：导图页套上站点外壳后，页头多了一条与其他页相同的站点导航，
# 所以这里要补上导航标签的英文。注意两处曾经撞车、现已分开：
#   导航「考试日程」= Timetable（课程表页），
#   工具栏「考试时间线」= Exam timeline（页内浮层）——
#   原来两者都叫「考试日程」，同一个中文键给不出两个英文，故把按钮改了名。
# 从 site-data.py 取导航标签。mindmap-inject-i18n.py 与它同目录，
# 直接按路径加载，避免依赖当前工作目录。
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("_site_data_for_i18n",
                                     Path(__file__).parent / "site-data.py")
_sd = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_sd)
_SITE_NAV = _sd.NAV

UI = {
    "AUSMAT 学习资料思维导图": "AUSMAT Study Notes — Mind Map",
    "全部展开": "Expand all",
    "全部收起": "Collapse all",
    "适应窗口": "Fit",
    "考试时间线": "Exam timeline",
    "滚轮缩放 · 拖拽平移 · 点击节点展开/收起 · 点击下方科目名展开整科":
        "Scroll to zoom · drag to pan · click a node to expand/collapse · click a subject below to expand it",
    # 时间线按钮的两种状态文案（由 clean-mindmap.py 的 JS 补丁按 LANG 取）
    "返回导图": "Back to map",
    "内容详情": "Details",
    "点击导图中的节点查看说明": "Click a node to see its details",
    "这里会显示该知识点的具体内容。": "Details of the selected topic appear here.",
    "搜索知识点…": "Search topics…",
    "科目（点击展开整科）": "Subjects (click to expand)",
    "（分类目录节点，展开可查看下属知识点）": "(Category node — expand to see the topics under it)",
    # 注意：叶子节点的兜底文案「（具体知识点）」已在 clean-mindmap.py 里改成留空 ——
    # 470/529 个节点没有 note，而 name 本身就是知识点，说这句是噪音。
    # 这里那个长键（…见桌面 Ausmart 文件夹内对应科目目录）已失效，删掉免得误导。
    # 外壳里三处漏翻译的元素（英文模式下扫出来的，与导航「术语表」同一个病根：
    # 元素没标 data-i18n，applyLang 就不会碰它）。
    "学习笔记": "Study Notes",
    "AUSMAT May 2026 · 个人学习笔记": "AUSMAT May 2026 · personal study notes",
    "滚轮缩放 · 拖拽平移 · 点击节点展开/收起 · 点击下方科目名展开整科":
        "Scroll to zoom · drag to pan · click a node to expand/collapse · "
        "click a subject below to expand it",
    "双指缩放 · 拖动平移 · 点击节点展开/收起 · 点击下方科目名展开整科":
        "Pinch to zoom · drag to pan · click a node to expand/collapse · "
        "click a subject below to expand it",
    "首页": "Home",
    # ── 站点导航标签：**从 site-data.NAV 派生，不要手写** ──
    # 原来这七个键是手抄的，注释还写着「与 site-data.NAV 一致」—— 结果加术语表页时
    # 只改了 NAV，这里没跟，英文模式下那一项静默退回中文（用户截图报的）。
    # 派生之后不可能再漂移。缺少 UI["术语表"] 这类键会在构建自检里报出来。
    **{zh: en for _u, zh, en, *_ in _SITE_NAV},
    # fitHint 的提示（本轮新加的元素，当时忘了配翻译）
    "已缩到最小可读比例，再小就看不清了；其余部分请拖动查看":
        "Already at the smallest readable scale; drag to see the rest",
    # ── 标题区副标题（与 clean-mindmap.py 的 MM_META 一致）──
    "五科知识点总览 · 可搜索、可缩放、可展开":
        "All five subjects · searchable, zoomable, expandable",
}

# 术语统一：导图的翻译由多个子代理分头完成，科目名与站点其他页面不一致。
# 这里按站点（school outline 的叫法）为准覆盖。
# ELD → EAL/D：学校官方名是 "English as an Additional Language or Dialect"，
# 站点五科页面用的是 "English (EALD)"，导图原来译成 "ELD English"。
TERM_OVERRIDES = {
    "AUSMAT May 2026 学习资料/ELD 英语": "English (EALD)",
}

# 注入的 JS：语言切换 + 尺寸刷新
PATCH_JS = r"""
// ============ 双语支持（由构建脚本注入）============
// 界面文案表（英文）。下面这行不能带 // 前缀——
// 占位符会被替换成 "var UI_EN = {...}"，若前面有 // 就会把整个声明注释掉，
// 导致运行时报 "UI_EN is not defined"。这个坑真实踩过。
<!--I18N_DATA-->
var I18N = /*I18N_JSON*/;

// 记住当前语言
let LANG = "zh";
try { const s = localStorage.getItem("mm-lang"); if (s) LANG = s; } catch(e) {}

// 只重算文字与尺寸，不动 _open（normalize 会把展开状态重置成 d<2，不能用）
function refreshDims(n, d, color){
  n._depth = d;
  if (n.color) n._color = n.color;
  n._lines = wrapText(n.name, d, MAX_W);
  n._w = Math.max(46, Math.max.apply(null, n._lines.map(l => textW(l, d))) + PAD_X*2 + (n.children && n.children.length ? 16 : 0));
  n._h = n._lines.length > 1 ? NODE_H + (n._lines.length-1)*15 : NODE_H;
  if (n.children) n.children.forEach(c => refreshDims(c, d+1, n._color));
}

// 按路径把 name/note 换成目标语言；源语言存在 _zh 里，便于来回切
function swapLang(n, lang, path, zhData){
  const p = path ? path + "/" + (n._zh ? n._zh.name : n.name) : n.name;
  if (!n._zh){ n._zh = { name: n.name, note: n.note || "" }; }
  const tr = I18N[p] || I18N[path];
  if (lang === "en" && tr && tr.name){
    n.name = tr.name;
    if (tr.note) n.note = tr.note;
  } else {
    n.name = n._zh.name;
    n.note = n._zh.note;
  }
  if (n.children) n.children.forEach(c => swapLang(c, lang, p, zhData));
}

function applyLang(lang, rerender){
  LANG = lang;
  try { localStorage.setItem("mm-lang", lang); } catch(e) {}
  swapLang(DATA, lang, "", null);
  refreshDims(DATA, 0, "#2f6fed");
  DATA._open = true;

  if (rerender){
    // 浏览器标签页也要跟着切。原来 applyLang 换了页内所有文字，
    // 却从没碰 document.title，EN 模式下标签页仍是中文（走查报的）。
    document.title = (lang === "en")
      ? "AUSMAT Study Notes — Mind Map"
      : "AUSMAT 学习资料思维导图";
    // 时间线面板是 buildTimeline 现生成的，不在 [data-i18n] 覆盖范围内，
    // 面板开着时必须重渲染一次，否则切了语言它还是旧语言。
    (function(){
      var tl = document.getElementById("timeline");
      if (tl && tl.classList.contains("show") && typeof buildTimeline === "function") {
        buildTimeline();
      }
    })();
    document.querySelectorAll("[data-i18n]").forEach(function(el){
      const k = el.getAttribute("data-i18n");
      if (lang === "en" && UI_EN[k]) el.textContent = UI_EN[k];
      else el.textContent = k;
    });
    // 站内导航与返回链接的目标也要跟着语言换。
    // 导图只有一份文件（不像其他页中英各一份），但站点是两棵目录树，
    // 所以每个链接同时带 href（中文目标）与 data-href-en（英文目标），
    // 这里按当前语言选用，并把中文目标缓存在 data-href-zh 里以便切回。
    document.querySelectorAll("[data-href-en]").forEach(function(a){
      if (!a.getAttribute("data-href-zh")) a.setAttribute("data-href-zh", a.getAttribute("href"));
      a.setAttribute("href", lang === "en" ? a.getAttribute("data-href-en")
                                           : a.getAttribute("data-href-zh"));
    });
    const si = document.getElementById("search");
    if (si) si.placeholder = lang === "en" ? UI_EN["搜索知识点…"] : "搜索知识点…";
    // placeholder 不是可访问名：读屏软件不会念它。真正要更新的是 aria-label，
    // 文案从元素自己的 data-* 取，省得再往字典里加一份。
    if (si) si.setAttribute("aria-label",
      (lang === "en" ? si.getAttribute("data-al-en") : si.getAttribute("data-al-zh"))
      || (lang === "en" ? "Search topics" : "搜索知识点"));
    document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
    // 顶栏标题结构是 <h1 id="mmTitle">文字<small id="stat">计数</small></h1>。
    // 之前逐节点删除文本节点的写法把 <small> 也弄丢了（stat 变 null，render 报错），
    // 改为整体重建 h1，并把 small 一起重建，最稳。
    //
    // 选择器从 "header h1" 改成 "#mmTitle"：2026-10 导图套上站点外壳后，
    // 页面的第一个 <header> 变成了站点导航条，里面没有 h1，旧选择器会取到 null，
    // 标题与计数就不再跟着语言切换。
    const h1 = document.getElementById("mmTitle");
    if (h1) {
      const old = document.getElementById("stat");
      const cnt = old ? old.textContent : "";
      h1.textContent = lang === "en" ? "AUSMAT Study Notes — Mind Map" : "AUSMAT 学习资料思维导图";
      const sm = document.createElement("small");
      sm.id = "stat";
      sm.textContent = cnt;
      h1.appendChild(sm);
    }
    const btn = document.getElementById("btnLang");
    if (btn) btn.textContent = lang === "en" ? "中文" : "EN";
    const st = document.getElementById("sideTitle");
    const sb = document.getElementById("sideBody");
    if (st) st.textContent = lang === "en" ? "Click a node to see its details" : "点击导图中的节点查看说明";
    if (sb) sb.textContent = lang === "en" ? "Details of the selected topic appear here." : "这里会显示该知识点的具体内容。";
    // 图例标题是 buildLegend() 在 JS 字符串里拼的，不能用 data-i18n 注，
    // 只能在这里跟着语言重写。
    const lh = document.querySelector("#legend h2");
    if (lh) lh.textContent = lang === "en" ? UI_EN["科目（点击展开整科）"] : "科目（点击展开整科）";
    buildLegend();
    const lh2 = document.querySelector("#legend h2");
    if (lh2) lh2.textContent = lang === "en" ? UI_EN["科目（点击展开整科）"] : "科目（点击展开整科）";
  }
  render();
  if (rerender) fit(0.5);
}
"""

def in_js_string(text: str, pos: int) -> bool:
    """判断 pos 处是否落在某个 JS 字符串字面量里。

    做法：从该行/该区域起点数未转义的双引号，奇数即在字符串内。
    必须判断——buildLegend() 里有
        el.innerHTML = "<h2>科目（点击展开整科）</h2>";
    这里的 >…< 是字符串内容而非 HTML 标签，往里插 data-i18n="…"
    会打断 JS 字符串引号，导致整页脚本语法错误、导图完全不渲染。
    """
    start = text.rfind("\n", 0, pos) + 1
    quotes = 0
    i = start
    while i < pos:
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == '"':
            quotes += 1
        i += 1
    return quotes % 2 == 1


def inject_attr(text: str, zh: str) -> tuple[str, bool]:
    """在「非 JS 字符串、且不在 <head> 内」的 >zh< 处插入 data-i18n 属性。

    两处必须排除：
      1. JS 字符串字面量 —— buildLegend() 里 el.innerHTML = "<h2>科目…</h2>"
         的 >…< 是字符串内容，插属性会打断引号、整页脚本语法错误。
      2. <head> 区域 —— 给 <title> 挂 data-i18n 之后，applyLang 会用长标题
         通过 textContent 写进 <title>，还把元数据元素当正文处理。
    """
    head_end = text.find("</head>")
    needle = f">{zh}<"
    idx = 0
    while True:
        i = text.find(needle, idx)
        if i < 0:
            return text, False
        in_head = head_end >= 0 and i < head_end
        if not in_head and not in_js_string(text, i):
            return text[:i] + f' data-i18n="{zh}"{text[i:]}', True
        idx = i + 1


def main() -> None:
    # 三种模式：
    #   默认              —— 就地处理 MM 文件（方便单独调试）
    #   --stdout          —— 从 stdin 读入 HTML，注入后写到 stdout
    #   --in F --out F    —— 从文件读、写到文件（构建脚本用这个）
    #
    # 2026-10：构建脚本改用 --in/--out。此前用 --stdout 让父进程把 218KB 通过
    # 管道喂进来，结果父子进程双双 0% CPU 卡死十几分钟——管道传递在这个环境里
    # 不可靠。文件传递没有这个问题，中途还能随时查看内容。
    argv = sys.argv[1:]
    use_stdout = "--stdout" in argv
    in_path = out_path = None
    if "--in" in argv:
        in_path = Path(argv[argv.index("--in") + 1])
    if "--out" in argv:
        out_path = Path(argv[argv.index("--out") + 1])

    if not I18N.exists():
        raise SystemExit(f"缺少翻译文件：{I18N}（等子代理翻译完成后再跑）")
    tr = json.loads(I18N.read_text(encoding="utf-8"))
    # 应用术语覆盖，保证与站点其他页面一致
    applied = 0
    for path, name in TERM_OVERRIDES.items():
        if path in tr and tr[path].get("name") != name:
            tr[path]["name"] = name
            applied += 1
    if applied:
        print(f"术语统一覆盖 {applied} 条", file=sys.stderr)

    filled = sum(1 for v in tr.values() if v.get("name"))
    print(f"翻译条目: {len(tr)}，其中已填 name: {filled}", file=sys.stderr)
    if filled < len(tr):
        print(f"⚠ 有 {len(tr)-filled} 条未翻译，将保留中文原文", file=sys.stderr)

    t = (in_path.read_text(encoding="utf-8") if in_path is not None
         else sys.stdin.read() if use_stdout
         else MM.read_text(encoding="utf-8"))

    # 0. 先撤销之前几版错误注入留下的痕迹（保护性：即使旧文件已被污染也能修回）
    t = re.sub(r'<h2 data-i18n="[^"]*">([^<]*)</h2>', r'<h2>\1</h2>', t)
    t = re.sub(r'(<title) data-i18n="[^"]*"', r"\1", t)       # <head> 内的元数据不该带此属性
    t = re.sub(r'(<meta[^>]*?) data-i18n="[^"]*"', r"\1", t)
    t = re.sub(r'(el\.innerHTML\s*=\s*"[^"]*?) data-i18n="[^"]*"', r"\1", t)

    # 1. 界面文案包一层 data-i18n —— 只处理真正的标签内容位置。
    #    必须跳过 JS 字符串里的同名文案（见 in_js_string 的说明）。
    for zh in UI:
        if zh not in t or f'data-i18n="{zh}"' in t:
            continue
        t, ok = inject_attr(t, zh)

    # 2. 注入语言按钮
    if 'id="btnLang"' not in t:
        t = t.replace('<button id="btnTimeline"',
                      '<button id="btnLang" title="切换语言 / Switch language">EN</button>\n'
                      '    <button id="btnTimeline"', 1)

    # 3. 注入 JS —— 必须插在 IIFE 之前。
    #    源文件结尾是：
    #        /* ============ 启动 ============ */
    #        (function init(){
    #          ...
    #        })();
    #    早期版本搜 "function init(){" 并直接插在它前面，结果插进了
    #    "(function " 与 "init(){" 之间，生成 "(function <注入代码> function init(){"
    #    —— 语法错误，整页脚本不执行。
    if "function applyLang(" not in t:
        js = PATCH_JS.replace("/*I18N_JSON*/", json.dumps(tr, ensure_ascii=False))
        js = js + "\n/* 搜索无结果时说一句话。原来只有输入框变黄，没有任何文字，\n   低分走查实测「不知道是没搜到还是搜索坏了」。\n   这里不去改搜索函数本身（它在上游源文件里），而是观察 DOM 变化。 */\n(function () {\n  function init() {\n    var input = document.getElementById('search');\n    if (!input) return;\n    var tip = document.createElement('div');\n    tip.id = 'noHitTip';\n    tip.style.cssText = 'margin:6px 0 0;padding:7px 12px;border-radius:6px;'\n      + 'font-size:.82rem;display:none;color:var(--warn);background:var(--warn-bg);';\n    var box = document.getElementById('canvasWrap') || input.parentNode;\n    box.appendChild(tip);\n    function upd() {\n      var q = (input.value || '').trim();\n      var gone = document.querySelectorAll('g.node-g').length === 0;\n      var show = q.length > 0 && gone;\n      tip.textContent = show\n        ? (LANG === 'en' ? 'No topic matches \\u201c' + q + '\\u201d.'\n                         : '\\u6ca1\\u6709\\u5339\\u914d\\u300c' + q + '\\u300d\\u7684\\u77e5\\u8bc6\\u70b9\\u3002')\n        : '';\n      tip.style.display = show ? 'block' : 'none';\n    }\n    input.addEventListener('input', function () { setTimeout(upd, 80); });\n    input.addEventListener('keyup', function () { setTimeout(upd, 80); });\n    setTimeout(upd, 500);\n  }\n  if (document.readyState === 'loading') {\n    document.addEventListener('DOMContentLoaded', init);\n  } else { init(); }\n})();\n"
        js = js.replace("<!--I18N_DATA-->", "var UI_EN = " + json.dumps(UI, ensure_ascii=False) + ";")
        anchor = "(function init(){"
        if anchor not in t:
            raise SystemExit("未找到启动锚点 '(function init(){'，注入中止（避免写坏文件）")
        t = t.replace(anchor, js + "\n" + anchor, 1)

    # 4. 按记忆的语言初始化 —— 必须放在 IIFE **之后**。
    #    IIFE 紧跟 var UI_EN / var I18N 声明之后立即执行；在它内部调用 applyLang 时，
    #    那两个 var 虽已提升但尚未赋值（undefined），会抛 "UI_EN is not defined"。
    #    放在 IIFE 之后则声明都已求值完毕。
    t = t.replace("  buildLegend(); buildTimeline(); render(); initialView();\n"
                  "  if (LANG === 'en') applyLang('en', true);",
                  "  buildLegend(); buildTimeline(); render(); initialView();")   # 清掉早期版本的错误位置
    if "if (LANG === 'en') applyLang('en', true);\n</script>" not in t:
        t = t.replace("})();\n</script>",
                      "})();\n\n"
                      "// 启动完成后按记忆的语言再应用一次。\n"
                      "// 不能放进上面的 IIFE：那时 var UI_EN / var I18N 还未赋值。\n"
                      "if (LANG === 'en') applyLang('en', true);\n"
                      "</script>", 1)

    # 5. 绑定按钮
    if 'getElementById("btnLang").onclick' not in t:
        t = t.replace('document.getElementById("btnFit").onclick = function(){ fit(); };',
                      'document.getElementById("btnFit").onclick = function(){ fit(); };\n  '
                      'document.getElementById("btnLang").onclick = function(){ applyLang(LANG === "en" ? "zh" : "en", true); };', 1)

    # 6. 节点计数小字是 render() 里动态拼的中文，也要跟着语言走。
    #    改法：把那段拼接换成走一个语言感知的函数 statText()。
    if "function statText(" not in t:
        t = t.replace(
            'document.getElementById("stat").textContent = "　共 " + nodes.length + " 个可见节点 · " + DATA.children.length + " 个科目";',
            'document.getElementById("stat").textContent = statText(nodes.length, DATA.children.length);', 1)

    # 6b. 注入 statText 定义。要放在 IIFE 之前，且必须在 LANG 声明之后被调用时已有定义——
    #     函数声明会提升，所以放哪里都行，但为清晰起见与其它注入代码放一起。
    if "function statText(" not in t.split("(function init(){")[0]:
        stat_fn = ('function statText(n, s){\n'
                   '  return LANG === "en"\n'
                   '    ? "  " + n + " visible nodes · " + s + " subjects"\n'
                   '    : "　共 " + n + " 个可见节点 · " + s + " 个科目";\n'
                   '}\n\n')
        t = t.replace("// ============ 双语支持（由构建脚本注入）============",
                      "// ============ 双语支持（由构建脚本注入）============\n" + stat_fn, 1)

    # 7. 写盘前做 JS 语法自检。
    #    之前几版都是「注入成功但脚本语法被破坏」——页面白屏，靠人工看才发现。
    #    这道检查真的拦住过一次（我把注释前缀误写成 #），务必保留。
    m = re.search(r"<script>([\s\S]*)</script>", t)
    if m:
        # 走临时文件而不是 stdin 管道：157KB 通过管道喂 node 同样会死锁。
        # 临时文件在 finally 里删掉。
        tmp = Path(tempfile.gettempdir()) / "_mm_check.js"
        try:
            tmp.write_text(m.group(1), encoding="utf-8")
            chk = subprocess.run(["node", "--check", str(tmp)],
                                 capture_output=True, text=True, encoding="utf-8")
            if chk.returncode != 0:
                raise SystemExit("注入后 JS 语法检查失败，已中止写盘：\n" + (chk.stderr or "")[:600])
            print("  JS 语法检查: 通过", file=sys.stderr)
        finally:
            tmp.unlink(missing_ok=True)
    else:
        raise SystemExit("未找到 <script> 块，中止")

    if out_path is not None:
        out_path.write_text(t, encoding="utf-8")
        print(f"已注入 -> {out_path}", file=sys.stderr)
    elif use_stdout:
        sys.stdout.write(t)
        print(f"已注入（stdout 模式）", file=sys.stderr)
    else:
        MM.write_text(t, encoding="utf-8")
        print(f"已写入 {MM}", file=sys.stderr)

    print(f"  界面文案 {len(UI)} 条", file=sys.stderr)
    print(f"  节点翻译 {filled} 条", file=sys.stderr)
    print(f"  applyLang 已定义: {'function applyLang(' in t}", file=sys.stderr)
    print(f"  按钮已绑定: {'btnLang\").onclick' in t}", file=sys.stderr)


if __name__ == "__main__":
    main()


