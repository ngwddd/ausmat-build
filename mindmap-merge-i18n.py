"""合并各批翻译 → mindmap-i18n.json，并做质量检查。

检查项：
  1. 每批条数与源文件是否一致（防止漏条）
  2. name 是否还有残留中文（未翻译）
  3. 公式/数学记号是否被改动（对比源文里出现的 d/dx、∫、^ 等）
  4. 是否有多余或缺失的 key
"""

import os
import json
import re
import sys
from pathlib import Path

D = Path(os.environ.get("AUSMAT_SITE")
             or (Path(__file__).resolve().parent / "my-site")) / "_i18n"
OUT = D / "mindmap-i18n.json"
CJK = re.compile(r"[\u4e00-\u9fff]")
MATH = re.compile(r"(d/dx|∫|∑|√|π|θ|δ|Δ|\^|lim|log|ln|sin|cos|tan|P\(X|C\(n)")


def main() -> int:
    zh = {r["path"]: r for r in json.loads((D / "mindmap-zh.json").read_text(encoding="utf-8"))}
    merged: dict = {}
    problems: list[str] = []
    total_in = 0

    batches = sorted(D.glob("batch-*.json"))
    batches = [b for b in batches if not b.name.endswith(".en.json")]

    print(f"{'批次':<16}{'源':>5}{'译':>5}   状态")
    for b in batches:
        src = json.loads(b.read_text(encoding="utf-8"))
        en_f = b.with_suffix(".en.json")
        total_in += len(src)
        if not en_f.exists():
            print(f"{b.name:<16}{len(src):>5}{'—':>5}   ⏳ 未完成")
            problems.append(f"{b.name} 尚未翻译")
            continue
        en = json.loads(en_f.read_text(encoding="utf-8"))
        missing = [r["path"] for r in src if r["path"] not in en]
        extra = [k for k in en if k not in {r["path"] for r in src}]
        untrans = [k for k, v in en.items() if v.get("name") and CJK.search(v["name"])
                   and not re.search(r"[（(][^）)]*[\u4e00-\u9fff]", v["name"])]  # 允许括号内保留中文术语
        tag = "✓"
        if missing or extra or untrans:
            tag = "⚠"
            if missing: problems.append(f"{b.name}: 缺 {len(missing)} 条")
            if extra: problems.append(f"{b.name}: 多 {len(extra)} 条")
            if untrans: problems.append(f"{b.name}: {len(untrans)} 条 name 仍含中文")
        merged.update(en)
        print(f"{b.name:<16}{len(src):>5}{len(en):>5}   {tag}"
              + (f"  缺{len(missing)} 多{len(extra)} 中{len(untrans)}" if tag == "⚠" else ""))

    # 公式保持检查
    math_changed = []
    for p, v in merged.items():
        z = zh.get(p)
        if not z:
            continue
        zm, em = set(MATH.findall(z["name"])), set(MATH.findall(v.get("name", "")))
        if zm and not zm.issubset(em):
            math_changed.append((p, sorted(zm - em)[:3]))
    if math_changed:
        problems.append(f"{len(math_changed)} 条疑似丢失数学记号")

    print(f"\n源条目合计 {total_in}，合并后 {len(merged)} 条（源共 {len(zh)} 条）")
    if math_changed:
        print(f"\n⚠ 疑似丢失数学记号 {len(math_changed)} 条：")
        for p, m in math_changed[:8]:
            print(f"    {m}  ← {p.split('/')[-1][:60]}")

    if problems:
        print("\n=== 问题 ===")
        for x in problems:
            print("  • " + x)
        if any("尚未翻译" in x for x in problems):
            print("\n有批次未完成，未写出合并文件。")
            return 1

    OUT.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    filled = sum(1 for v in merged.values() if v.get("name"))
    print(f"\n✓ 已写出 {OUT.name}：{len(merged)} 条，其中已填 name {filled} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
