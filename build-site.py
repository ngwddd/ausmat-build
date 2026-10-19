"""总构建脚本 —— 按正确顺序生成整站。

为什么需要它：
  site-build.py 会清空 notes/ 目录再重建，而导图是 clean-mindmap.py 生成的。
  如果顺序反了（先建站、后清洗），导图会被删掉，导航里的「知识导图」直接 404。
  这个坑真实发生过一次。跑这个脚本就不会踩。

顺序：
  1. site-build.py            清空并重建 notes/ 与 en/
  2. clean-mindmap.py         补回导图（第 1 步把它删了）
  3. advising-build/build.py  补回升学自检（第 1 步把它也删了）

2026-10 补第 3 步：此前这个脚本只补了导图，没补升学自检，于是每跑一次
构建，notes/advising/ 下八个文件就被删一次（advising-rules.js、courses.js、
history.js、index.html、en.html、两个跳转桩、README）。当时是靠 git status
发现八个 D 才察觉的——页面上不会报错，只是那个工具悄悄 404。

第 3 步只重生成它自己的产物；notes/advising/README.md 不在它的输出里，
要单独用 git 还原。
"""

import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Windows 控制台默认是 GBK，脚本里印的 ▶ / ✓ 会直接抛 UnicodeEncodeError
# （2026-10 实际踩到：整个构建在第一步就崩了）。钉死 UTF-8。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

D = Path(__file__).resolve().parent                      # 本文件所在目录 = 构建目录
SITE = Path(os.environ.get("AUSMAT_SITE") or (D / "my-site"))   # 站点输出目录
PY = r"C:\Program Files\Python314\python.exe"


def _site_url() -> str:
    """站点根 URL，形如 https://ngwddd.github.io/ausmat-guide/。

    sitemap 与 robots 里必须是绝对地址。和 404 页的路径前缀一样，从 git remote
    反推，免得下次改仓库名又来手工找这两个文件。
    """
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=str(SITE),
                             capture_output=True, text=True, encoding="utf-8",
                             timeout=10).stdout.strip()
    except Exception:
        url = ""
    m = re.search(r"[/:]([^/:]+)/([^/]+?)(?:\.git)?/?$", url)
    return f"https://{m.group(1)}.github.io/{m.group(2)}/" if m else \
        "https://ngwddd.github.io/ausmat-guide/"


SITE_URL = _site_url()
TODAY = datetime.date.today().isoformat()


def run(script: str) -> int:
    print(f"\n{'='*66}\n▶ {script}\n{'='*66}")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY, str(D / script)], cwd=str(D), capture_output=True,
                       text=True, encoding="utf-8", env=env)
    lines = (r.stdout or "").strip().splitlines()

    # ⚠ / ✗ 行必须**单独捞出来全文显示**，不能混在"最后 6 行"里。
    # 原因：这些脚本是靠字符串锚点打补丁的，锚点写错时那一处修改会被静默跳过，
    # 而页面照常生成、不报任何错。2026-10 的两次实际事故（窗口缩放补丁、
    # NAME_FIXES 顺序）都是这样漏过去的 —— 警告印出来了，但淹在几十行输出里没人看见。
    warns = [l for l in lines if "⚠" in l or "✗" in l]

    for line in lines[-6:]:
        if line in warns:
            continue
        print("  " + line)
    if warns:
        print("  ── 警告 ──────────────────────────────────")
        for w in warns:
            print("  " + w)
        print("  ↑ 锚点未命中＝那一处修改没有生效，必须修好再继续")

    if r.returncode != 0:
        print("  ⚠ stderr:", (r.stderr or "")[-400:])

    # 脚本自身非零退出，或印出了任何警告，都算失败
    return r.returncode | (1 if warns else 0)


def main() -> int:
    rc = 0

    # 1. 建站（这一步会清空 notes/）
    rc |= run("site-build.py")

    # 2. 补回导图（site-build.py 清空 notes/ 时把它删了）
    rc |= run("clean-mindmap.py")

    # 3. 补回升学自检（同样被清掉；漏掉这一步会让那个工具静默 404）
    rc |= run(os.path.join("advising-build", "build.py"))

    # 3b. 升学自检的设计文档。build.py 的输出清单里没有它，所以每跑一次构建
    #     它就被删一次，此前只能靠手工 git checkout 补。源放在 advising-build/src/，
    #     与 zh-copy.py / engine.js 同层，改文档改那份。
    readme_src = D / "advising-build" / "src" / "README.md"
    readme_dst = SITE / "notes" / "advising" / "README.md"
    if readme_src.exists():
        readme_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(readme_src, readme_dst)
        print(f"  已拷回 notes/advising/README.md（{readme_dst.stat().st_size} 字节）")
    else:
        print("  ⚠ 缺 advising-build/src/README.md，升学自检文档不会被发布")
        rc |= 1

    # 4. 后处理：表格滚动容器 + 站点地图
    #
    # 为什么套容器放在这里、而不是各自的生成脚本里：表是三个脚本各生各的
    # （site-build.py 8 处、advising build.py 4 处、导图 2 处），只改其中一处
    # 是迟早会漏的事。统一过一遍，以后新加页面也不用再记得。
    #
    # 例外：导图与升学自检的表格是脚本里拼出来的字符串，正则有可能改到 JS 里；
    # 且它们实测最宽 346px，本来就不溢出 390px 的手机视口，所以不碰。
    print(f"\n{'='*66}\n▶ 后处理：表格滚动容器 / sitemap / robots\n{'='*66}")
    import re as _re2

    skip = {"404.html", "notes/mindmap.html"}
    # 导图的两张表是在 JS 字符串里拼出来的，正则套容器会改到脚本里，所以跳过。
    # 升学自检的表虽然也是脚本生成的页面，但它们是静态 HTML，可以套。
    n_tables = 0
    for f in sorted(SITE.glob("**/*.html")):
        rel_f = f.relative_to(SITE).as_posix()
        if rel_f in skip:
            continue
        h = f.read_text(encoding="utf-8")
        before = len(_re2.findall(r"<table\b", h))
        if not before:
            continue
        h2 = _re2.sub(r"(<table\b[^>]*>.*?</table>)", r'<div class="tw">\1</div>',
                      h, flags=_re2.S)
        if len(_re2.findall(r"<table\b", h2)) != before:
            print(f"  ✗ {rel_f}：套容器后表格数变了，已跳过")
            rc |= 1
            continue
        f.write_text(h2, encoding="utf-8")
        n_tables += before
    print(f"  已给 {n_tables} 张表套上横向滚动容器")

    # 站点地图与 robots。之前两者都不存在 —— 站是公开的，收录全靠运气。
    # 语言成对的页面在 sitemap 里互相标 alternate，和页面里的 hreflang 对齐。
    zh_pages = ["index.html", "notes/timetable.html", "notes/subjects.html",
                "notes/glossary.html", "notes/timeline.html", "notes/papers.html",
                "notes/about.html"]
    pairs = [(p, "en/" + p) for p in zh_pages]
    pairs.append(("notes/advising/index.html", "notes/advising/en.html"))
    solo = ["notes/mindmap.html"]

    def _abs(rel_url: str) -> str:
        return SITE_URL + rel_url

    # lastmod 只在页面内容真的变了那天才前进。
    #
    # 原来 17 条 URL 全写构建当天 —— 内容一个字没改，重新构建一次 sitemap.xml
    # 就整个变一遍，git diff 里全是噪声。
    #
    # 先用 git 提交日期试过，不行：构建发生在提交之前，提交完再构建一次，
    # 日期又整体后移一天，越滚越乱。改成记内容哈希：状态文件放在仓库外面
    # （不跟着站点发布），某页的 sha256 与上次相同就沿用上次的日期。
    STATE = D / ".sitemap-state.json"
    try:
        _state = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        _state = {}

    def _digest(rel_url: str) -> str:
        p = SITE / rel_url
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else ""

    def _lastmod(rel_url: str) -> str:
        prev = _state.get(rel_url)
        h = _digest(rel_url)
        if isinstance(prev, dict) and prev.get("h") == h and h:
            return prev.get("d", TODAY)
        return TODAY

    rows = []
    _all_urls = []
    for zh_u, en_u in pairs:
        for me, other, lang_other in ((zh_u, en_u, "en"), (en_u, zh_u, "zh-CN")):
            _all_urls.append(me)
            rows.append(
                "  <url><loc>%s</loc><lastmod>%s</lastmod>"
                '<xhtml:link rel="alternate" hreflang="%s" href="%s"/></url>'
                % (_abs(me), _lastmod(me), lang_other, _abs(other)))
    for u in solo:
        _all_urls.append(u)
        rows.append("  <url><loc>%s</loc><lastmod>%s</lastmod></url>"
                    % (_abs(u), _lastmod(u)))

    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
               '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
               + "\n".join(rows) + "\n</urlset>\n")
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    # 记下这一轮的哈希与日期，下一轮用它判断「内容变了没有」。
    # 状态文件放在仓库目录之外（D 是上一级），不会被发布到站点上。
    try:
        STATE.write_text(json.dumps(
            {u: {"h": _digest(u), "d": _lastmod(u)} for u in _all_urls},
            ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ sitemap 状态文件写入失败（不影响发布）：{e}")

    robots = ("User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % SITE_URL)
    (SITE / "robots.txt").write_text(robots, encoding="utf-8")
    print(f"  sitemap.xml：{len(rows)} 条 URL · robots.txt 已更新")

    # 4. 自检
    print(f"\n{'='*66}\n▶ 产物自检\n{'='*66}")

    # 注意：函数里出现任何 `import X`，X 就成了**整个函数**的局部名，前半段
    # 用到 X 会抛 UnboundLocalError。所以公共模块一律在文件顶部 import；
    # 这里只留带别名的（_re / _re2 / _ET），它们不遮蔽原名。
    need = [
        "index.html",
        # 自定义 404：Pages 对任意未匹配路径都用它，一次覆盖
        # /notes/、/en/notes/、/glossary.html 这类手输或旧链接的路径。
        "404.html",
        "notes/timetable.html", "notes/timeline.html",
        "notes/subjects.html", "notes/papers.html", "notes/glossary.html", "notes/mindmap.html",
        "notes/about.html",
        "en/index.html", "en/notes/timetable.html", "en/notes/timeline.html",
        "en/notes/subjects.html", "en/notes/papers.html", "en/notes/glossary.html",
        "en/notes/about.html",
        # 升学自检：被 site-build.py 清掉、由第 3 步补回，所以必须在这里点名
        "notes/advising/index.html", "notes/advising/en.html",
        "notes/advising/advising-rules.js", "notes/advising/courses.js",
        "notes/advising/history.js",
        "assets/advising.js", "assets/advising.css",
    ]
    missing = [p for p in need if not (SITE / p).exists()]
    print(f"  期望页面 {len(need)} 个")
    if missing:
        print("  ✗ 缺失：")
        for m in missing:
            print("      " + m)
        rc |= 1
    else:
        print("  ✓ 全部存在")

    # 导图里的节点数与个人信息自检
    mm = SITE / "notes/mindmap.html"
    if mm.exists():
        t = mm.read_text(encoding="utf-8")
        # 这里以前有一行 `import re`。python 会把函数里任何位置的 import 都当成
        # 整个函数的**局部名**，于是本函数前半段（_lastmod 之类）用到 re 时抛
        # UnboundLocalError —— 被 `except Exception` 吞掉，静默退回默认值。
        # re 在文件顶部已经 import 过，这里直接用全局的。
        nodes = len(re.findall(r'name:\s*"', t))
        leaks = sum(len(re.findall(p, t, re.I)) for p in
                    (r"WEN\s*CHENGZHI", r"Sunwen|Sunway", r"学生：", r"src:\s*\""))
        print(f"  导图：{nodes} 个节点，个人信息残留 {leaks} 处  {'✓' if leaks == 0 else '✗'}")
        if leaks:
            rc |= 1
        # 节点说明必须真的挂上。注入靠路径字符串匹配，路径一改就静默落空
        # （改名、补前缀那两次都踩过），所以这里点名核对条数。
        m = re.search(r"var MM_NOTES = (\{.*?\});\n", t, re.S)
        if m:
            n_notes = len(json.loads(m.group(1)))
            print(f"  导图节点说明：{n_notes} 条")
            if n_notes < 400:
                print("  ✗ 节点说明条数异常偏低，注入可能落空")
                rc |= 1

    # 字面 Markdown 星号。站点不做 Markdown 解析，文案里的 `**` 会原样显示。
    # 首页的「索引」与真题页的说明都漏出过字面星号 —— 已踩两次。
    # 修法是 site-build.py 里的 md_inline()，这里守住不让它再回来。
    #
    # 只导入带别名的（_re），不重新导入 json/glob —— 见上面那段说明。
    import glob
    import re as _re
    star_pages = []
    for f in SITE.rglob("*.html"):
        if "node_modules" in f.parts:
            continue
        body = _re.sub(r"(?s)<script.*?</script>|<style>.*?</style>",
                       "", f.read_text(encoding="utf-8", errors="ignore"))
        n = len(_re.findall(r"\*\*", body))
        if n:
            star_pages.append((f.relative_to(SITE).as_posix(), n))
    if star_pages:
        print("  ✗ 页面上有字面 Markdown 星号（文案没走 md_inline）：")
        for p, n in star_pages[:6]:
            print(f"      {p}  {n} 处")
        rc |= 1
    else:
        print("  字面 Markdown 星号：0 处  ✓")

    # 导航顺序必须全站一致。NAV 是唯一来源，但页面是按语言分文件生成的，
    # 曾经出现过某一棵树用了本地残留的旧 NAV（英文页指回中文树）。
    orders = {}
    for f in glob.glob(str(SITE / "**/*.html"), recursive=True):
        if "node_modules" in f:
            continue
        h = _re.sub(r"(?s)<script.*?</script>", "", Path(f).read_text(encoding="utf-8", errors="ignore"))
        m = _re.search(r"(?s)<nav>(.*?)</nav>", h)
        if m:
            key = tuple(_re.findall(r">([^<>]+)</a>", m.group(1)))
            orders.setdefault(key, []).append(Path(f).relative_to(SITE).as_posix())
    zh_orders = [k for k in orders if k and k[0] == "首页"]
    en_orders = [k for k in orders if k and k[0] == "Home"]
    print(f"  导航：{len(zh_orders)} 种中文顺序、{len(en_orders)} 种英文顺序"
          f"  {'✓' if len(zh_orders) == 1 and len(en_orders) == 1 else '✗ 不一致'}")
    if len(zh_orders) != 1 or len(en_orders) != 1:
        for k, files in orders.items():
            print("      " + " · ".join(k) + "   ← " + ", ".join(files[:3]))
        rc |= 1

    # ── 静态资源与站点地图 ───────────────────────────────────────────────
    # KaTeX：站里一处公式都没有，但它曾是全站最重的一个请求（266KB JS +
    # 24KB CSS，占每页传输的 90%）。2026-10 整段下线，这里守住不让它回来。
    katex_hits = [f.relative_to(SITE).as_posix() for f in SITE.rglob("*.html")
                  if "node_modules" not in f.parts
                  and "katex" in f.read_text(encoding="utf-8", errors="ignore").lower()]
    print(f"  KaTeX 残留：{len(katex_hits)} 个页面  {'✓' if not katex_hits else '✗'}")
    if katex_hits:
        print("      " + ", ".join(katex_hits[:6]))
        rc |= 1

    # 表格滚动容器：手机宽 390px，日程表天然要 530px，没有容器就是整页横向溢出。
    unwrapped = []
    for f in SITE.rglob("*.html"):
        rel_f = f.relative_to(SITE).as_posix()
        if "node_modules" in f.parts or rel_f in {"404.html", "notes/mindmap.html"}:
            continue
        h = f.read_text(encoding="utf-8", errors="ignore")
        n_tbl = len(_re.findall(r"<table\b", h))
        n_tw = len(_re.findall(r'<div class="tw"><table\b', h))
        if n_tbl != n_tw:
            unwrapped.append(f"{rel_f}（表 {n_tbl} / 容器 {n_tw}）")
    print(f"  表格滚动容器：{'全部套上 ✓' if not unwrapped else '✗ ' + '; '.join(unwrapped[:4])}")
    if unwrapped:
        rc |= 1

    # sitemap 必须是合法 XML，且条数对得上；robots 要指到它。
    import xml.etree.ElementTree as _ET
    sm_path = SITE / "sitemap.xml"
    rb_path = SITE / "robots.txt"
    if not sm_path.exists() or not rb_path.exists():
        print("  ✗ 缺 sitemap.xml 或 robots.txt")
        rc |= 1
    else:
        try:
            root = _ET.parse(sm_path).getroot()
            n_url = len(root)
            bad = [u.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                   for u in root
                   if not (u.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc") or "")
                   .startswith(SITE_URL)]
            rb = rb_path.read_text(encoding="utf-8")
            ok = n_url > 0 and not bad and (SITE_URL + "sitemap.xml") in rb
            print(f"  sitemap.xml：{n_url} 条 · robots 指向正确  {'✓' if ok else '✗'}")
            if not ok:
                print(f"      URL 不符 {len(bad)} 条；robots 片段 {rb[-80:]!r}")
                rc |= 1
        except Exception as e:
            print(f"  ✗ sitemap.xml 解析失败：{e}")
            rc |= 1

    # 导图的英文词典已外置：页面里必须是 I18N = null，且旁边有这个文件。
    mm = SITE / "notes/mindmap.html"
    i18n_js = SITE / "notes/mindmap-i18n.js"
    if mm.exists():
        h = mm.read_text(encoding="utf-8", errors="ignore")
        # 原来这里写的是 h.replace(" ", " ") —— 两个参数都是空格，等于什么都没做。
        # 真正想拦的是「I18N 还以内联对象的形式留在页面里」，直接用正则数。
        inline_i18n = len(_re.findall(r"var I18N\s*=\s*\{", h))
        externalised = "var I18N = null" in h and inline_i18n == 0
        ok = externalised and i18n_js.exists()
        print(f"  导图英文词典外置：{'✓' if ok else '✗'}"
              f"（页面内联 {inline_i18n} 处，外部文件 {'有' if i18n_js.exists() else '无'}）")
        if not ok:
            rc |= 1

    # 首页卡片写的「N 条规则」必须等于规则库实际条数。
    # 这个数字以前是硬编码在文案里的，规则一改就会撒谎。
    rules_js = SITE / "notes" / "advising" / "advising-rules.js"
    if rules_js.exists():
        r = subprocess.run(
            ["node", "-e",
             "global.window={};eval(require('fs').readFileSync(process.argv[1],'utf8'));"
             "console.log((window.ADVISING.rules||[]).length)", str(rules_js)],
            capture_output=True, text=True, encoding="utf-8", timeout=60)
        actual = (r.stdout or "").strip()
        idx = (SITE / "index.html").read_text(encoding="utf-8", errors="ignore")
        shown = re.search(r"·\s*(\d+)\s*条规则", idx)
        if actual.isdigit() and shown:
            ok = int(actual) == int(shown.group(1))
            print(f"  首页规则数：写 {shown.group(1)} / 实际 {actual}  {'✓' if ok else '✗'}")
            if not ok:
                print("      改 site-data.py 里的 ADVISING_RULE_COUNT 再重跑")
                rc |= 1
        else:
            print(f"  首页规则数：无法核对（actual={actual!r}，shown={bool(shown)}）")
            rc |= 1

    print(f"\n{'构建完成' if rc == 0 else '构建有问题，见上'}　→ {SITE}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
