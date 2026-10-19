# -*- coding: utf-8 -*-
"""Chinese copy for the advising tool.

Translation policy, matching the rest of the site:
  - Simplified Chinese, concise, no marketing register.
  - The Chinese is written as the primary text, not as a gloss of the English.
    Where the English explains an English-speaking admissions process (UCAS,
    LNAT), the Chinese says what it is for a reader who has not met the term.
  - Rule ids, sources and thresholds are NOT translated: they are keys, and a
    translated key would stop matching.
"""

# ── page shell ───────────────────────────────────────────────────────────────
PAGE = {
    "zh": {
        "lang": "zh-CN",
        "brand": "学习笔记",
        "back": "← 首页",
        "alt_label": "EN",
        "footer": "AUSMAT May 2026 · 个人学习笔记",
        "shell_lang": "zh",
    },
    "en": {
        "lang": "en",
        "brand": "Study Notes",
        "back": "← Home",
        "alt_label": "中文",
        "footer": "AUSMAT May 2026 · personal study notes",
        "shell_lang": "en",
    },
}

# ── mode copy ────────────────────────────────────────────────────────────────
# Two modes, because the school-record half of this tool is dead weight for a
# reader who is not enrolled anywhere: it asks for a previous intake, its marks,
# and a school assessment calendar, none of which exist for a self-studying or
# already-graduated applicant. Mode is a build-time dimension like language, so
# a guest opens a different address rather than toggling something.
# One page per language now: the guest mode is gone, so this is keyed by language
# alone. The enrolled wording is kept — the guest wording described a page that no
# longer exists, and the two differed only in tone, never in content.
PAGE_COPY = {
    "zh": {
        "h1": "升学自检",
        "title": "AUSMAT Guide · 升学自检",
        "desc": "填四门成绩与目标 ATAR，算出合成分和对应 ATAR，再按规则库汇总适用的升学建议；每条建议都标出它来自哪条规则。",
        "lede": ("填四门成绩和目标 ATAR，工具算出合成分与对应 ATAR，"
                 "再按规则库汇总出适用的建议。每条建议都标出它来自哪条规则，"
                 "规则库本身可以逐条查看。"),
    },
    "en": {
        "h1": "Advising self-check",
        "title": "AUSMAT Guide · Advising",
        "desc": "Enter four subject marks and a target ATAR to get the aggregate, the matching ATAR and the advice that applies — every item cited to its rule.",
        "lede": ("Enter four subject marks and a target ATAR; the tool converts them "
                 "to an ATAR, then assembles the advice that applies. Each paragraph "
                 "is tagged with the rule behind it and the catalog is readable line "
                 "by line."),
    },
}

# ── interface strings the engine emits ───────────────────────────────────────
UI = {
    "zh": {
        "app_sub": "规则驱动 · 建议是数据，不是代码 · 全部内容在 advising-rules.js",
        "tab_student": "1 · 学生情况",
        "tab_report": "2 · 建议报告",
        "tab_coverage": "3 · 规则总览",
        "sec_identity": "身份与学业状况",
        "sec_interests": "升学意向",
        "interests_intro": ("只想算 ATAR 的话这一块可以留空；填了才会有目的国、专业、"
                            "先修科目、语言和费用这几类建议。"),
        "sec_subjects": "选课与成绩",
        "label_name": "姓名",
        "label_sid": "学号",
        "label_school": "Year 11 就读学校",
        "label_efl": "英语为母语",
        "label_intake": "曾就读的预科班次",
        "label_target": "目标 ATAR",
        "label_est": "当前预估 ATAR",
        "label_deciding": "仍在犹豫选什么专业",
        "label_funding": "学费来源已落实",
        "opt_unstated": "— 未填写 —",
        "opt_none": "— 无 —",
        "opt_yes": "是",
        "opt_no": "否",
        "col_country": "国家/地区",
        "col_field": "专业方向",
        "col_uni": "目标大学",
        "col_subject": "科目",
        "col_mark": "成绩 (%)",
        "btn_add_interest": "+ 增加一行",
        "btn_add_subject": "+ 增加一门",
        "sec_atar": "ATAR 估算",
        "atar_intro": ("按你上面填的成绩算：取最高的四门合计成合成分，再换算成 ATAR。"
                       "换算式来自源工作簿，是某一所院校某一个招生轮次的换算，"
                       "不是官方 ATAR 成绩单——只当估算，并以你自己的招生中心为准。"),
        "btn_atar": "算一下",
        "atar_need": "目标 {target} 需要合成分 {agg}（四门平均 {per}）。",
        "atar_above": "比你现在高 {gap}。",
        "atar_below": "你已经比这个目标需要的水平高 {gap}。",
        "atar_no_target": "填一个目标 ATAR，就能算出还差多少。",
        "atar_uni_nocourse": "课程库里没有匹配「{field}」方向的课程，所以这一栏无法对照。",
        "atar_uni_nouni": "课程库里没有 {uni} 在这个国家的记录，所以无法对照——换一所院校或换一个国家。",
        "atar_uni_nocountry": "课程库只覆盖 {countries}，没有这个国家的记录，所以无法对照。",
        "atar_uni_hold": "库里 {n} 门，记录最低 ATAR {lo}–{hi}。",
        "atar_uni_holdflat": "库里 {n} 门，记录最低 ATAR 都是 {lo}。",
        "atar_uni_above": "你在 {standing}，够得上其中 {n} 门（最高 {top}）。",
        "atar_uni_next": "再上一层是 {next}，差 {gap}。",
        "atar_uni_below": "你在 {standing}，{n} 门全部在你之上——最低的 {lo} 还差 {gap}。",
        "col_min_recorded": "记录最低 ATAR（门数）",
        "atar_out_of_range": ("合成分 {agg} 超出这套换算能回答的区间（{lo}–{hi}）。"
                              "这里不给数字——给一个会显得权威，而且是错的。"),
        "atar_insufficient": "至少要 {n} 门有成绩的科目才能算合成分。",
        "atar_unavailable": "换算式自检没通过，所以不输出数字。",
        "atar_row_agg": "合成分（最高 {n} 门合计）",
        "atar_row_atar": "换算 ATAR",
        "atar_row_target": "目标 ATAR",
        "atar_row_needed": "目标所需合成分",
        "atar_method": ("方法：最高的 {n} 门成绩相加得合成分，代入源工作簿标定的曲线。"
                        "曲线在合成分约 373 以上会掉头向下，所以超出区间时本工具拒绝给数。"
                        "自检：合成分 {ref} 应对应 ATAR 80，实测 {got}。"),
        "sec_history": "往届参考",
        "btn_history": "看往届分布",
        "sec_notes": "备注（给你的顾问或自己）",
        "notes_intro": "写在这里的内容会随记录一起保存和导出，打印时会印在报告末尾。"
                       "常用的说法可以存在这里重复使用。",
        "notes_heading": "备注",
        "history_intro": ("下面是工作簿里记录的往届学生结果，用来参照你估算出来的位置。"),
        "history_range": "共 {count} 名学生，ATAR 落在 {lo} 到 {hi} 之间。",
        "history_bands": "这组人内部的位置：",
        "history_examples": "几位往届学生的成绩与结果：",
        "history_col_atar": "记录的 ATAR",
        "history_col_top4": "最高四门合计",
        "history_col_marks": "各科成绩",
        "history_omitted": ("这里不列往届样例：源表没有任何一列标记某位学生的行到哪里结束，"
                        "所以单独的某一行无法可靠还原。上面的分布不受这个缺陷影响。"),
        "btn_generate": "生成报告 →",
        "btn_save": "保存到本浏览器",
        "btn_load": "读取已保存",
        "btn_clear": "全部清空",
        "btn_sample": "载入示例学生",
        "btn_print": "打印 / 存为 PDF",
        "btn_copy": "复制为文本",
        "btn_download": "下载 .md",
        "btn_csv": "下载记录表 (.csv)",
        "report_title": "建议报告",
        "col_assessment": "考核项目",
        "col_weight": "权重 (%)",
        "col_due": "日期",
        "col_importance": "重要度",
        "col_urgency": "紧急度",
        "col_done": "完成",
        "col_action": "建议动作",
        "btn_add_assess": "+ 增加一项考核",
        "coverage_title": "规则总览",
        "col_domain": "类别",
        # 「课程参考」容易被读成"五门课的参考资料"，而这一页实际是院校专业的最低 ATAR 表
        # （表头：院校 / 专业 / 最低 ATAR / 除分数外的要求 / 来源）。游客走查提出。
        # 页内标题 "courses_title" 本来就写对了（课程最低 ATAR 参考），只有页签名含糊。
        "tab_courses": "院校分数线",
        "courses_title": "课程最低 ATAR 参考",
        "col_uni_name": "院校",
        "col_course": "专业",
        "col_min_atar": "最低 ATAR",
        "col_req": "除分数外的要求",
        "col_source": "来源",
        "col_rule": "规则",
        "col_fired": "命中",
        "col_verified": "核实状态",
        "label_y11": "Year 11 成绩（每行一条：科目: 分数）",
        "label_prior": "往期班次成绩（每行一条：科目: 分数）",
    },
    "en": {
        "app_sub": "rules-driven · advice is data, not code · all copy lives in advising-rules.js",
        "tab_student": "1 · Student record",
        "tab_report": "2 · Advising report",
        "tab_coverage": "3 · Rule coverage",
        "sec_identity": "Identity & standing",
        "sec_interests": "Destinations & academic interests",
        "interests_intro": ("Leave this blank if all you want is the ATAR. Filling it in is what "
                            "unlocks the destination, course, prerequisite, language and funding advice."),
        "sec_subjects": "Subjects & results",
        "label_name": "Full name",
        "label_sid": "Student ID",
        "label_school": "Year 11 school",
        "label_efl": "English is first language",
        "label_intake": "Previous intake attended",
        "label_target": "Target ATAR",
        "label_est": "Current estimated ATAR",
        "label_deciding": "Still deciding on a course",
        "label_funding": "Funding arrangement confirmed",
        "opt_unstated": "— not stated —",
        "opt_none": "— none —",
        "opt_yes": "Yes",
        "opt_no": "No",
        "col_country": "Country",
        "col_field": "Field",
        "col_uni": "Target university",
        "col_subject": "Subject",
        "col_mark": "Mark (%)",
        "btn_add_interest": "+ Add row",
        "btn_add_subject": "+ Add subject",
        "sec_atar": "ATAR estimate",
        "atar_intro": ("Computed from the marks above: the best four are summed into an "
                       "aggregate, and the aggregate is converted to an ATAR. The "
                       "conversion comes from the source workbook and is the curve of "
                       "one institution for one intake — not an official ATAR "
                       "statement. Treat it as an estimate and confirm against your own "
                       "admissions centre."),
        "btn_atar": "Calculate",
        "atar_need": "Target {target} needs an aggregate of {agg} ({per} per subject across four).",
        "atar_above": "That is {gap} above where you are.",
        "atar_below": "You are already {gap} above what that target needs.",
        "atar_no_target": "Enter a target ATAR to see how far off it is.",
        "atar_uni_nocourse": "the library holds no course matching {field} for this choice, so there is nothing to compare against.",
        "atar_uni_nouni": "the library records nothing for {uni} in that country, so there is nothing to compare against — change the institution or the country.",
        "atar_uni_nocountry": "the library covers {countries} only, and nothing here is in this country, so there is nothing to compare against.",
        "atar_uni_hold": "{n} courses recorded, minimums {lo}–{hi}.",
        "atar_uni_holdflat": "{n} courses recorded, all at {lo}.",
        "atar_uni_above": "you are at {standing}, reaching {n} of them (highest {top}).",
        "atar_uni_next": "the next step up is {next}, {gap} away.",
        "atar_uni_below": "you are at {standing}, below all {n} of them — the lowest, {lo}, is {gap} away.",
        "col_min_recorded": "Recorded min. (count)",
        "atar_out_of_range": ("Aggregate {agg} is outside the span this conversion can "
                              "answer for ({lo}–{hi}). No number is given here — a number "
                              "would look authoritative and be wrong."),
        "atar_insufficient": "At least {n} subjects with marks are needed for an aggregate.",
        "atar_unavailable": "The conversion failed its own load-time check, so no number is produced.",
        "atar_row_agg": "Aggregate (best {n} summed)",
        "atar_row_atar": "Converted ATAR",
        "atar_row_target": "Target ATAR",
        "atar_row_needed": "Aggregate the target needs",
        "atar_method": ("Method: the best {n} marks are summed, then put through the curve "
                        "the source workbook is calibrated to. That curve turns over above "
                        "an aggregate of about 373, so outside the span the tool refuses to "
                        "answer. Check: an aggregate of {ref} should read ATAR 80; it "
                        "reads {got}."),
        "sec_history": "Prior cohorts",
        "btn_history": "Show prior outcomes",
        "sec_notes": "Notes (for your adviser, or yourself)",
        "notes_intro": "Whatever you write here is saved and exported with the record, and "
                       "printed at the end of the report. Reusable wording can be kept here.",
        "notes_heading": "Notes",
        "history_intro": ("Recorded outcomes of the students in the source workbook, for "
                          "reference against your own estimate."),
        "history_range": "{count} students in total, with ATARs from {lo} to {hi}.",
        "history_bands": "Positions within this group:",
        "history_examples": "A few prior students, their marks and their result:",
        "history_col_atar": "Recorded ATAR",
        "history_col_top4": "Best four summed",
        "history_col_marks": "Subject marks",
        "history_omitted": ("No example students are listed: the source sheet has no column "
                            "marking where one student rows end, so individual rows cannot be "
                            "reconstructed reliably. The distribution above is unaffected."),
        "btn_generate": "Generate report →",
        "btn_save": "Save to this browser",
        "btn_load": "Restore saved",
        "btn_clear": "Clear all",
        "btn_sample": "Load sample student",
        "btn_print": "Print / save as PDF",
        "btn_copy": "Copy as text",
        "btn_download": "Download as .md",
        "btn_csv": "Download record (.csv)",
        "report_title": "Advising report",
        "col_assessment": "Assessment",
        "col_weight": "Weight (%)",
        "col_due": "Due",
        "col_importance": "Importance",
        "col_urgency": "Urgency",
        "col_done": "Done",
        "col_action": "Action",
        "btn_add_assess": "+ Add assessment",
        "coverage_title": "Rule coverage",
        "col_domain": "Domain",
        "tab_courses": "University entry scores",
        "courses_title": "Recorded minimums",
        "col_uni_name": "Institution",
        "col_course": "Course",
        "col_min_atar": "Min. ATAR",
        "col_req": "Requirements beyond the score",
        "col_source": "Source",
        "col_rule": "Rule",
        "col_fired": "Fired",
        "col_verified": "Verification",
        "label_y11": "Year 11 results (one per line: Subject: mark)",
        "label_prior": "Prior intake results (one per line: Subject: mark)",
    },
}

# ── capability labels, for advice that names the missing preparation ────────
CAPABILITY_ZH = {
    "mathematics": "数学",
    "physicalScience": "物理或化学",
    "chemistry": "化学",
    "biology": "生物",
    "english": "英语",
    "computing": "计算机",
}

# ── field-of-study labels ───────────────────────────────────────────────────
# These appear inside advice alongside a capability ("Engineering / 物理或化学"),
# so leaving them in English produces a phrase in two languages at once.
FIELD_ZH = {
    "Engineering": "工程",
    "Computer Science": "计算机科学",
    "Medicine": "医学",
    "Dentistry": "牙医",
    "Nursing": "护理",
    "Sciences": "理科",
    "Psychology": "心理学",
    "Business": "商科",
    "Law": "法律",
    "Architecture": "建筑",
    "Education": "教育",
    "Humanities": "人文",
    "Undecided": "尚未确定",
}

# ── domain labels ────────────────────────────────────────────────────────────
DOMAINS = {
    "completeness": "填写完整度",
    "destination": "升学方向与申请",
    "course": "专业要求",
    "language": "语言要求",
    "funding": "奖学金与费用",
    "performance": "学业表现",
    "skills": "技能与准备度",
    "wellbeing": "学习方式与状态",
}

# ── importance bands and matrix ──────────────────────────────────────────────
BANDS = {
    "1 — Trivial": "1 — 可忽略",
    "2 — Minor": "2 — 次要",
    "3 — Moderate": "3 — 中等",
    "4 — Major": "4 — 重要",
    "5 — Critical": "5 — 关键",
}

# The ATAR caveat and its variants. These are the sentences that decide whether a
# reader treats the number as an estimate or as an official statement, so they are
# translated with the same care as the advice text. They live in the calibration
# block rather than in UI because the calibration is what they describe.
CALIBRATION_ZH = {
    "label": "源工作簿曲线 —— 一所院校、一个招生轮次",
    "verifiedAgainst": ("工作簿写明合成分 239.12838737245087 对应 ATAR 80；"
                        "本条曲线在该点复现 80.00，并在标定区间内全程单调"),
    "caveat": ("这是源工作簿里某所院校某个招生轮次的换算式，不是官方 ATAR 成绩单。"
               "只当估算，并以你自己的招生中心为准。"),
}

# matrix[urgency][level]
MATRIX = {
    1: {
        1: "先放着，时间真的宽裕再看。",
        2: "把材料归档，留一次短复习。",
        3: "未来几周安排一次短回顾。",
        4: "本周排一个专注时段。",
        5: "排一次深度复习，这项分量很重。",
    },
    2: {
        1: "这周清闲的话再扫一眼。",
        2: "做一份能反复用的精简笔记。",
        3: "下个主题开始前回顾课堂材料。",
        4: "做练习题，不要只看。",
        5: "本周定一个时段，别交给运气。",
    },
    3: {
        1: "别的事都落空了再看。",
        2: "用自己的笔记做一次短回顾。",
        3: "针对性回顾，然后限时练习。",
        4: "开始限时做真题。",
        5: "现在就开始，这项拖不得。",
    },
    4: {
        1: "主动推迟，它不是你的瓶颈。",
        2: "专注一小时，之后再判断。",
        3: "本周优先于常规作业。",
        4: "今天完整做一套真题。",
        5: "当作紧急事项：今天复习并自测。",
    },
    5: {
        1: "只有它确实是你最轻的一项才碰。",
        2: "把笔记压缩成一页回忆提纲。",
        3: "立刻优先于大多数其他任务。",
        4: "48 小时内做完整复习。",
        5: "立刻集中复习，马上做一套模拟。",
    },
}

# ── rule advice, by rule id ──────────────────────────────────────────────────
ADVICE = {
    "form-incomplete":
        "必填项还没填完，所以这份报告只是暂定的。建议的质量取决于你填进去的信息。",
    "subjects-fewer-than-four":
        "你只记录了 {{subjectCount}} 门 ATAR 科目。多数大学的合成分按四门及以上计算，"
        "先确认你所在体系里哪几门会计入合成分。",
    "dest-none-stated":
        "还没有填写任何目标国家。缺了这个，签证时间线、语言要求和申请截止日期都无从评估。",
    "dest-uk":
        "申请英国要通过统一的招生系统，而不是分别投递到各校。需要准备学术推荐信和个人陈述，"
        "一份申请可以包含多个志愿。动笔前先向顾问确认当轮的确切截止日期。",
    "dest-us":
        "申请美国通常需要标准化考试、文书，以及提前数月联系的推荐人。每所大学各有自己的申请系统，"
        "要按并行多份申请来规划。",
    "dest-au":
        "申请澳洲一般按院校分别递交，或通过所在州的招生中心。录取是分轮次放榜的，"
        "所以成绩公布的时间点和分数本身一样重要。",
    "course-medicine":
        "医学与牙医专业通常在学业成绩之外还要加考能力测试，部分院校还有面试。"
        "这类考试的报名窗口远早于申请截止日，是你整条时间线上最早的一项。",
    "course-law":
        "法律专业通常没有固定的先修科目，但部分地区要求额外的入学考试。"
        "先确认你考虑的那些院校是否需要。",
    "course-engineering":
        "工程学位一般以扎实的数学为基础，不少还要求物理。请逐个查阅课程的"
        "「假定知识」说明，不要只看录取分数线。",
    "course-undecided":
        "这个阶段还没定方向很正常，也完全可以处理。更有效的做法是**按约束条件缩小范围**，"
        "而不是按喜好：你哪几门最强、能负担哪些国家、哪些先修科目需要继续保留。"
        "把这三条列出来，通常就能排除掉大部分选项。",
    "lang-non-english-destination":
        "你填的目标国家以非英语国家为主。用其他语言授课的项目通常要求该语言的等级证书，"
        "而考取证书需要时间。",
    "lang-english-test":
        "这些目的地以英语授课，当地多数院校会要求提供英语能力证明；"
        "有些院校接受英语科目成绩替代标准化考试。要求因院校和课程而异——临床类专业通常最严。",
    "funding-not-recorded":
        "还没有记录任何学费来源安排。奖学金的截止日期通常早于录取截止日期，"
        "所以费用该有独立的时间线，而不是等拿到 offer 再说。",
    "perf-below-target":
        "按目前水平，你低于自己设定的目标 {{targetAtar}}。这是需要规划的差距，不是结论。"
        "关键问题是：剩下的考核权重够不够把目标拉回来。如果不够，现在调整目标，"
        "比成绩公布时才发现要好。",
    "perf-subject-weak":
        "至少有一门低于 {{weakMark}}。在全面增加学习时间之前，先分清问题出在"
        "知识本身、应试技巧，还是时间安排——三者的解法完全不同。"
        "看一遍批改过的卷子，通常比多刷题更快找到答案。",
    "perf-high-at-load":
        "你记录的全部 {{subjectCount}} 门都是最高难度科目。这是很重的负担，"
        "而合成分的优势只有在各门都稳得住时才成立。留意有没有哪一门在拖累其他几门。",
    "course-prereq-gap":
        "你选的至少一个方向，通常要求你尚未记录的科目准备。各院校之间、"
        "甚至同一所院校的不同专业之间要求都不同，所以先逐个确认具体课程的先修要求，"
        "不要预设这个缺口无法弥补——有些学校接受衔接课程。",
    "course-prereq-optional-available":
        "至少有一个方向缺一门并非必修、但常被建议修的科目。建议科目很少单独决定录取，"
        "但能减少大一需要补修学分的可能。",
    "atar-margin-thin":
        "按目前水平，你距离**你之上最近的一条记录最低 ATAR 的 **{{nearestCourse}}** 只差 "
        "{{atarMarginPoints}} 分以内。这么薄的余量，一次考核就能改变结果，"
        "所以把下一场当作决定性的，而不是练手。",
    "atar-figure-not-recorded":
        "至少有一个志愿，课程库里没有对应的课程，所以没有记录最低 ATAR 可以对照。"
        "可能是这个「国家 + 方向 + 院校」的组合本来就不在这份快照里，也可能是该校"
        "的录取写法不同——去当前课程页面确认，并把这个志愿当作**未评估**，"
        "而不是当作已经满足。",
    "wellbeing-plan":
        "有两件事能稳定地把成绩守住：一份**写明日期的计划**而不是「打算」，"
        "以及在**限时条件下做题**而不是反复看笔记。两者都不需要比现在多花时间。",
    "wellbeing-overload":
        "你记录了 {{subjectCount}} 门科目。这种负担下常见的失败方式不是懒，"
        "而是累积疲劳——表现为熟悉的内容也开始出错。请主动把恢复时间排进计划。",
    "course-prereq-named":
        "你所填方向里已记录的课程中，有几门**明确点名了先修科目**，而你的选课里没有："
        "{{namedPrereqGaps}}这是院校自己写的措辞，不是本工具的通用推测，"
        "所以改选课之前值得先去课程页确认一遍。",
    "skills-roadmap":        "{{roadmapField}}——这份工作实际在做什么：{{roadmapCareers}}"
        "分数之外，区分申请人的是这些：{{roadmapActivities}}"
        "值得刻意培养的能力：{{roadmapSkills}}{{roadmapWhy}}",
    "skills-narrowness":
        "你只记录了一个专业方向。这本身没问题，但单一而窄的目标恰恰是最需要备选方案的："
        "录取由你看不见的那一届人决定，今年够得上的课程，明年不一定。"
        "再写一个你同样能接受的相邻方向，并确认你的选课没有把它关掉。",
    "options-pathways":
        "直接读学位是一条路，不是唯一一条。{{optionsList}}"
        "建议现在就看而不是等到八月：这些路径有自己的截止日期，"
        "其中几条比学位申请开始得更早。",
    "options-timeline":
        "{{timelineList}}截止日期每轮都会变，所以把这些当成一年的形状而不是具体日子："
        "要紧的是这份工作远早于申请本身开始。",
}

# ── coverage view strings the engine emits ───────────────────────────────────
COVERAGE = {
    "zh": {
        "rules_in_catalog": "规则库共",
        "rules_unit": "条",
        "fired_unit": "条命中",
        "unverified_unit": "条待核实",
        "disabled_unit": "条已停用",
        "verify_note": "标记为「待核实」的规则含有尚未对照当前来源确认的事实性表述。",
        "verify_badge": "待核实",
        "fired_yes": "是",
        "fired_no": "否",
        "disabled_reason": "规则库中已停用",
        "compile_error": "编译错误",
        "threw": "求值出错",
    },
    "en": {
        "rules_in_catalog": "",
        "rules_unit": "rules in catalog",
        "fired_unit": "fired",
        "unverified_unit": "awaiting verification",
        "disabled_unit": "disabled",
        "verify_note": "Rules marked verify make a factual claim that a human has not yet confirmed against a current source.",
        "verify_badge": "verify",
        "fired_yes": "yes",
        "fired_no": "no",
        "disabled_reason": "disabled in catalog",
        "compile_error": "compile error",
        "threw": "threw",
    },
}
