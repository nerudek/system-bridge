# LM Studio — Auto-unload Configuration

Problem: LM Studio ładuje modele przy starcie i trzyma je w RAM (~15-22GB) nawet gdy nikt nie wysyła requestów.

## Plik konfiguracyjny
`~/.lmstudio/settings.json`

## Trzy kluczowe zmiany

```json
{
  "autoLoadBundledLLM": false,
  "developer": {
    "unloadPreviousJITModelOnLoad": true,
    "jitModelTTL": {
      "enabled": true,
      "ttlSeconds": 300
    }
  },
  "chat": {
    "unloadPreviousModelOnSelect": true
  }
}
```

## Co robi każda zmiana

| Ustawienie | Domyślnie | Po zmianie |
|-----------|-----------|-----------|
| `autoLoadBundledLLM` | `true` | `false` — nie ładuje modeli przy starcie aplikacji |
| `unloadPreviousJITModelOnLoad` | `false` | `true` — wywala stary model przy ładowaniu nowego |
| `jitModelTTL.enabled` | `false` | `true` — włącza auto-unload po idle |
| `jitModelTTL.ttlSeconds` | 3600 | 300 — 5 minut bezczynności = unload |
| `unloadPreviousModelOnSelect` | juź `true` | bez zmian — wyładowuje przy przełączaniu |

## Efekt
- LM Studio ładuje model TYLKO gdy dostanie request przez API (port 1234)
- Po 5 minutach bezczynności model jest automatycznie wyładowywany z RAM
- Zero marnowania pamięci na idle modele
- Restart LM Studio wymagany by zmiany weszły

## Weryfikacja
```bash
# Sprawdź czy serwer inference działa
ps aux | grep "llama\|lmstudio" | grep -v grep

# Sprawdź RAM po resecie
vm_stat | head -5
```
