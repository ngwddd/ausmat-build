"""从导图 DATA 中抽出全部可翻译文本（先前的正则法只抓到带 note 的 29 条，漏了 500 个叶子节点）。

用递归下降解析 DATA 这个 JS 对象字面量，输出：
  skill  →  mindmap-zh.json   每条 {path, name, note}
  i18n   →  mindmap-i18n.json {"<path>": {"name":"", "note":""}}  待填英文
"""

import os
import json
import re
from pathlib import Path

SITE = Path(os.environ.get("AUSMAT_SITE")
             or (Path(__file__).resolve().parent / "my-site"))
MM = SITE / "notes" / "mindmap.html"
OUT = SITE / "_i18n"
OUT.mkdir(exist_ok=True)


class P:
    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def ws(self):
        """跳过空白与注释 —— DATA 里散布着 /* ===== 1. MAM12 ===== */ 这类分节注释，
        不处理的话解析器会直接炸在注释上。"""
        while self.i < len(self.s):
            c = self.s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif self.s.startswith("//", self.i):
                nl = self.s.find("\n", self.i)
                self.i = len(self.s) if nl < 0 else nl + 1
            elif self.s.startswith("/*", self.i):
                end = self.s.find("*/", self.i)
                self.i = len(self.s) if end < 0 else end + 2
            else:
                return

    def expect(self, ch: str):
        self.ws()
        if self.i >= len(self.s) or self.s[self.i] != ch:
            raise ValueError(f"位置 {self.i}: 期望 {ch!r}，实际 {self.s[self.i:self.i+20]!r}")
        self.i += 1

    def string(self) -> str:
        self.ws()
        if self.s[self.i] != '"':
            raise ValueError(f"位置 {self.i}: 期望字符串，实际 {self.s[self.i:self.i+20]!r}")
        self.i += 1
        buf = []
        while self.s[self.i] != '"':
            if self.s[self.i] == "\\":
                nxt = self.s[self.i + 1]
                buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                self.i += 2
            else:
                buf.append(self.s[self.i])
                self.i += 1
        self.i += 1
        return "".join(buf)

    def ident(self) -> str:
        self.ws()
        m = re.match(r"[A-Za-z_$][\w$]*", self.s[self.i:])
        if not m:
            raise ValueError(f"位置 {self.i}: 期望标识符")
        self.i += len(m.group(0))
        return m.group(0)

    def value(self):
        self.ws()
        c = self.s[self.i]
        if c == '"':
            return self.string()
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c.isdigit() or c == "-":
            m = re.match(r"-?\d+(\.\d+)?", self.s[self.i:])
            self.i += len(m.group(0))
            return float(m.group(0)) if "." in m.group(0) else int(m.group(0))
        # true / false / null
        for kw, v in (("true", True), ("false", False), ("null", None)):
            if self.s.startswith(kw, self.i):
                self.i += len(kw)
                return v
        raise ValueError(f"位置 {self.i}: 无法解析 {self.s[self.i:self.i+30]!r}")

    def obj(self) -> dict:
        self.expect("{")
        o = {}
        self.ws()
        if self.s[self.i] == "}":
            self.i += 1
            return o
        while True:
            k = self.ident()
            self.ws()
            self.expect(":")
            o[k] = self.value()
            self.ws()
            if self.s[self.i] == ",":
                self.i += 1
                self.ws()
                if self.s[self.i] == "}":
                    self.i += 1
                    return o
                continue
            self.expect("}")
            return o

    def arr(self) -> list:
        self.expect("[")
        a = []
        self.ws()
        if self.s[self.i] == "]":
            self.i += 1
            return a
        while True:
            a.append(self.value())
            self.ws()
            if self.s[self.i] == ",":
                self.i += 1
                self.ws()
                if self.s[self.i] == "]":
                    self.i += 1
                    return a
                continue
            self.expect("]")
            return a


def extract_literal(t: str, marker: str, open_ch: str, close_ch: str) -> str:
    i = t.index(marker)
    j = t.index(open_ch, i)
    depth, k = 0, j
    while k < len(t):
        c = t[k]
        if c == '"':
            k += 1
            while k < len(t) and t[k] != '"':
                if t[k] == "\\":
                    k += 1
                k += 1
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return t[j:k + 1]
        k += 1
    raise ValueError(f"{marker} 未闭合")


def flatten(node: dict, prefix: list, out: list):
    path = "/".join(prefix + [node["name"]])
    out.append({"path": path, "name": node["name"], "note": node.get("note", "")})
    for c in node.get("children", []) or []:
        flatten(c, prefix + [node["name"]], out)


def main() -> None:
    t = MM.read_text(encoding="utf-8")
    lit = extract_literal(t, "const DATA", "{", "}")
    data = P(lit).obj()
    print(f"解析成功：顶层键 {list(data.keys())}")

    rows: list = []
    flatten(data, [], rows)
    # 顶层 note 也收进来
    if data.get("note"):
        rows.insert(0, {"path": "<root>/note", "name": "", "note": data["note"]})

    n_with_name = sum(1 for r in rows if r["name"])
    n_with_note = sum(1 for r in rows if r["note"])
    chars = sum(len(r["name"]) + len(r["note"]) for r in rows)
    print(f"条目总数 : {len(rows)}")
    print(f"有 name  : {n_with_name}")
    print(f"有 note  : {n_with_note}")
    print(f"总字符数 : {chars}")

    (OUT / "mindmap-zh.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    tpl = {r["path"]: {"name": "", "note": ""} for r in rows}
    (OUT / "mindmap-i18n.json").write_text(json.dumps(tpl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已写出 {OUT/'mindmap-zh.json'} 与 mindmap-i18n.json")
    print("\n样例：")
    for r in rows[1:6]:
        print(f"  {r['path'][:80]}")


if __name__ == "__main__":
    main()
