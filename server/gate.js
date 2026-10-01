// Cancello a parola d'ordine della landing di Arturo.
// La parola non sta qui né nel repository: nginx passa solo il suo sha256
// ($gate_hash) e una chiave casuale ($gate_chiave), dal file segreti/gate.conf
// che vive solo sul server.
import qs from 'querystring';
import crypto from 'crypto';

function uguali(a, b) {
    if (a.length !== b.length) return false;
    let d = 0;
    for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
    return d === 0;
}

// Il cookie vale finché non cambiano parola o chiave.
function gettone(r) {
    return crypto.createHmac('sha256', r.variables.gate_chiave)
        .update(r.variables.gate_hash).digest('hex');
}

function ammesso(r) {
    const c = r.variables.cookie_arturo_pass || '';
    return uguali(c, gettone(r)) ? '1' : '0';
}

function entra(r) {
    if (r.method !== 'POST') {
        r.return(302, '/entra');
        return;
    }
    const corpo = qs.parse(r.requestText || '');
    const parola = String(corpo.parola || '');
    const hash = crypto.createHash('sha256').update(parola).digest('hex');
    if (uguali(hash, r.variables.gate_hash)) {
        r.headersOut['Set-Cookie'] = 'arturo_pass=' + gettone(r)
            + '; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax';
        r.return(303, '/');
    } else {
        r.return(303, '/entra?respinto');
    }
}

export default { ammesso, entra };
