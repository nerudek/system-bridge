# Parallel DeepSeek Sessions via tmux

Wiele równoległych sesji DeepSeek V4 Pro na tym samym kluczu API — współdzielą budżet tokenów, nie wymagają osobnych kluczy.

## Uruchamianie

```bash
# Instalacja tmux (jednorazowo)
brew install tmux

# Spawn 2 dodatkowe sesje
tmux new-session -d -s hermes2 -x 120 -y 40 'hermes'
tmux new-session -d -s hermes3 -x 120 -y 40 'hermes'

# Sprawdź działające
tmux ls
```

## Wysyłanie zadań

```bash
tmux send-keys -t hermes2 'Przeanalizuj X i zapisz do /tmp/result2.md' Enter
tmux send-keys -t hermes3 'Przeanalizuj Y i zapisz do /tmp/result3.md' Enter
```

## Podgląd wyników

```bash
tmux capture-pane -t hermes2 -p | tail -30
```

## Zatrzymywanie

```bash
tmux send-keys -t hermes2 '/exit' Enter
sleep 2
tmux kill-session -t hermes2
```

## Ważne
- Ten sam klucz API DeepSeek — limit tokenów dzielony między wszystkie sesje
- Każda sesja to niezależny proces z osobną historią konwersacji
- Nie ma limitu równoległych połączeń per klucz — tylko globalny budżet tokenów
- Do zadań produkcyjnych: 3-4 równoległe sesje to sweet spot
