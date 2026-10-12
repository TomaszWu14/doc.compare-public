"""Generuje nagrania lektora (ElevenLabs) dla trybu prezentacji (?demo=1).

Czyta static/demo/demo_script.json i config/voice.json, zapisuje MP3 do
static/demo/audio/ oraz manifest.json (id kroku -> plik), który czyta demo.js.

Cache: plik = <id>-<hash>.mp3, hash z tekstu mówionego (po słowniku wymowy)
+ modelu + formatu + voice_settings. Generowane są tylko kroki bez pliku.
previous_text/next_text NIE wchodzą do hasha — zmiana tekstu jednego kroku
przegenerowuje tylko ten krok.

Użycie:
    python tools/generate_voiceover.py              # brakujące / zmienione kroki
    python tools/generate_voiceover.py --dry-run    # pokaż plan, bez API
    python tools/generate_voiceover.py --step krok03  # wymuś jeden krok
    python tools/generate_voiceover.py --force      # wszystko (np. po zmianie głosu)

Env: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID (nigdy w repo).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "static" / "demo" / "demo_script.json"
VOICE = ROOT / "config" / "voice.json"
AUDIO_DIR = ROOT / "static" / "demo" / "audio"
API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format={fmt}"


def spoken(text: str, wymowa: dict[str, str]) -> str:
    """Podmienia skróty na zapis fonetyczny (całe słowa, najdłuższe najpierw)."""
    for word in sorted(wymowa, key=len, reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(word)}(?!\w)", wymowa[word], text)
    return text


def clip_name(step_id: str, text: str, voice: dict) -> str:
    payload = json.dumps({"text": text, "voice": voice}, sort_keys=True, ensure_ascii=False)
    return f"{step_id}-{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:10]}.mp3"


def plan(script: dict, voice: dict, audio_dir: Path, only: str | None = None, force: bool = False):
    """Zwraca listę (krok, tekst mówiony, plik, czy_generować) w kolejności scenariusza."""
    steps = script["steps"]
    wymowa = script.get("wymowa", {})
    out = []
    for step in steps:
        text = spoken(step["text"], wymowa)
        name = clip_name(step["id"], text, voice)
        if only:
            todo = step["id"] == only
        else:
            todo = force or not (audio_dir / name).exists()
        out.append((step, text, name, todo))
    if only and not any(s["id"] == only for s in steps):
        raise SystemExit(f"Nie ma kroku {only!r} w {SCRIPT.name}")
    return out


def synthesize(text: str, prev_text: str, next_text: str, voice: dict, api_key: str, voice_id: str) -> bytes:
    body = {
        "text": text,
        "model_id": voice["model_id"],
        "voice_settings": voice["voice_settings"],
        "previous_text": prev_text,
        "next_text": next_text,
    }
    req = urllib.request.Request(
        API_URL.format(voice_id=voice_id, fmt=voice["output_format"]),
        data=json.dumps(body).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from e


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", help="przegeneruj tylko ten krok (np. krok03)")
    ap.add_argument("--dry-run", action="store_true", help="pokaż, co by się zmieniło")
    ap.add_argument("--force", action="store_true", help="przegeneruj wszystkie kroki")
    args = ap.parse_args(argv)

    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    voice = json.loads(VOICE.read_text(encoding="utf-8"))
    items = plan(script, voice, AUDIO_DIR, only=args.step, force=args.force)
    todo = [i for i, it in enumerate(items) if it[3]]

    for step, _text, name, need in items:
        print(f"{'GENERUJ' if need else 'cache  '}  {step['id']}  {name}")
    print(f"Do wygenerowania: {len(todo)} z {len(items)}")
    if args.dry_run or not todo:
        return 0

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    if not api_key or not voice_id:
        print("Brak ELEVENLABS_API_KEY albo ELEVENLABS_VOICE_ID w środowisku.", file=sys.stderr)
        return 2

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for i in todo:
        step, text, name, _ = items[i]
        prev_text = items[i - 1][1] if i > 0 else ""
        next_text = items[i + 1][1] if i + 1 < len(items) else ""
        (AUDIO_DIR / name).write_bytes(synthesize(text, prev_text, next_text, voice, api_key, voice_id))
        for old in AUDIO_DIR.glob(f"{step['id']}-*.mp3"):
            if old.name != name:
                old.unlink()
        print(f"zapisano {name}")

    manifest = {step["id"]: name for step, _t, name, _n in items if (AUDIO_DIR / name).exists()}
    (AUDIO_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
