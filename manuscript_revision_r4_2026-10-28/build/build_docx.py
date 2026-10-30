"""Build revised_manuscript.docx from the accepted manuscript (Strict OOXML) without converting formats.

Keeps body elements 0-20 (title, author block, section breaks) byte-identical, rewrites the abstract,
keywords and body from content.py using the template's own styles, converts the three floating figures
to inline figures with corrected images, builds tables, renumbers citations by first appearance, and
reuses the original reference entries (merging entries that were split over two paragraphs).
"""
from __future__ import annotations

import copy
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "original_accepted" / "conference-template-a4 (7).docx"
OUT = ROOT / "revised_manuscript.docx"
FIG = HERE / "figures"
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402

W = "http://purl.oclc.org/ooxml/wordprocessingml/main"
WP = "http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing"
A = "http://purl.oclc.org/ooxml/drawingml/main"
R = "http://purl.oclc.org/ooxml/officeDocument/relationships"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W, "wp": WP, "a": A, "r": R}


def q(tag):
    p, t = tag.split(":")
    return f"{{{NS[p]}}}{t}"


def el(tag, attrs=None, children=()):
    e = etree.Element(q(tag))
    for k, v in (attrs or {}).items():
        e.set(q(k) if ":" in k else k, str(v))
    for c in children:
        e.append(c)
    return e


# ------------------------------------------------------------------ runs and paragraphs
def run(text, italic=False, bold=False, sz=None, base_rpr=None):
    r = el("w:r")
    rpr = copy.deepcopy(base_rpr) if base_rpr is not None else el("w:rPr")
    if italic and rpr.find(q("w:i")) is None:
        rpr.insert(0, el("w:i"))
    if bold and rpr.find(q("w:b")) is None:
        rpr.insert(0, el("w:b"))
    if sz is not None:
        for old in rpr.findall(q("w:sz")):
            rpr.remove(old)
        rpr.append(el("w:sz", {"w:val": sz}))
    if len(rpr):
        r.append(rpr)
    parts = text.split("\t")
    for i, part in enumerate(parts):
        if i:
            r.append(el("w:tab"))
        if part:
            t = el("w:t")
            t.text = part
            t.set(f"{{{XML}}}space", "preserve")
            r.append(t)
    return r


def segments(text):
    """'*italic*' markup -> [(text, italic)]"""
    out, ital = [], False
    for piece in re.split(r"(\*)", text):
        if piece == "*":
            ital = not ital
        elif piece:
            out.append((piece, ital))
    assert not ital, f"unbalanced italics: {text[:80]}"
    return out


def para(ppr, text, sz=None, base_rpr=None, all_italic=False):
    p = el("w:p")
    p.append(copy.deepcopy(ppr))
    for s, it in segments(text):
        p.append(run(s, italic=it or all_italic, sz=sz, base_rpr=base_rpr))
    return p


def ppr(style=None, extra=()):
    pp = el("w:pPr")
    if style:
        pp.append(el("w:pStyle", {"w:val": style}))
    for e in extra:
        pp.append(e)
    return pp


def text_of(p):
    return "".join(p.xpath(".//w:t/text()", namespaces=NS))



def merge_adjacent_runs(p):
    """Merge neighbouring runs with identical formatting (text only) so phrase fixes can match."""
    def key(r_):
        rpr = r_.find(q("w:rPr"))
        return etree.tostring(rpr) if rpr is not None else b""
    prev = None
    for r_ in list(p.findall(q("w:r"))):
        kids = [etree.QName(c).localname for c in r_ if etree.QName(c).localname != "rPr"]
        if kids != ["t"]:
            prev = None
            continue
        if prev is not None and key(prev) == key(r_) and prev.getnext() is r_:
            pt = prev.find(q("w:t")); ct = r_.find(q("w:t"))
            pt.text = (pt.text or "") + (ct.text or "")
            pt.set(f"{{{XML}}}space", "preserve")
            p.remove(r_)
        else:
            prev = r_

# ------------------------------------------------------------------ citations
REF_SOURCE = {  # key -> original body index (or tuple for split entries)
    "vaswani": 104, "lewis": 105, "amazon": 107, "apple": 108, "kepuska": 109, "metz": 110, "maynez": 111,
    "ji": 112, "radford": 113, "gao2023": (114, 115), "dettmers8bit": 116, "qlora": 117, "rabiner": (118, 119),
    "pocketsphinx": 120, "devlin": 121, "brown": 122, "kaplan": (123, 124), "gptq": 125, "gaomodular": 127,
    "reimers": (128, 129), "johnson": 130, "snyder": 131, "nist": 133, "shokri": 134, "fastapi": 135,
}
DROPPED_REFS = {106: "LangChain (framework not used by the implementation)", 126: "Saini et al. (cited for an unrelated claim)",
                132: "Gupta et al. (cited for an unrelated claim)", 136: "OpenCV (not cited; not used)",
                137: "Montreal Forced Aligner (not cited; not used)"}
NEW_REFS = {  # verified via Crossref (see final_submission_checklist.md)
    "sudarsan": "S. Sudarsan and N. Karra, “The future of trustworthy AI: Trends and predictions,” in *Trustworthy AI Systems*, "
                "V. Gudur, B. Pandey, and A. Patel, Eds. Cham, Switzerland: Springer Nature, 2026, pp. 247–261, "
                "doi: 10.1007/978-3-032-15606-8_15.",
    "papineni": "K. Papineni, S. Roukos, T. Ward, and W.-J. Zhu, “BLEU: A method for automatic evaluation of machine translation,” "
                "in *Proc. 40th Annu. Meeting Assoc. Comput. Linguistics (ACL)*, 2002, pp. 311–318, doi: 10.3115/1073083.1073135.",
    "rajpurkar": "P. Rajpurkar, J. Zhang, K. Lopyrev, and P. Liang, “SQuAD: 100,000+ questions for machine comprehension of text,” "
                 "in *Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP)*, 2016, pp. 2383–2392, doi: 10.18653/v1/D16-1264.",
    "post": "M. Post, “A call for clarity in reporting BLEU scores,” in *Proc. 3rd Conf. Machine Translation: Research Papers*, "
            "2018, pp. 186–191, doi: 10.18653/v1/W18-6319.",
}
REF_TEXT_FIXES = [("Documenta- tion", "Documentation"), ("[On- line]", "[Online]"), ("Faith- fulness", "Faithfulness"),
                  ("Infor- mation", "Information"), ("Ad- vanced", "Advanced"), ("Pre- training", "Pre-training"),
                  ("Super- vision", "Supervision"), ("535– 547", "535–547"), ("2023,pp.", "2023, pp."),
                  ("Y. J.      Bang", "Y. J. Bang")]


def resolve_citations(texts):
    order = []
    for t in texts:
        for k in re.findall(r"\{(\w+)\}", t):
            if k not in order:
                order.append(k)
    num = {k: i + 1 for i, k in enumerate(order)}
    return order, (lambda t: re.sub(r"\{(\w+)\}", lambda m: f"[{num[m.group(1)]}]", t))


def keep_next(p):
    pp = p.find(q("w:pPr"))
    if pp.find(q("w:keepNext")) is None:
        st = pp.find(q("w:pStyle"))
        kn = el("w:keepNext")
        if st is not None:
            st.addnext(kn)
        else:
            pp.insert(0, kn)
    return p


# ------------------------------------------------------------------ main build
def main():
    work = HERE / "unz"
    if work.exists():
        shutil.rmtree(work)
    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        z.extractall(work)
    for p in work.rglob("*"):
        if p.is_symlink():
            p.unlink()

    doc = etree.parse(str(work / "word/document.xml"))
    body = doc.getroot().find(q("w:body"))
    old = list(body)
    head_keep = old[:21]                 # title, authors, section breaks (unchanged)
    abstract_p, keywords_p = old[21], old[22]
    sect_final = old[-1]
    assert etree.QName(sect_final).localname == "sectPr"
    h1_ppr = old[23].find(q("w:pPr"))
    h3_ppr_by_section = {"Literature Review": old[28].find(q("w:pPr")),
                         "System Design and Implementation": old[53].find(q("w:pPr")),
                         "Results and Discussion": old[87].find(q("w:pPr"))}
    ref_head = old[103]
    assert text_of(ref_head).strip() == "References"

    # numbering instance for Section IV subsections (restart at A.)
    numbering = etree.parse(str(work / "word/numbering.xml"))
    nroot = numbering.getroot()
    max_id = max(int(n.get(q("w:numId"))) for n in nroot.findall(q("w:num")))
    eval_num = str(max_id + 1)
    new_num = el("w:num", {"w:numId": eval_num}, [el("w:abstractNumId", {"w:val": "26"}),
                                                   el("w:lvlOverride", {"w:ilvl": "0"}, [el("w:startOverride", {"w:val": "1"})])])
    cleanup = nroot.find(q("w:numIdMacAtCleanup"))
    if cleanup is not None:
        cleanup.addprevious(new_num)
    else:
        nroot.append(new_num)
    h3_ppr_by_section["Evaluation Methodology"] = copy.deepcopy(old[28].find(q("w:pPr")))
    h3_ppr_by_section["Evaluation Methodology"].find("w:numPr/w:numId", NS).set(q("w:val"), eval_num)

    # figures: take graphics from the three anchors
    anchors = {}
    for idx, fig in ((50, 1), (62, 2), (76, 3)):
        a = old[idx].find(".//wp:anchor", NS)
        blip = a.find(".//a:blip", NS)
        svg = [e for e in a.iter() if etree.QName(e).localname == "svgBlip"]
        anchors[fig] = {"anchor": a, "png_rid": blip.get(q("r:embed")),
                        "svg_rid": svg[0].get(q("r:embed")) if svg else None}
    rels = etree.parse(str(work / "word/_rels/document.xml.rels")).getroot()
    rid_target = {r.get("Id"): r.get("Target") for r in rels}
    for fig, info in anchors.items():
        png_t, svg_t = rid_target[info["png_rid"]], rid_target[info["svg_rid"]]
        shutil.copy(FIG / "final" / f"fig{fig}_2x.png", work / "word" / png_t)
        shutil.copy(FIG / "final" / f"fig{fig}.svg", work / "word" / svg_t)
        info["targets"] = (png_t, svg_t)

    def figure_paragraph(fig):
        a = anchors[fig]["anchor"]
        ext = a.find("wp:extent", NS)
        cx, cy = int(ext.get("cx")), int(ext.get("cy"))
        import struct
        pw, ph = struct.unpack(">II", (FIG / "final" / f"fig{fig}_2x.png").read_bytes()[16:24])
        new_cx = int(3.30 * 914400)
        new_cy = round(new_cx * ph / pw)
        graphic = copy.deepcopy(a.find("a:graphic", NS))
        for e in graphic.iter():
            if etree.QName(e).localname == "ext" and e.get("cx") is not None:
                e.set("cx", str(new_cx)); e.set("cy", str(new_cy))
        docpr = copy.deepcopy(a.find("wp:docPr", NS))
        docpr.set("descr", f"Figure {fig}")
        inline = el("wp:inline", {"distT": 0, "distB": 0, "distL": 0, "distR": 0},
                    [el("wp:extent", {"cx": new_cx, "cy": new_cy}),
                     el("wp:effectExtent", {"l": 0, "t": 0, "r": 0, "b": 0}), docpr,
                     el("wp:cNvGraphicFramePr", {}, [el("a:graphicFrameLocks", {"noChangeAspect": 1})]), graphic])
        p = el("w:p", {}, [ppr(None, [el("w:keepNext"), el("w:spacing", {"w:before": "6pt", "w:after": "2pt"}),
                                       el("w:jc", {"w:val": "center"})]),
                           el("w:r", {}, [el("w:drawing", {}, [inline])])])
        return p

    def table_elements(key, roman_text_check=None):
        spec = C.TABLES[key]
        total = sum(spec["widths"])
        assert abs(total - 240.5) < 0.01, (key, total)
        head = para(ppr("tablehead", [el("w:keepNext")]), spec["title"])
        b = lambda: el("w:single", {})  # noqa: E731 (unused helper guard)
        borders = el("w:tblBorders", {}, [el(f"w:{s}", {"w:val": "single", "w:sz": 4, "w:space": 0, "w:color": "000000"})
                                         for s in ("top", "start", "bottom", "end", "insideH", "insideV")])
        tbl = el("w:tbl", {}, [el("w:tblPr", {}, [el("w:tblW", {"w:w": "240.5pt", "w:type": "dxa"}),
                                                  el("w:jc", {"w:val": "center"}), borders,
                                                  el("w:tblLayout", {"w:type": "fixed"}),
                                                  el("w:tblCellMar", {}, [el("w:start", {"w:w": "2.5pt", "w:type": "dxa"}),
                                                                         el("w:end", {"w:w": "2.5pt", "w:type": "dxa"})]),
                                                  el("w:tblLook", {"w:firstRow": 1, "w:lastRow": 0, "w:firstColumn": 1,
                                                                   "w:lastColumn": 0, "w:noHBand": 0, "w:noVBand": 1})]),
                               el("w:tblGrid", {}, [el("w:gridCol", {"w:w": f"{wd}pt"}) for wd in spec["widths"]])])
        for ri, row in enumerate([spec["header"]] + spec["rows"]):
            tr = el("w:tr", {}, [el("w:trPr", {}, [el("w:cantSplit")] + ([el("w:tblHeader")] if ri == 0 else []))])
            for ci, (cell, wd) in enumerate(zip(row, spec["widths"])):
                style = "tablecolhead" if ri == 0 else "tablecopy"
                jc = "start" if (ci == 0 and ri > 0) else "center"
                last_row = ri == len(spec["rows"])
                pp = ppr(style, ([] if last_row else [el("w:keepNext")]) + [el("w:spacing", {"w:before": "1pt", "w:after": "1pt"}), el("w:jc", {"w:val": jc})])
                cp = para(pp, cell, sz=16, base_rpr=el("w:rPr", {}, [el("w:b")]) if ri == 0 else None)
                tr.append(el("w:tc", {}, [el("w:tcPr", {}, [el("w:tcW", {"w:w": f"{wd}pt", "w:type": "dxa"}),
                                                            el("w:vAlign", {"w:val": "center"})]), cp]))
            tbl.append(tr)
        note = para(ppr(None, [el("w:spacing", {"w:before": "2pt", "w:after": "8pt"}),
                               el("w:ind", {"w:start": "8pt", "w:end": "8pt"}), el("w:jc", {"w:val": "both"})]), spec["note"], sz=14)
        return [head, tbl, note]

    # ---- citations
    all_texts = [x[1] for x in C.BODY if x[0] == "P"]
    order, cite = resolve_citations(all_texts)
    known = set(REF_SOURCE) | set(NEW_REFS)
    missing = [k for k in order if k not in known]
    unused = [k for k in known if k not in order]
    assert not missing and not unused, (missing, unused)

    # ---- abstract and keywords: keep lead-in runs ("Abstract—", "Keywords—")
    def rewrite_leadin(p, new_text):
        runs = p.findall(q("w:r"))
        acc, keep = "", []
        for r_ in runs:
            acc += "".join(r_.xpath(".//w:t/text()", namespaces=NS))
            keep.append(r_)
            if "—" in acc:
                break
        last_t = keep[-1].findall(q("w:t"))[-1]
        last_t.text = last_t.text.split("—")[0] + "—"
        body_rpr = None
        nxt = runs[len(keep)] if len(runs) > len(keep) else None
        if nxt is not None and nxt.find(q("w:rPr")) is not None:
            body_rpr = nxt.find(q("w:rPr"))
        for r_ in runs[len(keep):]:
            p.remove(r_)
        for e in list(p):
            if etree.QName(e).localname in ("hyperlink", "proofErr", "bookmarkStart", "bookmarkEnd") :
                p.remove(e)
        for s, it in segments(new_text):
            p.append(run(s, italic=it, base_rpr=body_rpr))
        assert text_of(p).startswith(("Abstract—", "Keywords—")), text_of(p)[:30]

    rewrite_leadin(abstract_p, C.ABSTRACT)
    rewrite_leadin(keywords_p, C.KEYWORDS)

    # ---- new body
    new = []
    section = None
    tab_seen = []
    for item in C.BODY:
        kind = item[0]
        if kind == "H1":
            section = item[1]
            new.append(keep_next(para(h1_ppr, item[1])))
        elif kind == "H3":
            new.append(keep_next(para(h3_ppr_by_section[section], item[1])))
        elif kind == "P":
            new.append(para(ppr("BodyText"), cite(item[1])))
        elif kind == "FIG":
            new.append(figure_paragraph(item[1]))
            new.append(para(ppr("figurecaption"), item[2]))
        elif kind == "TAB":
            tab_seen.append(item[1])
            new.extend(table_elements(item[1]))
        elif kind == "EQ":
            eq_ppr = ppr("equation", [el("w:tabs", {}, [el("w:tab", {"w:val": "center", "w:pos": "121pt"}),
                                                         el("w:tab", {"w:val": "end", "w:pos": "243pt"})]),
                                      el("w:spacing", {"w:before": "4pt", "w:after": "4pt"}),
                                      el("w:ind", {"w:start": "0pt", "w:firstLine": "0pt"})])
            tnr = lambda ital: el("w:rPr", {}, [el("w:rFonts", {"w:ascii": "Times New Roman", "w:hAnsi": "Times New Roman", "w:cs": "Times New Roman"})] + ([el("w:i")] if ital else []))  # noqa: E731
            p = el("w:p", {}, [eq_ppr, run("\t", base_rpr=tnr(False)), run(item[1], base_rpr=tnr(True)), run("\t" + item[2], base_rpr=tnr(False))])
            new.append(p)
    assert tab_seen == C.TABLE_ORDER, tab_seen

    # ---- references in citation order
    model_ref = old[104]
    ref_ppr = old[109].find(q("w:pPr"))
    refs = []
    for key in order:
        if key in NEW_REFS:
            p = el("w:p", {}, [copy.deepcopy(ref_ppr)])
            for s, it in segments(NEW_REFS[key]):
                p.append(run(s, italic=it, sz=16))
        else:
            src = REF_SOURCE[key]
            idxs = src if isinstance(src, tuple) else (src,)
            markup = []
            for i_, ix in enumerate(idxs):
                if i_:
                    markup.append(" ")
                for r_ in old[ix].iter(q("w:r")):
                    if r_.find(".//w:drawing", NS) is not None:
                        continue  # stray decorative graphic
                    t_ = "".join(r_.xpath("./w:t/text()", namespaces=NS))
                    if not t_:
                        continue
                    it = r_.find("w:rPr/w:i", NS) is not None
                    markup.append(f"*{t_}*" if it else t_)
            mtext = re.sub(r"\*\*", "", "".join(markup))       # join adjacent italic runs
            mtext = re.sub(r"\s+", " ", mtext).strip()
            for a_, b_ in REF_TEXT_FIXES:
                mtext = mtext.replace(a_, re.sub(r"\s+", " ", b_))
            if key == "fastapi":
                mtext += " https://fastapi.tiangolo.com"
            p = el("w:p", {}, [copy.deepcopy(ref_ppr)])
            for s_, it in segments(mtext):
                p.append(run(s_, italic=it, sz=16))
        refs.append(p)

    # remove any leftover drawing runs inside references (decorative anchors)
    for p in refs:
        for d in p.findall(".//w:drawing", NS):
            r_ = d.getparent()
            r_.getparent().remove(r_)

    for e in list(body):
        body.remove(e)
    for e in head_keep:
        body.append(e)
    body.append(abstract_p)
    body.append(keywords_p)
    for e in new:
        body.append(e)
    ack_head = copy.deepcopy(ref_head)
    ref_rpr = ref_head.find(".//w:r/w:rPr", NS)
    for r_ in ack_head.findall(q("w:r")):
        ack_head.remove(r_)
    for e in list(ack_head):
        if etree.QName(e).localname in ("hyperlink", "proofErr", "bookmarkStart", "bookmarkEnd"):
            ack_head.remove(e)
    ack_head.append(run("Acknowledgment", base_rpr=ref_rpr))
    body.append(keep_next(ack_head))
    body.append(para(ppr("BodyText"), C.ACKNOWLEDGMENT))
    body.append(copy.deepcopy(ref_head))
    for e in refs:
        body.append(e)
    body.append(sect_final)

    # fix wrong mailto target on Yash Rawat's displayed address (visible text unchanged)
    relp = work / "word/_rels/document.xml.rels"
    rt = relp.read_text(encoding="utf-8")
    assert rt.count("mailto:rahulkumar.phdmb@gmail.com") == 1
    relp.write_text(rt.replace("mailto:rahulkumar.phdmb@gmail.com", "mailto:yashrawats005@gmail.com"), encoding="utf-8")
    doc.write(str(work / "word/document.xml"), xml_declaration=True, encoding="UTF-8", standalone=True)
    numbering.write(str(work / "word/numbering.xml"), xml_declaration=True, encoding="UTF-8", standalone=True)

    # ---- integrity checks
    full = text_of(doc.getroot())
    for bad in ("Duplicate the template", "Using the Template", "ready for the template", "Mistral", "LLaMA 2",
                "AES-256", "GCM", "PBKDF2", "i7-12700", "RTX 3060", "Windows 11", "Ubuntu", "LangChain", "ChromaDB",
                "PyAudio", "WebRTC", "92 to 95", "98%", "85%", "90%", "llama-cpp", "{",
                "We wrote", "Manual review", "manually verified", "written in our own words", "review current trends"):
        assert bad not in full, f"forbidden text remains: {bad}"
    for a_, _ in REF_TEXT_FIXES:
        assert a_ not in full, a_
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", "".join(text_of(p) for p in new))})
    assert cited == list(range(1, len(refs) + 1)), (cited, len(refs))

    # author block unchanged
    orig_doc = etree.fromstring(zipfile.ZipFile(SRC).read("word/document.xml"))
    ob = list(orig_doc.find(q("w:body")))[:21]
    assert all(etree.tostring(a_) == etree.tostring(b_) for a_, b_ in zip(ob, list(body)[:21])), "author block changed"

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(work / n, n)
    print("written", OUT, "| refs:", len(refs), "| citation order:", order)
    print("sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
