import pathlib, re
src = (pathlib.Path(__file__).resolve().parent / "src" / "current-index.html").read_text(encoding="utf-8")

# The engine is the last <script> block (the first is the catalog include).
blocks = re.findall(r"<script>(.*?)</script>", src, re.S)
print(f"inline script blocks: {len(blocks)}")
engine = blocks[-1]
out = pathlib.Path(__file__).resolve().parent / "src" / "engine.js"
out.write_text(engine, encoding="utf-8")
print(f"engine extracted: {len(engine)} chars -> engine.js")

# The tool-specific CSS is the single <style> block.
styles = re.findall(r"<style>(.*?)</style>", src, re.S)
print(f"style blocks: {len(styles)}  ({len(styles[0]) if styles else 0} chars)")
(pathlib.Path(__file__).resolve().parent / "src" / "tool.css").write_text(styles[0], encoding="utf-8")

# Report what engine code touches the DOM, so the new shell keeps those ids.
ids = sorted(set(re.findall(r"\$\('([a-zA-Z0-9_-]+)'\)", engine)))
print(f"\nDOM ids the engine requires ({len(ids)}):")
for i in ids: print("   ", i)
sel = sorted(set(re.findall(r"querySelectorAll\('([^']+)'\)", engine)) | set(re.findall(r"querySelector\('([^']+)'\)", engine)))
print(f"\nCSS selectors the engine queries ({len(sel)}):")
for s in sel: print("   ", s)
