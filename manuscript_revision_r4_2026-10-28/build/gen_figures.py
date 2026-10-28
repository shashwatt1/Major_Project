"""Generate column-width (3.3 in) versions of Figs. 1 and 3 on a 3-column grid so that labels print at >= 6 pt.
Content is unchanged from the corrected figures (labels match the implementation). Writes figures/fig1.svg and
figures/fig3.svg (previous versions are kept as *_wide_backup.svg)."""
import shutil
from pathlib import Path

FIG = Path(__file__).resolve().parent / "figures"
W, H = 156, 56          # box size (px); canvas 520 px wide -> 3.3 in => 1 px = 0.457 pt
X = [8, 182, 356]       # column x positions
F1, F2 = 15, 13.5       # font sizes (px) -> ~6.9 pt and ~6.2 pt in print


def box(x, y, t1, t2, fill="#ffffff", bold=False):
    b = ' font-weight="bold"' if bold else ""
    return (f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="4" fill="{fill}" stroke="#000" stroke-width="1.4"/>'
            f'<text x="{x + W / 2}" y="{y + 24}" text-anchor="middle" font-size="{F1}"{b}>{t1}</text>'
            f'<text x="{x + W / 2}" y="{y + 43}" text-anchor="middle" font-size="{F2}" font-style="italic">{t2}</text>')


def arrow(x1, y1, x2, y2, dashed=False):
    d = ' stroke-dasharray="5,3"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-width="1.4"{d} marker-end="url(#a)"/>'


def label(x, y, t, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{F2}" font-style="italic" fill="#333">{t}</text>'


def svg(width, height, parts):
    return "\n".join([f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" font-family="Times New Roman, serif">',
                      '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
                      '<path d="M0,0 L0,6 L8,3 z" fill="#000"/></marker></defs>',
                      f'<rect width="{width}" height="{height}" fill="#ffffff"/>'] + parts + ["</svg>"])


def cx(i):
    return X[i] + W / 2


# ---------------- Fig. 1: implemented processing pipeline
r = [8, 96, 184, 272, 360]
p = []
p += [box(X[0], r[0], "User", "(speaks a request)", bold=True),
      box(X[1], r[0], "Web Interface", "(browser recording)", "#f0f0f0"),
      box(X[2], r[0], "FastAPI Upload", "(/assistant/run)")]
p += [arrow(X[0] + W, r[0] + H / 2, X[1] - 2, r[0] + H / 2), arrow(X[1] + W, r[0] + H / 2, X[2] - 2, r[0] + H / 2)]
p += [box(X[2], r[1], "Encrypted Copy", "(Fernet, stored)", "#f0f0f0"),
      box(X[1], r[1], "Temporary File", "(deleted after use)"),
      box(X[0], r[1], "Speech-to-Text", "(Whisper base)")]
p += [arrow(cx(2), r[0] + H, cx(2), r[1] - 2), arrow(X[2], r[1] + H / 2, X[1] + W + 2, r[1] + H / 2),
      arrow(X[1], r[1] + H / 2, X[0] + W + 2, r[1] + H / 2)]
p += [box(X[0], r[2], "Intent Classifier", "(keyword substring rule)", "#d8e8f8", True),
      box(X[1], r[2], "RAG Retrieval", "(MiniLM + FAISS, top-3)"),
      box(X[2], r[2], "LLM Generation", "(llama3.2 via Ollama)")]
p += [arrow(cx(0), r[1] + H, cx(0), r[2] - 2), arrow(X[0] + W, r[2] + H / 2, X[1] - 2, r[2] + H / 2),
      arrow(X[1] + W, r[2] + H / 2, X[2] - 2, r[2] + H / 2)]
p += [label(X[0] + W + 9, r[2] - 6, "query", "middle")]
p += [box(X[0], r[3], "Automation", "(macOS app / URL)", "#eaf5ea"),
      box(X[2], r[3], "Text-to-Speech", "(macOS say + ffmpeg)")]
p += [arrow(cx(0), r[2] + H, cx(0), r[3] - 2), label(cx(0) + 6, r[2] + H + 21, "command"),
      arrow(cx(2), r[2] + H, cx(2), r[3] - 2), arrow(X[0] + W, r[3] + H / 2, X[2] - 2, r[3] + H / 2),
      label(X[1] + W / 2, r[3] + H / 2 - 6, "status message", "middle")]
p += [box(X[2], r[4], "Reply to Interface", "(audio, transcript, sources)", "#d8e8f8", True),
      arrow(cx(2), r[3] + H, cx(2), r[4] - 2)]
fig1 = svg(520, r[4] + H + 8, p)

# ---------------- Fig. 3: RAG pipeline as implemented
r = [26, 110, 222, 306, 390]
q = [f'<rect x="2" y="2" width="516" height="{r[1] + H + 10}" rx="6" fill="#fafafa" stroke="#999" stroke-dasharray="6,3"/>',
     label(10, 18, "Offline indexing (once per process)"),
     f'<rect x="2" y="{r[2] - 26}" width="516" height="{r[4] + H + 10 - (r[2] - 26)}" rx="6" fill="#fafafa" stroke="#999" stroke-dasharray="6,3"/>',
     label(10, r[2] - 10, "Online retrieval (per query)")]
q += [box(X[0], r[0], "Local Documents", "(.txt files only)"),
      box(X[1], r[0], "Chunking", "(500 chars, 100 overlap)"),
      box(X[2], r[0], "Embedding", "(all-MiniLM-L6-v2)", "#f0f0f0")]
q += [arrow(X[0] + W, r[0] + H / 2, X[1] - 2, r[0] + H / 2), arrow(X[1] + W, r[0] + H / 2, X[2] - 2, r[0] + H / 2)]
q += [box(X[2], r[1], "FAISS Index", "(IndexFlatL2, in memory)", "#d8e8f8", True), arrow(cx(2), r[0] + H, cx(2), r[1] - 2)]
q += [box(X[0], r[2], "User Query", "(transcript)"),
      box(X[1], r[2], "Query Embedding", "(same model)", "#f0f0f0"),
      box(X[2], r[2], "Similarity Search", "(top-3, cosine &gt; 0.5)", "#d8e8f8", True)]
q += [arrow(X[0] + W, r[2] + H / 2, X[1] - 2, r[2] + H / 2), arrow(X[1] + W, r[2] + H / 2, X[2] - 2, r[2] + H / 2),
      arrow(cx(2), r[1] + H, cx(2), r[2] - 2, dashed=True)]
q += [box(X[2], r[3], "Retrieved Chunks", "(0 to 3 passages)"),
      box(X[1], r[3], "Prompt Assembly", "(context if any)", "#f0f0f0"),
      box(X[0], r[3], "LLM Generation", "(llama3.2 via Ollama)", "#eaf5ea")]
q += [arrow(cx(2), r[2] + H, cx(2), r[3] - 2), arrow(X[2], r[3] + H / 2, X[1] + W + 2, r[3] + H / 2),
      arrow(X[1], r[3] + H / 2, X[0] + W + 2, r[3] + H / 2)]
q += [box(X[0], r[4], "Generated Answer", "(spoken reply)", "#d8e8f8", True), arrow(cx(0), r[3] + H, cx(0), r[4] - 2)]
fig3 = svg(520, r[4] + H + 14, q)

for name, s in (("fig1", fig1), ("fig3", fig3)):
    src = FIG / f"{name}.svg"
    bak = FIG / f"{name}_wide_backup.svg"
    if not bak.exists():
        shutil.copy(src, bak)
    src.write_text(s)
    print(name, "written")
