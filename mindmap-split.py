"""把待翻译条目切成若干批，便于并行处理。

每批带上下文说明，确保术语一致（ATAR 课程术语、公式保持原样）。
"""

import os
import json
from pathlib import Path

SITE = Path(os.environ.get("AUSMAT_SITE")
             or (Path(__file__).resolve().parent / "my-site"))
D = SITE / "_i18n"
rows = json.loads((D / "mindmap-zh.json").read_text(encoding="utf-8"))

BATCH = 90
batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]

for n, b in enumerate(batches, 1):
    (D / f"batch-{n:02d}.json").write_text(
        json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"共 {len(rows)} 条，切成 {len(batches)} 批（每批 ≤{BATCH}）：")
for n, b in enumerate(batches, 1):
    chars = sum(len(r["name"]) + len(r["note"]) for r in b)
    print(f"  batch-{n:02d}.json  {len(b):>3} 条  {chars:>6} 字符")
