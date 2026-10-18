"""US-025: zewnętrzne skrypty z CDN muszą mieć przypiętą wersję i SRI (integrity).

Bez SRI przejęcie CDN lub nowa, złośliwa wersja pakietu (np. `@latest`)
wstrzykuje kod do każdej strony aplikacji.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

# Wyjątek: Tailwind Play CDN generuje kod dynamicznie — SRI nie jest możliwe.
# Docelowo zastąpić zbudowanym arkuszem CSS (US-025, kolejny krok).
SRI_EXCEPTIONS = {"https://cdn.tailwindcss.com"}

_SCRIPT_RE = re.compile(r"<script\b[^>]*\bsrc=\"(https?://[^\"]+)\"[^>]*>", re.I)


def _external_scripts():
    for path in sorted(TEMPLATES.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in _SCRIPT_RE.finditer(text):
            yield path.name, m.group(1), m.group(0)


def test_external_scripts_have_sri():
    missing = [f"{name}: {url}" for name, url, tag in _external_scripts()
               if url not in SRI_EXCEPTIONS
               and not re.search(r'\bintegrity="sha(256|384|512)-', tag)]
    assert not missing, "Skrypty z CDN bez SRI:\n" + "\n".join(missing)


def test_sri_scripts_use_anonymous_crossorigin():
    bad = [f"{name}: {url}" for name, url, tag in _external_scripts()
           if "integrity=" in tag and 'crossorigin="anonymous"' not in tag]
    assert not bad, "SRI wymaga crossorigin=\"anonymous\":\n" + "\n".join(bad)


def test_external_scripts_pin_exact_versions():
    """Pakiet z CDN musi mieć pełną wersję (x.y.z), nie @latest ani @18."""
    floating = []
    for name, url, _ in _external_scripts():
        if url in SRI_EXCEPTIONS:
            continue
        m = re.search(r"(?:unpkg\.com|cdn\.jsdelivr\.net/npm)/((?:@[^/]+/)?[^/@]+)(@[^/]*)?/", url)
        if m and not re.fullmatch(r"@\d+\.\d+\.\d+", m.group(2) or ""):
            floating.append(f"{name}: {url}")
    assert not floating, "Wersje niepiętowane:\n" + "\n".join(floating)
