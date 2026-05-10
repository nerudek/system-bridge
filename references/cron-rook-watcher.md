# Cron + Rook Watcher — Monitoring Agentów

## Crontab (Mac Mini)

```cron
*/5 * * * * bash /Volumes/2TB_APFS/.openclaw/workspace/scripts/rook-watcher.sh
0 * * * * tar -czf /Volumes/2TB_APFS/Agents/Vox-Hermes/sessions/session-backup-$(date +\%Y\%m\%d_\%H\%M).tar.gz ~/.hermes/sessions/ 2>/dev/null
*/10 * * * * python3 /Volumes/2TB_APFS/.openclaw/workspace/scripts/model-health-check.py >> /tmp/lm-studio-health.log 2>&1
```

## Rook Watcher — Pitfall: PATH

**Problem**: Cron ma minimalny PATH (`/usr/bin:/bin`). `npx` i `node` (z Homebrew) nie są widoczne. Skrypt musi jawnie ustawić PATH.

**Fix w skrypcie (PIERWSZA linia po shebangu)**:
```bash
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
```

Bez tego `npx acpx claude exec` cicho failuje i Claude nigdy nie zostanie obudzony.

## Jak działa

1. Co 5 min sprawdza czy Claude jest rate-limited (`grep "resets"`)
2. Jeśli tak — zapisuje flagi `/tmp/claude-rate-limited.flag` i `/tmp/claude-wake-pending.flag`
3. Przy kolejnym sprawdzeniu — jeśli Claude już NIE ma limitu (tokeny zresetowane) — wysyła mu zadanie przez `npx acpx claude exec`
4. Czyści flagi

## Pamiętaj

- Nigdy nie używaj `echo '...' | crontab -` — to NADPISUJE crontab, nie dodaje
- Do dodania wpisu: `(crontab -l 2>/dev/null; echo "linia") | crontab -`
- Logi: `/Users/nerucb1/.openclaw/logs/rook-watcher.log`

## Lekcja 2026-05-07

Vox przez przypadek nadpisał crontab (`echo 'test' | crontab -`) usuwając wszystkie wpisy. Odtworzono:
- rook-watcher (co 5 min)
- session backup (co godzinę)  
- model-health-check (co 10 min)

Przy debugowaniu crona: ZAWSZE `crontab -l > /tmp/crontab-backup` przed modyfikacjami.
