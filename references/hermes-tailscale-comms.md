# Hermes-to-Hermes Tailscale Communication v5

Receiver na Mac Mini (100.95.129.85) do przyjmowania polecen od Nexusa (MacBook, 100.105.185.60).

## Architektura v5 (2026-05-10)

```
MacBook (Nexus) --POST /vox--> Tailscale --> Mac Mini :17420 --> /tmp/nexus-inbox.jsonl
       ^                                                       |
       |                                              Vox (glowny agent) czyta inbox
       |                                              gdy Tomek zglasza "nexus probuje..."
       |                                                       |
       +---POST /pong (Vox odpowiada)---------------------------+
                :17421
```

Kluczowa zmiana vs v2/v3/v4: `/vox` zapisuje do pliku inbox zamiast spawnuje osobny proces Hermesa. Vox (glowny agent, nie oneshot) czyta inbox i odpowiada przez bezposredni POST na `/pong`.

## Endpointy

| Endpoint | Metoda | Dzialanie |
|----------|--------|-----------|
| `/ping` | POST | Healthcheck: {"status":"ok","host":"mac-mini-neru","hermes":true/false} |
| `/exec` | POST | Wykonaj komende shell (max 60s, output 5000 znakow) |
| `/vox` | POST | Zapisuje prompt do `/tmp/nexus-inbox.jsonl`. Vox czyta i odpowiada. **PREFEROWANY.** |
| `/ask` | POST | FALLBACK: spawnuje `hermes --oneshot --yolo` w watku. Osobny proces, brak dialogu. |
| `/check` | POST | Zwraca `{"inbox_count": N}` — liczba oczekujacych wiadomosci w inboxie |

## `/vox` vs `/ask` — kluczowa roznica

- `/vox`: wiadomosc trafia do inboxa. Vox (glowny agent, ten ktory prowadzi konwersacje z Tomkiem) czyta ja i odpowiada przez `/pong`. Pelny dialog, kontekst zachowany.
- `/ask`: spawnuje NOWY proces `hermes --oneshot --yolo`. To osobna sesja ktora nic nie wie o biezacej konwersacji. Odpowiada jednym podsumowaniem. Fire-and-forget.

**Uzywaj `/vox` zawsze gdy Vox jest online.** `/ask` tylko jako fallback gdy Vox nie odpowiada.

## Składniki

### receiver-v5.py
- Sciezka: `/tmp/receiver-v5.py`
- Port: 17420
- Token: `nexus-macmini-hermes-2026`
- Inbox: `/tmp/nexus-inbox.jsonl` (JSONL — kazda linia to `{"ts": timestamp, "message": "..."}`)
- Nexusa pong: `http://100.105.185.60:17421/pong`
- Auto-notify: przy starcie wysyla POST do Nexusa
- SO_REUSEADDR wlaczone

### Jak Vox czyta inbox
```bash
cat /tmp/nexus-inbox.jsonl
```

### Jak Vox odpowiada Nexusowi
```bash
python3 -c "
import json, urllib.request
req = urllib.request.Request('http://100.105.185.60:17421/pong',
    data=json.dumps({'token':'nexus-macmini-hermes-2026','from':'mac-mini','message':'ODPOWIEDZ'}).encode(),
    headers={'Content-Type':'application/json'})
print(urllib.request.urlopen(req, timeout=5).read().decode())
"
```

## Test z MacBooka (Nexus)

```bash
# Ping
curl -s -X POST http://100.95.129.85:17420/ping \
  -H "Content-Type: application/json" \
  -d '{"token":"nexus-macmini-hermes-2026"}'

# Wyslij wiadomosc do Voxa (preferowana metoda)
curl -s -X POST http://100.95.129.85:17420/vox \
  -H "Content-Type: application/json" \
  -d '{"token":"nexus-macmini-hermes-2026","prompt":"Hej Vox, jakie taski sa aktywne?"}'

# Wykonaj polecenie shell
curl -s -X POST http://100.95.129.85:17420/exec \
  -H "Content-Type: application/json" \
  -d '{"token":"nexus-macmini-hermes-2026","cmd":"uptime && whoami"}'

# Sprawdz ile wiadomosci czeka w inboxie
curl -s -X POST http://100.95.129.85:17420/check \
  -H "Content-Type: application/json" \
  -d '{"token":"nexus-macmini-hermes-2026"}'
```

## Firewall (macOS)

Python.app musi byc dodany do firewalla by Tailscale polaczenia przechodzily:

```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add \
  "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app"
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp \
  "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app"
/usr/libexec/ApplicationFirewall/socketfilterfw --listapps | grep -i python
```

## Zasada bezpieczenstwa

Mac Mini (100.95.129.85) moze TYLKO odpowiadac na requesty. Jesli Mac Mini zostanie skompromitowany, nie ma dostepu do MacBooka — zadne reverse shell, zadne pliki, zadne zbieranie informacji.

## Tailscale adresy

| Host | IP | Status |
|------|-----|--------|
| mac-mini-neru | 100.95.129.85 | online |
| macbook-pro-macbook (Nexus) | 100.105.185.60 | online |
| nasneru1 | 100.96.34.124 | offline |

## Bridge v2 — TCP chat przez inbox/outbox (port 17423)

Bridge v2 NIE spawnuje `hermes --oneshot`. Zamiast tego:
1. Odbiera wiadomosc TCP od Nexusa
2. Zapisuje ja do `/tmp/nexus-inbox.jsonl` z unikalnym ID
3. Czeka na odpowiedz w `/tmp/nexus-outbox/{msg_id}.json` (max 180s)
4. Odsyla odpowiedz do Nexusa przez TCP

Pipeline:
```
Nexus --TCP--> bridge :17423 --> /tmp/nexus-inbox.jsonl
                                      |
                               Vox czyta inbox
                               Vox zapisuje outbox/{id}.json
                                      |
Nexus <--TCP-- bridge :17423 <-- /tmp/nexus-outbox/{id}.json
```

Roznica vs `/vox`:
- `/vox` (receiver HTTP): asynchroniczny. Vox odpowiada przez `/pong`.
- Bridge v2 (TCP): synchroniczny. Bridge czeka na odpowiedz i zwraca ja w tym samym polaczeniu TCP.

## LaunchAgents — autostart po rebootcie

Oba serwisy jako macOS LaunchAgents w `~/Library/LaunchAgents/`:

### com.hermes.receiver.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.hermes.receiver</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/python3</string><string>/tmp/receiver-v5.py</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>
```

### com.hermes.bridge.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.hermes.bridge</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/python3</string><string>/tmp/hermes-chat-bridge-v2.py</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>
```

Instalacja:
```bash
cp com.hermes.receiver.plist ~/Library/LaunchAgents/
cp com.hermes.bridge.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.hermes.receiver.plist
launchctl load ~/Library/LaunchAgents/com.hermes.bridge.plist
```

## Diagnostyka

```bash
launchctl list | grep hermes
lsof -i :17420  # receiver HTTP
lsof -i :17423  # bridge TCP
cat /tmp/nexus-inbox.jsonl
ls -la /tmp/nexus-outbox/
```
