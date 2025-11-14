
Krótki przewodnik jak uruchomić i testować aplikację Flask zawartą w tym repozytorium.

## Co jest w repozytorium
- `app.py` — główny kod aplikacji Flask (endpointy `/` i `/artists` GET/POST).
- `dockerfile` — instrukcje budowy obrazu (bazuje na `python:3.11-slim`). Uwaga: nazwa pliku ma małą literę.
- `requirements.txt` — zależności Pythona (flask, flask-smorest, python-dotenv).
- `.flaskenv` — zmienne środowiskowe dla Flaska w trybie development (`FLASK_APP`, `FLASK_DEBUG`).
- `docker-compose.yml` — konfiguracja Compose (prod-like).
- `docker-compose.override.yml` — ustawienia dla development (bind mount, FLASK_DEBUG=1, `--reload`).

## Przed odpaleniem Dockera umieść w folderze /data baze danych udostępnioną pod tym linkiem: https://github.com/adamalama151212-code/songs-guesser-database

## Szybkie komendy (PowerShell)

### 1) Build obrazu lokalnie
```powershell
docker build -t rest-apis-flask-python .
```

### 2) Uruchomienie w trybie development (autoreload, bind mount)
Compose użyje pliku `docker-compose.override.yml` automatycznie — dzięki temu kod z hosta jest montowany do kontenera i Flask przeładowuje się po zmianach.

```powershell
# uruchom z logami w konsoli
docker compose up --build

# lub uruchom w tle
docker compose up -d --build

# śledź logi
docker compose logs -f web
```


Po uruchomieniu dev:
- Otwórz `http://localhost:5000/artists` — powinieneś zobaczyć listę artystów.
- Zmień `app.py` lokalnie, zapisz — w logach kontenera zobaczysz `Detected change...` i aplikacja się przeładuje.

### 3) Uruchomienie w trybie produkcyjnym (bez override, bez debug)
Compose domyślnie łączy `docker-compose.yml` i `docker-compose.override.yml`. Aby uruchomić wyłącznie produkcyjny plik (bez bind mount i bez debug):

```powershell
docker compose -f docker-compose.yml up --build -d

docker compose -f docker-compose.yml logs -f web
```

### 4) Zatrzymywanie / cleanup
```powershell
# zatrzymaj i usuń kontenery/stworzone sieci przez compose
docker compose down

### 5) Szybkie testy HTTP
- PowerShell:
```
Invoke-RestMethod http://localhost:5000/artists 



