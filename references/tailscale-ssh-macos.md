# Tailscale SSH na macOS — Pułapki i Rozwiązania

## Problem 1: App Store vs CLI

Tailscale z Mac App Store działa w sandboxie. Proces działa (PID widoczny), GUI pokazuje połączenie, ale `tailscale status` z terminala zwraca:
```
failed to connect to local Tailscale service; is Tailscale running?
```

**Rozwiązanie**: Uruchom `tailscale up` z terminala (sudo). To przejmuje kontrolę od wersji App Store i tworzy socket `/var/run/tailscaled.socket`.

## Problem 2: Host Key Verification (ED25519)

`tailscale ssh hostname` dodaje własną warstwę weryfikacji klucza hosta ED25519 (z coordination server), NIEZALEŻNIE od standardowego `StrictHostKeyChecking`. Nawet `-o StrictHostKeyChecking=no` tego nie omija.

Objaw:
```
No ED25519 host key is known for macbook-pro-macbook.tail0cd3c8.ts.net.
Host key verification failed.
```

**Obejścia**:
- SSH przez IP zamiast hostname Tailscale (omija weryfikację ED25519 Tailscale, zostaje tylko standardowe SSH)
- Użyj `tailscale status` by poznać IP, potem `ssh user@100.x.x.x`

## Problem 3: Publickey Auth odrzucany

Objaw (ssh -vv):
```
debug1: Offering public key: /Users/x/.ssh/github_nerua1 ED25519 SHA256:xxx explicit
debug2: we sent a publickey packet, wait for reply
debug2: we did not send a packet, disable method
Connection closed by X.X.X.X port 22
```

Serwer odebrał klucz, ale nie odpowiedział — zamknął połączenie. Przyczyny:
1. **Złe uprawnienia `authorized_keys`**: musi być `chmod 600`, katalog `.ssh` musi być `chmod 700`
2. **Zły klucz publiczny w authorized_keys**: zawsze sprawdź `ssh-add -l` i `cat ~/.ssh/*.pub` przed podaniem klucza użytkownikowi
3. **`PubkeyAuthentication no`** w `/etc/ssh/sshd_config` (rzadkie na macOS, częste na serwerach)
4. **`AuthenticationMethods`** ogranicza do np. tylko keyboard-interactive

## Problem 4: Agent bez tożsamości

`ssh-add -l` → "The agent has no identities." — klucze prywatne nie są załadowane do agenta SSH.

**Rozwiązanie**: Użyj `ssh -i ~/.ssh/konkretny_klucz` zamiast polegać na agencie. Albo `ssh-add ~/.ssh/konkretny_klucz`.

## Sekwencja debugowania Tailscale SSH

```bash
# 1. Czy tailscale CLI widzi sieć?
tailscale status | head -10

# 2. Jeśli nie — przejmij od App Store:
sudo tailscale up

# 3. Sprawdź IP celu:
tailscale status | grep hostname

# 4. Sprawdź swoje klucze:
ssh-add -l
ls -la ~/.ssh/

# 5. SSH z konkretnym kluczem:
ssh -i ~/.ssh/klucz -vv user@100.x.x.x "whoami" 2>&1 | grep -E "Offering|Accepted|closed"

# 6. Jeśli klucz odrzucony — sprawdź na CELU:
#    chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
#    cat ~/.ssh/authorized_keys  # czy klucz dokładnie pasuje?
```

## Tailscale na PCNERU (RTX 3090, 192.168.1.32)

PC nie pokazuje się w `tailscale status`. Powody:
- PC wyłączony
- Tailscale nie uruchomiony na PC
- PC na innym koncie Tailscale (sprawdź `tailscale status` — wszystkie node'y powinny być pod tym samym UserID)
