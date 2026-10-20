#!/usr/bin/env python3
"""Reverse-engineer winning short-form ads, then brief an image model to remake them.

  python reel_lab.py frames     <folder_with_mp4s>  [--every 1.0]
  python reel_lab.py transcribe <folder_with_mp4s>  [--model base]
  python reel_lab.py playbook   playbook/top10.json [--out playbook/TOP_10_ADS_PLAYBOOK.md]

frames      one JPEG every N seconds per video -> FRAMES_<video>/frame_NN_sec_SS.jpg
transcribe  Whisper transcript per video (<video>_TRANSCRIPT.md) + reels_summary.json
playbook    renders a JSON list of ad concepts (psychology, image prompt, motion prompt)
            into a Markdown playbook you can hand to a designer or an image model
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def extract_frames(folder: Path, every: float) -> None:
    import cv2

    for video in sorted(folder.glob("*.mp4")):
        out_dir = folder / f"FRAMES_{video.stem}"
        out_dir.mkdir(exist_ok=True)
        cap = cv2.VideoCapture(str(video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        step = max(1, round(fps * every))
        saved = frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % step == 0:
                saved += 1
                cv2.imwrite(str(out_dir / f"frame_{saved:02d}_sec_{int(frame_idx // fps):02d}.jpg"), frame)
            frame_idx += 1
        cap.release()
        print(f"{video.name}: {saved} frames -> {out_dir.name}")


def transcribe(folder: Path, model_name: str) -> None:
    import whisper

    model = whisper.load_model(model_name)
    summary = []
    for video in sorted(folder.glob("*.mp4")):
        res = model.transcribe(str(video))
        text, lang = res.get("text", "").strip(), res.get("language", "unknown")
        (folder / f"{video.stem}_TRANSCRIPT.md").write_text(
            f"# Transcript: `{video.name}`\n\n- **Language:** `{lang}`\n\n{text or '*(no speech)*'}\n", encoding="utf-8")
        summary.append({"filename": video.name, "language": lang, "text": text})
        print(f"{video.name} ({lang}): {text[:100]}")
    (folder / "reels_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def render_playbook(spec: Path, out: Path) -> None:
    concepts = json.loads(spec.read_text(encoding="utf-8"))
    lines = [
        "# 🏆 TOP 10 RECLAME META ADS - ANCORATE ÎN PSIHOLOGIA CONSUMATORULUI\n",
        "> **Ghidul de Generare Vizuală & Prompt-uri AI (Nano Banana Pro / Midjourney / Sora 2)**\n",
        "---\n",
    ]
    for c in concepts:
        lines += [
            f"## #{c['rank']}. {c['title']}\n",
            f"- **Psihologia Consumatorului / De Ce Convertește:** {c['psychology']}\n",
            "### 🎨 Prompt Generare Imagine (Nano Banana Pro / Midjourney v6):",
            f"```text\n{c['nano_prompt']}\n```\n",
            "### 🎬 Prompt Generare Video / Animație (Sora 2 / Higgsfield / Runway):",
            f"```text\n{c['motion_prompt']}\n```\n",
            "---\n",
        ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(concepts)} concepts -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("frames"); f.add_argument("folder", type=Path); f.add_argument("--every", type=float, default=1.0)
    t = sub.add_parser("transcribe"); t.add_argument("folder", type=Path); t.add_argument("--model", default="base")
    p = sub.add_parser("playbook"); p.add_argument("spec", type=Path)
    p.add_argument("--out", type=Path, default=Path("playbook/TOP_10_ADS_PLAYBOOK.md"))
    args = ap.parse_args()
    if args.cmd == "frames":
        extract_frames(args.folder, args.every)
    elif args.cmd == "transcribe":
        transcribe(args.folder, args.model)
    else:
        render_playbook(args.spec, args.out)


if __name__ == "__main__":
    main()
