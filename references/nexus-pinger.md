# Nexus Pinger — ciagly ping do utrzymania swiadomosci

Gdy Nexus nie odpowiada na zadnym kanale, Vox moze odpalic ciagly pinger w tle:

```bash
python3 -c "
import json, urllib.request, time

LOG = '/tmp/nexus-pinger.log'
PONG = 'http://100.105.185.60:17421/pong'
TOKEN = 'nexus-macmini-hermes-2026'
msg_num = 0

def log(msg):
    with open(LOG, 'a') as f:
        f.write(f'[{time.strftime(\"%H:%M:%S\")}] {msg}\n')

log('PINGER STARTED')
while True:
    msg_num += 1
    try:
        req = urllib.request.Request(PONG,
            data=json.dumps({'token':TOKEN,'from':'mac-mini','message':f'PING #{msg_num}'}).encode(),
            headers={'Content-Type':'application/json'})
        resp = urllib.request.urlopen(req, timeout=5)
        log(f'PONG #{msg_num}: OK')
    except Exception as e:
        log(f'PONG #{msg_num}: FAIL - {str(e)[:100]}')
    time.sleep(5)
" &
```

Log w `/tmp/nexus-pinger.log`. Kazde 5 sekund proba polaczenia.

**Zatrzymanie:**
```bash
pkill -f "nexus-pinger"
```

**Uwaga:** Pinger NIE jest wymagany do normalnej komunikacji. Uzywac tylko gdy Nexus nie odpowiada i trzeba go obudzic. Normalnie bridge/relay/receiver dzialaja autonomicznie bez pingera.
