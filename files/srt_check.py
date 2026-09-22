#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
srt_check.py  —  AIが直した字幕(SRT)の「文字以外が変わっていないか」を確認する

使い方:
  python srt_check.py 元の字幕.srt 直した字幕.srt
  python srt_check.py 元の字幕.srt 直した字幕.srt --normalize   # 文字コードと改行を元に合わせて保存し直す

確認すること:
  1. 字幕の枚数が同じ
  2. 各字幕の番号とタイムコード（開始 --> 終了）が1文字も変わっていない
  3. 各字幕の行数が同じ（違うと警告）
  4. 1行の文字数が多すぎないか（--max で指定・既定 20 文字。警告のみ）
結果:
  変更した字幕の一覧を「直した字幕_変更一覧.txt」に書き出す
  タイムコードや枚数が違えば終了コード 1（Premiere に読み込む前に止めるため）
"""
import argparse
import re
import sys
from pathlib import Path

TIME_RE = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}")


def read_srt(path: Path):
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig")
        enc = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("cp932")
        enc = "cp932"
    newline = "\r\n" if "\r\n" in text else "\n"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = []
    for chunk in re.split(r"\n\s*\n", text.strip("\n")):
        lines = chunk.split("\n")
        if len(lines) < 2:
            continue
        idx = lines[0].strip()
        if TIME_RE.match(lines[1]):
            blocks.append({"idx": idx, "time": lines[1].strip(), "text": lines[2:]})
        elif TIME_RE.match(lines[0]):
            blocks.append({"idx": "", "time": lines[0].strip(), "text": lines[1:]})
    return blocks, {"bom": bom, "enc": enc, "newline": newline}


def write_srt(path: Path, blocks, fmt):
    parts = []
    for b in blocks:
        head = [b["idx"]] if b["idx"] else []
        parts.append("\n".join(head + [b["time"]] + b["text"]))
    body = "\n\n".join(parts) + "\n"
    body = body.replace("\n", fmt["newline"])
    data = body.encode(fmt["enc"])
    if fmt["bom"] and fmt["enc"] == "utf-8":
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)


def main():
    ap = argparse.ArgumentParser(description="AIが直したSRTのタイムコード崩れを確認する")
    ap.add_argument("original")
    ap.add_argument("fixed")
    ap.add_argument("--max", type=int, default=20, help="1行の文字数の目安（警告のみ）")
    ap.add_argument("--normalize", action="store_true", help="直した字幕を元と同じ文字コード・改行で保存し直す")
    a = ap.parse_args()

    orig_p, fix_p = Path(a.original), Path(a.fixed)
    orig, fmt = read_srt(orig_p)
    fixed, _ = read_srt(fix_p)

    errors, warns, changes = [], [], []
    if len(orig) != len(fixed):
        errors.append(f"字幕の枚数が違う：元 {len(orig)} 枚 / 直した方 {len(fixed)} 枚")
    for i, (o, f) in enumerate(zip(orig, fixed), 1):
        if o["idx"] != f["idx"] or o["time"] != f["time"]:
            errors.append(f"{i}枚目：番号かタイムコードが変わっている\n    元　　：{o['idx']} {o['time']}\n    直した：{f['idx']} {f['time']}")
        if len(o["text"]) != len(f["text"]):
            warns.append(f"{i}枚目：行数が変わった（元 {len(o['text'])} 行 → {len(f['text'])} 行）")
        for line in f["text"]:
            if len(line) > a.max:
                warns.append(f"{i}枚目：1行 {len(line)} 文字（目安 {a.max}）「{line}」")
        if o["text"] != f["text"]:
            changes.append((i, o["time"], " / ".join(o["text"]), " / ".join(f["text"])))

    report = fix_p.with_name(fix_p.stem + "_変更一覧.txt")
    with report.open("w", encoding="utf-8") as w:
        w.write(f"変更した字幕：{len(changes)} 枚（全 {len(orig)} 枚）\n\n")
        for i, t, before, after in changes:
            w.write(f"[{i}] {t}\n  前：{before}\n  後：{after}\n\n")

    print(f"字幕 {len(orig)} 枚のうち {len(changes)} 枚を変更 → 一覧：{report.name}")
    for m in warns:
        print("⚠️ " + m)
    if errors:
        for m in errors:
            print("❌ " + m)
        print("❌ タイムコードか枚数が変わっています。Premiere に読み込まないでください。")
        sys.exit(1)
    if a.normalize:
        write_srt(fix_p, fixed, fmt)
        print(f"文字コード・改行を元の字幕に合わせて保存し直しました（{fmt['enc']}{' BOMあり' if fmt['bom'] else ''}）")
    print("✅ タイムコードと枚数は元のまま。Premiere に読み込めます。")


if __name__ == "__main__":
    main()
