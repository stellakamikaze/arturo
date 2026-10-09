#!/usr/bin/env python3
"""I pattern dei segreti vivono in due posti: hooks/credential-leak-scanner.py (rete, avvisa il
modello) e skills/redazione-segreti/hooks/patterns.ts (redige prima che il modello legga).
Il mod li ha copiati a mano, e due copie a mano divergono (successo il 3/10/2026).
Questo banco fallisce se lo scanner ha un tipo che il mod non mappa, o se la mappa punta a un
tipo che il mod non ha più. Le differenze volute stanno in VOLUTE, con il motivo.
Veleno: --avvelena aggiunge allo scanner un tipo finto e il banco deve diventare rosso."""
import importlib.util, os, re, sys

# Arturo: il repo e' la cartella sopra tests/ (o --repo).
H = sys.argv[sys.argv.index("--repo") + 1] if "--repo" in sys.argv else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPA = {
    "AWS Access Key": "aws-key", "GitHub Token": "github-token", "GitHub PAT": "github-pat",
    "API Key": "api-key", "Slack Token": "slack-token", "Stripe Secret Key": "stripe-secret",
    "Supabase Key": "supabase-key", "JWT Token": "jwt", "Private Key": "private-key",
    "Anthropic API Key": "anthropic-key", "OpenAI Project/Org Key": "openai-key",
    "OpenAI Legacy API Key": "openai-legacy-key", "Telegram Bot Token": "telegram-token",
    "Brave Search API Key": "brave-key", "Vercel Token": "vercel-token",
    "Discord Bot Token": "discord-token", "Firebase/Google API Key": "google-api-key",
    "Generic Secret": "generic-secret", "Database Connection String": "DB_URL",
}
VOLUTE = {"Stripe Publishable Key": "chiave pubblicabile, non un segreto: il mod non la redige"}

spec = importlib.util.spec_from_file_location("scanner", f"{H}/hooks/credential-leak-scanner.py")
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
nomi = [n for _, n in sc.CREDENTIAL_PATTERNS]
if "--avvelena" in sys.argv:
    nomi.append("Tipo Finto Avvelenato")
ts = open(f"{H}/skills/redazione-segreti/hooks/patterns.ts", encoding="utf-8").read()
tipi_mod = set(re.findall(r"/[gimsuy]*, '([a-z0-9-]+)'\]", ts))
if re.search(r"export const DB_URL\b", ts):
    tipi_mod.add("DB_URL")

rossi = []
for n in nomi:
    if n in VOLUTE:
        continue
    if n not in MAPPA:
        rossi.append(f"lo scanner ha «{n}», che il mod non mappa: aggiungilo a patterns.ts o a VOLUTE")
    elif MAPPA[n] not in tipi_mod:
        rossi.append(f"«{n}» punta a «{MAPPA[n]}», che patterns.ts non ha più")
CASI = len(nomi)
for r in rossi:
    print("ROSSO", r)
print(f"totale tipi dello scanner: {CASI} · mappati o voluti: {CASI - len(rossi)} · rossi: {len(rossi)}")
sys.exit(1 if rossi else 0)
