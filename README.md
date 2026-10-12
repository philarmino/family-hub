# Family Hub

Lokaler Familien-Wochenplaner für den HomePi: Kinder schlagen Essen vor und tragen Extra-Wünsche ein, Eltern finalisieren den Plan und pushen skalierte Zutaten sowie freigegebene Wünsche in **Bring!**.

Kein Login. Nur die Aktion „In Bring! legen“ verlangt das Passwort `BRING_PUSH_PASSWORD`.

## Features (v1)

- Essens-Katalog mit Fotos (eigene Rezepte **oder** Chefkoch-Import)
- Kinder-Ansicht: Foto-Tippen = Vorschlag, Freitext-Wunschfelder (nur aktuelle Woche)
- Eltern-Ansicht: Diese / Nächste / Übernächste Woche, Personen pro Tag, Wunsch-Sichtung, Bring!-Push
- PWA-Manifest für Homescreen-Shortcut auf dem Tablet
- Docker, nur LAN-Bind

## Schnellstart (HomePi)

```bash
cd ~/docker/family-hub   # oder dieses Repo
cp .env.example .env
# .env ausfüllen: HOMEPI_IP, BRING_*, BRING_PUSH_PASSWORD

docker compose up -d --build
```

Öffnen: `http://<HOMEPI_IP>:8080`

### Bring!-Liste finden

1. Bring!-Zugangsdaten in `.env` setzen
2. Listen abfragen:

```bash
curl -s -X POST http://127.0.0.1:8080/api/bring/lists \
  -H 'Content-Type: application/json' \
  -d '{"password":"DEIN_BRING_PUSH_PASSWORD"}'
```

UUID als `BRING_LIST_UUID` in `.env` eintragen und Container neu starten.

### Tablet-Shortcut

- **Android Chrome:** Seite öffnen → Menü → „Zum Startbildschirm“ / „App installieren“
- **iPad Safari:** Teilen → „Zum Home-Bildschirm“

Ohne HTTPS auf einer reinen IP ist die echte PWA-Installation je nach Browser eingeschränkt. Fallback: Lesezeichen oder manuelles Shortcut zur URL.

## Lokal entwickeln

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATA_DIR=../data uvicorn app.main:app --reload --port 8080

# Frontend (zweites Terminal)
cd frontend
npm install
npm run dev
```

Vite proxied `/api` und `/media` auf Port 8080.

## Env-Variablen

| Variable | Bedeutung |
|----------|-----------|
| `HOMEPI_IP` | LAN-IP für Port-Bind (Compose) |
| `DEFAULT_SERVINGS` | Standard-Personenanzahl |
| `BRING_EMAIL` / `BRING_PASSWORD` | Bring!-Account |
| `BRING_LIST_UUID` | Ziel-Einkaufsliste |
| `BRING_PUSH_PASSWORD` | Passwort im UI vor dem Push |

## Ablauf Sonntag

1. Kinder öffnen Family Hub: Essen tippen + Wünsche speichern (nur diese Woche)
2. Eltern: Diese / Nächste / Übernächste Woche planen, Mo–So untereinander, Personen pro Tag, Wünsche freigeben
3. Finalisieren (optional) → „In Bring! legen“ + Passwort

Beim ersten Start werden automatisch Familienrezepte von Chefkoch geladen (soweit noch nicht vorhanden).
