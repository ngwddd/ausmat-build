# -*- coding: utf-8 -*-
"""Field roadmaps and pathway timelines.

Two workbook sheets become one module each:

  SKILLS ROADMAP          -> ROADMAP, one entry per field the form offers
  OPTIONS AND OPPORTUNITIES -> OPPORTUNITIES, pathways plus per-country timelines

Everything here is written for this project. The workbook's own sheet has a
single worked example; copying its sentences would be copying its author's
writing, so only the SHAPE is taken: careers, activities, skills, and why the
field is worth the years.

The links ARE reproduced, because they point at public admissions services
rather than at anyone's prose, and a student needs the entry point. Every one was
requested and checked; the check result is recorded next to it.
"""

# ── field roadmaps ───────────────────────────────────────────────────────────
# Keyed by the exact strings in `vocabularies.fields`. The build asserts that
# every vocabulary field has an entry, because a key typo makes the module go
# silent for that field and nothing else would notice.
#
# "Undecided" is deliberately absent: a roadmap is per-field by construction, so
# there is nothing specific and true to say, and a generic paragraph would be
# filler. The rule stays silent instead.

ROADMAP = {
    "Medicine": {
        "en": {
            "careers": "clinical practice, surgery, general practice, medical research, "
                       "public health, and the specialties that branch off each of them.",
            "activities": "first-aid and St John qualifications, volunteering in a care "
                          "setting, hospital or hospice observation weeks, and any "
                          "sustained commitment where you are responsible for someone else.",
            "skills": "scientific reasoning under uncertainty, communication with people "
                      "who are frightened, and the stamina to keep studying for a decade.",
            "why": "Demand is driven by population ageing and it is one of the few fields "
                   "where the qualification travels across borders.",
        },
        "zh": {
            "careers": "临床、外科、全科、医学研究、公共卫生，以及从这些方向分出去的各个专科。",
            "activities": "急救与 St John 证书、在照护机构做志愿者、医院或临终关怀机构的见习周，"
                          "以及任何一段你真正对别人负责的长期投入。",
            "skills": "在信息不全时做科学判断、和害怕的人沟通，以及能连续读十年书的耐力。",
            "why": "需求由人口老龄化推动，而且它是少数几个资格能跨国使用的领域之一。",
        },
    },
    "Dentistry": {
        "en": {
            "careers": "general dental practice, orthodontics, oral surgery, paediatric "
                       "dentistry, and dental public health.",
            "activities": "manual dexterity work you can show (instrument, craft or "
                          "model-making), shadowing a practice, and health volunteering.",
            "skills": "fine motor control, working seated at close range for long "
                      "stretches, and explaining procedures to nervous patients.",
            "why": "Small cohorts and high demand keep it competitive, but the work is "
                   "steady and largely independent of economic cycles.",
        },
        "zh": {
            "careers": "全科牙医、正畸、口腔外科、儿童牙科，以及口腔公共卫生。",
            "activities": "能拿得出手的手工精细活（乐器、手作或模型制作）、在牙科诊所见习、"
                          "医疗类志愿服务。",
            "skills": "精细动作控制、长时间近距离坐姿操作，以及向紧张的病人解释治疗过程。",
            "why": "招生人数少、需求高，所以竞争激烈；但执业稳定，基本不受经济周期影响。",
        },
    },
    "Law": {
        "en": {
            "careers": "solicitor or barrister work, in-house counsel, policy, regulation, "
                       "and the compliance side of any large organisation.",
            "activities": "mooting, debating, a school or community legal centre, and "
                          "reading a judgment properly rather than a summary of it.",
            "skills": "reading a dense document and extracting what actually matters, "
                      "writing an argument someone can follow, and disagreeing without "
                      "escalating.",
            "why": "The core skill is applied reasoning on text, which moves easily into "
                   "policy, technology regulation and management.",
        },
        "zh": {
            "careers": "事务律师或出庭律师、企业法务、政策、监管，以及任何大型机构的合规岗位。",
            "activities": "模拟法庭、辩论、学校或社区法律中心，以及完整读一份判决书而不是读摘要。",
            "skills": "从冗长文件里读出真正要紧的部分、把论证写到别人能跟上，以及在对立中不升级冲突。",
            "why": "核心能力是对文本做应用推理，这套能力转向政策、技术监管和管理都很顺。",
        },
    },
    "Engineering": {
        "en": {
            "careers": "design and build roles across civil, mechanical, electrical, "
                       "chemical and biomedical work, plus project and systems engineering.",
            "activities": "a physical project you finished and can talk about (robotics, "
                          "Arduino, a repair, a build), and maths or physics competitions.",
            "skills": "turning a vague requirement into a specification, estimating before "
                      "measuring, and documenting your own work so someone else can use it.",
            "why": "It is the most directly transferable technical degree: the same "
                   "modelling skills apply to infrastructure, energy and medicine.",
        },
        "zh": {
            "careers": "土木、机械、电气、化工、生物医学等方向的设计与建造岗，以及项目与系统工程。",
            "activities": "一个你真做完并能讲清楚的项目（机器人、Arduino、一次维修或搭建），"
                          "以及数学或物理竞赛。",
            "skills": "把模糊需求变成规格书、先估算再测量，以及把自己做的东西写成别人能接着用的文档。",
            "why": "它是最容易迁移的技术学位：同一套建模能力可以用在基础设施、能源和医疗上。",
        },
    },
    "Computer Science": {
        "en": {
            "careers": "software engineering, data and machine learning, security, "
                       "infrastructure, and research.",
            "activities": "a public repository with real commit history, a project that "
                          "other people actually use, and competitive programming if you "
                          "enjoy it.",
            "skills": "breaking an ambiguous problem into parts you can test, reading "
                      "code you did not write, and finishing things.",
            "why": "The demand is broad rather than deep, so the field absorbs people with "
                   "strong fundamentals even when specific tools change.",
        },
        "zh": {
            "careers": "软件工程、数据与机器学习、安全、基础设施，以及研究岗。",
            "activities": "一个有真实提交记录的公开仓库、一个真有人用的项目，以及你确实喜欢的算法竞赛。",
            "skills": "把模糊问题拆成可测试的小块、读别人写的代码，以及把东西做完。",
            "why": "需求广而不窄，所以只要基本功扎实，具体工具换代也不影响你被需要。",
        },
    },
    "Business": {
        "en": {
            "careers": "accounting and finance, consulting, operations, marketing, and "
                       "general management.",
            "activities": "running something with a budget or a team, a part-time job with "
                          "real responsibility, and any competition where you had to "
                          "present or defend a number.",
            "skills": "reading a set of accounts, writing persuasively in plain language, "
                      "and building a spreadsheet that someone else can audit.",
            "why": "It is a generalist degree whose value comes from what you do alongside "
                   "it, so the activities matter more here than the marks.",
        },
        "zh": {
            "careers": "会计与金融、咨询、运营、市场，以及综合管理。",
            "activities": "管过一笔预算或一个团队、一份真有责任的兼职，以及任何需要你讲清或守住一个数字的比赛。",
            "skills": "看懂一套账、用平实语言写出有说服力的文字，以及做出别人能复核的表格。",
            "why": "它是通识型学位，价值来自你在它之外做了什么，所以这个领域里经历比分数更被看。",
        },
    },
    "Psychology": {
        "en": {
            "careers": "clinical and counselling psychology, organisational psychology, "
                       "research, and the behavioural side of policy and product work.",
            "activities": "volunteering that involves listening to people in difficulty, "
                          "and reading a study properly enough to say what it does not show.",
            "skills": "statistical literacy, interviewing without leading, and holding "
                      "your own reaction back while someone describes something hard.",
            "why": "Behavioural evidence is now expected in policy, health and product "
                   "design, which widened the field beyond clinical practice.",
        },
        "zh": {
            "careers": "临床与咨询心理、组织心理、研究，以及政策与产品里的行为科学岗位。",
            "activities": "需要倾听困境中的人的志愿服务，以及能把一篇研究读到说得出「它没有证明什么」。",
            "skills": "统计素养、不带引导地访谈，以及在别人讲述难事时稳住自己的反应。",
            "why": "现在政策、健康和产品设计都要行为证据，这个领域早已超出临床执业的范围。",
        },
    },
    "Nursing": {
        "en": {
            "careers": "hospital and community nursing, midwifery, critical care, mental "
                       "health nursing, and clinical education.",
            "activities": "a care-related volunteering role, first aid training, and any "
                          "job where you handled a shift roster and did not drop it.",
            "skills": "prioritising several urgent things at once, recording accurately "
                      "under time pressure, and recovering between difficult shifts.",
            "why": "Consistently short-staffed, geographically mobile, and one of the "
                   "fastest routes from a degree to secure professional work.",
        },
        "zh": {
            "careers": "医院与社区护理、助产、重症护理、精神科护理，以及临床教学。",
            "activities": "与照护相关的志愿岗位、急救培训，以及任何需要你顶住排班且没有掉链子的工作。",
            "skills": "同时处理多件急事时的排序能力、在时间压力下准确记录，以及在难熬的班次之间恢复。",
            "why": "长期缺人、地点流动性强，而且是从学位到稳定专业工作最快的路径之一。",
        },
    },
    "Architecture": {
        "en": {
            "careers": "architectural practice, urban design and planning, heritage and "
                       "conservation, and construction project leadership.",
            "activities": "a portfolio, not a certificate: drawings, models, photographs "
                          "of a space you designed, and a build you helped on.",
            "skills": "drawing to explain rather than to decorate, spatial reasoning, and "
                      "taking criticism on work you spent weeks on.",
            "why": "Cities are being retrofitted rather than only expanded, which keeps "
                   "the work close to energy, planning and policy.",
        },
        "zh": {
            "careers": "建筑设计、城市设计与规划、遗产保护，以及建造项目的带队工作。",
            "activities": "作品集而不是证书：图纸、模型、你设计过的空间的照片，以及你参与过的实际建造。",
            "skills": "用图解释而不是用图装饰、空间推理，以及承受别人对你做了几周的东西提出批评。",
            "why": "城市正在被改造而不只是扩张，这让这份工作紧贴能源、规划和政策。",
        },
    },
    "Sciences": {
        "en": {
            "careers": "laboratory and field research, data science, medical and "
                       "environmental technology, and science communication.",
            "activities": "a sustained investigation of your own (even a small one), and "
                          "reading primary papers rather than textbooks alone.",
            "skills": "designing a fair test, quantifying your own uncertainty, and "
                      "writing up a result that did not go the way you wanted.",
            "why": "The degree is a method rather than a job title, which is why it "
                   "converts into research, industry and teaching alike.",
        },
        "zh": {
            "careers": "实验室与野外研究、数据科学、医疗与环境技术，以及科学传播。",
            "activities": "一次属于你自己的持续探究（哪怕很小），以及读原始论文而不只是读教材。",
            "skills": "设计公平的对照、量化你自己的不确定度，以及把一个没做出预期结果的实验写清楚。",
            "why": "这个学位给的是一套方法而不是一个职位名，所以它同样能转向研究、产业和教学。",
        },
    },
    "Humanities": {
        "en": {
            "careers": "policy and public administration, law, journalism and editing, "
                       "teaching, and cultural institutions.",
            "activities": "editing or running a publication, a long essay you are proud "
                          "of, and debate or model UN if the speaking appeals to you.",
            "skills": "arguing from evidence rather than assertion, reading a whole book "
                      "closely, and writing to a length limit without padding.",
            "why": "It trains judgement on ambiguous material, which is the part of white-"
                   "collar work least likely to be automated away.",
        },
        "zh": {
            "careers": "政策与公共行政、法律、新闻与编辑、教学，以及文化机构。",
            "activities": "编辑或运营一份刊物、一篇你自己满意的长文，以及如果你喜欢表达就去辩论或模联。",
            "skills": "用证据支撑观点而不是断言、把一整本书读细，以及在字数限制内写完不注水。",
            "why": "它训练的是面对模糊材料时的判断力，而这正是白领工作里最不容易被自动化取代的部分。",
        },
    },
    "Education": {
        "en": {
            "careers": "school teaching, curriculum and assessment design, educational "
                       "psychology, and learning technology.",
            "activities": "tutoring or coaching that lasted a term or more, and any role "
                          "where you were responsible for a group of younger people.",
            "skills": "explaining one idea three different ways, managing a room, and "
                      "assessing what someone actually misunderstood.",
            "why": "Shortages are structural in most systems, and the qualification "
                   "transfers across countries more easily than most.",
        },
        "zh": {
            "careers": "学校教学、课程与评估设计、教育心理，以及学习技术。",
            "activities": "持续一个学期以上的家教或带训，以及任何你真正对一群更年轻的人负责的角色。",
            "skills": "把同一个概念用三种方式讲清楚、管理一间教室，以及判断对方到底哪里理解错了。",
            "why": "多数体系里师资短缺是结构性的，而且这个资格比大多数专业更容易跨国使用。",
        },
    },
}

# ── pathways and timelines ───────────────────────────────────────────────────
# Each link was requested; `check` records what came back. A link that failed is
# removed rather than shipped hopeful.

OPPORTUNITIES = {
    "pathways": {
        "en": [
            {"key": "foundation",
             "text": "A foundation or pathway year at the destination institution, "
                     "which is the usual route when the qualification you hold is not "
                     "recognised directly.",
             "links": [{"label": "Studies in Australia", "url": "https://www.studiesinaustralia.com/",
                        "check": "ok"}]},
            {"key": "tafe",
             "text": "A vocational or diploma route into a degree, which often carries "
                     "credit and can be entered with lower academic requirements.",
             "links": [{"label": "TAFE International WA", "url": "https://www.tafeinternational.wa.edu.au/",
                        "check": "ok"}]},
            {"key": "course-search",
             "text": "Searching by the published admission criteria rather than by course "
                     "name, so you compare the actual numbers instead of the marketing.",
             "links": [{"label": "Course Seeker", "url": "https://www.courseseeker.edu.au/",
                        "check": "ok"}]},
        ],
        "zh": [
            {"key": "foundation",
             "text": "在目标院校读预科或衔接年——当你手上的学历不被直接承认时，这是通常的路径。",
             "links": [{"label": "Studies in Australia", "url": "https://www.studiesinaustralia.com/",
                        "check": "ok"}]},
            {"key": "tafe",
             "text": "先读职业或文凭课程再进学位——通常能带学分，入学学术要求也更低。",
             "links": [{"label": "TAFE International WA", "url": "https://www.tafeinternational.wa.edu.au/",
                        "check": "ok"}]},
            {"key": "course-search",
             "text": "按公布的录取标准而不是按专业名称去搜，这样你比较的是真实数字而不是宣传语。",
             "links": [{"label": "Course Seeker", "url": "https://www.courseseeker.edu.au/",
                        "check": "ok"}]},
        ],
    },
    "timelines": {
        "Australia": {
            "en": "Australia: applications go through the state admissions centre or the "
                  "institution directly, and offers are released in rounds, so the timing "
                  "of your results matters as much as the marks.",
            "zh": "澳洲：申请走州招生中心或直接向院校递交，录取是分轮次放榜的，所以成绩出来的时间点和分数本身一样重要。",
        },
        "United Kingdom": {
            "en": "United Kingdom: one application through UCAS covers five choices, the "
                  "personal statement is written months ahead, and there is a firm "
                  "deadline rather than rolling offers.",
            "zh": "英国：通过 UCAS 一份申请填五个志愿，个人陈述要提前几个月写，而且是有硬性截止日期的，不像滚动录取。",
        },
        "United States": {
            "en": "United States: each institution has its own application, early rounds "
                  "close in November, and testing and essays are prepared the year before.",
            "zh": "美国：每所院校各自一套申请，早申轮次在 11 月截止，考试和文书要提前一年准备。",
        },
        "Malaysia": {
            "en": "Malaysia: intakes are usually January and September, and institutions "
                  "assess directly, so the timeline is driven by the intake you target.",
            "zh": "马来西亚：入学通常是 1 月和 9 月，由院校直接审核，所以时间线取决于你瞄准哪一季入学。",
        },
        "Canada": {
            "en": "Canada: provincial systems differ, most deadlines fall between January "
                  "and March, and some programmes require supplementary applications.",
            "zh": "加拿大：各省体系不同，多数截止日期在 1 月到 3 月之间，部分专业还要额外面试或补充申请。",
        },
    },
}
