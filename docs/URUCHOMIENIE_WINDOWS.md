# Uruchomienie na Windows i udostępnienie w sieci LAN

> Dawny `README.txt` z katalogu głównego (instalacja „na biurku” w dziale). Szybki start
> i opis projektu: [`README.md`](../README.md).

## Pierwsza instalacja

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python migrate_db.py
python app.py
```

Aplikacja jest dostępna na `http://localhost:5000`, a w sieci lokalnej na `http://[twoj-ip]:5000`
(poza trybem debug serwer nasłuchuje na `0.0.0.0`).

## Domyślne konta

Przy pierwszym starcie (brak użytkownika `admin`) aplikacja tworzy konta `admin`, `superuser`,
`jan.kowalski` i `anna.nowak` z losowymi hasłami. Hasło admina jest wypisywane w konsoli
i zapisywane w `INITIAL_ADMIN_PASSWORD.txt` (usuń po pierwszym logowaniu). Hasła pozostałych
kont ustawia admin.

## Zapora (dostęp z innego komputera)

W PowerShell jako Administrator:

```powershell
netsh advfirewall firewall add rule name="DocCompare" dir=in action=allow protocol=TCP localport=5000
```

## Ghostscript (opcjonalny — poprawia jakość parsowania tabel PDF)

Pobierz `ghostpcl-10.07.0-win64.zip` z
<https://github.com/ArtifexSoftware/ghostpdl-downloads/releases> i rozpakuj do folderu
`[projekt]\ghostscript\` (bez instalacji, bez uprawnień administratora).
