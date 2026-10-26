#!/usr/bin/env python3
"""SURFACE Qur'an UNISON scene review renderer — safe, offline HTML preview.

USAGE: python3 tools/unison_quran_preview.py \
  --scene examples/unison_quran_scene.json \
  --output build/previews/unison_quran.html

This is a standalone SOURCE REVIEW surface, not the native Surface engine.
It delegates Arabic glyph shaping to the OS/browser and does not invent phonemes.
No external resources, libraries or network requests. All source text escaped.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re

SCHEMA = "surface.unison.quran-scene/0.1"
HEX_ID = re.compile(r"^[0-9a-f]{20}$")


def admit_scene(scene: dict) -> dict:
    if not isinstance(scene, dict) or scene.get("schema") != SCHEMA:
        raise ValueError("UNISON scene schema/version mismatch")
    text = scene.get("text_layer")
    if not isinstance(text, dict) or text.get("kind") != "quran_verse_source":
        raise ValueError("Missing source-preserving Qur'an text layer")
    raw = text.get("raw")
    if not isinstance(raw, str) or len(raw) > 100_000:
        raise ValueError("Invalid text or size budget")
    raw_bytes = raw.encode("utf-8")
    if hashlib.sha256(raw_bytes).hexdigest() != text.get("source_sha256"):
        raise ValueError("Source digest mismatch; refuse the scene")
    if not isinstance(text.get("edition"), str) or not text["edition"]:
        raise ValueError("Explicit edition/reading context required")
    for k in ("surah", "ayah"):
        v = text.get(k)
        if type(v) is not int or (not 1 <= v <= 114 if k == "surah" else v < 1):
            raise ValueError(f"Invalid {k}")
    words = text.get("word_spans")
    if not isinstance(words, list) or len(words) > 20000:
        raise ValueError("Missing or oversized lexical index")
    for w in words:
        if not isinstance(w, dict) or not HEX_ID.fullmatch(str(w.get("id", ""))):
            raise ValueError("Invalid lexical node ID")
        start, end = w.get("start_byte"), w.get("end_byte")
        if type(start) is not int or type(end) is not int or not 0 <= start <= end <= len(raw_bytes):
            raise ValueError("Out-of-bounds word source span")
        if raw_bytes[start:end].decode("utf-8") != w.get("raw"):
            raise ValueError("Word position/source mismatch")
    initials = scene.get("initials_layer")
    if not isinstance(initials, dict) or initials.get("source") != raw:
        raise ValueError("Initial-letter layer must match exact source")
    if not isinstance(scene.get("astro_layer"), dict) or not isinstance(scene.get("qitt_layer"), dict):
        raise ValueError("Missing independent research layers")
    return scene


def render_review(scene: dict) -> str:
    """Build a full, standalone offline page from a validated scene dict."""
    admit_scene(scene)
    text = scene["text_layer"]
    frame = scene["initials_layer"]
    words = text["word_spans"]
    title = f'{text["surah"]}:{text["ayah"]} · {text["edition"]}'
    e = lambda value: html.escape(str(value), quote=True)

    word_rows = "".join(
        '<tr><td class="number">' + str(i+1) + '</td><td class="ar w">' + e(w["raw"]) +
        '</td><td><code>' + e(w["id"]) + '</code></td><td class="number">' +
        str(w["start_byte"]) + '–' + str(w["end_byte"]) + "</td></tr>"
        for i, w in enumerate(words)
    )
    source_layers = (
        '<span class="tag">Written source — immutable</span>'
        '<span class="tag">Rasm projection — research only</span>'
        '<span class="tag">Tajwīd phonetics — MUQRI authoritative</span>'
        '<span class="tag">QITṬ address — experimental</span>'
    )
    if frame.get("recognized_sequence"):
        cells = frame.get("letter_nodes") or []
        initials_view = (
            '<section><h2>الحروف المقطعات · Disconnected-letter frame</h2>'
            '<p class="muted">Spoken letter-name targets are delegated to MUQRI; numeric address is a separate experimental view.</p>'
            '<div class="strip" dir="rtl">' + "".join(
                '<article><div class="large ar">'+e(c["letter"])+'</div>'
                '<div class="ar">'+e(c["name_written"])+'</div>'
                '<div class="muted">R='+e(c["native_weight_research"])+'</div></article>'
                for c in cells
            ) + '</div><p>QITṬ native additive projection: <strong>' +
            e(frame["qitt_native_value"])+'</strong>. No semantic equivalence is inferred.</p></section>'
        )
    else:
        initials_view = '<section><h2>الحروف المقطعات</h2><p class="muted">No verse-initial classification is admitted for this source/context.</p></section>'

    sky_objects = scene["astro_layer"].get("objects", [])
    astro_view = ('<p class="muted">Optional astronomical observations: <strong>' +
                  e(len(sky_objects)) + '</strong> sourced objects. Star positions are not assigned to letters.</p>')
    stylesheet = r"""
:root{color-scheme:dark;--bg:#10151e;--fg:#ebdfbd;--muted:#a6b0be;--edge:#364657;--panel:#19232e;--gold:#eec77d}
*{box-sizing:border-box}body{background:radial-gradient(ellipse at 50% 0%,#25374a,#10151e 70%);color:var(--fg);font:16px/1.6 system-ui,Segoe UI,sans-serif;margin:0}
main{max-width:1060px;margin:auto;padding:40px 22px 90px}
header{text-align:center;margin-bottom:36px}h1{font-weight:500;font-size:2rem;letter-spacing:.02em;margin:.2rem}h2{font-weight:500;font-size:1.1rem;margin:0 0 10px}
.kicker{font-size:.73rem;letter-spacing:.16em;color:var(--gold);text-transform:uppercase}.muted{color:var(--muted);font-size:.91rem}
.ar{font-family:"Noto Naskh Arabic","Amiri","Noto Sans Arabic",Tahoma,serif;line-height:1.8}
.verse{font-size:clamp(2.5rem,6vw,4.4rem);text-align:center;direction:rtl;unicode-bidi:isolate;padding:40px 20px;word-spacing:.1em;background:linear-gradient(135deg,#1b2933,#121e28);border:1px solid var(--edge);border-radius:18px}
section{margin-top:24px;padding:26px;background:var(--panel);border:1px solid var(--edge);border-radius:15px}
.tags{display:flex;gap:7px;flex-wrap:wrap;margin:20px 0 0}.tag{border:1px solid var(--edge);padding:3px 10px;color:var(--muted);font-size:.78rem;border-radius:30px}
.strip{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}.strip article{min-width:120px;text-align:center;border:1px solid var(--edge);border-radius:13px;padding:8px 22px}
.strip .large{font-size:3.3rem;color:var(--gold)}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid var(--edge);padding:9px;text-align:left}th{color:var(--muted);font-weight:500;font-size:.83rem}
.w{font-size:1.45rem}.number{font-variant-numeric:tabular-nums}code{font-size:.77rem;word-break:break-all}
footer{text-align:center;padding:25px;color:var(--muted);font-size:.8rem}
"""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'style-src &#39;unsafe-inline&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">'
        '<title>UNISON Qur’an · '+e(title)+'</title><style>'+stylesheet+'</style></head>'
        '<body><main><header><div class="kicker">GLASS × MUQRI × SURFACE / UNISON 0.1</div>'
        '<h1>القرآن · Computational Reader</h1><div class="muted">'+e(title)+'</div></header>'
        '<div class="verse ar" dir="rtl" lang="ar">'+e(text["raw"])+'</div>'
        '<div class="tags">'+source_layers+'</div>'+initials_view+
        '<section><h2>Lexical address index</h2>'
        '<p class="muted">Byte-addressed nodes, preserving the exact source and ordered spans.</p>'
        '<table><thead><tr><th>#</th><th>Word</th><th>Node address</th><th>UTF-8 byte span</th>'
        '</tr></thead><tbody>'+word_rows+'</tbody></table></section>'
        '<section><h2>SURFACE observer / cosmic layer</h2>'+astro_view+
        '<p class="muted">Observed stellar coordinates require a declared sky frame, epoch, provenance and uncertainty. '
        'A logical clock and a catalog are not a simulation of all stellar energy.</p></section>'
        '<section><h2>Scientific boundary</h2><p class="muted">'
        'This is a source-review rendering, not a native Android build or authoritative Qur’anic interpretation. '
        'Arabic shaping comes from the installed platform font engine; Muqri determines spoken targets. '
        'No network or embedded executable script is used.</p></section>'
        '<footer>Source SHA-256: '+e(text["source_sha256"])+'</footer></main></body></html>'
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Offline UNISON Qur'an scene review")
    ap.add_argument("--scene", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.scene.stat().st_size > 2_000_000:
        raise ValueError("RESOURCE_LIMIT: input bytes")
    scene = json.loads(args.scene.read_text(encoding="utf-8"))
    markup = render_review(scene)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markup, encoding="utf-8")
    print(f"Generated offline review: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
