"""Validate the exported submission PDF (read-only)."""
import re, sys
import pypdf
p = sys.argv[1]
r = pypdf.PdfReader(p)
out, bad = [], []
def chk(name, ok, detail=""):
    out.append(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}"); (None if ok else bad.append(name))
pages = [pg.extract_text() or "" for pg in r.pages]
full = "\n".join(pages); flat = re.sub(r"\s+", " ", full)
chk("page count <= 6", len(r.pages) <= 6, f"pages={len(r.pages)}")
sizes = {(round(float(pg.mediabox.width)), round(float(pg.mediabox.height))) for pg in r.pages}
chk("A4 page size (595x842 pt)", sizes == {(595, 842)}, str(sizes))
# fonts
fonts, unemb = set(), set()
for pg in r.pages:
    res = pg.get("/Resources") or {}
    for f in (res.get("/Font") or {}).values():
        f = f.get_object(); name = str(f.get("/BaseFont")); fonts.add(name)
        fd = f.get("/FontDescriptor")
        if f.get("/Subtype") == "/Type0":
            fd = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
        fd = fd.get_object() if fd else None
        if not fd or not any(k in fd for k in ("/FontFile", "/FontFile2", "/FontFile3")): unemb.add(name)
chk("all fonts embedded", not unemb, f"unembedded={sorted(unemb)}")
out.append("      fonts: " + ", ".join(sorted({re.sub(r'^/[A-Z]{6}\+', '', f) for f in fonts})))
p1 = re.sub(r"\s+", " ", pages[0])
chk("title (spaces ignored: title font letter-spacing splits 'V oice' in text extraction)", "voice-basedaiassistantusinglocalapiintegration" in re.sub(r"\s", "", p1.lower()), "")
authors = ["Anita Saroj", "Pramod Mehra", "Shashwat Malviya", "Ritendra Negi", "Siddhant Srivastava", "Yash Rawat"]
pos = [p1.find(a) for a in authors]
chk("all six authors on page 1", all(x >= 0 for x in pos), str(dict(zip(authors, pos))))
# IEEE 3-column author block reads row-wise; check against the original accepted PDF order separately
out.append("      author positions in page-1 text: " + str(pos))
chk("abstract present", "Abstract" in p1 and "0.250 to 0.364" in p1, "")
chk("keywords present", "Keywords" in p1, "")
for t in ("TABLE I.", "TABLE II.", "TABLE III.", "TABLE IV."):
    chk(f"{t} caption", t in full, "")
chk("no TABLE V", "TABLE V" not in full, "")
for f in ("Fig. 1.", "Fig. 2."):
    chk(f"{f} caption", f in flat, "")
chk("no Fig. 3 caption", "Fig. 3." not in flat, "")
nimg = sum(len(pg.images) for pg in r.pages)
out.append(f"      raster images: {nimg} (figures are SVG, exported by LibreOffice as vector drawings)")
for lab in ("Intent Classifier", "Encrypted Copy", "Reply to Interface", "FAISS Index", "Similarity Search", "Prompt Assembly"):
    chk(f"vector figure label drawn: '{lab}'", lab in flat, "")
refs = sorted({int(x) for x in re.findall(r"\[(\d+)\]", flat)})
chk("references [1]..[29] all present, none beyond", refs == list(range(1, 30)), f"found={refs[:3]}..{refs[-3:]} n={len(refs)}")
chk("References heading", "References" in full or "REFERENCES" in full, "")
chk("Acknowledgment present", re.search(r"ACKNOWLEDG", full, re.I) is not None, "")
for t in ("Duplicate the template", "Using the Template", "ready for the template", "Save As command", "Formatting toolbar", "Lorem", "Type title", "Abstract—This electronic", "Identify applicable funding", "Authors and Affiliations"):
    chk(f"no template text: '{t}'", t.lower() not in flat.lower(), "")
for t in ("0.364 ± 0.005", "8.14 ± 0.64", "4.48 ± 0.38", "sample SD", "not human-validated", "in a list naming it", "0.297", "0.054", "0.155", "21/120", "1/120", "11/120", "0.054 to 0.297", "p = 0.0006", "p = 0.008", "0.078 and 0.055", "21 to 33 of 120", "from 1 to 21", "53 sampled items"):
    chk(f"final value '{t}'", t in flat, "")
for t in ("0.365", "8.15", "4.48 ± 0.37", "0.318", "0/120", "against none", "0.00057", "one clause and reject"):
    chk(f"no stale value '{t}'", t not in flat, "")
print("\n".join(out)); print(f"\n{len(out)-2} lines; FAIL={len(bad)} {bad}")
sys.exit(1 if bad else 0)
