# -*- coding: utf-8 -*-
"""Build the merged advising pages: one tool, two languages, sharing the site shell.

What this does and why:

  The site pairs every page with a translation and switches between them with a
  plain link, no JavaScript. Its stylesheet already hides `.en` or `.zh` by
  reading `data-lang` on the root element. So the shell is generated twice, with
  the UI labels baked into the markup in both languages, and the engine picks up
  the language from `document.documentElement.dataset.lang`.

  The engine is NOT rewritten here. It is extracted verbatim from the shipped
  page and then adjusted by targeted replacements, each anchored on an exact
  string. A regex that rewrites a whole function would eventually swallow
  something adjacent — that has already happened once in this project, when a
  non-greedy pattern ate the rule compiler.

  Rule prose is treated as data: Chinese advice is injected into the catalog as a
  `zh` field per rule, so the engine resolves text the same way for both
  languages and a translator never touches engine code.

Outputs (into the site):
  notes/advising/index.html          Chinese
  notes/advising/en.html             English
  notes/advising/advising-rules.js   catalog, now bilingual
  assets/advising.js                 engine, language-aware
  assets/advising.css                tool-only styles, palette from the site
"""

import os
import pathlib
import re
import importlib.util

# 站内导航从 site-data.py 读，不在这里另写一份。原先这里硬编码 7 项，
# 站点后来加「真题与资料」时漏了这页，从升学工具出不去真题页
# （低分学生走查发现：其他 15 页都是 8 项，只有这页 7 项）。
_SD_PATH = pathlib.Path(__file__).resolve().parent.parent / "site-data.py"
_SD = importlib.util.spec_from_file_location("site_data", _SD_PATH)
site_data = importlib.util.module_from_spec(_SD)
_SD.loader.exec_module(site_data)

# The copy file has a hyphen in its name, so it cannot be imported by name.
_spec = importlib.util.spec_from_file_location(
    "zh_copy", pathlib.Path(__file__).parent / "src" / "zh-copy.py"
)
copy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(copy)

# Roadmaps and pathways live in their own module next to it, for the same reason.
_spec2 = importlib.util.spec_from_file_location(
    "modules", pathlib.Path(__file__).parent / "src" / "modules.py"
)
modules = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(modules)


def replace_once(text, old, new, label):
    """Replace exactly one occurrence, or stop the build.

    Anchored replacement with a count assertion. An interval replacement ("swap
    everything between A and B") was tried early in this project and deleted two
    unrelated things; a substring replace without a count silently did nothing
    when the anchor had drifted across multiple lines. Both failure modes are
    invisible in the output, so the count is checked every time.
    """
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"replacement '{label}' matched {count} times, expected exactly 1")
    return text.replace(old, new, 1)

SRC = pathlib.Path(__file__).resolve().parent / "src"
SITE = pathlib.Path(os.environ.get("AUSMAT_SITE")
                    or (pathlib.Path(__file__).resolve().parent.parent / "my-site"))
TOOL = SITE / "notes" / "advising"
ASSETS = SITE / "assets"

# ── pages: language only ────────────────────────────────────────────────────
# There used to be a second dimension here: an enrolled reader and a "guest".
# Measured before removing it — the two differed by exactly three things: the
# guest page had no assessment tracker, no previous-intake field, and no
# still-deciding/funding pair. All three have since been deleted as dead weight,
# and every one of the 30 rules already listed both modes. So after those
# deletions the two pages were byte-identical, and a mode that changes nothing is
# a mode that only costs a reader a click and costs this build four pages.
#
# index.html keeps its name so existing links and bookmarks survive.
PAGES = {
    ("zh",): "index.html",
    ("en",): "en.html",
}

# There used to be a MODES table here tagging each rule with the modes it applied
# in. Every rule listed both modes, so the tag filtered nothing, and with the
# guest pages gone there is no second mode left to filter by. The tag, the
# injection loop that wrote it, and the engine's mode filter are all removed
# together — a rule that cannot vary by mode should not claim to.


def js_string(text):
    """Escape for a single-quoted JS string, joined onto one line."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


# ── 1. catalog: inject the Chinese advice per rule ──────────────────────────
def build_catalog():
    source = (SRC / "advising-rules.current.js").read_text(encoding="utf-8")
    injected = 0
    missing = []

    # ── the roadmap and opportunities tables ─────────────────────────────────
    # Injected as JS object literals at their markers. The point of a marker is
    # that a missing marker fails the build: a silently un-injected table would
    # make two rules go quiet and nothing downstream would notice.
    import json as _json
    fields = ["Medicine", "Dentistry", "Law", "Engineering", "Computer Science",
              "Business", "Psychology", "Nursing", "Architecture", "Sciences",
              "Humanities", "Education"]

    roadmap = {}
    for field in fields:
        entry = modules.ROADMAP.get(field)
        if entry is None:
            raise SystemExit(f"roadmap: no entry for the form field {field!r}")
        roadmap[field] = {lang: entry[lang] for lang in ("en", "zh")}
    extra = sorted(set(modules.ROADMAP) - set(fields))
    if extra:
        raise SystemExit(f"roadmap: entries for fields the form does not offer: {extra}")

    roadmap_marker = "  const ROADMAP_MARKER = null // replaced at build time"
    if source.count(roadmap_marker) != 1:
        raise SystemExit(
            f"roadmap marker matched {source.count(roadmap_marker)} times, expected 1")
    source = source.replace(
        roadmap_marker,
        "  const roadmap = " + _json.dumps(roadmap, ensure_ascii=False, indent=2
                                           ).replace("\n", "\n  "),
        1)

    opportunities_marker = "  const OPPORTUNITIES_MARKER = null // replaced at build time"
    if source.count(opportunities_marker) != 1:
        raise SystemExit(
            f"opportunities marker matched {source.count(opportunities_marker)} times, expected 1")
    source = source.replace(
        opportunities_marker,
        "  const opportunities = " + _json.dumps(
            modules.OPPORTUNITIES, ensure_ascii=False, indent=2).replace("\n", "\n  "),
        1)

    # Both tables must reach the public surface, or the helpers cannot read them.
    source = replace_once(source, "    matrix,\n",
                          "    matrix,\n    roadmap,\n    opportunities,\n",
                          "roadmap and opportunities exported")

    for rule_id, zh in copy.ADVICE.items():
        start = source.find(f"id: '{rule_id}'")
        if start < 0:
            missing.append(rule_id)
            continue
        adv = source.find("      advice:", start)
        if adv < 0:
            missing.append(rule_id + " (no advice field)")
            continue
        src_at = source.find("\n      source:", adv)
        if src_at < 0:
            missing.append(rule_id + " (no source field)")
            continue
        # Keep any line comment attached to the advice field, drop the rest:
        # the English text is already there, the Chinese is what we add.
        block = source[adv:src_at]
        en_body = re.sub(r"^      advice:\s*", "", block)
        en_body = re.sub(r"\n\s*//.*$", "", en_body, flags=re.M)
        en_body = en_body.rstrip().rstrip(",").rstrip()
        zh_js = "'" + js_string(zh) + "'"
        # Guard on the field name so a Chinese string containing ' is still valid.
        replacement = f"      advice: {en_body},\n      zh: {zh_js},"
        source = source[:adv] + replacement + source[src_at:]
        injected += 1

    # perf-prior-intake-underperformed was removed from the catalog outright.
    # It read record.priorIntake and record.priorResults; the free-text box
    # that supplied the latter was deleted as a dead field, so no form control
    # could set it and the rule could never fire. A rule nobody can satisfy is
    # worse than no rule: it is advice that silently never appears.
    #
    # It used to be deleted HERE, on every build, which left the catalog source
    # showing one rule more than shipped — counting rules by reading the source
    # gave the wrong answer. Same class of problem as the two library rules
    # that used to be assembled in this file; both now live in the catalog and
    # this file holds none of them.

    # Capabilities carry a Chinese label: the advice names the missing capability,
    # and a reader should see "物理或化学" rather than the key "physicalScience".
    # Field-of-study names appear inside advice, so they get a Chinese label too:
    # "Engineering / 物理或化学" mixes two languages in one phrase.
    for key, zh in copy.FIELD_ZH.items():
        pattern = re.compile(r"(\n    (?:'" + re.escape(key) + r"'|" + re.escape(key) + r"): \{\s*\n)")
        source, n = pattern.subn(lambda m: m.group(1) + f"      zhLabel: '{js_string(zh)}',\n", source, count=1)
        if n == 0:
            print(f"    WARN field label not found: {key}")

    for key, zh in copy.CAPABILITY_ZH.items():
        pattern = re.compile(r"(\b" + re.escape(key) + r": \{\s*\n\s*label: ')([^']*)(')")
        source, n = pattern.subn(
            lambda m: m.group(1) + m.group(2) + m.group(3) + f", zhLabel: '{js_string(zh)}'",
            source, count=1)
        if n == 0:
            print(f"    WARN capability label not found: {key}")

    # Two rules name the gap they found instead of describing it in general.
    # Rewritten as whole objects: replacing the advice field alone meant reasoning
    # about where a `zh:` line starts and ends, and getting that wrong silently
    # produces a rule with no Chinese text.
    def rewrite_rule(src_text, rule_id, when_line, en_advice, zh_advice, title_en, title_zh):
        start_at = src_text.find(f"id: '{rule_id}'")
        if start_at < 0:
            raise SystemExit(f"rule {rule_id} not found for rewrite")
        obj_start = src_text.rfind("    {", 0, start_at)
        obj_end = src_text.find("\n    },\n", start_at)
        if obj_start < 0 or obj_end < 0:
            raise SystemExit(f"could not bound rule {rule_id}")
        new_obj = (
            "    {\n"
            f"      id: '{rule_id}',\n"
            f"      domain: 'course',\n"
            f"      title: {title_en},\n"
            f"      zhTitle: {title_zh},\n"
            f"      when: {when_line},\n"
            f"      advice:\n{en_advice},\n"
            f"      zh:\n{zh_advice},\n"
            "      source: 'Confirm the prerequisite for each specific programme',\n"
            "      verified: null,\n"
            "    },\n"
        )
        return src_text[:obj_start] + new_obj + src_text[obj_end + len("\n    },\n"):]

    source = rewrite_rule(
        source, "course-prereq-gap",
        '\'anyInterestExpectationGap("i.field", record.subjects)\'',
        "        'At least one of your chosen fields normally expects preparation you have ' +\n"
        "        'not recorded. Specifically: ' +\n"
        "        '{{gapFields}}. Requirements differ between institutions and between ' +\n"
        "        'programmes inside one institution, so confirm the exact prerequisite for ' +\n"
        "        'each course before assuming the gap is fatal — some accept a bridging unit.'",
        "        '你选的以下方向通常要求你尚未记录的科目准备：{{gapFields}}。' +\n"
        "        '各院校之间、甚至同一所院校的不同专业之间要求都不同，所以先逐个确认具体课程的' +\n"
        "        '先修要求，不要预设这个缺口无法弥补——有些学校接受衔接课程。'",
        "'A stated prerequisite is not among the recorded subjects'",
        "'已记录科目中缺少某个方向通常要求的准备'",
    )
    source = rewrite_rule(
        source, "course-prereq-optional-available",
        '\'anyInterestOptionalGap("i.field", record.subjects)\'',
        "        'Not required, but commonly recommended, and missing from your list: ' +\n"
        "        '{{optionalFields}}. Recommended subjects rarely decide an offer on their ' +\n"
        "        'own, but they reduce the chance of needing catch-up units in first year.'",
        "        '以下科目并非必修、但常被建议修，而你的清单里没有：{{optionalFields}}。' +\n"
        "        '建议科目很少单独决定录取，但能减少大一需要补修学分的可能。'",
        "'A recommended subject is missing'",
        "'缺少一门常被建议修的科目'",
    )


    # form-incomplete used to be patched here, because its condition named the
    # Year 11 school, which the form no longer collects. It is now `enabled:
    # false` in the catalog with the reason written next to it: the only clause
    # that survived the identity-block removal is an empty subject list, which is
    # already a hard validation error. Patching a condition onto a rule that can
    # never fire was the wrong shape of fix, so the patch is gone.

    # The engine reads domain labels and band labels from the catalog, so those
    # carry translations too.
    # ── a rule named for one thing, triggering on another ───────────────────
    # funding-west-au promised Western Australia but tested `i.country ===
    # "Australia"`, so a Monash applicant in Melbourne was told about a Western
    # Australian programme and never told which choice prompted it. That is the
    # same defect the prerequisite rules had — a category claim instead of a
    # named one — and it survived because the earlier fix only touched those two.
    # funding-west-au used to be spliced in here as a whole new object,
    # replacing whatever the catalog said. That made the catalog's copy of the
    # rule dead text: a fix applied there changed nothing, which is how a
    # verification date went missing without anyone noticing. The rule now
    # lives in src/advising-rules.current.js like every other rule, and this
    # build only injects its Chinese advice through the normal pass.

    # The rule needs a substring match and a record of what matched. anyInterest
    # compares whole values, so this is its own helper rather than an extra flag
    # argument, which would be invisible at the call site.
    #
    # The engine-side half of that helper, and the rule-scope plumbing it needs,
    # live in build_engine where the other sub_once calls are.

    # The two course-library rules used to be assembled here as string
    # literals and spliced in before wellbeing-plan, with English and Chinese
    # both written in this file. That gave 'add a rule' two different answers
    # and left the catalog source holding 29 rules while 30 shipped. They now
    # live in src/advising-rules.current.js like every other rule: modes from
    # MODES, and no rule text in this file.
    # ── rule id uniqueness ───────────────────────────────────────────────────
    # The modes tag used to be injected here and double as a "did the injection
    # run" assertion. It is gone with the modes dimension, so the check that
    # remains is the one that was doing real work anyway: no duplicate ids.
    _ids = re.findall(r"(?m)^      id: '([a-z0-9-]+)',$", source)
    if len(_ids) != len(set(_ids)):
        from collections import Counter
        raise SystemExit("duplicate rule ids: " + str([k for k, v in Counter(_ids).items() if v > 1]))
    if re.search(r"modes: \[", source):
        raise SystemExit("a rule still carries a modes tag, but there is only one mode now")
    print(f"  catalog: {len(_ids)} rules, no mode tags")

    for key, zh in copy.DOMAINS.items():
        pattern = re.compile(r"(\{ id: '" + re.escape(key) + r"',\s*label: ')([^']*)(')")
        source, n = pattern.subn(lambda m: m.group(1) + m.group(2) + m.group(3) + f", zhLabel: '{js_string(zh)}'", source, count=1)
        if n == 0:
            print(f"    WARN domain label not found: {key}")

    for key, zh in copy.BANDS.items():
        # actual shape: { max: 5, label: '1 — Trivial', level: 1 },
        pattern = re.compile(r"(label: '" + re.escape(key) + r"')")
        source, n = pattern.subn(lambda m: m.group(1) + f", zhLabel: '{js_string(zh)}'", source, count=1)
        if n == 0:
            print(f"    WARN band label not found: {key}")

    # matrix[urgency][level] gains a parallel zhMatrix
    zh_rows = []
    for urgency in sorted(copy.MATRIX):
        cells = ", ".join(f"{lvl}: '{js_string(copy.MATRIX[urgency][lvl])}'" for lvl in sorted(copy.MATRIX[urgency]))
        zh_rows.append(f"    {urgency}: {{ {cells} }},")
    zh_matrix = "  const zhMatrix = {\n" + "\n".join(zh_rows) + "\n  }\n\n"

    anchor = "  /* --------------------------------------------------------------------------\n   * 4. Subject capabilities."
    if anchor not in source:
        raise SystemExit("catalog anchor for zhMatrix not found")
    source = source.replace(anchor, zh_matrix + anchor, 1)

    # export the new tables
    source = source.replace("    matrix,\n", "    matrix,\n    zhMatrix,\n", 1)
    source = source.replace(
        "  return {\n    domains,",
        "  const uiStrings = " + repr(copy.UI).replace("'", '"') + "\n\n  return {\n    uiStrings,\n    domains,",
        1,
    )
    # repr() produces Python True/False/None in the UI dict; fix any that appear
    source = source.replace('": True', '": true').replace('": False', '": false').replace('": None', '": null')

    # ── the verification gate ──────────────────────────────────
    # Runs HERE, at the end, on the finished catalog. It used to sit near the
    # top, before the two course-library rules were appended and before the
    # dead rule was removed — so it checked 29 rules while 30 shipped. A gate
    # that inspects a different text than the one that ships will eventually
    # pass something that should not have shipped.
    INTERNAL = ("internal",)
    unverified_external = []
    checked = 0
    for m in re.finditer(r"id: '([a-z0-9-]+)',\n(.*?)\n    \},", source, re.S):
        rule_id, body = m.group(1), m.group(2)
        # Quote-agnostic on purpose. An earlier version matched only 'internal',
        # but the advice-injection pass above rewrites strings through js_string,
        # which flips them to "internal" — so the gate silently skipped exactly the
        # rules it was written to catch and still reported success. A check that
        # cannot see its own subject is worse than no check.
        src_m = re.search(r"""source: ['"]([^'"]*)['"]""", body)
        ver_m = re.search(r"""verified: (null|'[^']*'|"[^"]*")""", body)
        if not src_m or not ver_m:
            raise SystemExit(
                f"verification gate: {rule_id} has no source or verified field")
        source_text = src_m.group(1)
        verified = ver_m.group(1)
        checked += 1
        if source_text in INTERNAL and verified == "null":
            raise SystemExit(
                f"verification gate: {rule_id} names an internal source but stays "
                "unverified. Internal copy is written here, so there is nothing "
                "external to wait for — give it a date, or name the source that "
                "actually needs checking.")
        if source_text not in INTERNAL and verified == "null":
            unverified_external.append(rule_id)
    rule_total = len(re.findall(r"\n      id: '[a-z0-9-]+',", source))
    if checked != rule_total:
        raise SystemExit(
            f"verification gate saw {checked} rules but the catalog has {rule_total}; "
            "it is not reading what it thinks it is reading")
    print(f"  gate: {checked} rules checked · {len(unverified_external)} awaiting an "
          f"external source · {checked - len(unverified_external)} dated")

    # ── one zh per rule ────────────────────────────────────────────────────
    # Runs HERE, immediately before the file is written, and deliberately not
    # near the top. The advice-injection loop above is what CREATES a second
    # zh key when a rule already carries its own; an earlier version of this
    # gate sat before that loop, so it tested a catalog in which the defect
    # could not yet exist and reported success. Injecting a duplicate zh into
    # dest-uk and watching the build print "build complete" is how that was
    # found. Two `zh` keys in one object literal is legal JavaScript and the
    # second silently wins, so the rule renders whichever came last.
    for m in re.finditer(r"id: '([a-z0-9-]+)',\n(.*?)\n    \},", source, re.S):
        zh_count = len(re.findall(r"\n      zh:\s", m.group(2)))
        if zh_count > 1:
            raise SystemExit(
                f"zh gate: {m.group(1)} has {zh_count} zh keys — the second one "
                "wins silently, so one of them is dead text")
        if zh_count == 0:
            raise SystemExit(f"zh gate: {m.group(1)} has no Chinese copy")

    (TOOL / "advising-rules.js").write_text(source, encoding="utf-8")
    print(f"  catalog: {injected} rules given Chinese advice")
    if missing:
        print(f"  catalog: MISSING translations for {missing}")
    return not missing


# ── 2. engine: make it language-aware ───────────────────────────────────────
L10N = """
  /* ── language and mode ───────────────────────────────────────────────
   * Both come from the page, not from runtime state: the site pairs pages and
   * switches with a plain link, so there is nothing to keep in sync and no
   * JavaScript needed to change either one. Everything user-visible that the
   * engine generates resolves through the helpers below, so no branch further
   * down tests the language, and no rule tests the mode.
   * ------------------------------------------------------------------*/
  var LANG = (function () {
    var v = document.documentElement.dataset.lang || 'en'
    return (v === 'zh' || v === 'zh-CN') ? 'zh' : 'en'
  })()
  var MODE = (function () {
    var v = document.documentElement.dataset.mode || 'student'
    return v === 'guest' ? 'guest' : 'student'
  })()
  var U = R.uiStrings[LANG] || R.uiStrings.en
  function pick(en, zh) { return LANG === 'zh' && zh ? zh : en }
  // The calibration's own sentences, in the reader's language.
  //
  // Deliberately NOT injected into the catalog. An earlier attempt did that and
  // collided with the passes that inject zhLabel into every `label:` field, so the
  // caveat is resolved here, beside the rest of the interface copy. The English
  // still comes from the catalog, which stays the single source for what the
  // calibration IS; only its rendering is translated.
  var CAL_ZH = {
    label: '源工作簿曲线 —— 一所院校、一个招生轮次',
    verifiedAgainst:
      '工作簿写明合成分 239.12838737245087 对应 ATAR 80；本条曲线在该点复现 80.00。' +
      '另用电子表格程序独立重算了原工作簿，各合成分处两边一致；并与工作簿里 272 名' +
      '有四门以上成绩的学生逐一比对过',
    caveat:
      '这是源工作簿里某所院校某个招生轮次的换算式，不是官方 ATAR 成绩单。' +
      '只当估算，并以你自己的招生中心为准。',
    schoolMarkNote:
      '这里把你填进去的分数一律当作最终分数来换算。学期中途从学校成绩册上读到的' +
      '分数并不是最终换算分，所以请把结果读成「照这个水平走完会落在哪」，而不是对' +
      '你 ATAR 的预测。',
  }
  function calText(key) {
    var c = R.calibration || {}
    if (LANG === 'zh' && CAL_ZH[key]) return CAL_ZH[key]
    return c[key] || ''
  }
  function domainLabel(d) { return (LANG === 'zh' && d.zhLabel) ? d.zhLabel : d.label }
  function bandLabel(b) { return (LANG === 'zh' && b.zhLabel) ? b.zhLabel : b.label }

  /* ── course library ──────────────────────────────────────────────────
   * Course facts from the workbook's database, with a link check this project
   * performed (see courses.js). The engine matches them against what the student
   * entered and compares the student's standing against the recorded minimums.
   * Nothing here hard-codes a course: the library is data.
   * ------------------------------------------------------------------*/
  var LIBRARY = (typeof window !== 'undefined' && window.COURSES)
    ? window.COURSES
    : { rows: [], snapshot: '', count: 0 }

  function fieldWords(text) {
    return String(text || '').toLowerCase().split(/[^a-z]+/).filter(function (w) { return w.length > 3 })
  }
  function countryMatches(courseCountry, interestCountry) {
    // 同 fieldMatches：没填就不筛这一维。三个匹配函数的空值语义必须一致。
    if (!interestCountry) return true
    var a = String(courseCountry || '').toLowerCase()
    var b = String(interestCountry).toLowerCase()
    if (a === b) return true
    // The library writes 'UK' where the form writes 'United Kingdom'.
    if ((a === 'uk' || a === 'united kingdom') && (b === 'uk' || b === 'united kingdom')) return true
    return false
  }
  function fieldMatches(course, interestField) {
    // 没填方向 = 这一维不参与筛选，而不是「什么都不匹配」。
    // 原来返回 false，而 matchingCourses 要求三者全中，于是只填国家的学生
    // 得到 0 命中、国家那栏等于白填（走查实测）。
    // 三个匹配函数现在行为一致：空值不限制。universityMatches 本来就是这么写的。
    if (!interestField) return true
    var want = String(interestField).toLowerCase()
    var cat = String(course.category || '').toLowerCase()
    var name = String(course.course || '').toLowerCase()
    // A course with no stated category is not restricted to a field, so it
    // matches whatever field the student named, including "Undecided" — a
    // student who has not chosen yet is exactly who a course named "ANY
    // offered" is for. The source workbook records the National University of
    // Singapore that way, with a blank category, and the blank was being read as
    // "matches nothing": the row was reachable by country and invisible to every
    // field. Absence of a restriction is not a restriction.
    if (!cat) return true
    if (cat && (cat.indexOf(want) !== -1 || want.indexOf(cat) !== -1)) return true
    if (name.indexOf(want) !== -1) return true
    // Word overlap, but only on words that carry meaning here. A first attempt
    // matched any shared word longer than three characters, which let 'Computer
    // Science' match 'Zoology and Animal Science' and 'Environmental Science' —
    // 'science' is shared by half the catalogue and distinguishes nothing. The
    // stop list names the words that appear across unrelated fields; a synonym
    // map carries the cases where the form and the catalogue use different words
    // for the same thing.
    var STOP = { science: 1, sciences: 1, studies: 1, study: 1, general: 1, other: 1, health: 1, arts: 1 }
    var SYNONYM = {
      'computer science': ['computing', 'information tech', 'information technology', 'software', 'cyber'],
      'business': ['business', 'commerce', 'finance', 'accounting', 'marketing', 'management'],
      'sciences': ['science', 'sciences', 'biology', 'chemistry', 'physics', 'biomedical'],
      'humanities': ['arts', 'humanities', 'history', 'literature'],
      'psychology': ['psychology', 'psychological'],
      'engineering': ['engineering', 'engineer'],
      'law': ['law', 'legal'],
      'nursing': ['nursing', 'nurse'],
      'medicine': ['medicine', 'medical', 'surgery'],
      'dentistry': ['dentistry', 'dental'],
      'architecture': ['architecture', 'architectural'],
      'education': ['education', 'teaching'],
    }
    // Aliases are matched per WORD, not as substrings. A substring check is how
    // 'Medicine' matched 'BioMedical Engineering': indexOf('medical') finds a hit
    // inside 'biomedical', so an engineering degree was offered as a medical
    // option. Matching whole words costs a little recall and removes that class of
    // error entirely.
    var hayWords = fieldWords(cat + ' ' + name)
    var aliases = SYNONYM[want] || [want]
    for (var i = 0; i < aliases.length; i++) {
      var alias = String(aliases[i]).toLowerCase()
      var aliasWords = alias.split(/[^a-z]+/).filter(function (w) { return w.length > 2 })
      var every = aliasWords.length > 0 && aliasWords.every(function (aw) {
        return hayWords.some(function (hw) { return hw === aw || hw === aw + 's' || hw + 's' === aw })
      })
      if (every) return true
    }
    // Word overlap on the words the INTEREST carries and the course NAME carries.
    // An earlier attempt let the category contribute too, which is how 'Medicine'
    // reached 'Biomedical Engineering' — both sit in 'Health Sciences'.
    var words = fieldWords(interestField).filter(function (w) { return !STOP[w] })
    if (!words.length) return false
    var nameWords = fieldWords(course.course)
    return words.some(function (w) {
      return nameWords.some(function (cw) {
        return cw === w || cw === w + 's' || cw + 's' === w
      })
    })
  }
  function universityMatches(course, interestUniversity) {
    if (!interestUniversity) return true
    // Exact, because the form is now a pick-list of the library's own names.
    //
    // It used to fall back to word overlap for a typed name, and that fallback
    // was quietly wrong: "Curtin University" and "University of Western
    // Australia" share the word "university", so EVERY institution matched every
    // other one. A student comparing against Curtin was shown UWA's minimums,
    // and the panel named a course they had not chosen — with no error anywhere,
    // because a course list that is too long still looks like a course list.
    //
    // Equality is now sufficient as well as honest: the value can only come from
    // `universityNames()`, which reads the same rows this compares against.
    return String(course.university || '').trim().toLowerCase() ===
           String(interestUniversity).trim().toLowerCase()
  }
  function matchingCourses(record) {
    var out = []
    ;(record.interests || []).forEach(function (interest) {
      ;(LIBRARY.rows || []).forEach(function (course) {
        if (!countryMatches(course.country, interest.country)) return
        if (!fieldMatches(course, interest.field)) return
        if (!universityMatches(course, interest.university)) return
        if (out.indexOf(course) === -1) out.push(course)
      })
    })
    return out.sort(function (a, b) { return a.atar - b.atar })
  }
  // The nearest recorded minimum at or below the student's standing, and the
  // nearest above it. Both are what an advisor would actually say out loud.
  function atarComparison(record, courses) {
    // The standing is the number the tool computed from the marks, not one the
    // student typed. Reading a typed estimate here is what kept every
    // library-comparison rule silent until the student guessed: no standing means
    // this returns null, which means anyInterestHasCourses is false, which means
    // none of them fire.
    var standing = record.computedAtar
    if (standing === null || standing === undefined || !courses.length) return null
    var reachable = courses.filter(function (c) { return c.atar <= standing })
    var above = courses.filter(function (c) { return c.atar > standing })
    return {
      standing: standing,
      reachable: reachable.length ? reachable[reachable.length - 1] : null,
      nearest: above.length ? above[0] : null,
      count: courses.length,
    }
  }
  function courseLabel(c) {
    return c.university + ' ' + c.course + ' (' + c.atar + ')'
  }
  // The same, but honest when the named course is one of several at the same
  // minimum. "University of Western Australia Biomedical Engineering (80)" reads
  // as the requirement; it is one of three courses at 80, and which one the sort
  // put first is not information. Ties are common — a whole engineering school
  // usually publishes one entry score — so the prose says so instead.
  function courseSetLabel(courses, c) {
    var tied = (courses || []).filter(function (x) { return x.atar === c.atar })
    if (tied.length < 2) return courseLabel(c)
    var names = tied.slice(0, 3).map(function (x) { return x.course })
    var rest = tied.length > names.length ? (LANG === 'zh' ? ' 等 ' : ', …') : ''
    return LANG === 'zh'
      ? (c.atar + ' 分并列的 ' + tied.length + ' 门（' + names.join('、') + rest + '）')
      : (tied.length + ' courses tied at ' + c.atar + ' (' + names.join(', ') + rest + ')')
  }
  // Every pass reads the catalog directly. A rule that is switched off stays in
  // the set on purpose: `evaluate` returns it with a reason instead of firing it,
  // which is what puts it in the coverage view as deliberately silent.
"""


def build_engine():
    src = (SRC / "engine.js").read_text(encoding="utf-8")

    def sub_once(old, new, label):
        nonlocal src
        if src.count(old) != 1:
            raise SystemExit(f"engine replacement '{label}' matched {src.count(old)} times, expected 1")
        src = src.replace(old, new, 1)

    # inject the language layer right after the catalog is read
    sub_once("  var R = window.ADVISING\n", "  var R = window.ADVISING\n" + L10N, "language layer")

    # ── the notes box ────────────────────────────────────────────────────────
    # The workbook gives teachers a custom column to keep their own wording in.
    # This is that, as one free-text box per record: saved with the record,
    # exported with the report, and printed at the end.
    #
    # Inserted BEFORE the dead-field removals below, because the anchor line it
    # sits next to is one of the lines those removals delete. Running it after
    # them matched nothing — the ordering is load-bearing, not stylistic.
    # ── dead fields removed from the record shape ────────────────────────────
    # The identity block is gone, so everything it collected goes with it:
    # fullName, studentId, year11School, englishFirstLanguage, previousIntake,
    # stillDeciding, fundingSecured, and the two free-text result boxes. Of these
    # only targetAtar and estimatedAtar were still read by anything, and both
    # moved into the ATAR card rather than dying.
    #
    # Removed by exact line with an assertion. An earlier attempt anchored on
    # multi-line blocks and silently matched nothing, which is how the fields
    # survived a "cleanup" and then crashed the guest page.
    for dead in [
        "      fullName: $('fullName').value.trim(),\n",
        "      studentId: $('studentId').value.trim(),\n",
        "      year11School: $('year11School').value.trim(),\n",
        "      englishFirstLanguage: boolOrNull($('englishFirstLanguage').value),\n",
        "      previousIntake: $('previousIntake').value || null,\n",
        "      stillDeciding: $('stillDeciding').value === 'true',\n",
        "      fundingSecured: boolOrNull($('fundingSecured').value),\n",
        # priorResults is back in this list: the notes step that used to consume
        # this exact line is gone, and nothing else rewrites it.
        "      priorResults: parsePairs($('priorResults').value),\n",
        "      year11: parsePairs($('year11Results').value),\n",
        "    $('fullName').value = rec.fullName || ''\n",
        "    $('studentId').value = rec.studentId || ''\n",
        "    $('year11School').value = rec.year11School || ''\n",
        "    $('englishFirstLanguage').value = rec.englishFirstLanguage === null || rec.englishFirstLanguage === undefined ? '' : String(rec.englishFirstLanguage)\n",
        "    $('previousIntake').value = rec.previousIntake || ''\n",
        "    $('stillDeciding').value = rec.stillDeciding ? 'true' : 'false'\n",
        "    $('fundingSecured').value = rec.fundingSecured === null || rec.fundingSecured === undefined ? '' : String(rec.fundingSecured)\n",
        "      fullName: 'Sample Student',\n",
        "      studentId: 'S-000000',\n",
        "      year11School: 'Sample Secondary College',\n",
        "      englishFirstLanguage: false,\n",
        "      previousIntake: 'September intake',\n",
        "      stillDeciding: false,\n",
        "      fundingSecured: false,\n",
        "      year11: { English: 71, Mathematics: 82 },\n",
        "      priorResults: { Chemistry: 52 },\n",
    ]:
        if src.count(dead) != 1:
            raise SystemExit(f"dead-field line matched {src.count(dead)} times: {dead.strip()}")
        src = src.replace(dead, "", 1)

    # the two textarea writers reference elements the page no longer has
    for el_id in ("year11Results", "priorResults"):
        marker = f"    $('{el_id}').value = Object.keys("
        at = src.find(marker)
        if at < 0:
            raise SystemExit(f"writeRecord line for {el_id} not found")
        src = src[:at] + src[src.find("\n", at) + 1:]

    # The clear button and the initial seed no longer carry the dead keys.
    if src.count("writeRecord({ interests: [], subjects: [], year11: {}, priorResults: {} })") != 2:
        raise SystemExit("expected exactly two seed calls carrying the dead keys")
    src = src.replace("writeRecord({ interests: [], subjects: [], year11: {}, priorResults: {} })",
                      "writeRecord({ interests: [], subjects: [] })")

    # ── an element lookup that tolerates absence ─────────────────────────────
    # The guest page that first showed why is gone, but a hand-edited page can
    # still omit a control the engine wires.
    # The wiring block used to call addEventListener on it unconditionally, which
    # threw and aborted init — every listener registered after that point was
    # never attached, which is why the report button and both tabs appeared dead
    # on the guest page while working fine on the enrolled one. One missing node
    # took the whole engine down, so lookups now return null and each wiring call
    # guards itself.
    sub_once("  function $(id) { return document.getElementById(id) }",
             "  function $(id) { return document.getElementById(id) || null }\n"
             "  // Wires a listener only if the control is on this page.\n"
             "  function on(id, event, handler) {\n"
             "    var node = $(id)\n"
             "    if (node && node.addEventListener) node.addEventListener(event, handler)\n"
             "    return node\n"
             "  }", "safe lookup")

    for el_id, event, handler in [
        ("addInterest", "click", "function () { addInterestRow() }"),
        ("addSubject", "click", "function () { addSubjectRow() }"),
        ("btnGenerate", "click", "renderReport"),
        ("btnSample", "click", "function () { writeRecord(sample()); renderReport() }"),
        ("btnPrint", "click", "function () { window.print() }"),
    ]:
        sub_once(f"  $('{el_id}').addEventListener('{event}', {handler})",
                 f"  on('{el_id}', '{event}', {handler})", f"wire {el_id}")

    # the remaining ones have multi-line bodies; replace the opening call only
    for el_id in ("btnClear", "btnSave", "btnLoad", "btnCopy", "btnDownload"):
        sub_once(f"  $('{el_id}').addEventListener('click', function () {{",
                 f"  on('{el_id}', 'click', function () {{", f"wire {el_id}")

    # header text: the shell bakes it in, but a hand-edited page must not crash
    sub_once("  $('appTitle').textContent = R.meta.title\n",
             "  if ($('appTitle')) $('appTitle').textContent = R.meta.title\n", "appTitle")
    sub_once("  $('appSub').textContent = R.meta.subtitle + ' · v' + R.meta.version + ' · ' + R.meta.contentPolicy\n",
             "  if ($('appSub')) $('appSub').textContent = R.meta.subtitle + ' · v' + R.meta.version + ' · ' + R.meta.contentPolicy\n",
             "appSub")

    # renderers guard their own targets too
    src = src.replace("    $('reportBody').innerHTML = ''", "    if ($('reportBody')) $('reportBody').innerHTML = ''")
    src = src.replace("    $('validationBox').innerHTML = '<div class=\"note ok\">", "    if ($('validationBox')) $('validationBox').innerHTML = '<div class=\"note ok\">")
    src = src.replace("    $('validationBox').innerHTML = '<div class=\"note err\">", "    if ($('validationBox')) $('validationBox').innerHTML = '<div class=\"note err\">")
    src = src.replace("    $('validationBox').innerHTML = '<div class=\"note\">", "    if ($('validationBox')) $('validationBox').innerHTML = '<div class=\"note\">")

    # The seed also added a sample assessment row. The tracker is gone with
    # its tab, so that call went with it.

    # ── the assessment tracker is gone, so its code goes too ─────────────────
    # The tab and its panel were removed with the mode dimension, but the three
    # functions behind them stayed in the shipped bundle, still reaching for ids
    # like assessRows and trackerSummary that no page has any more. The suites
    # noticed, because they check every id the bundle reads against the markup —
    # which is the whole point of that check. Nothing else calls these: the matrix
    # accessor was only ever the tracker's own lookup, and the catalog's
    # importanceBands and matrix are asserted directly by the rules suite.
    def drop_function(name, label):
        """Remove a whole `function name(...) { ... }` block.

        Brace-counted from the signature rather than line-matched: these bodies
        hold nested blocks, and a partial removal would leave a function that
        still parses and silently does nothing.
        """
        nonlocal src
        at = src.find(f"\n  function {name}(")
        if at < 0:
            raise SystemExit(f"drop_function: {label} ({name}) not found")
        open_at = src.index("{", at)
        depth = 0
        i = open_at
        while i < len(src):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if depth != 0:
            raise SystemExit(f"drop_function: {label} ({name}) has unbalanced braces")
        end = i + 1
        while end < len(src) and src[end] == "\n":
            end += 1
        src = src[:at + 1] + src[end:]

    sub_once("  /* -------------------------- assessment tracker ---------------------- */\n",
             "", "tracker section comment")
    for _fn in ("importanceFor", "addAssessRow", "summariseAssessments"):
        drop_function(_fn, "tracker")
    if "addAssessRow" in src or "summariseAssessments" in src or "importanceFor" in src:
        raise SystemExit("tracker code survived the removal")
    for _gone in ("assessRows", "trackerSummary", "addAssess"):
        if f"$('{_gone}')" in src:
            raise SystemExit(f"the bundle still reads the removed id {_gone}")
    # was any unconditional write to a possibly-absent id left behind?
    leftovers = [m.group(0).strip() for m in re.finditer(r"\$\('[A-Za-z0-9_-]+'\)\.addEventListener", src)]
    if leftovers:
        raise SystemExit("unguarded listeners survived: " + " | ".join(leftovers))

    # ── rule filtering ───────────────────────────────────────────────────────
    # There used to be an ACTIVE_RULES set here: the catalog filtered by mode,
    # with evaluation, the report and the coverage view all reading it so they
    # could not disagree. With the mode dimension gone the filter is a no-op that
    # still reads a tag no rule carries, so the layer is gone rather than left
    # behind as a variable named "active" whose contents include the two rules
    # that are switched off. Every pass now reads R.rules, and `evaluate` is the
    # single place that decides a disabled rule does not run.
    occurrences = src.count("R.rules.length")
    if occurrences != 2:
        raise SystemExit(f"expected 2 uses of R.rules.length, found {occurrences}")



    # ── the course tab ───────────────────────────────────────────────────────
    # Rendered on demand: 56 rows of data that most visits never open. It listens
    # on the nav button and on a button in the form.
    # ── the roadmap / timeline / pathway resolvers ───────────────────────────
    # Module scope, next to the course library, because the rules read them
    # through the scope object rather than computing them inside a helper.
    sub_once("  function fieldWords(text) {",
             "  var ROADMAP = R.roadmap || {}\n"
             "  var OPPORTUNITIES = R.opportunities || { pathways: {}, timelines: {} }\n"
             "  function roadmapRow(rec) {\n"
             "    for (var i = 0; i < rec.interests.length; i++) {\n"
             "      var f = rec.interests[i].field\n"
             "      if (f && ROADMAP[f]) return { field: f, row: ROADMAP[f][LANG] || ROADMAP[f].en }\n"
             "    }\n"
             "    return null\n"
             "  }\n"
             "  function timelineParts(rec) {\n"
             "    var out = []\n"
             "    for (var i = 0; i < rec.interests.length; i++) {\n"
             "      var c = rec.interests[i].country\n"
             "      var t = c ? OPPORTUNITIES.timelines[c] : null\n"
             "      if (!t) continue\n"
             "      var text = t[LANG] || t.en\n"
             "      if (out.indexOf(text) === -1) out.push(text)\n"
             "    }\n"
             "    return out\n"
             "  }\n"
             "  function optionParts() {\n"
             "    var list = OPPORTUNITIES.pathways[LANG] || OPPORTUNITIES.pathways.en || []\n"
             "    return list.map(function (p) {\n"
             "      var labels = (p.links || []).map(function (l) { return l.label }).join(', ')\n"
             "      return p.text + (labels ? ' (' + labels + ')' : '')\n"
             "    })\n"
             "  }\n"
             "  // Which named prerequisites the recorded courses ask for and the\n"
             "  // student has not taken. Reads the requirement lines the workbook\n"
             "  // itself carries; a course that names no subject contributes nothing.\n"
             "  function namedPrereqGaps(rec) {\n"
             "    var taken = {}\n"
             "    ;(rec.subjects || []).forEach(function (s) {\n"
             "      if (s.subject) taken[String(s.subject).toUpperCase()] = true\n"
             "    })\n"
             "    var groups = {}\n"
             "    matchingCourses(rec).forEach(function (c) {\n"
             "      var needs = c.needs || {}\n"
             "      Object.keys(needs).forEach(function (name) {\n"
             "        var codes = needs[name] || []\n"
             "        var have = codes.some(function (code) { return taken[code] })\n"
             "        if (have) return\n"
             "        var label = c.university + ' ' + c.course\n"
             "        if (!groups[name]) groups[name] = []\n"
             "        if (groups[name].indexOf(label) === -1) groups[name].push(label)\n"
             "      })\n"
             "    })\n"
             "    return groups\n"
             "  }\n"
             "  // Rendered the same way the field-expectation gaps are, so both read\n"
             "  // alike in the report.\n"
             "  function namedPrereqParts(rec) {\n"
             "    var groups = namedPrereqGaps(rec)\n"
             "    return Object.keys(groups).map(function (name) {\n"
             "      return name + ' (' + groups[name].join(LANG === 'zh' ? '、' : '; ') + ')'\n"
             "    })\n"
             "  }\n"
             "  // Fills the module tokens for one record. Deliberately NOT done inside the\n"
             "  // helpers: a helper returns its own boolean, so anything after that return\n"
             "  // is dead code, and the first version of this shipped em dashes in the\n"
             "  // prose for exactly that reason. Named rather than inlined so a test can\n"
             "  // call it and prove the tokens actually get set.\n"
             "  function primeModuleScope(rec, ruleScope) {\n"
             "    var road = roadmapRow(rec)\n"
             "    if (road) {\n"
             "      ruleScope.roadmapField = road.field\n"
             "      ruleScope.roadmapCareers = road.row.careers\n"
             "      ruleScope.roadmapActivities = road.row.activities\n"
             "      ruleScope.roadmapSkills = road.row.skills\n"
             "      ruleScope.roadmapWhy = road.row.why\n"
             "    }\n"
             "    var times = timelineParts(rec)\n"
             "    if (times.length) ruleScope.timelineList = times.join(' ')\n"
             "    var opts = optionParts()\n"
             "    if (opts.length) ruleScope.optionsList = opts.join(' ')\n"
             "    var named = namedPrereqParts(rec)\n"
             "    if (named.length) ruleScope.namedPrereqGaps = named.join('; ')\n"
             "    return ruleScope\n"
             "  }\n\n"
             "  function fieldWords(text) {",
             "roadmap resolvers")

    # ── the ATAR panel ──────────────────────────────────────────────────────
    # The one thing the original workbook does that arithmetic alone cannot
    # replace. Rendered on demand from whatever is in the subject table, so a
    # student can adjust a mark and press again without regenerating the report.
    sub_once("  function showTab(which) {",
             "  function atarRow(label, value, cls) {\n"
             "    var tr = el('tr')\n"
             "    tr.appendChild(el('th', { 'class': 'atar-key', text: label }))\n"
             "    tr.appendChild(el('td', { 'class': 'num ' + (cls || ''), text: value }))\n"
             "    return tr\n"
             "  }\n"
             "  function renderAtar() {\n"
             "    var box = $('atarBox')\n"
             "    if (!box) return\n"
             "    var rec = readRecord()\n"
             "    var p = atarPicture(rec)\n"
             "    box.innerHTML = ''\n"
             "    var n = R.calibration.aggregateSize\n"
             "    if (p.status === 'unavailable') {\n"
             "      box.appendChild(el('p', { 'class': 'warn', text: U.atar_unavailable }))\n"
             "      atarMethod()\n"
             "      return\n"
             "    }\n"
             "    if (p.status === 'insufficient') {\n"
             "      box.appendChild(el('p', { 'class': 'warn',\n"
             "        text: U.atar_insufficient.replace('{n}', String(n)) }))\n"
             "      atarMethod()\n"
             "      return\n"
             "    }\n"
             "    var table = el('table', { 'class': 'atar-table' })\n"
             "    table.appendChild(atarRow(U.atar_row_agg.replace('{n}', String(n)), p.aggregate.toFixed(R.calibration.display.aggregate)))\n"
             "    // An unconvertible aggregate suppresses the ATAR row and nothing else.\n"
             "    // The target rows are computed from the target alone, so they are still\n"
             "    // answered — withholding them was the bug this replaces: the student\n"
             "    // who cannot be told where they are is exactly the one who needs to be\n"
             "    // told what the goal costs.\n"
             "    var outOfRange = p.status === 'out-of-range'\n"
             "    if (!outOfRange) {\n"
             "      table.appendChild(atarRow(U.atar_row_atar, p.atar.toFixed(R.calibration.display.atar), 'big'))\n"
             "    }\n"
             "    if (typeof p.target === 'number') {\n"
             "      table.appendChild(atarRow(U.atar_row_target, String(p.target)))\n"
             "      if (p.neededAggregate !== null) {\n"
             "        table.appendChild(atarRow(U.atar_row_needed, p.neededAggregate.toFixed(R.calibration.display.aggregate)))\n"
             "      }\n"
             "    }\n"
             "    box.appendChild(table)\n"
             "    if (outOfRange) {\n"
             "      var range = R.calibration.saneRange\n"
             "      box.appendChild(el('p', { 'class': 'warn', text: U.atar_out_of_range\n"
             "        .replace('{agg}', p.aggregate.toFixed(R.calibration.display.aggregate))\n"
             "        .replace('{lo}', String(range[0])).replace('{hi}', String(range[1])) }))\n"
             "    }\n"
             "    var line = el('p')\n"
             "    if (p.neededAggregate !== null) {\n"
             "      line.appendChild(el('span', { text: U.atar_need\n"
             "        .replace('{target}', String(p.target))\n"
             "        .replace('{agg}', p.neededAggregate.toFixed(R.calibration.display.aggregate))\n"
             "        .replace('{per}', p.neededPerSubject.toFixed(R.calibration.display.aggregate)) + ' ' }))\n"
             "      var gap = Math.abs(p.gapToTarget)\n"
             "      line.appendChild(el('strong', { text: p.gapToTarget > 0\n"
             "        ? U.atar_above.replace('{gap}', gap.toFixed(R.calibration.display.aggregate))\n"
             "        : U.atar_below.replace('{gap}', gap.toFixed(R.calibration.display.aggregate)) }))\n"
             "    } else {\n"
             "      line.appendChild(el('span', { 'class': 'muted', text: U.atar_no_target }))\n"
             "    }\n"
             "    box.appendChild(line)\n"
             "    // One line per choice, each stating what the library holds for THAT\n"
             "    // choice and where the standing sits inside it. The first version\n"
             "    // printed a single line over the union of every choice and named one\n"
             "    // course out of the set; with three courses tied at 80 it named\n"
             "    // whichever the sort happened to put first, which tells the reader\n"
             "    // that Biomedical Engineering is the requirement when it is one of\n"
             "    // three. It also never said how many courses it was summarising.\n"
             "    // Every filled choice gets a line, including one with no institution\n"
             "    // chosen: that row still constrains country and field, and the report\n"
             "    // already speaks about it, so the panel staying silent was the two\n"
             "    // disagreeing about which choices exist.\n"
             "    var picked = rec.interests.filter(function (i) { return i.country || i.field || i.university })\n"
             "    if (picked.length && p.status !== 'out-of-range') {\n"
             "      var d = R.calibration.display.atar\n"
             "      picked.forEach(function (i) {\n"
             "        var list = coursesFor(i.country, i.field, i.university)\n"
             "        var row = el('p', { 'class': 'muted' })\n"
             "        var head = i.university || ((i.country || '—') + ' · ' + (i.field || '—'))\n"
             "        row.appendChild(el('strong', { text: head + '：' }))\n"
             "        if (!list.length) {\n"
             "          var why = libraryDiagnosis(i.country, i.field, i.university)\n"
             "          row.appendChild(el('span', { text: why === 'country'\n"
             "            ? U.atar_uni_nocountry.replace('{countries}', countriesInLibrary().join(LANG === 'zh' ? '、' : ', '))\n"
             "            : why === 'university'\n"
             "              ? U.atar_uni_nouni.replace('{uni}', String(i.university))\n"
             "              : U.atar_uni_nocourse.replace('{field}', String(i.field || '—')) }))\n"
             "          box.appendChild(row)\n"
             "          return\n"
             "        }\n"
             "        var lo = list[0].atar\n"
             "        var hi = list[list.length - 1].atar\n"
             "        row.appendChild(el('span', { text: (lo === hi\n"
             "          ? U.atar_uni_holdflat.replace('{n}', String(list.length)).replace('{lo}', lo.toFixed(d))\n"
             "          : U.atar_uni_hold.replace('{n}', String(list.length)).replace('{lo}', lo.toFixed(d)).replace('{hi}', hi.toFixed(d))) + ' ' }))\n"
             "        var cmpRow = atarComparison(rec, list)\n"
             "        var mine = p.atar\n"
             "        if (cmpRow && cmpRow.reachable) {\n"
             "          row.appendChild(el('span', { text: U.atar_uni_above\n"
             "            .replace('{standing}', mine.toFixed(d))\n"
             "            .replace('{n}', String(cmpRow.reachable ? list.filter(function (c) { return c.atar <= mine }).length : 0))\n"
             "            .replace('{top}', cmpRow.reachable.atar.toFixed(d)) }))\n"
             "          if (cmpRow.nearest) {\n"
             "            row.appendChild(el('span', { text: ' ' + U.atar_uni_next\n"
             "              .replace('{next}', cmpRow.nearest.atar.toFixed(d))\n"
             "              .replace('{gap}', (cmpRow.nearest.atar - mine).toFixed(d)) }))\n"
             "          }\n"
             "        } else if (cmpRow && cmpRow.nearest) {\n"
             "          row.appendChild(el('span', { text: U.atar_uni_below\n"
             "            .replace('{standing}', mine.toFixed(d))\n"
             "            .replace('{n}', String(list.length))\n"
             "            .replace('{lo}', lo.toFixed(d))\n"
             "            .replace('{gap}', (lo - mine).toFixed(d)) }))\n"
             "        }\n"
             "        row.appendChild(el('span', { 'class': 'muted', text: ' ' + list.slice(0, 3).map(function (c) { return c.course + ' (' + c.atar + ')' }).join(LANG === 'zh' ? '、' : ', ') + (list.length > 3 ? ' …' : '') }))\n"
             "        box.appendChild(row)\n"
             "      })\n"
             "    }\n"
             "    box.appendChild(el('p', { 'class': 'muted', text: calText('caveat') }))\n"
             "    // Printed under every figure rather than only the low ones. The earlier\n"
             "    // version warned that the curve ran ten points high below ATAR 90; that\n"
             "    // measurement was wrong, and a warning attached to a number that was\n"
             "    // right teaches the reader to discount it. What is true of every figure\n"
             "    // is the one thing worth saying every time.\n"
             "    box.appendChild(el('p', { 'class': 'muted', text: calText('schoolMarkNote') }))\n"
             "    atarMethod()\n"
             "  }\n"
             "  function atarMethod() {\n"
             "    var el2 = $('atarMethod')\n"
             "    if (!el2) return\n"
             "    var check = R.calibrationCheck || { ok: false, reference: 0 }\n"
             "    el2.textContent = U.atar_method\n"
             "      .replace('{n}', String(R.calibration.aggregateSize))\n"
             "      .replace('{ref}', '239.1')\n"
             "      .replace('{got}', check.reference ? check.reference.toFixed(2) : '—')\n"
             "  }\n"
             "  on('btnAtar', 'click', renderAtar)\n"
             "  // The prior-cohort panel. Its whole value is context, so the cohort\n"
             "  // caveat is rendered with the numbers rather than tucked away: these\n"
             "  // students are a narrow high band, and a band label without that\n"
             "  // sentence reads as a position in the population.\n"
             "  function renderHistory() {\n"
             "    var box = $('historyBox')\n"
             "    if (!box) return\n"
             "    box.innerHTML = ''\n"
             "    var H = (typeof window !== 'undefined' && window.HISTORY) ? window.HISTORY : null\n"
             "    if (!H || !H.count) {\n"
             "      box.appendChild(el('p', { 'class': 'muted', text: U.atar_unavailable }))\n"
             "      return\n"
             "    }\n"
             "    box.appendChild(el('p', { text: U.history_intro }))\n"
             "    box.appendChild(el('p', { text: U.history_range\n"
             "      .replace('{count}', String(H.count))\n"
             "      .replace('{lo}', String(H.atarMin)).replace('{hi}', String(H.atarMax)) }))\n"
             "    var caveat = H.cohortCaveat || {}\n"
             "    box.appendChild(el('p', { 'class': 'warn',\n"
             "      text: (LANG === 'zh' ? caveat.zh : caveat.en) || '' }))\n"
             "    box.appendChild(el('p', { 'class': 'muted', text: U.history_bands }))\n"
             "    var bandTable = el('table', { 'class': 'atar-table' })\n"
             "    ;(H.bands || []).forEach(function (b) {\n"
             "      bandTable.appendChild(atarRow(LANG === 'zh' ? (b.labelZh || b.label) : b.label,\n"
             "        String(b.atar)))\n"
             "    })\n"
             "    box.appendChild(bandTable)\n"
             "    // The examples are omitted when the source sheet cannot be split into\n"
             "    // individual students — it has no column marking where one student's\n"
             "    // rows end. Rendering the heading regardless left column labels above\n"
             "    // nothing, which reads as a rendering fault rather than a decision.\n"
             "    var examples = H.examples || []\n"
             "    if (examples.length) {\n"
             "      box.appendChild(el('p', { 'class': 'muted', text: U.history_examples }))\n"
             "      var table = el('table')\n"
             "      var head = el('tr')\n"
             "      ;[U.history_col_atar, U.history_col_top4, U.history_col_marks].forEach(function (h) {\n"
             "        head.appendChild(el('th', { text: h }))\n"
             "      })\n"
             "      table.appendChild(head)\n"
             "      examples.forEach(function (e) {\n"
             "        var tr = el('tr')\n"
             "        tr.appendChild(el('td', { 'class': 'num', text: String(e.atar) }))\n"
             "        tr.appendChild(el('td', { 'class': 'num', text: String(e.top4) }))\n"
             "        var cell = el('td')\n"
             "        ;(e.marks || []).forEach(function (m, i) {\n"
             "          cell.appendChild(el('span', { 'class': 'mark-chip',\n"
             "            text: ((e.codes || [])[i] || '?') + ' ' + m }))\n"
             "        })\n"
             "        tr.appendChild(cell)\n"
             "        table.appendChild(tr)\n"
             "      })\n"
             "      box.appendChild(table)\n"
             "    } else if (H.examplesOmitted) {\n"
             "      box.appendChild(el('p', { 'class': 'warn', text: U.history_omitted }))\n"
             "    }\n"
             "  }\n"
             "  on('btnHistory', 'click', renderHistory)\n\n"
             "  function showTab(which) {",
             "atar panel renderer")

    # Rendered on demand: the course table is 54 rows of data that most visits
    # never open. It listens on the tab bar.
    sub_once("  function showTab(which) {",
             "  function renderCourses() {\n"
             "    var body = $('courseRows')\n"
             "    if (!body) return\n"
             "    var rec = readRecord()\n"
             "    var matched = matchingCourses(rec)\n"
             "    var list = matched.length ? matched : LIBRARY.rows.slice(0, 25)\n"
             "    body.innerHTML = ''\n"
             "    list.forEach(function (c) {\n"
             "      var tr = el('tr')\n"
             "      tr.appendChild(el('td', { text: c.university }))\n"
             "      tr.appendChild(el('td', { text: c.course }))\n"
             "      tr.appendChild(el('td', { 'class': 'num', text: String(c.atar) }))\n"
             "      // A blank requirement cell is NOT the same as 'there is no' +\n"
             "      // requirement' — the source workbook simply leaves the cell empty for\n"
             "      // 44 of the 54 rows. The shared placeholder renders both as an em dash,\n"
             "      // so a student could read a missing record as a stated absence. Named\n"
             "      // differently on purpose.\n"
             "      tr.appendChild(el('td', { 'class': c.req ? '' : 'muted',\n"
             "        text: c.req || pick('blank in the source table — not the same as \"no requirement\"',\n"
             "                             '原表这一格是空的 —— 不等于「没有要求」') }))\n"
             "      var cell = el('td')\n"
             "      if (c.url) {\n"
             "        var mark = c.link === 'ok' ? ''\n"
             "          : (c.link === 'blocked' ? pick(' (not verified)', '（未验证）') : pick(' (section page)', '（院系入口）'))\n"
             "        cell.appendChild(el('a', { href: c.url, target: '_blank',\n"
             "          rel: 'noopener noreferrer', text: pick('verify', '去核对') + mark }))\n"
             "      } else {\n"
             "        cell.appendChild(el('span', { 'class': 'muted',\n"
             "          text: pick('search the institution site', '请在院校官网搜索') }))\n"
             "      }\n"
             "      tr.appendChild(cell)\n"
             "      body.appendChild(tr)\n"
             "    })\n"
             "    var note = $('courseNote')\n"
             "    if (note) {\n"
             "      var total = LIBRARY.count || (LIBRARY.rows || []).length\n"
             "      note.textContent = LANG === 'zh'\n"
             "        ? ('共 ' + total + ' 条课程记录，数据截至 ' + LIBRARY.snapshot + '。' +\n"
             "           (matched.length ? ('已按你填写的条件筛出 ' + matched.length + ' 条。')\n"
             "                           : '没有填国家或方向，先列出前 25 条（按课程库原顺序）。'\n"
             "                             + '填了国家或方向就会按你填的筛。') +\n"
             "           '最低分每轮都会变，请以院校官网为准。')\n"
             "        : (total + ' course records, snapshot ' + LIBRARY.snapshot + '. ' +\n"
             "           (matched.length ? (matched.length + ' match what you entered.')\n"
             "                           : 'No country or field entered, so the first 25 are listed; '\n"
             "                             + 'fill either one and it will filter.') +\n"
             "           ' Minimums change every intake; verify at the institution.')\n"
             "    }\n"
             "  }\n"
             "  // No on('navcourses') here. There is no such element: the courses tab is\n"
             "  // the data-tab button in the tab bar, and showTab calls the renderer via\n"
             "  // TAB_RENDERERS. A binding for a nonexistent id is not harmless — on()\n"
             "  // returns quietly, so it looks wired and is not.\n"
             "  // Every panel the page actually has. A test compares this list to the\n"
             "  // panels in the real markup, because it once omitted 'courses': the tab\n"
             "  // bar offered it, clicking it set aria-selected, and the panel stayed\n"
             "  // hidden forever, so the course table could never be seen at all. A hand\n"
             "  // written list of tab names is exactly the kind of thing that rots\n"
             "  // quietly. The hiding loop below reads THIS list rather than carrying\n"
             "  // its own copy, which is how the omission lasted.\n"
             "  var TAB_PANELS = ['student', 'report', 'tracker', 'courses', 'coverage']\n"
             "  // Panels that fill themselves when first shown. The course table is 54\n"
             "  // rows most visits never open, so rendering it on load would be waste;\n"
             "  // but naming it here rather than in an on-click handler is what keeps the\n"
             "  // list of tabs in ONE place. Fixing TAB_PANELS alone once left the tab\n"
             "  // visible and empty, because the only thing that rendered it was a\n"
             "  // listener on a button the page does not have.\n"
             "  var TAB_RENDERERS = { courses: function () { renderCourses() } }\n\n"
             "  function showTab(which) {",
             "course tab renderer")
    sub_once("    ['student', 'report', 'tracker', 'coverage'].forEach(function (t) {\n"
             "      $('tab-' + t).classList.toggle('hidden', t !== which)\n"
             "    })",
             "    TAB_PANELS.forEach(function (t) {\n"
             "      // A panel this page does not have is skipped, not fatal. The guest\n"
             "      // pages emit no tracker panel, and a null dereference here is what\n"
             "      // once took the whole engine down on the guest page.\n"
             "      var node = $('tab-' + t)\n"
             "      if (!node) return\n"
             "      node.classList.toggle('hidden', t !== which)\n"
             "    })\n"
             "    if (TAB_RENDERERS[which]) TAB_RENDERERS[which]()",
             "showTab reads TAB_PANELS")

    # The tracker is an enrolment tool: without an enrolment there are no school
    # assessments to track. The guest pages simply do not emit its markup, and
    # showTab tolerates a tab that is not on the page. That tolerance lives in the
    # `if (!node) return` guard injected by the TAB_PANELS rewrite above, which is
    # why there is no second replacement here: there used to be, and it became
    # dead the moment the loop started reading the list.

    # ── advice resolution: prefer the catalog's `zh` when the page is Chinese ──
    sub_once(
        "      lines.push(interpolate(item.rule.advice, rec))",
        "      lines.push(interpolate(pick(item.rule.advice, item.rule.zh), rec))",
        "report line advice",
    )
    sub_once(
        "        escapeHtml(interpolate(item.rule.advice, rec)) }))",
        "        escapeHtml(interpolate(pick(item.rule.advice, item.rule.zh), rec)) }))",
        "rendered advice",
    )
    sub_once("      var label = d ? d.label : item.rule.domain", "      var label = d ? domainLabel(d) : item.rule.domain", "domain label in report")
    sub_once("'<span class=\"badge\">' + escapeHtml(d ? d.label : item.rule.domain) + '</span>' +",
             "'<span class=\"badge\">' + escapeHtml(d ? domainLabel(d) : item.rule.domain) + '</span>' +",
             "domain badge")
    sub_once("      tr.appendChild(el('td', { text: d ? d.label : item.rule.domain }))",
             "      tr.appendChild(el('td', { text: d ? domainLabel(d) : item.rule.domain }))",
             "domain cell in coverage")
    sub_once("      cell.appendChild(el('div', { text: item.rule.title || item.rule.id }))",
             "      cell.appendChild(el('div', { text: pick(item.rule.title, item.rule.zhTitle) || item.rule.id }))",
             "rule title in coverage")

    # ── every message a reader can see, in their language ────────────────────
    # The earlier pass replaced only bare quoted fragments, so anything embedded
    # in an HTML string stayed English: a Chinese page said "Record passes
    # validation." and "Saved to this browser only." A student who cannot read the
    # confirmation cannot tell whether their record was accepted.
    sub_once("box.appendChild(el('div', { 'class': 'note err', html: '<strong>Cannot generate a report:</strong>"
             "<ul style=\"margin:6px 0 0 18px\">' +",
             "box.appendChild(el('div', { 'class': 'note err', html: '<strong>' + pick('Cannot generate a report:', '无法生成报告：') + '</strong>"
             "<ul style=\"margin:6px 0 0 18px\">' +", "err heading")
    sub_once("box.appendChild(el('div', { 'class': 'note', html: '<strong>Worth checking:</strong>"
             "<ul style=\"margin:6px 0 0 18px\">' +",
             "box.appendChild(el('div', { 'class': 'note', html: '<strong>' + pick('Worth checking:', '有几处值得核对：') + '</strong>"
             "<ul style=\"margin:6px 0 0 18px\">' +", "warn heading")
    sub_once("box.appendChild(el('div', { 'class': 'note ok', text: 'Record passes validation.' }))",
             "box.appendChild(el('div', { 'class': 'note ok', text: pick('Record passes validation.', '记录通过校验。') }))",
             "ok message")
    # A ternary arm, so the replacement must not add parentheses of its own.
    # Assigning first and using the variable keeps the expression valid.
    sub_once("    $('reportWarnings').innerHTML = check.errors.length\n"
             "      ? '<div class=\"note err\">This report was generated from a record with ' + check.errors.length + ' validation error(s). Treat it as a draft.</div>'\n"
             "      : ''",
             "    var draftWarning = LANG === 'zh'\n"
             "      ? ('这份报告基于一份有 ' + check.errors.length + ' 处校验错误的记录生成，请当作草稿。')\n"
             "      : ('This report was generated from a record with ' + check.errors.length + ' validation error(s). Treat it as a draft.')\n"
             "    $('reportWarnings').innerHTML = check.errors.length\n"
             "      ? '<div class=\"note err\">' + draftWarning + '</div>'\n"
             "      : ''",
             "draft warning")
    sub_once("$('validationBox').innerHTML = '<div class=\"note ok\">Saved to this browser only. Nothing was sent anywhere.</div>'",
             "$('validationBox').innerHTML = '<div class=\"note ok\">' + pick('Saved to this browser only. Nothing was sent anywhere.', '只保存在本浏览器里，没有发送到任何地方。') + '</div>'",
             "save confirmation")
    sub_once("$('validationBox').innerHTML = '<div class=\"note err\">Could not save: ' + escapeHtml(e.message) + '</div>'",
             "$('validationBox').innerHTML = '<div class=\"note err\">' + pick('Could not save: ', '保存失败：') + escapeHtml(e.message) + '</div>'",
             "save failure")
    sub_once("if (!raw) { $('validationBox').innerHTML = '<div class=\"note\">Nothing saved in this browser yet.</div>'; return }",
             "if (!raw) { $('validationBox').innerHTML = '<div class=\"note\">' + pick('Nothing saved in this browser yet.', '本浏览器里还没有保存过记录。') + '</div>'; return }",
             "nothing saved")

    # Bug 3: a capability label used as a noun in the "field / capability"
    # phrase. The English label is "a physical science", which reads as half a
    # sentence in that slot. Moved here because capabilityLabel is created by the
    # label-helpers replacement above; anchoring on it earlier matched nothing.

    # The anchor was `anyInterestMissing: function …`, which no longer exists: it
    # and belowStatedMinimum were removed from the engine with the per-interest
    # minimum ATAR field they served. Anchoring on a helper that is still there is
    # not cosmetic — with a missing anchor the build aborts, and while it aborted
    # the suite went on testing the previous bundle and reported all green,
    # because nothing checked the build's exit code. That hole is now closed in
    # run-suite.ps1; this is the repair it was hiding.
    sub_once("      anyInterestExpectationGap: function (currentScope, args) {",
             "      // Substring match over a field, recording what matched so the\n"
             "      // advice can name it instead of alluding to it.\n"
             "      anyInterestMatching: function (currentScope, args) {\n"
             "        var path = evaluateAst(args[0], currentScope)\n"
             "        var needles = evaluateAst(args[1], currentScope)\n"
             "        var list = Array.isArray(needles) ? needles : [needles]\n"
             "        var hits = []\n"
             "        record.interests.forEach(function (interest) {\n"
             "          var value = String(resolvePath({ i: interest, item: interest }, path) || '')\n"
             "          list.forEach(function (needle) {\n"
             "            if (value && value.toLowerCase().indexOf(String(needle).toLowerCase()) !== -1\n"
             "                && hits.indexOf(value) === -1) hits.push(value)\n"
             "          })\n"
             "        })\n"
             "        if (hits.length) currentScope.__matched = hits.join(LANG === 'zh' ? '、' : '; ')\n"
             "        return hits.length > 0\n"
             "      },\n\n"
             "      // fieldPath -> a capability field the stated course expectation requires.\n"
             "      anyInterestExpectationGap: function (currentScope, args) {",
             "anyInterestMatching helper")

    # ── the two course-comparison helpers ────────────────────────────────────
    # Both read the library at phrase time, so every number in the advice comes
    # from the data rather than from anything written into a condition.
    sub_once("      anyInterestMatching: function (currentScope, args) {",
             "      // True when the recorded interests match at least one library row.\n"
             "      anyInterestHasCourses: function (currentScope, args) {\n"
             "        var cmp = atarComparison(currentScope.record, matchingCourses(currentScope.record))\n"
             "        if (!cmp) return false\n"
             "        currentScope.__standing = cmp.standing\n"
             "        currentScope.__courseCount = cmp.count\n"
             "        if (cmp.nearest) {\n"
             "          currentScope.__nearest = courseSetLabel(matchingCourses(currentScope.record), cmp.nearest)\n"
             "          currentScope.__gap = Math.round((cmp.nearest.atar - cmp.standing) * 10) / 10\n"
             "        }\n"
             "        return cmp.count > 0\n"
             "      },\n"
             "      // True when the standing reaches at least one recorded minimum.\n"
             "      anyReachableCourse: function (currentScope, args) {\n"
             "        var cmp = atarComparison(currentScope.record, matchingCourses(currentScope.record))\n"
             "        if (!cmp) return false\n"
             "        currentScope.__standing = cmp.standing\n"
             "        currentScope.__courseCount = cmp.count\n"
             "        if (cmp.reachable) currentScope.__reachable = courseSetLabel(matchingCourses(currentScope.record), cmp.reachable)\n"
             "        if (cmp.nearest) {\n"
             "          currentScope.__nearest = courseSetLabel(matchingCourses(currentScope.record), cmp.nearest)\n"
             "          currentScope.__gap = Math.round((cmp.nearest.atar - cmp.standing) * 10) / 10\n"
             "        }\n"
             "        return !!cmp.reachable\n"
             "      },\n"
             "      // True when the nearest recorded minimum ABOVE the standing is within\n"
             "      // the margin: the near-miss case, which neither helper above can\n"
             "      // express. anyReachableCourse means you are already past something;\n"
             "      // anyInterestHasCourses means a comparison is possible at all. This\n"
             "      // one is the only shape that says 'this close'.\n"
             "      nearestAboveWithin: function (currentScope, args) {\n"
             "        var margin = Number(evaluateAst(args[0], currentScope))\n"
             "        var cmp = atarComparison(currentScope.record, matchingCourses(currentScope.record))\n"
             "        if (!cmp || isNaN(margin)) return false\n"
             "        currentScope.__standing = cmp.standing\n"
             "        currentScope.__courseCount = cmp.count\n"
             "        if (cmp.nearest) {\n"
             "          currentScope.__nearest = courseSetLabel(matchingCourses(currentScope.record), cmp.nearest)\n"
             "          currentScope.__gap = Math.round((cmp.nearest.atar - cmp.standing) * 10) / 10\n"
             "        }\n"
             "        if (!cmp.nearest) return false\n"
             "        return cmp.nearest.atar - cmp.standing <= margin\n"
             "      },\n"
             "      // True when at least one recorded choice matches no library course.\n"
             "      // anyInterestHasCourses unions across choices, so a single unmatched\n"
             "      // choice disappears from the comparison with nothing said about it:\n"
             "      // the student sees a comparison that silently covers fewer choices\n"
             "      // than they entered. This asks per-choice, which is the only way to\n"
             "      // notice the one that dropped out.\n"
             "      anyInterestUnmatched: function (currentScope, args) {\n"
             "        var any = false\n"
             "        ;(currentScope.record.interests || []).forEach(function (i) {\n"
             "          if (!i.country && !i.field && !i.university) return\n"
             "          any = true\n"
             "        })\n"
             "        if (!any) return false\n"
             "        return (currentScope.record.interests || []).some(function (i) {\n"
             "          if (!i.country && !i.field && !i.university) return false\n"
             "          return matchingCourses({ interests: [i] }).length === 0\n"
             "        })\n"
             "      },\n"
             "      // The field roadmap. True only when the student named a field the\n"
             "      // roadmap covers, so the rule stays silent rather than printing a\n"
             "      // generic paragraph — filler advice in a report is worse than a gap.\n"
             "      // The scope slots are filled by primeRoadmap() BEFORE evaluation:\n"
             "      // these helpers return their own boolean, so nothing after that\n"
             "      // return would ever run, and a first version of this that set the\n"
             "      // slots here instead produced '—' in the prose.\n"
             "      roadmapFor: function (currentScope, args) {\n"
             "        return roadmapRow(currentScope.record) !== null\n"
             "      },\n"
             "      timelineFor: function (currentScope, args) {\n"
             "        return timelineParts(currentScope.record).length > 0\n"
             "      },\n"
             "      optionsFor: function (currentScope, args) {\n"
             "        return optionParts().length > 0\n"
             "      },\n"
             "      // True when at least one recorded course for the stated interest\n"
             "      // names a prerequisite subject the student has not taken. The prose\n"
             "      // value is primed by primeModuleScope, for the same reason as the\n"
             "      // others: a helper's own return makes later statements dead code.\n"
             "      anyNamedPrereqMissing: function (currentScope, args) {\n"
             "        return namedPrereqParts(currentScope.record).length > 0\n"
             "      },\n\n"
             "      anyInterestMatching: function (currentScope, args) {",
             "course comparison helpers")


    # The rule-scope plumbing lives with the compiled-rule replacement below:
    # the lines it edits are introduced there, so anchoring on them here would
    # match nothing.



    # ── the advice must name specifics, not just point at categories ─────────
    # "at least one of your choices expects preparation you have not recorded"
    # is true and useless: it does not say which choice, or which subject. The
    # capability layer already knows both, so the helpers now record what they
    # found and the prose interpolates it. That is the difference between advice
    # and a category label.
    sub_once("      anyInterestExpectationGap: function (currentScope, args) {",
             "      anyInterestExpectationGap: function (currentScope, args) {\n"
             "        var __gaps = []", "gap collector")
    src = src.replace(
        "        return record.interests.some(function (interest) {\n"
        "          var field = resolvePath({ i: interest, item: interest }, path)\n"
        "          var expectation = expectationFor(field)\n"
        "          if (!expectation) return false\n"
        "          return expectation.expects.some(function (key) { return !hasCapability(subjects, key) })\n"
        "        })\n"
        "      },",
        "        record.interests.forEach(function (interest) {\n"
        "          var field = resolvePath({ i: interest, item: interest }, path)\n"
        "          var expectation = expectationFor(field)\n"
        "          if (!expectation) return\n"
        "          expectation.expects.forEach(function (key) {\n"
        "            if (capabilityKnown(key) && !hasCapability(subjects, key))\n              __gaps.push(field + '\u0000' + key)\n"
        "          })\n"
        "        })\n"
        "        if (__gaps.length) currentScope.__gapFields = renderGaps(__gaps)\n"
        "        return __gaps.length > 0\n"
        "      },", 1)
    sub_once("      anyInterestOptionalGap: function (currentScope, args) {",
             "      anyInterestOptionalGap: function (currentScope, args) {\n"
             "        var __opts = []", "optional collector")
    src = src.replace(
        "        return record.interests.some(function (interest) {\n"
        "          var field = resolvePath({ i: interest, item: interest }, path)\n"
        "          var expectation = expectationFor(field)\n"
        "          if (!expectation || !expectation.optional.length) return false\n"
        "          if (expectation.expects.some(function (key) { return !hasCapability(subjects, key) })) return false\n"
        "          return expectation.optional.some(function (key) { return !hasCapability(subjects, key) })\n"
        "        })\n"
        "      },",
        "        record.interests.forEach(function (interest) {\n"
        "          var field = resolvePath({ i: interest, item: interest }, path)\n"
        "          var expectation = expectationFor(field)\n"
        "          if (!expectation || !expectation.optional.length) return\n"
        "          // Silent while a required capability is still missing: the gap\n"
        "          // message is the one that matters, two hints read as noise.\n"
        "          if (expectation.expects.some(function (key) { return !hasCapability(subjects, key) })) return\n"
        "          expectation.optional.forEach(function (key) {\n"
        "            // A capability nobody defined is skipped, never reported as a\n"
        "            // gap: hasCapability answers false for an unknown key, so a\n"
        "            // typo would otherwise name every subject as missing.\n"
        "            if (capabilityKnown(key) && !hasCapability(subjects, key))\n"
        "              __opts.push(field + '\u0000' + key)\n"
        "          })\n"
        "        })\n"
        "        if (__opts.length) currentScope.__optionalFields = renderGaps(__opts)\n"
        "        return __opts.length > 0\n"
        "      },", 1)
    sub_once("  function expectationFor(field) {",
             "  // The label a reader recognises, in their language. Both halves of a\n"
             "  // gap phrase go through here, or the advice reads \"Engineering / 物理或化学\"\n"
             "  // with the two languages spliced together.\n"
             "  function capabilityLabel(key) {\n"
             "    var cap = R.capabilities && R.capabilities[key]\n"
             "    if (!cap) return key\n"
             "    return (LANG === 'zh' && cap.zhLabel) ? cap.zhLabel : cap.label\n"
             "  }\n"
             "  // A capability nobody defined is skipped, never treated as missing:\n"
             "  // hasCapability answers false for an unknown key, so a typo in an\n"
             "  // expectation would otherwise report every subject as a gap.\n"
             "  function capabilityKnown(key) {\n"
             "    var cap = R.capabilities && R.capabilities[key]\n"
             "    return !!(cap && cap.subjects && cap.subjects.length)\n"
             "  }\n"
             "  function fieldLabel(key) {\n"
             "    var exp = expectationFor(key)\n"
             "    if (exp && LANG === 'zh' && exp.zhLabel) return exp.zhLabel\n"
             "    var zh = (R.fieldLabelsZh && R.fieldLabelsZh[key])\n"
             "    if (LANG === 'zh' && zh) return zh\n"
             "    return key\n"
             "  }\n"
             "  // Gaps are collected as field<NUL>capability so two interests in the\n"
             "  // same field collapse to one phrase. Keying on the finished phrase\n"
             "  // failed: the phrase carries the field name, so a repeat never looks\n"
             "  // like a duplicate of itself.\n"
             "  function renderGaps(list) {\n"
             "    var seen = {}\n"
             "    var parts = []\n"
             "    list.forEach(function (entry) {\n"
             "      if (seen[entry]) return\n"
             "      seen[entry] = true\n"
             "      var bits = entry.split('\\u0000')\n"
             "      parts.push(fieldLabel(bits[0]) + ' / ' + capabilityLabel(bits[1]))\n"
             "    })\n"
             "    return parts.join(LANG === 'zh' ? '、' : '; ')\n"
             "  }\n\n"
             "  function expectationFor(field) {",
             "label helpers")

    sub_once("  function capabilityLabel(key) {",
             "  function capabilityLabel(key) {\n"
             "    // Standalone noun for the \"field / capability\" phrase: the English\n"
             "    // label 'a physical science' reads as half a sentence there.\n"
             "    var standalone = { physicalScience: { en: 'Physics or Chemistry', zh: '物理或化学' } }\n"
             "    var fixed = standalone[key]\n"
             "    if (fixed) return LANG === 'zh' ? fixed.zh : fixed.en",
             "standalone capability label")



    # Interpolation gains a per-rule scope, so {{gapFields}} resolves to the real
    # missing subjects instead of a generic phrase.
    sub_once("  function interpolate(text, record) {\n"
             "    return String(text).replace(/\\{\\{(\\w+)\\}\\}/g, function (whole, key) {",
             "  function interpolate(text, record, extra) {\n"
             "    var scope = extra || {}\n"
             "    // Optional clauses. A rule may fire in a case where one of its tokens\n"
             "    // has nothing to say — reaching a course with no course above you is\n"
             "    // the ordinary case, not an error — and substituting '—' there leaves\n"
             "    // half a sentence behind (\"the nearest one above you is —, — points\n"
             "    // away\"). {{#if key}} … {{/if}} drops the clause entirely when the key\n"
             "    // is absent, empty, or false. Unmatched markers are stripped so a\n"
             "    // typo shows up as missing text, not as braces on the page.\n"
             "    text = String(text).replace(/\\{\\{#if (\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/if\\}\\}/g,\n"
             "      function (whole, key, body) {\n"
             "        var v = Object.prototype.hasOwnProperty.call(scope, key) ? scope[key] : null\n"
             "        if (v === null || v === undefined || v === '' || v === false) return ''\n"
             "        return body\n"
             "      })\n"
             "    text = String(text).replace(/\\{\\{[#/]if \\w+\\}\\}|\\{\\{\\/if\\}\\}/g, '')\n"
             "    return String(text).replace(/\\{\\{(\\w+)\\}\\}/g, function (whole, key) {\n"
             "      if (Object.prototype.hasOwnProperty.call(scope, key)) return String(scope[key])",
             "interpolate takes a rule scope")
    sub_once("      compiled[rule.id] = function (record, helpers) {\n"
             "        return evaluateAst(ast, Object.assign({ record: record, T: R.thresholds }, helpers))\n"
             "      }",
             "      compiled[rule.id] = function (record, helpers, ruleScope) {\n"
             "        var scope = Object.assign({ record: record, T: R.thresholds }, helpers)\n"
             "        scope.__gapFields = null\n"
             "        scope.__optionalFields = null\n"
             "        var result = evaluateAst(ast, scope)\n"
             "        if (ruleScope) {\n"
             "          if (scope.__gapFields) ruleScope.gapFields = scope.__gapFields\n"
             "          if (scope.__optionalFields) ruleScope.optionalFields = scope.__optionalFields\n"
             "        }\n"
             "        return result\n"
             "      }",
             "compiled passes a rule scope")

    # The rule-scope plumbing the naming helpers need: __matched carries what
    # anyInterestMatching found, __gapFields what the expectation helpers found,
    # and both reach the prose through the per-rule scope. Placed here because
    # the lines it edits are introduced by the replacement just above.
    for old_line, new_line in [
        ("        scope.__gapFields = null\n",
         "        scope.__gapFields = null\n        scope.__matched = null\n"),
        ("          if (scope.__gapFields) ruleScope.gapFields = scope.__gapFields\n",
         "          if (scope.__gapFields) ruleScope.gapFields = scope.__gapFields\n"
         "          if (scope.__matched) ruleScope.waUniversities = scope.__matched\n"),
    ]:
        if src.count(old_line) != 1:
            raise SystemExit(f"rule-scope line matched {src.count(old_line)} times")
        src = src.replace(old_line, new_line, 1)

    sub_once("        scope.__matched = null\n",
             "        scope.__matched = null\n"
             "        scope.__standing = null\n        scope.__reachable = null\n"
             "        scope.__nearest = null\n        scope.__gap = null\n        scope.__courseCount = null\n"
             "        scope.__roadmapField = null\n        scope.__roadmapCareers = null\n"
             "        scope.__roadmapActivities = null\n        scope.__roadmapSkills = null\n"
             "        scope.__roadmapWhy = null\n        scope.__timelineList = null\n"
             "        scope.__optionsList = null\n",
             "course comparison scope slots")

    sub_once("        outcome.fired = !!compiled[rule.id](rec, helpers)",
             "        var ruleScope = {}\n"
             "        outcome.fired = !!compiled[rule.id](rec, helpers, ruleScope)\n"
             "        outcome.scope = ruleScope",
             "capture rule scope")
    # Prime the module tokens from the record BEFORE each rule runs, then hand
    # them to the prose. See primeModuleScope for why this is not inside the
    # helpers.
    sub_once("        var ruleScope = {}\n",
             "        var ruleScope = primeModuleScope(rec, {})\n",
             "prime the roadmap scope")
    sub_once("          if (scope.__matched) ruleScope.waUniversities = scope.__matched\n",
             "          if (scope.__matched) ruleScope.waUniversities = scope.__matched\n"
             "          if (scope.__standing !== null && scope.__standing !== undefined) ruleScope.standing = scope.__standing\n"
             "          if (scope.__reachable) ruleScope.reachableCourse = scope.__reachable\n"
             "          if (scope.__nearest) ruleScope.nearestCourse = scope.__nearest\n"
             "          if (scope.__gap !== null && scope.__gap !== undefined) ruleScope.atarGap = scope.__gap\n"
             "          if (scope.__courseCount) ruleScope.courseCount = scope.__courseCount\n"
             "          if (scope.__roadmapField) ruleScope.roadmapField = scope.__roadmapField\n"
             "          if (scope.__roadmapCareers) ruleScope.roadmapCareers = scope.__roadmapCareers\n"
             "          if (scope.__roadmapActivities) ruleScope.roadmapActivities = scope.__roadmapActivities\n"
             "          if (scope.__roadmapSkills) ruleScope.roadmapSkills = scope.__roadmapSkills\n"
             "          if (scope.__roadmapWhy) ruleScope.roadmapWhy = scope.__roadmapWhy\n"
             "          if (scope.__timelineList) ruleScope.timelineList = scope.__timelineList\n"
             "          if (scope.__optionsList) ruleScope.optionsList = scope.__optionsList\n",
             "course comparison scope wiring")

    sub_once("      lines.push(interpolate(pick(item.rule.advice, item.rule.zh), rec))",
             "      lines.push(stripEmphasis(interpolate(pick(item.rule.advice, item.rule.zh), rec, item.scope)))",
             "export line uses the rule scope")
    sub_once("        escapeHtml(interpolate(pick(item.rule.advice, item.rule.zh), rec)) }))",
             "        emphasise(escapeHtml(interpolate(pick(item.rule.advice, item.rule.zh), rec, item.scope))) }))",
             "rendered advice uses the rule scope")

    # ── a translated source line, and no literal markup in the prose ─────────
    # The advice is inserted as escaped HTML, so a **bold** marker reached the
    # screen as two asterisks. Emphasis now becomes a real element, added after
    # escaping so the escape step cannot flatten it, and the plain-text export
    # drops it entirely.
    sub_once("  function escapeHtml(s) {",
             "  function emphasise(escaped) {\n"
             "    return String(escaped).replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>')\n"
             "  }\n"
             "  function stripEmphasis(text) {\n"
             "    return String(text).replace(/\\*\\*([^*]+)\\*\\*/g, '$1')\n"
             "  }\n\n  function escapeHtml(s) {",
             "emphasis helpers")
    # Anchored on escapeHtml, which IS in the source. Anchoring on localiseReason
    # would match nothing: that function is created by a later replacement, so at
    # this point in the pipeline it does not exist yet.
    sub_once("  function escapeHtml(s) {",
             "  // Some sources are internal markers; the rest are instructions telling a\n"
             "  // human where to look, so they stay as written. Translating those would\n"
             "  // hide the only actionable part of the line.\n"
             "  function sourceLabel(src) {\n"
             "    if (src === 'internal') return LANG === 'zh' ? '站内判断' : 'internal'\n"
             "    return src\n"
             "  }\n\n  function escapeHtml(s) {",
             "source label")
    sub_once("      $('reportBody').appendChild(el('span', { 'class': 'src',\n"
             "        text: 'rule: ' + item.rule.id + ' · source: ' + item.rule.source +\n"
             "              (item.rule.verified ? ' · verified ' + item.rule.verified : ' · NOT VERIFIED') }))",
             "        var srcLine = LANG === 'zh'\n"
             "          ? ('规则：' + item.rule.id + ' · 依据：' + sourceLabel(item.rule.source) +\n"
             "             (item.rule.verified ? ' · 核实于 ' + item.rule.verified : ' · 待核实'))\n"
             "          : ('rule: ' + item.rule.id + ' · source: ' + item.rule.source +\n"
             "             (item.rule.verified ? ' · verified ' + item.rule.verified : ' · NOT VERIFIED'))\n"
             "        $('reportBody').appendChild(el('span', { 'class': 'src', text: srcLine }))",
             "translated source line")
    sub_once("      lines.push('   [rule: ' + item.rule.id + ' · source: ' + item.rule.source + ']')",
             "      lines.push(LANG === 'zh'\n"
             "        ? ('   [规则：' + item.rule.id + ' · 依据：' + sourceLabel(item.rule.source) + ']')\n"
             "        : ('   [rule: ' + item.rule.id + ' · source: ' + item.rule.source + ']'))",
             "export source line")


    # report header
    sub_once("    lines.push(R.meta.title.toUpperCase())",
             "    lines.push(LANG === 'zh' ? '升学自检报告' : R.meta.title.toUpperCase())", "report title")
    # The report is no longer addressed to anyone: the name field is gone, so a
    # header that read "学生：（未填姓名）" on every single report would be noise.
    sub_once("    lines.push('Advising report for ' + (rec.fullName || '(unnamed)'))",
             "    lines.push(LANG === 'zh' ? '升学自检报告' : 'Advising self-check report')",
             "report subject")
    sub_once("    if (rec.studentId) lines.push('Student ID: ' + rec.studentId)\n",
             "",
             "report student id")
    # The name was also a validation error, and because the field is gone it was
    # about to fire on every report: "Full name is required" on a form with no
    # name field. That is the shape of bug this project has shipped before.
    sub_once("    if (!rec.fullName) errors.push('Full name is required — the report is addressed to the student.')\n",
             "",
             "name validation")
    sub_once("  var TAB_PANELS = ['student', 'report', 'tracker', 'courses', 'coverage']",
             "  var TAB_PANELS = ['student', 'report', 'courses', 'coverage']",
             "tab panels")
    # The cohort CSV loses the two columns whose fields are gone. A `name` column
    # that is empty on every row is worse than no column: it invites the reader to
    # think the export dropped something.
    sub_once("      name: rec.fullName || '',\n", "", "csv name")
    sub_once("      notes: rec.notes || '',\n", "", "csv notes")
    sub_once("  var CSV_HEADERS = ['name', 'country', 'field', 'university', 'targetAtar',\n"
             "                     'computedAtar', 'subjectCount', 'aggregate', 'convertedAtar',\n"
             "                     'subjects', 'notes']",
             "  var CSV_HEADERS = ['country', 'field', 'university', 'targetAtar',\n"
             "                     'computedAtar', 'subjectCount', 'aggregate', 'convertedAtar',\n"
             "                     'subjects']",
             "csv headers")
    sub_once("    lines.push('Generated: ' + new Date().toLocaleString())",
             "    lines.push((LANG === 'zh' ? '生成时间：' : 'Generated: ') + new Date().toLocaleString())", "timestamp")
    sub_once("    if (fired.length === 0) lines.push('No rule conditions were met. The record may be too sparse to advise on.')",
             "    if (fired.length === 0) lines.push(pick('No rule conditions were met. The record may be too sparse to advise on.', '没有命中任何规则，可能是记录信息太少，不足以给出建议。'))",
             "empty report")
    sub_once("      lines.push('Best ' + R.calibration.aggregateSize + ' subject marks total ' +\n"
             "        (picture.aggregate === null ? '(not countable)' : picture.aggregate.toFixed(1)) + '.')",
             "      lines.push(LANG === 'zh'\n"
             "        ? ('最好的 ' + R.calibration.aggregateSize + ' 门科目合计 ' +\n"
             "           (picture.aggregate === null ? '（无法计入）' : picture.aggregate.toFixed(R.calibration.display.aggregate)) + '。')\n"
             "        : ('Best ' + R.calibration.aggregateSize + ' subject marks total ' +\n"
             "           (picture.aggregate === null ? '(not countable)' : picture.aggregate.toFixed(R.calibration.display.aggregate)) + '.'))",
             "aggregate line")
    sub_once("        lines.push('Indicative ATAR: ' + picture.atar.toFixed(2))",
             "        lines.push(LANG === 'zh' ? ('参考 ATAR：' + picture.atar.toFixed(R.calibration.display.atar))\n"
             "                                : ('Indicative ATAR: ' + picture.atar.toFixed(R.calibration.display.atar)))",
             "atar line")
    sub_once("          lines.push('Target ' + picture.target + ' needs an aggregate of ' +\n"
             "            picture.neededAggregate.toFixed(1) + ' (' + picture.neededPerSubject.toFixed(1) +\n"
             "            ' per subject across ' + R.calibration.aggregateSize + ').')",
             "          lines.push(LANG === 'zh'\n"
             "            ? ('目标 ' + picture.target + ' 需要合成分 ' + picture.neededAggregate.toFixed(R.calibration.display.aggregate) +\n"
             "               '（' + R.calibration.aggregateSize + ' 门平均 ' + picture.neededPerSubject.toFixed(R.calibration.display.aggregate) + '）。')\n"
             "            : ('Target ' + picture.target + ' needs an aggregate of ' +\n"
             "               picture.neededAggregate.toFixed(R.calibration.display.aggregate) + ' (' + picture.neededPerSubject.toFixed(R.calibration.display.aggregate) +\n"
             "               ' per subject across ' + R.calibration.aggregateSize + ').'))",
             "target aggregate line")
    sub_once("          lines.push(picture.gapToTarget > 0\n"
             "            ? 'That is ' + picture.gapToTarget.toFixed(1) + ' above where you are.'\n"
             "            : 'You are already ' + Math.abs(picture.gapToTarget).toFixed(1) + ' above what that target needs.')",
             "          lines.push(picture.gapToTarget > 0\n"
             "            ? (LANG === 'zh' ? ('比你现在高 ' + picture.gapToTarget.toFixed(R.calibration.display.aggregate) + '。')\n"
             "                             : ('That is ' + picture.gapToTarget.toFixed(R.calibration.display.aggregate) + ' above where you are.'))\n"
             "            : (LANG === 'zh' ? ('你已经比这个目标需要的水平高 ' + Math.abs(picture.gapToTarget).toFixed(R.calibration.display.aggregate) + '。')\n"
             "                             : ('You are already ' + Math.abs(picture.gapToTarget).toFixed(R.calibration.display.aggregate) + ' above what that target needs.')))",
             "gap line")
    sub_once("          lines.push('Target ' + picture.target + ' is outside the range this conversion can answer for.')",
             "          lines.push(LANG === 'zh'\n"
             "            ? ('目标 ' + picture.target + ' 超出这个换算能回答的范围。')\n"
             "            : ('Target ' + picture.target + ' is outside the range this conversion can answer for.'))",
             "target out of range")
    sub_once("        lines.push('No ATAR is reported: ' + picture.reason + '.')",
             "        lines.push(LANG === 'zh' ? ('不给 ATAR 数字：' + picture.reason + '。')\n"
             "                                : ('No ATAR is reported: ' + picture.reason + '.'))",
             "no atar line")
    sub_once("        lines.push('   [Refusing to guess is the point — a number here would look authoritative and be wrong.]')",
             "        lines.push(LANG === 'zh'\n"
             "          ? '   [这里拒绝猜是有意的——给个数字会显得权威，而且是错的。]'\n"
             "          : '   [Refusing to guess is the point — a number here would look authoritative and be wrong.]')",
             "no atar note")
    sub_once("      lines.push('— AGGREGATE CONVERSION —')",
             "      lines.push(LANG === 'zh' ? '— 合成分换算 —' : '— AGGREGATE CONVERSION —')", "aggregate heading")
    sub_once("      lines.push('— NOTES —')",
             "      lines.push(LANG === 'zh' ? '— 备注 —' : '— NOTES —')", "notes heading")
    sub_once("        lines.push('   [' + R.calibration.caveat + ']')",
             "        lines.push('   [' + calText('caveat') + ']')",
             "report caveat in the reader's language")
    sub_once("    var currentDomain = null", "    var currentDomain = null", "noop")

    # section headings in the report
    src = src.replace("        lines.push('— ' + label.toUpperCase() + ' —')",
                      "        lines.push('— ' + (LANG === 'zh' ? label : label.toUpperCase()) + ' —')")

    # coverage summary sentence
    #
    # The count comes from renderCoverage's own `firedCount`, not from a report:
    # the tab is rendered on arrival as well as after generating, so it cannot
    # assume a report exists.
    summary_en = ("R.rules.length + ' rules in catalog · ' + firedCount + "
                  "' fired · ' + unverified + ' awaiting verification · ' + disabled + ' disabled.'")
    summary_zh = ("'规则库共 ' + R.rules.length + ' 条 · ' + firedCount + "
                  "' 条命中 · ' + unverified + ' 条待核实 · ' + disabled + ' 条已停用。'")
    note_en = "' Rules marked <em>verify</em> make a factual claim that a human has not yet confirmed against a current source.'"
    note_zh = "'标记为「待核实」的规则含有尚未对照当前来源确认的事实性表述。'"
    sub_once(
        "    $('coverageSummary').innerHTML =\n"
        "      '<div class=\"note' + (unverified ? '' : ' ok') + '\"><strong>' + R.rules.length + ' rules in catalog · ' +\n"
        "      firedCount + ' fired · ' + unverified + ' awaiting verification · ' + disabled + ' disabled.</strong>' +\n"
        "      (unverified ? ' Rules marked <em>verify</em> make a factual claim that a human has not yet confirmed against a current source.' : '') +\n"
        "      '</div>'",
        "    var summaryLine = LANG === 'zh'\n"
        f"      ? ({summary_zh})\n"
        f"      : ({summary_en})\n"
        "    var verifyNote = LANG === 'zh'\n"
        f"      ? {note_zh}\n"
        f"      : {note_en}\n"
        "    $('coverageSummary').innerHTML =\n"
        "      '<div class=\"note' + (unverified ? '' : ' ok') + '\"><strong>' + summaryLine + '</strong>' +\n"
        "      (unverified ? verifyNote : '') + '</div>'",
        "coverage summary",
    )
    sub_once("      tr.appendChild(el('td', { html: item.fired ? '<span class=\"badge\">yes</span>' : '<span class=\"badge off\">no</span>' }))",
             "      tr.appendChild(el('td', { html: item.fired ? '<span class=\"badge\">' + (LANG === 'zh' ? '是' : 'yes') + '</span>' : '<span class=\"badge off\">' + (LANG === 'zh' ? '否' : 'no') + '</span>' }))",
             "fired badge")
    sub_once("        : '<span class=\"badge warn\">verify</span>' }))",
             "        : '<span class=\"badge warn\">' + (LANG === 'zh' ? '待核实' : 'verify') + '</span>' }))", "verify badge")
    sub_once("      if (item.reason) cell.appendChild(el('div', { 'class': 'muted', text: '→ ' + item.reason }))",
             "      if (item.reason) cell.appendChild(el('div', { 'class': 'muted', text: '→ ' + localiseReason(item.reason) }))",
             "reason line")

    # Validation warnings the user reads. These are built by concatenation in the
    # engine, so each fragment is replaced exactly rather than matched as a whole
    # sentence. Every fragment must be found: a silently skipped one would leave
    # an English sentence inside a Chinese report.
    fragment_pairs = [
        # The full-name fragment is gone with the name field. It cannot stay in
        # this list: the line it localises is deleted earlier in this function,
        # and the count assertion below would fail on a fragment that no longer
        # exists anywhere.
        "'At least one subject is required.'",
        "': subject name is empty.'",
        "': mark must be between 0 and 100.'",
        "'Duplicate subject recorded: '",
        "': no country selected, so destination rules cannot fire.'",
        "': no field selected, so course rules cannot fire.'",
        "'Rule \"'",
        "'\" cannot be evaluated: '",
    ]
    translations = {
        "'At least one subject is required.'": "至少需要填写一门科目。",
        "': subject name is empty.'": "：科目名为空。",
        "': mark must be between 0 and 100.'": "：成绩必须在 0 到 100 之间。",
        "'Duplicate subject recorded: '": "科目重复：",
        "': no country selected, so destination rules cannot fire.'": "：未选择国家，方向类规则不会触发。",
        "': no field selected, so course rules cannot fire.'": "：未选择专业方向，专业类规则不会触发。",
    }
    # Iterate the translations, not a slice of the fragment list. The slice was
    # `[:9]` against a list that has since shrunk, so it ran one entry past the
    # last translated fragment and failed on a KeyError. Driving the loop from the
    # dictionary removes the coupling between two lists that must agree.
    for source_fragment in list(translations):
        if src.count(source_fragment) != 1:
            raise SystemExit(
                f"validation fragment matched {src.count(source_fragment)} times: {source_fragment}")
        zh = translations[source_fragment]
        src = src.replace(source_fragment, f"pick({source_fragment}, '{js_string(zh)}')", 1)

    # the rule-compile error sentence
    src = src.replace(
        "errors.push('Rule \"' + id + '\" cannot be evaluated: ' + compileErrors[id] + '.')",
        "errors.push(pick('Rule \"' + id + '\" cannot be evaluated: ', '规则「' + id + '」无法求值：') + compileErrors[id] + '.')",
        1,
    )

    # reason strings from the evaluator
    sub_once("      if (rule.enabled === false) { outcome.reason = 'disabled in catalog'; return outcome }",
             "      if (rule.enabled === false) { outcome.reason = pick('disabled in catalog', '规则库中已停用'); return outcome }",
             "disabled reason")
    sub_once("      if (compileErrors[rule.id]) { outcome.reason = 'compile error: ' + compileErrors[rule.id]; return outcome }",
             "      if (compileErrors[rule.id]) { outcome.reason = pick('compile error: ', '编译错误：') + compileErrors[rule.id]; return outcome }",
             "compile reason")
    sub_once("        outcome.reason = 'threw: ' + error.message",
             "        outcome.reason = pick('threw: ', '求值出错：') + error.message", "threw reason")

    # a tiny localiser for the reason strings the renderer receives
    sub_once("  function escapeHtml(s) {",
             "  function localiseReason(reason) {\n"
             "    if (LANG !== 'zh') return reason\n"
             "    return reason\n"
             "      .replace(/^disabled in catalog/, '规则库中已停用')\n"
             "      .replace(/^compile error: /, '编译错误：')\n"
             "      .replace(/^threw: /, '求值出错：')\n"
             "  }\n\n  function escapeHtml(s) {", "reason localiser")

    # Storage used to be keyed per language AND per mode, because a draft from the
    # enrolled page must not be restored onto the guest page, where the record
    # shape differed. There is one page per language now, so the mode key is gone
    # — and with it the engine's MODE variable, which has nothing left to read.
    sub_once("  var STORAGE_KEY = 'advising-workbook-record-v1'",
             "  var STORAGE_KEY = 'advising-workbook-record-v2-' + LANG", "storage key")
    # v2, not v1: the record shape changed (six fields removed), so a draft saved
    # by the old build must not be silently half-restored. A new key means the old
    # draft is simply not found, which is the honest outcome.
    sub_once("  var MODE = (function () {\n"
             "    var v = document.documentElement.dataset.mode || 'student'\n"
             "    return v === 'guest' ? 'guest' : 'student'\n"
             "  })()\n",
             "",
             "mode variable")
    # The engine used to filter rules by mode here. There is no mode and no
    # filtered rule set left, so the variable that held it is gone from the
    # injected preamble and nothing needs neutering.


    (ASSETS / "advising.js").write_text(src, encoding="utf-8")
    print("  engine: written to assets/advising.js")
    return True


# ── 3. styles: keep the site palette, scope every override ──────────────────
CSS_HEADER = """/* ─────────────────────────────────────────────────────────────
   升学自检 · 仅此页使用的样式
   配色全部沿用 assets/style.css 的变量：这里不定义任何颜色，
   换整站配色时本文件不需要改。
   类名统一加 .advising 前缀作用域，避免影响站内其他页面。
   ───────────────────────────────────────────────────────────── */

/* 表单与数据表比阅读栏宽，只放宽这一页 */
body.advising-wide .wrap { max-width: 1180px; }

.advising .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
@media (max-width: 900px) { .advising .grid { grid-template-columns: 1fr; } }

.advising .card {
  border: 1px solid var(--line); border-radius: var(--radius);
  padding: 4px 18px 14px; margin: 0 0 18px; background: var(--bg-soft);
}
.advising .card > h2 {
  font-size: .82rem; letter-spacing: .1em; text-transform: uppercase;
  color: var(--text-soft); margin: 18px 0 12px;
}

.advising nav.tabs { display: flex; gap: 6px; flex-wrap: wrap; margin: 0 0 22px; }
.advising nav.tabs button {
  font: inherit; font-size: .9rem; cursor: pointer;
  padding: 7px 14px; border: 1px solid var(--line); border-radius: 6px;
  background: var(--bg); color: var(--text-soft);
}
.advising nav.tabs button[aria-selected="true"] {
  background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600;
}

.advising label { display: block; font-size: .84rem; color: var(--text-soft); margin-bottom: 4px; }
.advising input[type=text], .advising input[type=number], .advising input[type=date],
.advising select, .advising textarea {
  width: 100%; padding: 7px 9px; font: inherit; font-size: .92rem;
  border: 1px solid var(--line); border-radius: 6px;
  background: var(--bg); color: var(--text);
}
.advising input:focus, .advising select:focus, .advising textarea:focus {
  outline: 2px solid var(--accent-bg); border-color: var(--accent);
}
.advising .field { margin-bottom: 12px; }
.advising .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 620px) { .advising .row2 { grid-template-columns: 1fr; } }

/* 站点样式把表格首列设成不折行，这里要允许折行：科目名与建议都很长 */
.advising table { font-size: .88rem; }
.advising th, .advising td { white-space: normal; }
.advising td:first-child, .advising th:first-child { white-space: normal; }

.advising button.action {
  font: inherit; font-weight: 600; cursor: pointer;
  padding: 8px 15px; border: 1px solid var(--accent); border-radius: 6px;
  background: var(--accent); color: #fff;
}
.advising button.ghost {
  font: inherit; cursor: pointer;
  padding: 8px 15px; border: 1px solid var(--line); border-radius: 6px;
  background: var(--bg); color: var(--text);
}
.advising button.mini { padding: 3px 10px; font-size: .84rem; }
.advising .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 18px; }

.advising .report { white-space: pre-wrap; font-size: .96rem; line-height: 1.85; }
.advising .advice { margin: 0 0 2px; }
.advising .report .src {
  display: block; font-size: .78rem; color: var(--text-soft);
  border-left: 2px solid var(--line); padding-left: 9px; margin: 2px 0 16px;
}
.advising .badge {
  display: inline-block; font-size: .74rem; font-weight: 600;
  padding: 1px 8px; margin-right: 6px; vertical-align: 1px;
  border-radius: 20px; background: var(--accent-bg); color: var(--accent);
}
.advising .badge.off { background: var(--bg-code); color: var(--text-soft); }
.advising .badge.warn { background: var(--warn-bg); color: var(--warn); }
.advising .note {
  border-left: 3px solid var(--warn); background: var(--warn-bg);
  padding: 12px 16px; margin: 0 0 16px; font-size: .9rem;
  border-radius: 0 var(--radius) var(--radius) 0;
}
.advising .note.err { border-left-color: var(--warn); }
.advising .note.ok { border-left-color: var(--accent); background: var(--accent-bg); }
.advising .muted { color: var(--text-soft); font-size: .85rem; }
.advising code { font-size: .85em; }
.advising .hidden { display: none !important; }

/* 报告是要交出去的成品：打印时去掉一切交互外壳 */
@media print {
  body.advising-wide .wrap { max-width: none; }
  .advising nav.tabs, .advising .toolbar, .advising .note,
  .advising #tab-student, .advising #tab-tracker, .advising #tab-coverage { display: none !important; }
  .advising #tab-report.hidden { display: block !important; }
  .advising .card { border: none; background: #fff; padding: 0; margin: 0; }
  .advising .card > h2 { display: none; }
  .advising .advice, .advising .report .src { break-inside: avoid; page-break-inside: avoid; }
  .advising .badge { background: none; border: 1px solid #999; color: #000; }
  .advising .report .src { color: #555; border-left-color: #ccc; }
}
"""


def build_css():
    (ASSETS / "advising.css").write_text(CSS_HEADER, encoding="utf-8")
    print("  styles: written to assets/advising.css")


# ── 4. the page shell, generated once per language × mode ───────────────────
def shell(lang):
    p = copy.PAGE[lang]
    u = copy.UI[lang]
    m = copy.PAGE_COPY[lang]
    # 两个前缀必须分开，混用会同时踩两个坑：
    #
    #   root   —— 站点根。assets/ 与共用的导图都在根上，**不随语言变化**。
    #   prefix —— 语言树。站内页面（首页/日程/时间线/五科/关于）在各自语言树下。
    #
    # 2026-10 修（两次）：
    #   1) 原先两种语言共用写死的 "../../"，于是英文页（/notes/advising/en.html）的
    #      每一个导航项都落回中文 —— Home→/index.html、About→/notes/about.html，
    #      连 Advising 都指向中文版自己。表现是"在英文界面点任何一项都掉回中文"。
    #   2) 只按语言改 prefix 又改过头：assets/ 在站点根，`{prefix}assets/...` 让英文页
    #      去要 /en/assets/style.css 与 /en/assets/advising.js，两者都是 404，
    #      英文升学页当场变成无样式、无脚本。所以资源路径一律用 root。
    root = "../../"
    prefix = "../../" if lang == "zh" else "../../en/"
    # 导图只有一份文件，中英两棵树都指向它，所以要把语言显式带上 ——
    # 不带的话落地页只能靠 localStorage 猜，从英文站点进来会停在中文。
    mindmap_href = "../../notes/mindmap.html?lang=" + ("en" if lang == "en" else "zh")
    advising_href = "index.html" if lang == "zh" else "en.html"

    # 导航按 site-data.NAV 生成。三处特殊：
    #   index.html          在语言根，其余在 notes/ 下
    #   mindmap.html        只有一份、住在中文树，两种语言都跨树指过去
    #   advising/index.html 本页自己；中英是两个文件（index.html / en.html）
    _nav = []
    for _e in site_data.NAV:
        _name, _zh, _en = _e[0], _e[1], _e[2]
        _en_name = _e[3] if len(_e) > 3 else _name
        if _name == "advising/index.html":
            _nav.append(f'<a href="{advising_href}" class="on">{_en if lang == "en" else _zh}</a>')
        elif _name == "mindmap.html":
            _nav.append(f'<a href="{mindmap_href}">{_en if lang == "en" else _zh}</a>')
        else:
            _pick = _en_name if lang == "en" else _name
            _href = prefix + ("index.html" if _pick == "index.html" else f"notes/{_pick}")
            _nav.append(f'<a href="{_href}">{_en if lang == "en" else _zh}</a>')
    nav_items = "\n      ".join(_nav)

    def T(key):
        return u[key]

    # One page per language, switched by a plain link. No mode dimension and no
    # mode switch: after the guest page's three extras were deleted, the two were
    # byte-identical.
    alt_lang_page = PAGES[("en" if lang == "zh" else "zh",)]

    # The identity block is gone. It asked for a name, a student id, a Year 11
    # school, whether English is a first language, which intake, whether the
    # reader is still deciding, and whether funding is secured. Of those only the
    # ATAR target is read by the ATAR calculation, and that moved into the ATAR
    # card where a reader would look for it. The rest fed rules that have either
    # been retired with their inputs or never needed identity at all.
    #
    # The two free-text result boxes went the same way earlier: they wrote
    # record.year11 and record.priorResults, and no rule read either one — a box a
    # student could fill in that changed nothing in the output.
    record_lists = ""

    tabs = """  <button role="tab" aria-selected="true" data-tab="student">{student}</button>
  <button role="tab" aria-selected="false" data-tab="report">{report}</button>
  <button role="tab" aria-selected="false" data-tab="courses">{courses}</button>
  <button role="tab" aria-selected="false" data-tab="coverage">{coverage}</button>""".format(
        student=T('tab_student'), report=T('tab_report'),
        courses=T('tab_courses'), coverage=T('tab_coverage'))

    # The assessment tracker panel is gone with its tab. It asked a student to
    # hand-enter every assessment, its weight and its due date, and its whole
    # output was a hand-rolled Eisenhower sort of rows the student had just typed
    # in — work the school already does, and now does better in Teams (see
    # 06_TEAMS_LIVE: the official ACCT/EE schedule lives there as an image the
    # school maintains). Nothing else read assessRows.

    return f"""<!doctype html>
<html lang="{p['lang']}" data-lang="{p['shell_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{m['title']}</title>
<meta name="description" content="{m['desc']}">
<link rel="alternate" hreflang="{copy.PAGE['en' if lang == 'zh' else 'zh']['lang']}" href="{alt_lang_page}">
<link rel="stylesheet" href="{root}assets/style.css">
<link rel="stylesheet" href="{root}assets/advising.css">
</head>
<body class="advising advising-wide">
<header class="site">
  <div class="wrap">
    <a class="brand" href="{prefix}index.html">{p['brand']}</a>
    <nav>{nav_items}</nav>
    <div class="lang-switch">
      <a class="lang-link" href="{alt_lang_page}" hreflang="{copy.PAGE['en' if lang == 'zh' else 'zh']['lang']}">{p['alt_label']}</a>
    </div>
  </div>
</header>
<main><div class="wrap">
<div class="advising">

<div class="note-head"><a class="back" href="{prefix}index.html">{p['back']}</a>
<h1>{m['h1']}</h1>
<div class="meta">{m['lede']}</div></div>

<nav class="tabs" role="tablist">
{tabs}
</nav>

<div id="tab-student">
  <div id="validationBox"></div>

  <section class="card">
    <h2>{T('sec_interests')}</h2>
    <p class="muted">{T('interests_intro')}</p>
    <table><thead><tr><th style="width:26%">{T('col_country')}</th>
      <th style="width:26%">{T('col_field')}</th><th>{T('col_uni')}</th>
      <th style="width:14%">{T('col_min_recorded')}</th><th style="width:38px"></th></tr></thead>
      <tbody id="interestRows"></tbody></table>
    <button class="ghost mini" id="addInterest">{T('btn_add_interest')}</button>
  </section>

  <section class="card">
    <h2>{T('sec_subjects')}</h2>
    <table><thead><tr><th>{T('col_subject')}</th>
      <th style="width:18%">{T('col_mark')}</th>
      <th style="width:38px"></th></tr></thead>
      <tbody id="subjectRows"></tbody></table>
    <button class="ghost mini" id="addSubject">{T('btn_add_subject')}</button>{record_lists}
  </section>

  <section class="card">
    <h2>{T('sec_atar')}</h2>
    <p class="muted">{T('atar_intro')}</p>
    <div class="row2">
      <div class="field"><label for="targetAtar">{T('label_target')}</label>
        <input type="number" id="targetAtar" min="0" max="99.95" step="0.05"></div>
    </div>
    <div class="toolbar">
      <button class="ghost" id="btnAtar">{T('btn_atar')}</button>
    </div>
    <div id="atarBox"></div>
    <p class="muted" id="atarMethod"></p>
  </section>

  <section class="card">
    <h2>{T('sec_history')}</h2>
    <div class="toolbar">
      <button class="ghost" id="btnHistory">{T('btn_history')}</button>
    </div>
    <div id="historyBox"></div>
  </section>

  <div class="toolbar">
    <button class="action" id="btnGenerate">{T('btn_generate')}</button>
    <button class="ghost" id="btnSave">{T('btn_save')}</button>
    <button class="ghost" id="btnLoad">{T('btn_load')}</button>
    <button class="ghost" id="btnClear">{T('btn_clear')}</button>
    <button class="ghost" id="btnSample">{T('btn_sample')}</button>
  </div>
</div>

<div id="tab-report" class="hidden">
  <div id="reportWarnings"></div>
  <div class="toolbar">
    <button class="ghost" id="btnPrint">{T('btn_print')}</button>
    <button class="ghost" id="btnCopy">{T('btn_copy')}</button>
    <button class="ghost" id="btnDownload">{T('btn_download')}</button>
    <button class="ghost" id="btnCsv">{T('btn_csv')}</button>
  </div>
  <section class="card">
    <h2>{T('report_title')} <span class="muted" id="reportStamp"></span></h2>
    <div class="report" id="reportBody"></div>
  </section>
</div>

<div id="tab-courses" class="hidden">
  <section class="card">
    <h2>{T('courses_title')}</h2>
    <p class="muted" id="courseNote"></p>
    <table><thead><tr><th>{T('col_uni_name')}</th><th>{T('col_course')}</th>
      <th style="width:9%">{T('col_min_atar')}</th><th>{T('col_req')}</th>
      <th style="width:12%">{T('col_source')}</th></tr></thead>
      <tbody id="courseRows"></tbody></table>
  </section>
</div>

<div id="tab-coverage" class="hidden">
  <div id="coverageSummary"></div>
  <section class="card">
    <h2>{T('coverage_title')}</h2>
    <table><thead><tr><th style="width:15%">{T('col_domain')}</th><th>{T('col_rule')}</th>
      <th style="width:9%">{T('col_fired')}</th><th style="width:14%">{T('col_verified')}</th></tr></thead>
      <tbody id="coverageRows"></tbody></table>
  </section>
</div>

</div>
</div></main>
<footer class="site"><div class="wrap">{p['footer']}</div></footer>
<span class="hidden" id="appTitle"></span><span class="hidden" id="appSub"></span>
<script src="advising-rules.js"></script>
<script src="courses.js"></script>
<script src="history.js"></script>
<script src="{root}assets/advising.js"></script>
</body>
</html>
"""


def build_courses():
    """Place the generated course library next to the page.

    It is emitted by a separate script that measures every source link, so it
    lives in src/ until the build copies it. The page loads it as a plain script
    before the engine, which reads window.COURSES.
    """
    src_file = SRC / "courses.js"
    if not src_file.exists():
        raise SystemExit(f"course library missing: {src_file}")
    payload = src_file.read_text(encoding="utf-8")
    # ── course-library gate ─────────────────────────────────────────────────
    # A course row whose `country` is not one a student can pick is invisible to
    # every country-filtered rule and nothing reports it. This shipped once: two
    # rows carried the placeholder "—" instead of Singapore, because a second,
    # abandoned generator wrote a dash where the workbook's cell was blank, and
    # the page copied it. The rows looked fine in the table and could never
    # match. Both halves are checked here — no placeholder, and every country
    # present in the vocabulary the form is built from.
    import json as _json
    import re as _re
    m = _re.search(r"rows:\s*(\[.*\])\s*,?\s*\}\s*$", payload, _re.S)
    if not m:
        raise SystemExit("course library gate: cannot find the rows array")
    try:
        rows = _json.loads(m.group(1))
    except ValueError as exc:
        raise SystemExit(f"course library gate: rows are not valid JSON — {exc}")
    if len(rows) < 40:
        raise SystemExit(
            f"course library gate: only {len(rows)} rows survived — "
            "a generator that drops most of the library has run over it")

    placeholders = [r for r in rows if not r.get("country", "").strip()
                    or r["country"].strip() in ("-", "—", "–", "N/A", "?")]
    if placeholders:
        raise SystemExit(
            "course library gate: rows carry a placeholder country, so no rule "
            "can ever match them — " +
            "; ".join(f"{r['university']} / {r['course']}" for r in placeholders[:6]))

    vocab_match = _re.search(r"countries:\s*\[(.*?)\]",
                             (TOOL / "advising-rules.js").read_text(encoding="utf-8"), _re.S)
    vocab = set(_re.findall(r"'([^']+)'", vocab_match.group(1))) if vocab_match else set()
    unreachable = sorted({r["country"] for r in rows} - vocab)
    if vocab and unreachable:
        raise SystemExit(
            "course library gate: courses sit in countries the form never offers, "
            "so a student cannot select them — " + ", ".join(unreachable))

    (TOOL / "courses.js").write_text(payload, encoding="utf-8")
    rows_n = payload.count('{"country"')
    print(f"  courses: courses.js ({len(payload) // 1024} KB, {rows_n} rows, "
          f"countries {sorted({r['country'] for r in rows})})")


def build_history():
    """Place the prior-cohort snapshot next to the page.

    Same arrangement as the course library: emitted by its own script, which
    enforces that nothing personal crosses over, and copied here so the page can
    load it as a plain script.
    """
    src_file = SRC / "history.js"
    if not src_file.exists():
        raise SystemExit(f"history snapshot missing: {src_file}")
    payload = src_file.read_text(encoding="utf-8")

    # This file is published. Re-check the shape here rather than trusting the
    # emitter: a key that should not be there must not reach a public directory.
    import json as _json
    m = re.search(r"window\.HISTORY = (\{.*\})\s*$", payload, re.S)
    if not m:
        raise SystemExit("history gate: cannot find the payload")
    try:
        data = _json.loads(m.group(1))
    except ValueError as exc:
        raise SystemExit(f"history gate: payload is not valid JSON — {exc}")
    for banned in ("name", "studentId", "school", "email", "id", "dob"):
        # Compared structurally, not by substring: a substring test for "id" also
        # matches the innocent "source" key, and a gate that cries wolf gets
        # deleted rather than fixed.
        if _json.dumps(data) and f'"{banned}":' in _json.dumps(data):
            raise SystemExit(
                f"history gate: the payload carries a {banned!r} field — this file "
                "is published, so stop")
    if not data.get("count"):
        raise SystemExit("history gate: no students in the snapshot")
    if not data.get("cohortCaveat"):
        raise SystemExit(
            "history gate: the cohort caveat is missing. The bands are positions "
            "within a narrow high band, and without that sentence they read as "
            "positions in the population.")
    (TOOL / "history.js").write_text(payload, encoding="utf-8")
    print(f"  history: history.js ({len(payload) // 1024} KB, "
          f"{data['count']} students, ATAR {data['atarMin']}–{data['atarMax']})")


def redirect_stub(target, lang):
    """A page that sends a reader to the site's home page.

    The mode pages were removed, but guest.html and en-guest.html were shared as
    links before that, and a 404 is a poor way to answer a link someone handed
    out. They now land on the home page — the same page the site's own nav calls
    首页 — rather than on the tool, which is where a reader clicking an old
    advising link was previously dropped without the rest of the site around it.

    The target is RELATIVE, so the stub works under the /ausmat-guide/ base path
    and from a local file alike; an absolute path would be wrong in one of them.
    """
    title = "正在跳转…" if lang == "zh" else "Redirecting…"
    body = "如果浏览器没有自动跳转，请点这里：" if lang == "zh" else "If your browser does not follow the redirect, use this link:"
    label = "回到首页" if lang == "zh" else "Home"
    desc = ("页面已移走，正在跳转到首页。" if lang == "zh"
            else "This page has moved; redirecting to the home page.")
    html_lang = "zh-CN" if lang == "zh" else "en"   # 与全站其余页面保持一致
    return f"""<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
</head>
<body>
<p>{body} <a href="{target}">{label}</a></p>
</body>
</html>
"""


def build_pages():
    for (lang,), name in PAGES.items():
        (TOOL / name).write_text(shell(lang), encoding="utf-8")
        print(f"  page: {name:<16} ({lang})")
    # The removed mode pages, answered by a redirect to the site's home page
    # rather than a 404. Written on every build, so a hand-restored copy of the
    # old tool page cannot survive here: the file is always this stub.
    for stale, target, lang in (("guest.html", "../../index.html", "zh"),
                                ("en-guest.html", "../../en/index.html", "en")):
        (TOOL / stale).write_text(redirect_stub(target, lang), encoding="utf-8")
        print(f"  stub: {stale:<16} -> {target}")


if __name__ == "__main__":
    TOOL.mkdir(parents=True, exist_ok=True)
    # The two guest pages were removed as pages; build_pages writes a redirect
    # stub at each path, so the old shared links still land somewhere useful.
    ok_catalog = build_catalog()
    build_engine()
    build_css()
    build_courses()
    build_history()
    build_pages()

    # ── syntax gate ─────────────────────────────────────────────────────────
    # A missing `+` between two string literals in a rewritten advice field
    # produced a catalog that was fine as Python and not valid JavaScript, and it
    # reached disk before anything noticed. Nothing downstream should have to
    # discover that: the build refuses to finish with a file node cannot parse.
    import subprocess
    for gate_path in (TOOL / "advising-rules.js", ASSETS / "advising.js"):
        gate = subprocess.run(["node", "--check", str(gate_path)], capture_output=True, text=True)
        if gate.returncode != 0:
            print(f"\nSYNTAX GATE FAILED for {gate_path.name}:\n{gate.stderr}")
            raise SystemExit(1)
        print(f"  syntax ok: {gate_path.name}")

    print("\nbuild complete" + ("" if ok_catalog else "  (WITH MISSING TRANSLATIONS)"))
