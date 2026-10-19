"""五科真实考核数据（从语料里抽出的原始大纲）。

每一条都有来源。只记录事实性字段：任务号 / 类型 / 权重 / 日期。
不复制大纲的描述性文字——那些是 SCSA 与学校的版权内容。

关键事实（推翻了我此前站上的错误数据）：
  * 学期自 2026-05-25 开课，至 2027-02-04 结束（CSC 周次表）
  * 期末考在 2027 年 1 月底至 2 月中，不是 2026 年 11 月
  * 11 月中下旬是 ACCT/EE 考试周
"""

# 学期结构（来源：CSC 007_Course-Outline 周次表）
SEMESTER = {
    "start": "2026-05-25",
    "end": "2027-02-04",
    # 全部考核结束的日期。原先把 end 只当「结课」展示，但四门期末排到 2/12–2/13，
    # 晚于 2/4 —— 同一张表里自相矛盾（高分学生走查发现）。
    # 分开表述：2/4 是最后教学日，2/13 是最后一门考试。
    "last_exam": "2027-02-13",
    "breaks": [("2026-10-05", "2026-10-09", "Term break"),
               ("2026-12-21", "2027-01-01", "Term break")],
    "exam_windows": [("2026-11-02", "2026-11-20", "ACCT / EE examination weeks"),
                     ("2027-01-25", "2027-02-13", "Final evaluation period")],
}

# 各科考核任务。date 为起止范围时用 ~ 连接。
TASKS = [
    # ── CSC（来源：006_Assessment-Outline_ATCSC_May_2026.DOCX）────────────
    {"subj": "CSC", "task": "Task 1", "type": "Project",
     "weight": 20, "date": "2026-08-07", "end": "2026-08-18",
     "note_zh": "Part 1 设计与开发 5%、Part 2 评估 5%、Part 3 项目验证 10%",
     "note_en": "Part 1 design & development 5%, Part 2 evaluation 5%, Part 3 project validation 10%"},
    {"subj": "CSC", "task": "Task 2", "type": "Practical Test",
     "weight": 10, "date": "2026-07-28", "end": None, "note_zh": "", "note_en": ""},
    {"subj": "CSC", "task": "Task 3", "type": "Examination",
     "weight": 15, "date": "2026-09-21", "end": "2026-10-02",
     "note_zh": "第一学期期末考试，3 小时（第 18–19 周）",
     "note_en": "Semester 1 examination, 3 hours (weeks 18–19)"},
    {"subj": "CSC", "task": "Task 4", "type": "Theory Test",
     "weight": 10, "date": "2026-11-19", "end": None,
     "note_zh": "网络通信与网络安全", "note_en": "Network communications and cyber security"},
    {"subj": "CSC", "task": "Task 5", "type": "Project",
     "weight": 20, "date": "2026-11-23", "end": "2027-01-04",
     "note_zh": "Part 1 数据库方案 8%（12/18 交）、Part 2 项目验证 12%",
     "note_en": "Part 1 database solution 8% (due 18 Dec), Part 2 project validation 12%"},
    {"subj": "CSC", "task": "Task 6", "type": "Examination",
     "weight": 25, "external": True, "date": "2027-01-04", "end": "2027-01-21",
     "note_zh": "第二学期期末考试，3 小时。大纲写 Week 34-36，本站按开学日推算 1/4–1/21 属于第 33–35 周 —— 学校周历与本站编号不同，两个说法都列在这里，日期以学校通知为准",
     "note_en": "Semester 2 examination, 3 hours. The outline says Week 34-36; counting from the start of semester this site places 4–21 Jan in weeks 33–35. The school calendar and this site count differently, so both are shown — treat the school's notice as final"},

    # ── MAM ─────────────────────────────────────────────────────────────
    # 来源：学校 OneNote《003_Assessment Outline.md》（MAM 12 May 2026 笔记本 /
    # _Content Library / Introduction），学院发的 SCSA 官方 ASSESSMENT OUTLINE
    # 扫描件的 OCR。权重行原文：Response (40%) · Investigation (20%) · Examination。
    #
    # 2026-10 更正：这里原本写 Tests 34 + Investigation 26（TT3=4、Investigation
    # 两部分各 13），与大纲不符，而且注释把来源记成了 _Content Library__Introduction.txt
    # ——那个文件里根本没有权重表（grep 百分号零命中）。知识导图里的 40/20/40 才是对的，
    # 之前是站点的数据错了、导图对了。数字错的后果是学生按错的比重分配复习时间。
    #
    # 2026-10-19 再更正：Investigation 两部分此前各写 10%，是二次核对时从学院扫描件
    # 《May 2026 Intake Assessment Outline / Mathematics Methods》（Introduction.pdf
    # 第 12 页）读到的：Response 40%（TT1 10 / TT2 20 / TT3 10）、Investigation 20%
    # （**Part 1 = 4%**，Part 2 = 16%）、Examination 40%。所以 Part 1 由 10 改 4、
    # Part 2 由 10 改 16，合计仍是 20%。
    {"subj": "MAM", "task": "Readiness 1", "type": "Test",
     "weight": None, "date": "2026-06-08", "end": None, "note_zh": "预备测试，不计权重", "note_en": "Readiness task, unweighted"},
    {"subj": "MAM", "task": "Readiness 2", "type": "Test",
     "weight": None, "date": "2026-06-12", "end": None, "note_zh": "预备测试，不计权重", "note_en": "Readiness task, unweighted"},
    {"subj": "MAM", "task": "Topic Test 1", "type": "Test",
     "weight": 10, "date": "2026-07-29", "end": None, "note_zh": "", "note_en": ""},
    {"subj": "MAM", "task": "Investigation Pt 1", "type": "Investigation",
     "weight": 4, "date": "2026-08-28", "end": "2026-09-09",
     "note_zh": "8/28 布置，9/9 提交；两部分合计 20%（官方大纲：Part 1 = 4%、Part 2 = 16%）",
     "note_en": "Assigned 28 Aug, submitted 9 Sep; the two parts total 20% (official outline: Part 1 = 4%, Part 2 = 16%)"},
    {"subj": "MAM", "task": "Investigation Pt 2", "type": "Investigation",
     "weight": 16, "date": "2026-09-09", "end": None,
     "note_zh": "两部分合计 20%（官方大纲：Part 1 = 4%、Part 2 = 16%）",
     "note_en": "The two parts total 20% (official outline: Part 1 = 4%, Part 2 = 16%)"},
    # ACCT（加分测试）：学校 10/6 的通知给出日期与规格。权重不是 100% 里的
    # 一部分，而是「5% 加分计入期末」，所以 weight 留 None，避免各科合计超过 100。
    {"subj": "MAM", "task": "ACCT", "type": "Test",
     "weight": None, "date": "2026-11-02", "end": None,
     "note_zh": "占 5%，作为加分计入期末成绩", "note_en": "Counts 5%, added as a bonus to the final exam"},
    # 日期用学校通知的实际日期（11/2），大纲给的是窗口 10/28–11/13；两者都写进备注，
    # 免得看的人以为站上的日期和大纲对不上。
    {"subj": "MAM", "task": "Topic Test 2", "type": "Test",
     "weight": 20, "date": "2026-11-02", "end": None,
     "note_zh": "学校通知的日期；大纲给的窗口是 10/28–11/13",
     "note_en": "The date from the school's notice; the outline gives the window 28 Oct – 13 Nov"},
    {"subj": "MAM", "task": "Topic Test 3", "type": "Test",
     "weight": 10, "date": "2026-12-16", "end": None, "note_zh": "", "note_en": ""},
    {"subj": "MAM", "task": "Final Examination", "type": "Examination",
     "weight": 40, "external": True, "date": "2027-02-01", "end": "2027-02-12",
     "note_zh": "覆盖 Unit 3 + Unit 4 全部", "note_en": "All Unit 3 and Unit 4 content"},

    # ── ELD（来源：004_Assessment Outline_May 2026.docx）────────────────
    {"subj": "ELD", "task": "Task 1", "type": "Written production",
     "weight": 10, "date": "2026-07-08", "end": None, "note_zh": "", "note_en": ""},
    {"subj": "ELD", "task": "Task 2A", "type": "Investigation Part A",
     "weight": 5, "date": "2026-08-03", "end": "2026-08-07",
     "note_zh": "口头研究提案", "note_en": "Oral research proposal"},
    {"subj": "ELD", "task": "Task 3", "type": "Common Oral Assessment (COAT)",
     "weight": 10, "date": "2026-09-07", "end": "2026-09-18",
     "note_zh": "SCSA 统一口语考核，为期两周", "note_en": "SCSA common oral task, two-week window"},
    {"subj": "ELD", "task": "Task 4", "type": "Response",
     "weight": 7, "date": "2026-11-02", "end": "2026-11-20",
     "note_zh": "听力理解", "note_en": "Listening comprehension"},
    {"subj": "ELD", "task": "Task 5", "type": "Response",
     "weight": 8, "date": "2026-11-02", "end": "2026-11-20",
     "note_zh": "阅读理解 + 综合写作", "note_en": "Comprehension and synthesis writing"},
    {"subj": "ELD", "task": "Task 6", "type": "Written production",
     "weight": 10, "date": "2026-12-09", "end": None,
     "note_zh": "说服性演讲（书面）", "note_en": "Persuasive speech (written)"},
    {"subj": "ELD", "task": "Task 7", "type": "Oral production",
     "weight": 10, "date": "2027-01-04", "end": "2027-01-08",
     "note_zh": "口头说服演讲", "note_en": "Persuasive oral presentation"},
    {"subj": "ELD", "task": "Task 2B", "type": "Investigation Part B",
     "weight": 10, "date": "2027-01-08", "end": None,
     "note_zh": "研究报告提交", "note_en": "Written research report due"},
    {"subj": "ELD", "task": "Task 8", "type": "Final examination",
     "weight": 30, "external": True, "date": "2027-01-29", "end": "2027-02-12",
     "note_zh": "第二学期期末笔试", "note_en": "Semester 2 written examination"},

    # ── PHY（来源：VAULT OF ATPHY.pdf 第 10 页，ATPHY 考核表）──────────────
    # 2026-10 更正：本站此前六项全部写「日期未在大纲中给出」，那是错的——
    # 日期一直在上面这份文件里。表格底部另有一行「ASSESSMENT DATES ARE
    # TENTATIVE AND SUBJECT TO CHANGE」，所以这些日期是暂定的。
    {"subj": "PHY", "task": "Task 1", "type": "Topic Test 1",
     "weight": 14, "date": "2026-08-14", "end": None,
     "note_zh": "重力、水平与竖直面圆周运动、静力平衡与质心",
     "note_en": "Gravity, circular motion in horizontal and vertical planes, static equilibrium and centre of mass"},
    {"subj": "PHY", "task": "Task 5", "type": "Topic Test 2",
     "weight": 14, "date": "2027-01-14", "end": None,
     "note_zh": "电磁学、波粒二象性与量子理论",
     "note_en": "Electromagnetism, wave-particle duality and quantum theory"},
    {"subj": "PHY", "task": "Task 2", "type": "Evaluation & Analysis",
     "weight": 12, "date": "2026-10-02", "end": None,
     "note_zh": "重力与水平、竖直面圆周运动",
     "note_en": "Gravity and circular motion in horizontal and vertical planes"},
    {"subj": "PHY", "task": "Task 3", "type": "Evaluation Exam",
     "weight": 20, "date": "2026-10-27", "end": "2026-11-13",
     "note_zh": "静力平衡与质心、相对论、电磁学",
     "note_en": "Static equilibrium and centre of mass, relativity, electromagnetism"},
    {"subj": "PHY", "task": "Task 6", "type": "Final Evaluation",
     "weight": 30, "external": True, "date": "2027-01-29", "end": "2027-02-13",
     "note_zh": "覆盖 Unit 3 + 4 全部", "note_en": "All of Units 3 and 4"},
    {"subj": "PHY", "task": "Task 4", "type": "Lab Assessment",
     "weight": 10, "date": "2026-11-27", "end": "2026-12-09",
     "note_zh": "Science Inquiry 类：11/27 实操、12/9 笔试；范围波粒二象性",
     "note_en": "Science Inquiry: practical 27 Nov, written 9 Dec; wave-particle content"},

    # ── HBY（来源：HBY FILES.pdf 第 38 页，May'26 Assessment outline）──────
    # 2026-10 补：本站此前整科留空并写着「没找到可核实的考核数据」。
    # 该大纲一直在上面这份文件里，只是那一页是图片、没有文字层，
    # 之前的提取没看到。七项合计 100%。
    {"subj": "HBY", "task": "Topic Test", "type": "Topic Test",
     "weight": 10, "date": "2026-08-03", "end": None,
     "note_zh": "第 1–3 章", "note_en": "Chapters 1–3"},
    {"subj": "HBY", "task": "Extended Response", "type": "Extended Response",
     "weight": 7, "date": "2026-09-17", "end": None,
     "note_zh": "第 4–7 章", "note_en": "Chapters 4–7"},
    {"subj": "HBY", "task": "Lab Assessment", "type": "Lab Assessment",
     "weight": 10, "date": "2026-10-17", "end": None,
     "note_zh": "第 1 章", "note_en": "Chapter 1"},
    {"subj": "HBY", "task": "Evaluation Exam", "type": "Examination",
     "weight": 20, "date": "2026-11-02", "end": "2026-11-20",
     "note_zh": "第 1–8 章", "note_en": "Chapters 1–8"},
    {"subj": "HBY", "task": "Extended Response", "type": "Extended Response",
     "weight": 8, "date": "2026-12-17", "end": None,
     "note_zh": "第 8–10 章", "note_en": "Chapters 8–10"},
    {"subj": "HBY", "task": "Topic Test", "type": "Topic Test",
     "weight": 15, "date": "2027-01-13", "end": None,
     "note_zh": "第 10–12 章", "note_en": "Chapters 10–12"},
    {"subj": "HBY", "task": "Final Exam", "type": "Examination",
     "weight": 30, "external": True, "date": "2027-01-29", "end": "2027-02-12",
     "note_zh": "第 1–13 章全部", "note_en": "All chapters 1–13"},
]

# ── 每场考核的形式细节（并入考试日程表的备注行，不单独开页）────────────
# 只补表格里没有的那部分：几点考、考多久、多少分、允许带什么、考哪几章。
# 来源是学校发来的考前通知。三条红线：不写人名、不抄原文、不写考场
# （考场经常临时改，写上去很快过期，反而误事）。
# 键是 (科目, 任务名, 日期) —— 必须带日期：HBY 有两条 Extended Response、
# 两条 Topic Test，只按名字会串。对不上的键静默忽略，所以只写核实得到的。
ASSESS_FMT = {
    ("CSC", "Task 2", "2026-07-28"): (
        "4:30–5:30 pm，60 分钟；编程实作，题目由浅入深",
        "4:30–5:30 pm, 60 minutes; practical programming, increasing in difficulty"),
    ("MAM", "Topic Test 1", "2026-07-29"): (
        "4:30–5:30 pm，60 分钟；第 1 章微分（不含最优化）",
        "4:30–5:30 pm, 60 minutes; Chapter 1 differentiation (optimisation excluded)"),
    ("HBY", "Topic Test", "2026-08-03"): (
        "4:30–5:45 pm，5 分钟阅读 + 70 分钟作答",
        "4:30–5:45 pm, 5 min reading + 70 min working"),
    ("PHY", "Task 1", "2026-08-14"): (
        "4:30–5:30 pm，5 分钟阅读 + 55 分钟作答，47 分；科学计算器（不许 CAS），发公式册",
        "4:30–5:30 pm, 5 min reading + 55 min working, 47 marks; scientific calculator only (no CAS), formula booklet provided"),
    ("MAM", "Investigation Pt 2", "2026-09-09"): (
        "4:30–5:30 pm，60 分钟；微分（最优化），课堂内验证",
        "4:30–5:30 pm, 60 minutes; differentiation (optimisation), in-class validation"),
    ("HBY", "Extended Response", "2026-09-17"): (
        "4:30–5:25 pm，5 分钟阅读 + 50 分钟作答",
        "4:30–5:25 pm, 5 min reading + 50 min working"),
    ("PHY", "Task 2", "2026-10-02"): (
        "4:30–5:30 pm，5 分钟阅读 + 50 分钟作答，44 分",
        "4:30–5:30 pm, 5 min reading + 50 min working, 44 marks"),
    ("MAM", "ACCT", "2026-11-02"): (
        "9:20–10:20 am，60 分钟，60 分；第 1 节无计算器（3 题 25 分钟 27 分），"
        "第 2 节可用计算器（4 题 33 分钟 33 分）；两节都发公式表，可带 4 页 A4 笔记",
        "9:20–10:20 am, 60 minutes, 60 marks; Section 1 calculator-free "
        "(3 questions, 25 min, 27 marks), Section 2 calculator-assumed "
        "(4 questions, 33 min, 33 marks); formula sheet in both, four A4 pages of notes allowed"),
    ("MAM", "Topic Test 2", "2026-11-02"): (
        "2:00–3:51 pm，111 分钟；两节都发公式表",
        "2:00–3:51 pm, 111 minutes; formula sheet in both sections"),
}

# 升学自检的规则条数。首页卡片上写的是这个数字，以前直接硬编码在文案里，
# 规则库增删之后不会跟着变。这里只留一处，build-site.py 会拿生成出来的
# advising-rules.js 实际条数跟它核对，对不上就让构建失败。
ADVISING_RULE_COUNT = 30

# 各科权重汇总（来源同上）
WEIGHTS = {
    "CSC": [("Project", 40), ("Examination", 40), ("Theory test", 10), ("Practical Test", 10)],
    "MAM": [("Tests", 40), ("Investigation", 20), ("Examination", 40)],
    # 按官方大纲的 Assessment type 列汇总：Task 1/6 书面 20、Task 4/5 阅读 15、
    # Task 2A/2B 探究 15、Task 3 COAT 与 Task 7 口语合计 20、Task 8 笔试 30。
    # 2026-10 更正：原先写 Written production 30 + Oral production 10，把 Task 3
    # 那 10% 的 COAT 错记进了书面里。TASKS 逐条本来是对的，只有这张汇总表错。
    "ELD": [("Written production", 20), ("Response", 15), ("Investigation", 15),
            ("Oral", 20), ("Final examination", 30)],
    "PHY": [("Tests", 40), ("Examination", 50), ("Science Inquiry", 10)],
    # HBY：七项按类型归并 —— Topic Test 10+15、Extended Response 7+8、
    # Lab Assessment 10、Examination 20+30，合计 100%。
    "HBY": [("Tests", 25), ("Extended Response", 15),
            ("Lab Assessment", 10), ("Examination", 50)],
}

SUBJECT_NAMES = {
    "MAM": ("数学方法", "Mathematics Methods"),
    "HBY": ("人类生物", "Human Biology"),
    "PHY": ("物理", "Physics"),
    "ELD": ("英语", "English (EALD)"),
    "CSC": ("计算机", "Computer Science"),
}

SOURCES = {
    "CSC": "006_Assessment-Outline_ATCSC_May_2026.DOCX + 007_Course-Outline_ATCSC_May_2026.DOCX",
    "MAM": "01-MAM …/Introduction.txt（May 2026 Intake Assessment Outline）",
    "ELD": "004_Assessment Outline_May 2026.docx",
    "PHY": "VAULT OF ATPHY.pdf 第 10 页（ATPHY Assessment Outline，含日期；表下注明日期为暂定）",
    "HBY": "HBY FILES.pdf 第 38 页（May'26 Assessment outline，图片页）与第 36 页（May'26 Course Outline，13 章周次表）",
}

# ── 各科考核的内容范围 ────────────────────────────────────────────────────
# 只到「主题层面」——说明每项考核覆盖哪些内容，不复述大纲的任务描述原文
# （那些属学校与 SCSA 版权）。主题名是课程通用术语。
SCOPE = {
    "MAM": [
        ("Topic Tests 1–3",
         "Three separate tests, each covering what has been taught by then: further differentiation; then integrals and the logarithmic function; then discrete and continuous random variables and interval estimates for proportions",
         "三次测验，各考当时已教的内容：先是进阶微分；然后是积分与对数函数；再是离散与连续随机变量、比例的区间估计"),
        ("Investigation",         "Plan, research, conduct and communicate findings; in-class validation",
         "制定方案、研究、实施并汇报；课堂内验证"),
        ("Final Examination",     "All Unit 3 and Unit 4 content, including integrals, the logarithmic function, discrete and continuous random variables, the normal distribution, and interval estimates for proportions",
         "Unit 3 与 Unit 4 全部内容：积分、对数函数、离散与连续随机变量、正态分布、比例的区间估计"),
    ],
    "PHY": [
        ("Topic Test 1 / 2",      "Unit content as taught to that point, assessed through problems and calculations",
         "截至该阶段所学的单元内容，以题目与计算形式考查"),
        ("Evaluation & Analysis", "Extended evaluation and analysis of a physical situation",
         "对物理情境做延伸性的评估与分析"),
        ("Lab Assessment",        "Science Inquiry: practical work plus a written component",
         "科学探究：实操加笔试两部分"),
        ("Evaluation Exam / Final Evaluation", "Cumulative examination; the final covers all of Units 3 and 4",
         "累积性考试；期末覆盖 Unit 3 与 Unit 4 全部"),
    ],
    "ELD": [
        ("Task 1 / Task 6",       "Written production: essay and persuasive speech, responding to previously unseen questions",
         "书面产出：论述文与说服性演讲，现场命题"),
        ("Task 2A / 2B",          "Investigation: oral research proposal, then a written research report",
         "调查研究：先做口头研究提案，再提交书面研究报告"),
        ("Task 3 (COAT)",         "Common Oral Assessment Task set by SCSA and administered by the school",
         "由 SCSA 统一命题、学校组织的口语统考"),
        ("Task 4 / Task 5",       "Response: listening comprehension, and reading comprehension with synthesis writing",
         "应答：听力理解，以及阅读理解配综合写作"),
        ("Task 7",                "Oral production: persuasive speech delivered to peers",
         "口语产出：面向同伴的说服性演讲"),
        ("Task 8",                "Final written examination",
         "期末笔试"),
    ],
    "CSC": [
        ("Task 1 (Project)",      "Object-oriented program for a business client: two-dimensional array, classes, control structures; design and development, evaluation, project validation",
         "为客户编写面向对象程序：二维数组、类、控制结构；含设计开发、评估、项目验证"),
        ("Task 2 (Practical Test)", "A series of programming items of increasing difficulty, completed on a computer",
         "在电脑上完成的一组难度递增的编程题"),
        ("Task 4 (Theory Test)",  "Network communications and cyber security, including network diagrams using CISCO conventions, addressing, subnets, segmentation and security",
         "网络通信与网络安全：CISCO 规范的网络图、编址、子网、分段与安全"),
        ("Task 5 (Project)",      "Integrated database programming solution; relational database design and SQL queries, including referential integrity, insert/delete, inner joins, calculated fields",
         "集成数据库编程方案：关系数据库设计与 SQL 查询，含参照完整性、增删、内连接、计算字段"),
        ("Task 3 / Task 6 (Examination)", "Three-hour examinations using the ATAR Year 12 examination design brief",
         "各 3 小时笔试，依据 ATAR Year 12 考试设计概要"),
    ],
    "HBY": [
        # 注意：元组第一项是中英共用的标签，不能写中文——会漏进英文页。
        ("Topic Test (x2)",       "August: Chapters 1–3. January: Chapters 10–12.",
         "8 月：第 1–3 章。1 月：第 10–12 章。"),
        ("Extended Response (x2)", "September: Chapters 4–7. December: Chapters 8–10.",
         "9 月：第 4–7 章。12 月：第 8–10 章。"),
        ("Lab Assessment",        "Practical skills drawn from Chapter 1.",
         "第 1 章的实验技能。"),
        ("Evaluation Exam / Final Exam", "November: Chapters 1–8. February: all thirteen chapters.",
         "11 月：第 1–8 章。2 月：全书 13 章。"),
    ],
}

# ── 站内导航（单一来源）────────────────────────────────────────────────
# site-build.py 与 clean-mindmap.py 都读这一份。导图页不是 site-build 生成的，
# 以前它完全没有站点导航，这正是"跟其他页割裂"的主要来源；两边共用同一份列表，
# 才不会改一处漏一处。
#
# (文件名, 中文标签, 英文标签[, 英文文件名])
#   第 4 项只在两种语言的目标文件名不同时才写：升学自检中文是 advising/index.html、
#   英文是 advising/en.html，共用一个名字会让英文站在导航里点回中文版。
# ⚠ 顺序是按**三个走查代理的权重均值**排的（2026-10），不是拍脑袋：
#   高分学生 / 低分学生 / 游客 各给 9 项打 1–5 分，取均值，由重到轻。
#
#     考试日程 4.67 · 五科要点 4.00 · 知识导图 3.00 · 升学自检 3.00
#     术语表 3.00 · 学期时间线 3.00 · 真题与资料 2.67 · 关于 2.33 · 首页 2.33
#
#   首页虽然均值最低，但作为「回到主页」的入口按惯例留第一位（品牌名也可点）。
#   原顺序（时间线第 3、真题第 5）把「学期时间线」排得过高——高分学生说
#   「信它会判断错」，低分学生说「与考试日程重复」。**以后改顺序请一并改这段注释。**
NAV = [
    ("index.html", "首页", "Home"),
    ("timetable.html", "考试日程", "Timetable"),
    ("subjects.html", "五科要点", "Subjects"),
    ("mindmap.html", "知识导图", "Mind Map"),
    ("advising/index.html", "升学自检", "Advising", "advising/en.html"),
    ("glossary.html", "术语表", "Glossary"),
    ("timeline.html", "学期时间线", "Timeline"),
    # 英文标签要比中文短：页头容器内容宽只有 736px（780 减左右内边距），
    # 英文九个标签实测要 756px 会溢出 20px，把语言切换挤到第二行。
    # "Past Papers"（11 字符）改成 "Papers"（6）省下约 40px，留出余量。
    ("papers.html", "真题与资料", "Papers"),
    ("about.html", "关于", "About"),
]

BRAND_ZH = "学习笔记"
BRAND_EN = "Study Notes"
FOOTER_ZH = "AUSMAT May 2026 · 个人学习笔记"
FOOTER_EN = "AUSMAT May 2026 · personal study notes"


# ── 术语表 ──────────────────────────────────────────────────────────────
# 两位走查的学生都指出：ATAR 出现在至少 8 个页面却全站没有一处解释，
# EE/EA/FE/TT/ER 这些缩写也只在个别地方展开过。这一页补上。
#
# 事实来源都写在 src 里。凡本站无法核实的（例如各校具体换算），一律不写死。
GLOSSARY = [
    # 五科缩写必须排在最前 —— 它们是全站出现频率最高的词，而这一页
    # 自称解释「站内反复出现的名词与缩写」。第一版漏了它们，游客走查指出：
    # 「站点最常用的 5 个词，唯一该解释名词的页面不管」。
    ("五科缩写", "The five subjects", [
        {"t": "MAM", "full": "Mathematics Methods", "zh": "数学方法。微积分与统计。",
         "en": "Mathematics Methods — calculus and statistics.",
         "src": "西澳 SCSA 课程大纲（本科考核构成见本站五科要点页）", "srcEn": "this site's Subjects page"},
        {"t": "HBY", "full": "Human Biology", "zh": "人体生物学。",
         "en": "Human Biology.",
         "src": "西澳 SCSA 课程大纲（本科考核构成见本站五科要点页）", "srcEn": "this site's Subjects page"},
        {"t": "PHY", "full": "Physics", "zh": "物理。",
         "en": "Physics.",
         "src": "西澳 SCSA 课程大纲（本科考核构成见本站五科要点页）", "srcEn": "this site's Subjects page"},
        {"t": "ELD", "full": "English as an Additional Language or Dialect (EAL/D)",
         "zh": "英语（作为附加语言或方言）。**不是** English ATAR——那是另一门课，"
               "给英语为第一语言的学生。本站的真题页专门提醒过这一点。",
         "en": "English as an Additional Language or Dialect (EAL/D). **Not** the same as the "
               "English ATAR course, which is for first-language speakers; the Past Papers page "
               "flags that distinction.",
         "src": "SCSA", "srcEn": "SCSA"},
        {"t": "CSC", "full": "Computer Science", "zh": "计算机科学。",
         "en": "Computer Science.",
         "src": "西澳 SCSA 课程大纲（本科考核构成见本站五科要点页）", "srcEn": "this site's Subjects page"},
        {"t": "AUSMAT", "full": "Australian Matriculation",
         "zh": "澳洲大学预科课程，在马来西亚授课、考西澳 WACE 的 ATAR。"
               "本站记录的是这个体系的一届学生。",
         "en": "Australian Matriculation: a pre-university programme taught in Malaysia that "
               "sits the Western Australian WACE / ATAR. This site documents one intake of it.",
         "src": "SCSA / 课程常识", "srcEn": "SCSA and general course knowledge"},
    ]),
    ("升学制度", "Admissions", [
        {"t": "ATAR", "full": "Australian Tertiary Admission Rank",
         "zh": "0 到 99.95 之间的**排名**，不是分数也不是百分比。它表示你在同届中的相对位置——"
               "ATAR 80 的意思是排在同届前 20%。大学按它录取。",
         "en": "A **rank** between 0 and 99.95 — not a mark and not a percentage. It states your "
               "position within your cohort: an ATAR of 80 means you are in the top 20%. "
               "Universities admit on this number.",
         "src": "TISC《Tertiary Entrance Aggregate and ATAR》",
         "srcEn": "TISC, Tertiary Entrance Aggregate and ATAR"},
        {"t": "TEA", "full": "Tertiary Entrance Aggregate",
         "zh": "合成分：**计入 ATAR 的最好四门**的标准分之和，再加上适用的加分。"
               "TISC 公布的上限是 **430**。ATAR 由它换算而来，所以合成分是中间量，不是最终结果。",
         "en": "The aggregate: the scaled marks of your **best four ATAR subjects**, summed, plus "
               "any bonus that applies. TISC publishes a **maximum of 430**. The ATAR is derived "
               "from it, so the aggregate is an intermediate value, not the outcome.",
         "src": "TISC 招生指南（2027–2029 版均写明上限 430）",
         "srcEn": "TISC admission guides (the 2027–2029 editions all state the 430 maximum)"},
        {"t": "标准分 / Scaling", "tEn": "Scaling", "full": "Scaled marks",
         "zh": "把各科原始分按**课程难度**调整后的分数。ATAR 用的是标准分，不是学校给的原始分——"
               "所以「数学考 80、英语考 80」对合成分的贡献并不相同。"
               "本站的 ATAR 估算用的是某机构某一届的拟合曲线，**不是官方换算**。",
         "en": "Marks adjusted for **course difficulty**. The ATAR uses scaled marks, not the raw "
               "marks on a school report — so 80 in Mathematics and 80 in English do not contribute "
               "equally. This site's estimate uses one institution's curve for one intake; it is "
               "**not the official conversion**.",
         "src": "TISC 说明",
         "srcEn": "TISC documentation"},
        {"t": "AT 课程", "tEn": "AT course", "full": "ATAR course",
         "zh": "可以计入 ATAR 的课程类型。WACE 课程另有 General、Foundation 等类型，"
               "**那些的分数不计入 ATAR**。本站只记录 AT 科目。",
         "en": "The course type that counts toward an ATAR. WACE also has General and Foundation "
               "courses, whose marks **do not count toward an ATAR**. This site records AT subjects only.",
         "src": "SCSA《WACE Manual》",
         "srcEn": "SCSA, WACE Manual"},
        {"t": "数学加分", "tEn": "Mathematics bonus", "full": "Mathematics bonus",
         "zh": "修读并考核 Mathematics Methods 和/或 Mathematics Specialist，"
               "**各按该科标准分的 10%** 加进最好四门的合成分，**不论该科是否在最好四门之内**。"
               "官方指南写明 **TEA 上限 430**。",
         "en": "Studying and examining in Mathematics Methods and/or Mathematics Specialist adds "
               "**10% of that subject's scaled score** to the best-four aggregate — **regardless of "
               "whether the subject is one of the best four**. The same guide states the **maximum "
               "TEA is 430**.",
         "src": "TISC《Steps to uni for Year 12 students》2027 / 2028 / 2029 三版均如此写明",
         "srcEn": "TISC, Steps to uni for Year 12 students — stated identically in the 2027, 2028 and 2029 editions",
         "note_zh": "2024 年 2 月有过一则新闻报道称这类加分将取消，一度被广泛转述；"
                    "但 TISC 自己针对 2027–2029 入学的指南至今仍写「加分照旧」，本站按 TISC 原文为准。",
         "note_en": "A February 2024 news report said bonuses like this would be scrapped, and that "
                    "report was widely repeated. TISC's own guides for 2027–2029 entry still state the "
                    "bonus applies, so this site follows TISC's own wording."},
        {"t": "WACE", "full": "Western Australian Certificate of Education",
         "zh": "西澳高中毕业证书。拿到它和拿到 ATAR 是两件事：毕业有单独的学分与"
               "读写算术要求（见 OLNA）。",
         "en": "The Western Australian Certificate of Education. Earning it and earning an ATAR are "
               "two separate things: graduation has its own credit and literacy/numeracy "
               "requirements (see OLNA).",
         "src": "SCSA",
         "srcEn": "SCSA"},
        {"t": "SCSA", "full": "School Curriculum and Standards Authority",
         "zh": "西澳课程与标准局。制定大纲、命制外部考试、发布评分标准与考官报告。"
               "本站引用的官方真题都来自它的网站。域名是 `scsa.wa.edu.au`——网上常见写成 "
               "`scsa.wa.gov.au`，那个域名不存在。",
         "en": "The Western Australian curriculum and standards authority: it writes the syllabuses, "
               "sets the external exams, and publishes marking keys and examiner reports. Every "
               "official paper linked from this site comes from its website, `scsa.wa.edu.au` "
               "(often mis-cited online as `scsa.wa.gov.au`, which does not exist).",
         "src": "SCSA",
         "srcEn": "SCSA"},
        {"t": "TISC", "full": "Tertiary Institutions Service Centre",
         "zh": "负责计算 ATAR、受理大学志愿与录取的机构。ATAR 由它发布，不是学校算的。",
         "en": "The body that calculates the ATAR and handles university applications and offers in "
               "Western Australia. The ATAR is issued by TISC, not by your school.",
         "src": "TISC",
         "srcEn": "TISC"},
        {"t": "OLNA", "full": "Online Literacy and Numeracy Assessment",
         "zh": "读写与算术测试，**WACE 毕业的硬性要求**，与 ATAR 无关。"
               "阅读、写作、算术三项各须达到 Level 3；未过可以重考。"
               "本站时间线里没有它的日期，需要的话以学校通知为准。",
         "en": "The literacy and numeracy assessment required to **graduate** with a WACE — separate "
               "from the ATAR. You need Level 3 in reading, writing and numeracy; resits are "
               "available. This site's timeline does not carry its dates; check with the school.",
         "src": "SCSA",
         "srcEn": "SCSA"},
    ]),
    ("考核任务缩写", "Assessment task abbreviations", [
        {"t": "TT", "full": "Topic Test",
         "zh": "阶段性测验，通常覆盖一到几章。各科权重不同，是学期内最频繁的计分项。",
         "en": "A staged test, usually covering one to a few chapters. Weighting varies by subject; "
               "it is the most frequent scored item during the semester.",
         "src": "各科 Assessment Outline", "srcEn": "Subject assessment outlines"},
        {"t": "EE", "full": "Evaluation Exam",
         "zh": "学期内的评估考试，多在第一学期末或第二学期初。别与 FE 混——EE 是学期中，FE 是结课。",
         "en": "An evaluation exam held during the course, usually at the end of semester 1 or the "
               "start of semester 2. Not the same as FE, which comes at the end.",
         "src": "PHY / HBY Assessment Outline", "srcEn": "PHY and HBY assessment outlines"},
        {"t": "EA", "full": "Evaluation & Analysis",
         "zh": "物理的评估与分析任务，权重 12%。",
         "en": "Physics' evaluation-and-analysis task, weighted 12%.",
         "src": "PHY Assessment Outline", "srcEn": "PHY assessment outline"},
        {"t": "FE", "full": "Final Evaluation / Final Examination",
         "zh": "结课考试，通常覆盖全课程（Unit 3 + Unit 4）。各科权重最重的一项。",
         "en": "The final exam, usually covering the whole course (Units 3 and 4). Normally the "
               "heaviest single item in a subject.",
         "src": "各科 Assessment Outline", "srcEn": "Subject assessment outlines"},
        {"t": "ER", "full": "Extended Response",
         "zh": "长答/论述题任务，人体生物学用它考若干章的内容。",
         "en": "A long-answer or essay-style task. Human Biology uses it to assess set chapters.",
         "src": "HBY Assessment Outline", "srcEn": "HBY assessment outline"},
        {"t": "Synthesis", "full": "综合写作（不是 summary）",
         "fullEn": "Combining sources, not summarising",
         "zh": "把**多个来源**的信息整合成一篇，而不是逐篇总结。EAL/D 的 Section Two 有这一项，"
               "考官报告连着三年点名它是弱项：考生只做 summary —— 一段一个来源、彼此不搭话。"
               "**合格的做法是让来源之间发生关系**：谁支持谁、谁和谁冲突、合起来能推出什么。",
         "en": "Combining **several sources** into one piece, rather than summarising each in turn. "
               "It is part of EAL/D Section Two, and the examiner reports have flagged it as weak "
               "three years running: candidates summarise — one paragraph per source, with no "
               "connection between them. **The passing move is to make the sources talk to each "
               "other**: which supports which, where they conflict, and what the combination implies.",
         "src": "SCSA EAL/D 考官报告与考试设计简报",
         "srcEn": "SCSA EAL/D examiner reports and examination design brief"},
        {"t": "COAT", "full": "Common Oral Assessment Task",
         "zh": "SCSA **统一命制**、由学校实施的口语考核（ELD 的 Task 3）。"
               "给 5 分钟准备一张图片并做笔记，随后进行 10 分钟访谈，全程录音录像送 SCSA。",
         "en": "An oral task **set by SCSA** and administered by the school (ELD Task 3). You get "
               "five minutes to view an image and make notes, then a ten-minute interview; the "
               "recording goes to SCSA.",
         "src": "ELD Assessment Outline", "srcEn": "ELD assessment outline"},
        {"t": "Readiness task", "full": "—",
         "zh": "开学初的诊断性测试，本站记录的两项**不计权重**，用来摸底。",
         "en": "A diagnostic test at the start of the course. The two recorded here are "
               "**unweighted** and serve to establish a baseline.",
         "src": "MAM Assessment Outline", "srcEn": "MAM assessment outline"},
        {"t": "Investigation", "full": "—",
         "zh": "探究任务：自己提出问题、研究并汇报。数学方法是两部分（计划 + 课堂内验证），"
               "英语是 Part A 口头提案 + Part B 书面报告。",
         "en": "An investigation: you pose a question, research it and report. In Mathematics "
               "Methods it runs in two parts (plan, then in-class validation); in ELD it is an oral "
               "proposal (Part A) plus a written report (Part B).",
         "src": "MAM / ELD Assessment Outline", "srcEn": "MAM and ELD assessment outlines"},
        {"t": "ACCT", "full": "学校内部考核代码（未见官方展开）",
         "fullEn": "Internal school assessment code (no published expansion)",
         "zh": "学校在日程里用的内部代号，是一份 **60 分钟**的测试，与 EE 同期。"
               "**它的全称没有公开出处，本站不替它编一个。** 是否计入总评以学校通知为准"
               "（课程资料里记的是「待确认」）。",
         "en": "An internal code the school uses in its calendar: a **60-minute** test held "
               "alongside EE. **Its full form is not published anywhere this site could find, and "
               "it is not invented here.** Whether it counts toward your grade is for the school to "
               "confirm — the course materials record it as unconfirmed.",
         "src": "学校课程资料中仅以代号出现", "srcEn": "Course materials, where it appears as a code only"},
        {"t": "CAS", "full": "Computer Algebra System（计算器代数学系统）",
         "fullEn": "Computer Algebra System",
         "zh": "能**符号运算**的计算器，不只是算数值：可以求导、积分、解方程、化简。"
               "MAM 外部考试分两节——**第一节禁用任何计算器**（50 分钟，35%），"
               "**第二节允许绘图/CAS 计算器**（100 分钟，65%，可带 2 张 A4 手写笔记，公式表由考场提供）。"
               "导图里写「用 CAS 计算」的就是指第二节。",
         "en": "A calculator that does **symbolic** algebra, not just numbers: differentiation, "
               "integration, solving equations, simplification. The MAM external exam has two sections — "
               "**Section One bans all calculators** (50 minutes, 35%), **Section Two allows a graphics/CAS "
               "calculator** (100 minutes, 65%, two A4 sheets of handwritten notes permitted, formula sheet "
               "supplied). Where the mind map says “use CAS”, it means Section Two.",
         "src": "MAM 课程与考核大纲", "srcEn": "MAM course and assessment outline"},
        {"t": "Lab Assessment", "full": "—",
         "zh": "实验技能评估，取材于课程中的实验。物理包含实验操作与书面部分。",
         "en": "Assessment of practical skills, drawn from the experiments done during the course. "
               "In Physics it has a practical component and a written one.",
         "src": "PHY / HBY Assessment Outline", "srcEn": "PHY and HBY assessment outlines"},
    ]),
]

GLOSSARY_NOTE_ZH = ("本页只解释名词，不给预测。凡是本站无法核实的数字（例如你那一届的实际换算曲线）"
                    "都不写死；标了「来源」的条目可在对应机构网站上复核。")
GLOSSARY_NOTE_EN = ("This page defines terms only; it makes no predictions. Figures this site cannot "
                    "verify — your own intake's conversion curve, for instance — are deliberately left "
                    "out. Items marked with a source can be checked on the issuing body's website.")


# ── 真题与资料入口 ────────────────────────────────────────────────────────
# 本站只做「指路」，不托管试卷文件。理由见页面上的说明：SCSA 试卷有版权，
# 而且已有同类站点因官方下架要求关站（atar-wace-archive.github.io，公告
# 2022-08-21）。把试卷放进这个公开仓库等于把风险引到自己身上。
#
# 下列每一个 URL 都在 2026-10 用 HTTP 请求实测过，状态码记在 STATUS 里。
# 域名注意：SCSA 是 scsa.wa.edu.au，不是 scsa.wa.gov.au（后者根本不存在，
# 网上大量二手资料写错，包括给本项目提供线索的检索结果）。
PAPERS = {
    "MAM": {"scsa": "mathematics-methods-past-atar-course-exams",
            "vault": "https://wacevault.com/methods/"},
    "HBY": {"scsa": "human-biology-past-atar-course-exams",
            "vault": "https://wacevault.com/human_bio/"},
    "PHY": {"scsa": "physics-past-atar-course-exams",
            "vault": "https://wacevault.com/physics/"},
    "ELD": {"scsa": "english-as-an-additional-languagedialect-past-atar-course-exams",
            "vault": "https://wacevault.com/eld/"},
    "CSC": {"scsa": "computer-science-past-atar-course-exams",
            "vault": "https://wacevault.com/compsci/"},
}

SCSA_PAPERS_BASE = "https://www.scsa.wa.edu.au/publications/past-atar-course-exams/"

# 逐年覆盖（2026-10 逐目录实测）。
# 官方五科的年份完全一致，社区库逐科略有差别（MAM/HBY 从 2010 起，其余从 2009 起），
# 所以分列而不是笼统写一个区间——之前那句「五科相同」是错的。
#   (科目, SCSA 官方, WACE Vault)
PAPER_COVERAGE = [
    ("MAM", "2020–2025", "2010–2024"),
    ("HBY", "2020–2025", "2010–2024"),
    ("PHY", "2020–2025", "2009–2024"),
    ("ELD", "2020–2025", "2009–2024"),
    ("CSC", "2020–2025", "2009–2024"),
]

COVERAGE_HEAD_ZH = ["科目", "SCSA 官方", "WACE Vault"]
COVERAGE_HEAD_EN = ["Subject", "SCSA (official)", "WACE Vault"]

COVERAGE_NOTE_ZH = (
    "两栏合起来覆盖 2009–2025，但**各科起止年份不同**：官方页一律 2020 起，社区库多数科目 2010 起、计算机到 2009，而社区库没有一年到 2025。官方页按年给出考卷、评分标准与公式手册，年份从 2020 起；"
    "社区库年份更长（多数科目 2010 起，计算机到 2009），数学方法还另有一份"
    "「按主题排序的题目」目录，想针对某个知识点刷题时比按年份翻省事。"
    "**各科起止年份不完全相同，具体看上面那张表。**")
COVERAGE_NOTE_EN = (
    "Between them the two columns cover 2009–2025, but **the range differs by subject**: the official pages all start at 2020, the vault reaches 2010 for most subjects and 2009 for Computer Science, and the vault has no year as recent as 2025. The official pages give the paper, the "
    "marking key and the formula sheet for each year, starting from 2020; the vault goes "
    "further back (2010 for most subjects, 2009 for Computer Science), and for Mathematics "
    "Methods it adds a questions-sorted-by-topic folder that beats paging through years when "
    "drilling one concept. **The exact start and end years differ by subject — see the table "
    "above.**")

# 「社区库」这件事必须说明白。2026-10 核查发现 wacevault.com 收录的不只是
# 官方历年卷，还有商业出版社教材 PDF 与学校内部考卷 —— 后者正是本站在别处
# 明确排除的类别。链接本身不是收录，所以保留入口，但不能装作没这回事：
# 不写清楚，等于替一个性质不明的站背书。
VAULT_CAVEAT_ZH = (
    "「社区库」那一栏是第三方整理的，<b>不是官方来源</b>。核查发现它除了历年卷，"
    "还收录商业出版社教材与学校内部考卷；那类内容本站不收录、也不为其背书，"
    "这里只提供入口。要稳妥就用上面的 SCSA 官方页 —— 免费、免登录、年份 2020 起。")
VAULT_CAVEAT_EN = (
    "The “community” column is a third-party collection, <b>not an official source</b>. "
    "It was found to carry commercial textbook PDFs and internal school test papers alongside "
    "past exams. This site neither hosts nor endorses that material; the link is an entry point "
    "only. If you want to stay clear of it, use the SCSA pages above — free, no login, 2020 "
    "onwards.")

# ── 考官报告的常见失分点 ──────────────────────────────────────────────
# 来源：SCSA 每年随真题一起公开的 ATAR course examination report（考官报告）。
# 官方发布它就是为了让师生知道「哪里普遍丢分」，这里做的是归类转述。
#
# 三条纪律：
#   1. **只写失分现象，不写题目原文**。
#   2. 标明是哪一年的报告 —— 报告逐年写，今年提的不代表年年提。
#   3. ELD 那条合并了 2025/2024/2023 三份，因为 2025 那份只有两页、偏简。
#
# 版权口径：这些报告版权属 SCSA，其条款允许的复制限于教育机构内部非商业使用，
# 公开个人站不在豁免里。所以这里**只转述事实、注明来源、并给出原文入口**，
# 不转载原文、不在站上存放 PDF。读者要看原话，按上面的链接去官方页面。
EXAMINER_FINDINGS = [
    ("MAM", "2025", [
        ("对数（4.1）", "Logarithms (4.1)"),
        ("直线运动与「以积分定义的函数」（3.1 / 3.2）",
         "Rectilinear motion and functions defined by an integral (3.1 / 3.2)"),
        ("置信区间**算得对但解释不出**（4.3，报告三次点名）",
         "Confidence intervals computed correctly but **not explained** (4.3 — flagged three times)"),
        ("「show that」类题步骤不足", "Insufficient working on “show that” questions"),
        ("作图时关键特征定位不准", "Key features mislocated when sketching graphs"),
    ]),
    ("HBY", "2025", [
        ("**生物技术**：PCR、凝胶电泳、蛋白质分析",
         "**Biotechnology**: PCR, gel electrophoresis, protein analysis"),
        ("**Unit 4 的 extended answer 是全卷最弱环节**（得分率 42.53%，U3 为 56.73%）",
         "**The Unit 4 extended answer is the weakest part of the paper** "
         "(42.53% versus 56.73% for Unit 3)"),
        ("绝对年代测定（钾-氩法）", "Absolute dating (potassium–argon)"),
        ("基因流 vs 遗传漂变、奠基者效应 vs 物种形成",
         "Gene flow versus genetic drift; founder effect versus speciation"),
        ("反射弧的组成", "Components of a reflex arc"),
        ("半衰期计算", "Half-life calculations"),
    ]),
    ("PHY", "2025", [
        ("**三角函数的应用**", "**Applying trigonometry**"),
        ("**代数式变形、分离变量**", "**Algebraic manipulation and separating variables**"),
        ("解释题不先规划再写", "Not planning before writing explanation questions"),
        ("**从第一性原理推导**", "**Deriving from first principles**"),
        ("**相对论效应与相对论动量/能量**（报告说是普遍的错误概念）",
         "**Relativistic effects and relativistic momentum/energy** "
         "(the report calls these widespread misconceptions)"),
        ("**Section Three（理解与数据分析）是三节里最差的**",
         "**Section Three (comprehension and data analysis) is the weakest of the three**"),
    ]),
    ("ELD", "2025 + 2024 + 2023", [
        ("**synthesis 只总结不综合**（三年连考连弱）",
         "**Synthesis that only summarises without combining sources** (weak three years running)"),
        ("**交背好的作文、答非所问**",
         "**Submitting a memorised essay that does not answer the question**"),
        ("**模板化的 firstly / secondly / thirdly**",
         "**Formulaic “firstly / secondly / thirdly”**"),
        ("**把 speech 写成 essay**", "**Writing a speech as though it were an essay**"),
        ("多部分题漏答其中的分点", "Leaving parts of multi-part questions unanswered"),
        ("时间分配失衡", "Poor time allocation"),
    ]),
    ("CSC", "2025", [
        ("**子网划分与 IP 编址**（含路由器接口）",
         "**Subnetting and IP addressing** (including router interfaces)"),
        ("网络性能数据的解读", "Interpreting network performance data"),
        ("**SQL join**", "**SQL joins**"),
        ("**二维数组、字典、排序、面向对象**等多步骤算法",
         "**Multi-step algorithms**: 2-D arrays, dictionaries, sorting, object-oriented code"),
        ("**加密概念的应用**（识别可以，结合情境解释不足）",
         "**Applying encryption concepts** (recognition is fine; contextual explanation is not)"),
        ("低脚手架情境题不会拆解", "Struggling to break down low-scaffold scenario questions"),
    ]),
]

EXAMINER_NOTE_ZH = (
    "来源是 SCSA **每年随真题一起公开的考官报告**（ATAR course examination report）。"
    "它本就是官方用来告诉师生「哪里普遍丢分」的文件，这里只做了归类转述，"
    "**不含任何试题原文**。报告逐年写 —— 标 2025 的条目来自 2025 年那份，"
    "不代表年年都提；ELD 那条合并了三份，因为 2025 年那份只有两页、写得简。"
    "**想看原话请去官方页面**（就在试卷与评分标准旁边）。")
EXAMINER_NOTE_EN = (
    "Source: the **examiner's report SCSA publishes alongside each year's paper** "
    "(ATAR course examination report) — the document the Authority issues precisely to tell "
    "teachers and students where marks are commonly lost. This is a categorised summary of it "
    "and **contains no question text**. Reports are written year by year, so an item marked "
    "2025 comes from the 2025 report and is not a claim that it recurs annually; the ELD row "
    "merges three reports because the 2025 one runs only two pages. "
    "**For the original wording, go to the official page** — it sits beside the paper and the "
    "marking key.")


VAULT_EXTRA_ZH = "另含 2007–08 草稿卷与 2015–16 样卷。"
VAULT_EXTRA_EN = "plus a 2007–08 draft and 2015–16 samples."

# 可整目录下载的镜像。
#
# 2026-10 逐个实测后只留了这一个。其余四个查过之后删掉了，理由记在这里，
# 免得以后又有人把它们加回来：
#   rinr4t/wacevault      8.6 GB 的 wacevault 全量镜像，止于 2022，且没有 eld / compsci。
#                         体积与收益完全不成比例——要的那几科官方页本来就有。
#   GrimReaper2654/...    不是文件库，是个按知识点打标签的刷题网站（JS 应用），
#                         本身不含试卷。性质不同，不适合放在「可整目录下载」下面。
#   goanna247/...         只有计算机一科，且 2022 年 4 月后没再更新，
#                         而 WACE 计算机大纲 2024 年改过版。
#   jamesbrayy/atar-notes ATAR 通识笔记，没有人体生物学也没有计算机。
PAPER_MIRRORS = [
    {"name": "shortfusemini/past-wace",
     "url": "https://github.com/shortfusemini/past-wace",
     "zh": "按科目与年份分目录的历年试卷，逐科覆盖 2016–2024。"
           "两点注意：<b>没有人体生物学</b>；这里的「英语」是 English ATAR，"
           "与 EAL/D 不是同一门课，不能当 EAL/D 用。",
     "en": "Past papers filed by subject and year, each covering 2016–2024. Two caveats: "
           "<b>there is no Human Biology</b>, and its \u201cEnglish\u201d is the English ATAR "
           "course rather than EAL/D."},
]

# 为什么不在本站放试卷文件 —— 这句话要留在页面上
PAPERS_STANCE_ZH = (
    "本页只提供入口，不存放试卷文件。WACE 试卷的版权属 SCSA，"
    "此前已有同类站点因官方下架要求关站（atar-wace-archive.github.io，2022 年 8 月）。"
    "上面每个链接都在 2026 年 10 月实测可用；官方页面免费、无需登录。")
PAPERS_STANCE_EN = (
    "This page links only; it hosts no papers. WACE papers are SCSA copyright, and an earlier "
    "site carrying them was shut down at official request (atar-wace-archive.github.io, August "
    "2022). Every link above was tested working in October 2026; the official pages are free and "
    "need no login.")

