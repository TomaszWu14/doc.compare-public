"""Tryb prezentacji (?demo=1): generator lektora i bramka w szablonie."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_voiceover as gv  # noqa: E402

VOICE = {"model_id": "m", "output_format": "f", "voice_settings": {"stability": 0.5}}


def _script(**texts):
    return {"wymowa": {"SAP": "es-a-pe"}, "steps": [{"id": k, "text": v} for k, v in texts.items()]}


def test_spoken_replaces_whole_words_only():
    assert gv.spoken("Nie łączy się z SAP.", {"SAP": "es-a-pe"}) == "Nie łączy się z es-a-pe."
    assert gv.spoken("SAPPHIRE", {"SAP": "es-a-pe"}) == "SAPPHIRE"


def test_name_depends_on_text_and_voice_settings():
    a = gv.clip_name("krok01", "tekst", VOICE)
    assert a.startswith("krok01-") and a.endswith(".mp3")
    assert gv.clip_name("krok01", "tekst", VOICE) == a
    assert gv.clip_name("krok01", "inny", VOICE) != a
    tuned = {**VOICE, "voice_settings": {"stability": 0.6}}
    assert gv.clip_name("krok01", "tekst", tuned) != a


def test_changing_one_step_regenerates_only_that_step(tmp_path):
    first = gv.plan(_script(k1="Jeden.", k2="Dwa.", k3="Trzy."), VOICE, tmp_path)
    for _s, _t, name, _n in first:
        (tmp_path / name).write_bytes(b"mp3")

    edited = gv.plan(_script(k1="Jeden.", k2="Dwa, zmienione.", k3="Trzy."), VOICE, tmp_path)
    assert [s["id"] for s, _t, _n, todo in edited if todo] == ["k2"]


def test_step_flag_forces_single_step(tmp_path):
    items = gv.plan(_script(k1="Jeden.", k2="Dwa."), VOICE, tmp_path, only="k2")
    assert [s["id"] for s, _t, _n, todo in items if todo] == ["k2"]
    with pytest.raises(SystemExit):
        gv.plan(_script(k1="Jeden."), VOICE, tmp_path, only="nie-ma")


def test_dry_run_needs_no_api_key(monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert gv.main(["--dry-run"]) == 0
    assert "Do wygenerowania" in capsys.readouterr().out


def test_repo_script_is_valid():
    script = json.loads((ROOT / "static/demo/demo_script.json").read_text(encoding="utf-8"))
    ids = [s["id"] for s in script["steps"]]
    assert len(ids) == len(set(ids))
    assert script["steps"][0].get("url"), "pierwszy krok musi wskazać stronę"
    for s in script["steps"]:
        assert s["action"] in {"navigate", "highlight", "click"}
        assert s["text"].strip()


def test_demo_assets_only_with_demo_param():
    flask = pytest.importorskip("flask")
    app = flask.Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
    with app.test_request_context("/compare"):
        assert "demo.js" not in flask.render_template("_demo_mode.html")
    with app.test_request_context("/compare?demo=0"):
        assert "demo.js" not in flask.render_template("_demo_mode.html")
    with app.test_request_context("/compare?demo=1"):
        assert "demo/demo.js" in flask.render_template("_demo_mode.html")
