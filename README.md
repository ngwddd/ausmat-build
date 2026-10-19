# ausmat-build

**asumat-guide 站点（https://ngwddd.github.io/ausmat-guide/）的生成器。**

站点仓库里只有生成出来的 HTML；这个仓库是**造它们的程序**。
两边的对应关系：

```
ausmat-build  ──运行──>  ausmat-guide/my-site  ──推送──>  GitHub Pages
 （本仓库）                （产物仓库）
```

## 它做什么

一条命令，从数据文件生成整套静态站：

```bash
python build-site.py
```

执行顺序：

| 步骤 | 脚本 | 产出 |
|---|---|---|
| 1 | `site-build.py` | 23 个页面（中英双语） |
| 2 | `clean-mindmap.py` | 知识导图页（清洗 + 内联标点 + 外置 i18n） |
| 3 | `advising-build/build.py` | 升学自检工具（规则引擎，30 条规则） |
| 4 | 收尾 | 表格滚动容器、sitemap.xml、robots.txt |
| 5 | 自检 | 页面齐全、导图节点数、导航顺序、KaTeX 残留、sitemap 条数 |

自检不过会以非 0 退出，并打印是哪一项。

## 依赖

- Python **3.11+**（用了 `tomllib`、`str.removeprefix` 等）
- **无第三方库**

## 怎么跑

### 1. 拿到产物仓库

```bash
git clone https://github.com/ngwddd/ausmat-guide.git my-site
```

### 2. 指路径（二选一）

**方式 A**：产物就在 `./my-site`（上面那样 clone 到本仓库目录下）—— 什么都不用设。

**方式 B**：产物在别处 —— 设环境变量：

```powershell
$env:AUSMAT_SITE = "D:\somewhere\ausmat-guide"
```

### 3. 导图源文件（只在重建导图页时需要）

导图页来自一份导出 HTML。放 `./corpus/mindmap.html`，或者：

```powershell
$env:AUSMAT_MINDMAP = "D:\path\to\思维导图.html"
```

没有这个文件时，`clean-mindmap.py` 那一步会失败，其余步骤不受影响。

### 4. 跑

```bash
python build-site.py
```

## 目录

```
build-site.py            总调度 + 收尾 + 自检
site-build.py            页面骨架与所有页面的渲染
site-data.py             全部内容数据（37 个考核项、权重、术语、真题信息）
clean-mindmap.py         导图页：清洗原始 HTML、外置 i18n
mindmap-*.py             导图 i18n 的提取 / 合并 / 拆分 / 注入
advising-build/          升学自检工具（独立子项目，有自己的 README）
_sp/                     构建数据（JSON）—— 不是草稿，删了页面内容会缺
.sitemap-state.json      上次生成的页面哈希，用来算 sitemap 的 lastmod
```

`_sp/` 里的 JSON 是**页面背后的内容**，例如：

| 文件 | 作用 |
|---|---|
| `findings-fixes.json` | 考官报告里「普遍失分点 + 怎么办」的结构化数据 |
| `notes-{SUBJ}.json` / `notes-en-{SUBJ}.json` | 五科要点（中 / 英） |
| `timeline-en.json` | 学期时间线的英文条目 |

## 内容边界

这个仓库只包含**自己整理的摘要与结构**，不含：

- 学校讲义、试卷原文
- 任何学生或教师的姓名
- 具体考试地点（每年会变）

页面上凡是引用官方文件的地方，都是转述 + 注明来源，不复制原文。

## 已知限制

- **不是通用建站框架**：数据结构、页面布局、文案都是为这一个站点写死的。
- **导图页依赖外部 HTML**：没有源文件就重建不了那一页。
- **`.sitemap-state.json` 是构建状态**：删掉它会让所有页面的 `lastmod` 变成当天。
- macOS 未验证（只在 Windows 与 Linux 上跑过）。
