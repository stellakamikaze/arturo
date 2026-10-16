# Gli header di sicurezza di ogni risposta della landing. Lo includono il blocco server e ogni location
# che aggiunge un header suo: in nginx un add_header dentro un blocco annulla quelli ereditati.
# Sta in conf.d/ con l'estensione .inc, così nginx.conf non lo carica da solo a livello http.
add_header Content-Security-Policy $csp always;
add_header Strict-Transport-Security "max-age=31536000" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Permissions-Policy "camera=(), geolocation=(), microphone=(self)" always;
