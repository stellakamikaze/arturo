"""Generato da prefiltro_bash.py (`python3 hooks/prefiltro_bash.py genera`): non modificare a mano.

Le regex Python dei pattern del pre-filtro, già tradotte. Valgono solo con l'impronta del sorgente.
"""
IMPRONTA = 'd04c30ff17aa9722996befc1ac2139f0beccc5165671542a42c202169885f1d9'
REGEX = {
    # PATTERN_API_GITHUB
    'E:api\\.github\\.com': [
        'api\\.github\\.com',
    ],
    # PATTERN_COMMIT
    'L:(^|[;&|(`\'"\n])[[:space:]]*((env|command|exec|nohup|time|xargs|sudo|then|else|elif|do|if|while|until|!|\\{)[[:space:]]+)*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*(([^[:space:];&|]*/)?git([[:space:]]+-[^[:space:]]+([[:space:]]+[^-[:space:]][^[:space:]]*)?)*[[:space:]]+commit|gh[[:space:]]+pr[[:space:]]+create)': [
        '(^|[;\\&\\|\\(`\'"\\\n])[ \\t\\r\\f\\v]*((env|command|exec|nohup|time|xargs|sudo|then|else|elif|do|if|while|until|!|\\{)[ \\t\\r\\f\\v]+)*([A-Za-z_][A-Za-z0-9_]*=[^ \\t\\n\\r\\f\\v]*[ \\t\\r\\f\\v]+)*(([^ \\t\\n\\r\\f\\v;\\&\\|]*/)?git([ \\t\\n\\r\\f\\v]+-[^ \\t\\n\\r\\f\\v]+([ \\t\\n\\r\\f\\v]+[^\\- \\t\\n\\r\\f\\v][^ \\t\\n\\r\\f\\v]*)?)*[ \\t\\n\\r\\f\\v]+commit|gh[ \\t\\n\\r\\f\\v]+pr[ \\t\\n\\r\\f\\v]+create)',
    ],
    # PATTERN_COMMS
    'L:(^|[[:space:];|&("\'`])(sendmail|mailx|mutt|msmtp|swaks|mail)([[:space:]]|$)|mailto:|smtps?://|gws[[:space:]].*(messages[[:space:]]+send|send[[:space:]]+message|gmail[[:space:]].*(\\+send|drafts[[:space:]]+send|forwardingAddresses|updateAutoForwarding|delegates|filters))|osascript.*(Mail|Messages)|api\\.telegram\\.org|hooks\\.slack\\.com|slack\\.com/api/chat|api\\.sendgrid|api\\.mailgun|api\\.postmarkapp|api\\.resend|api\\.mailjet|api\\.brevo|smtp2go|api\\.sparkpost|api\\.elasticemail|zeptomail|mailchannels|email[.-][a-z0-9-]*\\.amazonaws|hooks\\.zapier|hook\\.[a-z0-9.]*make\\.com|integromat|graph\\.microsoft\\.com.*sendmail|gmail\\.googleapis\\.com.*messages/send|discord(app)?\\.com/api/webhooks|api\\.twilio\\.com|graph\\.facebook\\.com.*messages|whatsapp[_/-]?send|telegram[_/-]?send|smtplib|SMTP_SSL|http\\.client|git[[:space:]]+(send-email|imap-send)|\\+send([[:space:]]|$)|drafts[[:space:]]+send|sendUpdates|sendNotifications|permissions[[:space:]]+(create|update)|mailgun\\.net|nodemailer|wa\\.me/|whatsapp\\.com/send|whatsapp://|t\\.me/share|tg://msg': [
        '(^|[ \\t\\n\\r\\f\\v;\\|\\&\\("\'`])(sendmail|mailx|mutt|msmtp|swaks|mail)([ \\t\\n\\r\\f\\v]|\\Z)',
        'mailto:',
        'smtps?://',
        'gws[ \\t\\n\\r\\f\\v](?:(?!gws[ \\t\\n\\r\\f\\v]).)*(messages[ \\t\\n\\r\\f\\v]+send|send[ \\t\\n\\r\\f\\v]+message|gmail[ \\t\\n\\r\\f\\v](?:(?!gmail[ \\t\\n\\r\\f\\v]).)*(\\+send|drafts[ \\t\\n\\r\\f\\v]+send|forwardingAddresses|updateAutoForwarding|delegates|filters))',
        'osascript(?:(?!osascript).)*(Mail|Messages)',
        'api\\.telegram\\.org',
        'hooks\\.slack\\.com',
        'slack\\.com/api/chat',
        'api\\.sendgrid',
        'api\\.mailgun',
        'api\\.postmarkapp',
        'api\\.resend',
        'api\\.mailjet',
        'api\\.brevo',
        'smtp2go',
        'api\\.sparkpost',
        'api\\.elasticemail',
        'zeptomail',
        'mailchannels',
        'email[\\.\\-][a-z0-9\\-]*\\.amazonaws',
        'hooks\\.zapier',
        'hook\\.[a-z0-9\\.]*make\\.com',
        'integromat',
        'graph\\.microsoft\\.com(?:(?!graph\\.microsoft\\.com).)*sendmail',
        'gmail\\.googleapis\\.com(?:(?!gmail\\.googleapis\\.com).)*messages/send',
        'discord(app)?\\.com/api/webhooks',
        'api\\.twilio\\.com',
        'graph\\.facebook\\.com(?:(?!graph\\.facebook\\.com).)*messages',
        'whatsapp[_/\\-]?send',
        'telegram[_/\\-]?send',
        'smtplib',
        'SMTP_SSL',
        'http\\.client',
        'git[ \\t\\n\\r\\f\\v]+(send-email|imap-send)',
        '\\+send([ \\t\\n\\r\\f\\v]|\\Z)',
        'drafts[ \\t\\n\\r\\f\\v]+send',
        'sendUpdates',
        'sendNotifications',
        'permissions[ \\t\\n\\r\\f\\v]+(create|update)',
        'mailgun\\.net',
        'nodemailer',
        'wa\\.me/',
        'whatsapp\\.com/send',
        'whatsapp://',
        't\\.me/share',
        'tg://msg',
    ],
    # PATTERN_DANGER
    'L::\\(\\)|/dev/(sd|nvme|disk|hd)|chmod[[:space:]]+-R[[:space:]]+0*777|chown[[:space:]]+-R|\\|&?[[:space:]]*(#.*)?([({][[:space:]]*([^|]*[;&[:cntrl:]][[:space:]]*)?)?((sudo|doas)[[:space:]][^|;&]*)?(bash|sh|zsh|fish|python3?|perl|ruby|node|php|powershell|pwsh)([^[:alnum:]_.-]|$)|<\\([[:space:]]*(curl|wget|fetch)|eval[[:space:]]|mkfs\\.|(^|[^[:alnum:]_.-])(del|erase|rd|rmdir|format(\\.com)?)[[:space:]]|rm[[:space:]][^|;&]*(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)|find[[:space:]].*(-delete|-(exec|execdir|ok|okdir)[[:space:]].*(rm|unlink|shred)|xargs[^|;&]*(rm|unlink|shred))|bw[[:space:]].*export|unlock|\\.claude|(^|[;&|(){[:cntrl:]])[[:space:]]*\\$[{A-Za-z_]|CLAUDE(\\.local)?\\.md|firme/|rilasci\\.allowed_signers|aggiornamenti\\.py|aggiorna-applica\\.sh|arturo/radice|\\.git/hooks|LaunchAgents|\\.config/(systemd/user|autostart)|Start[[:space:]]+Menu|profile\\.ps1|schtasks|(^|[^[:alnum:]_.-])reg(\\.exe)?[[:space:]]+(add|import|restore|load)|(^|[^[:alnum:]_.-])sc(\\.exe)?[[:space:]]+create|Register-ScheduledTask|New-Service|\\.ssh([/[:space:]\\"\';&|)]|$)|id_(rsa|ed25519|ecdsa|dsa)|\\.aws([/[:space:]\\"\';&|)]|$)|\\.gnupg([/[:space:]\\"\';&|)]|$)|\\.secrets([/[:space:]\\"\';&|)]|$)|\\.netrc|security[[:space:]]+(find-(generic|internet)-password|dump-keychain)|\\.[^[:space:]/]*[]*?[][^[:space:]/]*/|(^|[[:space:]/=:({,<])\\.[^[:space:]/]*[]*?[{}][^[:space:]/]*|\\.(config|docker|kube)/[^[:space:];&|]*[]*?[{]|dotglob|[Gg][Ll][Oo][Bb]_?[Dd][Oo][Tt][Ss]|\\.git-credentials|\\.pem|service-account|credentials\\.json|client_secret|token_cache|\\.pypirc|secrets\\.env|\\.secrets/|\\.config/gh/hosts|\\.npmrc|\\.docker/config|\\.kube/config|docker[[:space:]]+(volume[[:space:]]+rm|system[[:space:]]+prune)|(^|[^[:alnum:]_.-])sed[[:space:]]|\\.env([^[:alnum:]_]|$)|rmtree|rm(dir)?Sync|\\.rm[[:space:]]*\\(|[Rr]emove-[Ii]tem|(^|[^[:alnum:]_.-])(powershell|pwsh)(\\.exe)?[[:space:]]|-[a-zA-Z]*c[[:space:]]+\\$\\([[:space:]]*(curl|wget|fetch)|curl[[:space:]][^;&|]*(-[a-zA-Z]*[oOJ]|--output|--remote-name)[^;&|]*[;&[:cntrl:]]|wget[[:space:]][^;&|]*[;&[:cntrl:]]|base64[[:space:]][^|;&]*(-[a-zA-Z]*[dD]|--decode)|xxd[[:space:]][^|;&]*-[a-zA-Z]*r|openssl[[:space:]]+(enc|base64)|find[[:space:]].*-i?(name|path|wholename|regex)[[:space:]].*(-(exec|execdir|ok|okdir)[[:space:]]|xargs)|git[[:space:]]([^|;&]*[[:space:]])?credential(-[a-z]+)?[[:space:]]|git-credential|_history|\\.zhistory|remove_tree|FileUtils|rm_rf|(^|[^[:alnum:]_.-])(docker|podman|nerdctl)[[:space:]].*(-v|--volume|--mount)|(^|[^[:alnum:]_.-])(diskutil|newfs(_[a-z0-9]+)?)[[:space:]]': [
        ':\\(\\)',
        '/dev/(sd|nvme|disk|hd)',
        'chmod[ \\t\\n\\r\\f\\v]+-R[ \\t\\n\\r\\f\\v]+0*777',
        'chown[ \\t\\n\\r\\f\\v]+-R',
        '\\|&?[ \\t\\n\\r\\f\\v]*(#(?:(?!\\|&?[ \\t\\n\\r\\f\\v]*#).)*)?([\\(\\{][ \\t\\n\\r\\f\\v]*([^\\|]*[;\\&\\x00-\\x1f\\x7f][ \\t\\n\\r\\f\\v]*)?)?((sudo|doas)[ \\t\\n\\r\\f\\v][^\\|;\\&]*)?(bash|sh|zsh|fish|python3?|perl|ruby|node|php|powershell|pwsh)([^A-Za-z0-9_\\.\\-]|\\Z)',
        '<\\([ \\t\\n\\r\\f\\v]*(curl|wget|fetch)',
        'eval[ \\t\\n\\r\\f\\v]',
        'mkfs\\.',
        '(^|[^A-Za-z0-9_\\.\\-])(del|erase|rd|rmdir|format(\\.com)?)[ \\t\\n\\r\\f\\v]',
        'rm[ \\t\\n\\r\\f\\v](?:(?!rm[ \\t\\n\\r\\f\\v])[^\\|;\\&])*(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)',
        'find[ \\t\\n\\r\\f\\v](?:(?!find[ \\t\\n\\r\\f\\v]).)*(-delete|-(exec|execdir|ok|okdir)[ \\t\\n\\r\\f\\v](?:(?!-(exec|execdir|ok|okdir)[ \\t\\n\\r\\f\\v]).)*(rm|unlink|shred)|xargs(?:(?!xargs)[^\\|;\\&])*(rm|unlink|shred))',
        'bw[ \\t\\n\\r\\f\\v](?:(?!bw[ \\t\\n\\r\\f\\v]).)*export',
        'unlock',
        '\\.claude',
        '(^|[;\\&\\|\\(\\)\\{\\x00-\\x1f\\x7f])[ \\t\\n\\r\\f\\v]*\\$[\\{A-Za-z_]',
        'CLAUDE(\\.local)?\\.md',
        'firme/',
        'rilasci\\.allowed_signers',
        'aggiornamenti\\.py',
        'aggiorna-applica\\.sh',
        'arturo/radice',
        '\\.git/hooks',
        'LaunchAgents',
        '\\.config/(systemd/user|autostart)',
        'Start[ \\t\\n\\r\\f\\v]+Menu',
        'profile\\.ps1',
        'schtasks',
        '(^|[^A-Za-z0-9_\\.\\-])reg(\\.exe)?[ \\t\\n\\r\\f\\v]+(add|import|restore|load)',
        '(^|[^A-Za-z0-9_\\.\\-])sc(\\.exe)?[ \\t\\n\\r\\f\\v]+create',
        'Register-ScheduledTask',
        'New-Service',
        '\\.ssh([/ \\t\\n\\r\\f\\v\\\\"\';\\&\\|\\)]|\\Z)',
        'id_(rsa|ed25519|ecdsa|dsa)',
        '\\.aws([/ \\t\\n\\r\\f\\v\\\\"\';\\&\\|\\)]|\\Z)',
        '\\.gnupg([/ \\t\\n\\r\\f\\v\\\\"\';\\&\\|\\)]|\\Z)',
        '\\.secrets([/ \\t\\n\\r\\f\\v\\\\"\';\\&\\|\\)]|\\Z)',
        '\\.netrc',
        'security[ \\t\\n\\r\\f\\v]+(find-(generic|internet)-password|dump-keychain)',
        '\\.(?:(?!\\.)[^ \\t\\n\\r\\f\\v/])*[\\]\\*\\?\\[][^ \\t\\n\\r\\f\\v/]*/',
        '(^|[ \\t\\n\\r\\f\\v/=:\\(\\{,<])\\.(?:(?!(^|[ \\t\\n\\r\\f\\v/=:\\(\\{,<])\\.)[^ \\t\\n\\r\\f\\v/])*[\\]\\*\\?\\[\\{\\}][^ \\t\\n\\r\\f\\v/]*',
        '\\.(config|docker|kube)/(?:(?!\\.(config|docker|kube)/)[^ \\t\\n\\r\\f\\v;\\&\\|])*[\\]\\*\\?\\[\\{]',
        'dotglob',
        '[Gg][Ll][Oo][Bb]_?[Dd][Oo][Tt][Ss]',
        '\\.git-credentials',
        '\\.pem',
        'service-account',
        'credentials\\.json',
        'client_secret',
        'token_cache',
        '\\.pypirc',
        'secrets\\.env',
        '\\.secrets/',
        '\\.config/gh/hosts',
        '\\.npmrc',
        '\\.docker/config',
        '\\.kube/config',
        'docker[ \\t\\n\\r\\f\\v]+(volume[ \\t\\n\\r\\f\\v]+rm|system[ \\t\\n\\r\\f\\v]+prune)',
        '(^|[^A-Za-z0-9_\\.\\-])sed[ \\t\\n\\r\\f\\v]',
        '\\.env([^A-Za-z0-9_]|\\Z)',
        'rmtree',
        'rm(dir)?Sync',
        '\\.rm[ \\t\\n\\r\\f\\v]*\\(',
        '[Rr]emove-[Ii]tem',
        '(^|[^A-Za-z0-9_\\.\\-])(powershell|pwsh)(\\.exe)?[ \\t\\n\\r\\f\\v]',
        '-[a-zA-Z]*c[ \\t\\n\\r\\f\\v]+\\$\\([ \\t\\n\\r\\f\\v]*(curl|wget|fetch)',
        'curl[ \\t\\n\\r\\f\\v](?:(?!curl[ \\t\\n\\r\\f\\v])[^;&|])*(-[a-zA-Z]*[oOJ]|--output|--remote-name)[^;&|\\x00-\\x1f\\x7f]*[;&\\x00-\\x1f\\x7f]',
        'wget[ \\t\\n\\r\\f\\v](?:(?!wget )[^;&|\\x00-\\x1f\\x7f])*[;&\\x00-\\x1f\\x7f]',
        'base64[ \\t\\n\\r\\f\\v](?:(?!base64[ \\t\\n\\r\\f\\v])[^\\|;\\&])*(-[a-zA-Z]*[dD]|--decode)',
        'xxd[ \\t\\n\\r\\f\\v](?:(?!xxd[ \\t\\n\\r\\f\\v])[^\\|;\\&])*-[a-zA-Z]*r',
        'openssl[ \\t\\n\\r\\f\\v]+(enc|base64)',
        'find[ \\t\\n\\r\\f\\v](?:(?!find[ \\t\\n\\r\\f\\v]).)*-i?(name|path|wholename|regex)[ \\t\\n\\r\\f\\v](?:(?!-i?(name|path|wholename|regex)[ \\t\\n\\r\\f\\v]).)*(-(exec|execdir|ok|okdir)[ \\t\\n\\r\\f\\v]|xargs)',
        'git[ \\t\\n\\r\\f\\v]((?:(?!git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?credential(-[a-z]+)?[ \\t\\n\\r\\f\\v]',
        'git-credential',
        '_history',
        '\\.zhistory',
        'remove_tree',
        'FileUtils',
        'rm_rf',
        '(^|[^A-Za-z0-9_\\.\\-])(docker|podman|nerdctl)[ \\t\\n\\r\\f\\v](?:(?!(^|[^A-Za-z0-9_\\.\\-])(docker|podman|nerdctl)[ \\t\\n\\r\\f\\v]).)*(-v|--volume|--mount)',
        '(^|[^A-Za-z0-9_\\.\\-])(diskutil|newfs(_[a-z0-9]+)?)[ \\t\\n\\r\\f\\v]',
    ],
    # PATTERN_DATA
    'L:[Rr][Oo][Bb][Oo][Cc][Oo][Pp][Yy][^|&;]*[[:space:]]["\']?/+([Mm][Ii][Rr]|[Pp][Uu][Rr][Gg][Ee])|(^|[^[:alnum:]_.-])[Rr][Ee][Gg][[:space:]]+[Dd][Ee][Ll][Ee][Tt][Ee]|[Dd][Rr][Oo][Pp][[:space:]]+([Tt][Aa][Bb][Ll][Ee]|[Dd][Aa][Tt][Aa][Bb][Aa][Ss][Ee]|[Ss][Cc][Hh][Ee][Mm][Aa])|[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]|[Dd][Ee][Ll][Ee][Tt][Ee][[:space:]]+[Ff][Rr][Oo][Mm]|docker([[:space:]]+compose|-compose)[^|&;]*[[:space:]]down[^|&;]*(-v|--volumes)|rsync[^|&;]*--del(ete)?([^[:alnum:]_]|$)|>[[:space:]]*[^>[:space:]|&;]*\\.(db|sqlite|sqlite3|sql|dump)': [
        '[Rr][Oo][Bb][Oo][Cc][Oo][Pp][Yy](?:(?![Rr][Oo][Bb][Oo][Cc][Oo][Pp][Yy])[^\\|\\&;])*[ \\t\\n\\r\\f\\v]["\']?/+([Mm][Ii][Rr]|[Pp][Uu][Rr][Gg][Ee])',
        '(^|[^A-Za-z0-9_\\.\\-])[Rr][Ee][Gg][ \\t\\n\\r\\f\\v]+[Dd][Ee][Ll][Ee][Tt][Ee]',
        '[Dd][Rr][Oo][Pp][ \\t\\n\\r\\f\\v]+([Tt][Aa][Bb][Ll][Ee]|[Dd][Aa][Tt][Aa][Bb][Aa][Ss][Ee]|[Ss][Cc][Hh][Ee][Mm][Aa])',
        '[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]',
        '[Dd][Ee][Ll][Ee][Tt][Ee][ \\t\\n\\r\\f\\v]+[Ff][Rr][Oo][Mm]',
        'docker([ \\t\\n\\r\\f\\v]+compose|-compose)(?:(?!docker([ \\t\\n\\r\\f\\v]+compose|-compose))[^\\|\\&;])*[ \\t\\n\\r\\f\\v]down(?:(?![ \\t\\n\\r\\f\\v]down)[^\\|\\&;])*(-v|--volumes)',
        'rsync(?:(?!rsync)[^\\|\\&;])*--del(ete)?([^A-Za-z0-9_]|\\Z)',
        '>[ \\t\\n\\r\\f\\v]*(?:(?!>[ \\t\\n\\r\\f\\v]*)[^> \\t\\n\\r\\f\\v\\|\\&;])*\\.(db|sqlite|sqlite3|sql|dump)',
    ],
    # PATTERN_DEV_TCP
    'E:[<>]&?[[:space:]]*/dev/(tcp|udp)/': [
        '[<>]&?[ \\t\\n\\r\\f\\v]*/dev/(tcp|udp)/',
    ],
    # PATTERN_EGRESS_SOSPETTO
    'E:(^|[^[:alnum:]_.-])(nc|ncat|netcat|socat)([[:space:]]|$)|/dev/(tcp|udp)/': [
        '(^|[^A-Za-z0-9_\\.\\-])(nc|ncat|netcat|socat)([ \\t\\n\\r\\f\\v]|\\Z)',
        '/dev/(tcp|udp)/',
    ],
    # PATTERN_EXFIL
    'L:([cC][uU][rR][lL]|[wW][gG][eE][tT])([^|;&]|&[^[:space:]&|;])*(-[[:alnum:]]*F([[:space:]]|["\'],[[:space:]]*["\']?)*[^[:space:]]*[@<]|--form([[:space:]]|["\'],[[:space:]]*["\']?)*[^[:space:]]*[@<]|-[[:alnum:]]*T([[:space:]]|["\'],[[:space:]]*["\']?)|-[[:alnum:]]*T[^[:space:]]|--data-urlencode([[:space:]]|["\'],[[:space:]]*["\']?)*["\']?[^[:space:]=@"\']*@|--upload-file|--(post|body)-file|-[[:alnum:]]*d([[:space:]]|["\'],[[:space:]]*["\']?)*["\']?@|--data[a-z-]*([[:space:]]|["\'],[[:space:]]*["\']?)*["\']?@|--json([[:space:]]|["\'],[[:space:]]*["\']?)*["\']?@|--url-query([[:space:]]|["\'],[[:space:]]*["\']?)*["\']?@)': [
        '([cC][uU][rR][lL]|[wW][gG][eE][tT])(?:(?![cC][uU][rR][lL]|[wW][gG][eE][tT])([^\\|;\\&]|&[^ \\t\\n\\r\\f\\v\\&\\|;]))*(-[A-Za-z0-9]*F([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)*[^ \\t\\n\\r\\f\\v]*[@<]|--form([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)*[^ \\t\\n\\r\\f\\v]*[@<]|-[A-Za-z0-9]*T([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)|-[A-Za-z0-9]*T[^ \\t\\n\\r\\f\\v]|--data-urlencode([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)*["\']?[^ \\t\\n\\r\\f\\v=@"\']*@|--upload-file|--(post|body)-file|-[A-Za-z0-9]*d([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)*["\']?@|--data[a-z\\-]*([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)*["\']?@|--json([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)*["\']?@|--url-query([ \\t\\n\\r\\f\\v]|["\'],[ \\t\\n\\r\\f\\v]*["\']?)*["\']?@)',
    ],
    # PATTERN_GH_ANY
    'E:(^|[^[:alnum:]_.-])gh[[:space:]]': [
        '(^|[^A-Za-z0-9_\\.\\-])gh[ \\t\\n\\r\\f\\v]',
    ],
    # PATTERN_GIT_ALTRI
    'L:(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?(config|reset|checkout|restore|credential(-[a-z]+)?)([[:space:]]|$)|(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?(-c[[:space:]]|--config-env)': [
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v]((?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?(config|reset|checkout|restore|credential(-[a-z]+)?)([ \\t\\n\\r\\f\\v]|\\Z)',
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v]((?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?(-c[ \\t\\n\\r\\f\\v]|--config-env)',
    ],
    # PATTERN_GIT_AMEND
    'L:(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?commit[[:space:]]([^|;&]*[[:space:]])?--am': [
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v]((?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?commit[ \\t\\n\\r\\f\\v]((?:(?![ \\t\\n\\r\\f\\v]commit[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?--am',
    ],
    # PATTERN_GIT_CLEAN
    'L:(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?clean[[:space:]]([^|;&]*[[:space:]])?(-[[:alpha:]]*f|--f)|(^|[^[:alnum:]_.-])git[[:space:]][^|;&]*[cC]lean\\.[rR]equire[fF]orce': [
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v]((?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?clean[ \\t\\n\\r\\f\\v]((?:(?![ \\t\\n\\r\\f\\v]clean[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?(-[A-Za-z]*f|--f)',
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v](?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[cC]lean\\.[rR]equire[fF]orce',
    ],
    # PATTERN_GIT_DEST
    'L:(^|[^[:alnum:]_.-])git[[:space:]][^|;&]*(-c|--config-env)[^|;&]*[[:space:]]push|GIT_CONFIG_(COUNT|KEY_[0-9]+|PARAMETERS)=': [
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v](?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*(-c|--config-env)(?:(?!(-c|--config-env))[^\\|;\\&])*[ \\t\\n\\r\\f\\v]push',
        'GIT_CONFIG_(COUNT|KEY_[0-9]+|PARAMETERS)=',
    ],
    # PATTERN_GIT_INVIA
    'E:send-email|imap-send': [
        'send-email',
        'imap-send',
    ],
    # PATTERN_GIT_OPZIONI
    'E:(^|[[:space:]])(--output|--exec-path|--config-env|--no-index|-c[[:space:]])|(^|[^>])>>?[^&|;]': [
        '(^|[ \\t\\n\\r\\f\\v])(--output|--exec-path|--config-env|--no-index|-c[ \\t\\n\\r\\f\\v])',
        '(^|[^>])>>?[^\\&\\|;]',
    ],
    # PATTERN_GIT_PERDE
    'L:(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?(branch[[:space:]]([^|;&]*[[:space:]])?(-[[:alpha:]]*D|--d|-[[:alpha:]]*d)|stash[[:space:]]+(drop|clear)|worktree[[:space:]]+remove)': [
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v]((?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?(branch[ \\t\\n\\r\\f\\v]((?:(?![ \\t\\n\\r\\f\\v]branch[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?(-[A-Za-z]*D|--d|-[A-Za-z]*d)|stash[ \\t\\n\\r\\f\\v]+(drop|clear)|worktree[ \\t\\n\\r\\f\\v]+remove)',
    ],
    # PATTERN_GIT_PUSH
    'L:(^|[^[:alnum:]_.-])git[[:space:]]([^|;&]*[[:space:]])?push([[:space:]]|$)': [
        '(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v]((?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^\\|;\\&])*[ \\t\\n\\r\\f\\v])?push([ \\t\\n\\r\\f\\v]|\\Z)',
    ],
    # PATTERN_GIT_TEXT
    'E:(^|[;&|][[:space:]]*)git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?(commit|log|show|tag|stash[[:space:]]+(push|save))': [
        '(^|[;\\&\\|][ \\t\\n\\r\\f\\v]*)git[ \\t\\n\\r\\f\\v]+(-C[ \\t\\n\\r\\f\\v]+[^ \\t\\n\\r\\f\\v]+[ \\t\\n\\r\\f\\v]+)?(commit|log|show|tag|stash[ \\t\\n\\r\\f\\v]+(push|save))',
    ],
    # PATTERN_NASCOSTO
    'E:\\$[({A-Za-z_]|`|(^|[^[:alnum:]_.-])(g?xargs|alias|python[0-9.]*|perl|ruby|node|nodejs|php|deno|bun|osascript|sh|bash|zsh|dash|ksh|fish|pwsh|powershell)(\\.exe)?([^[:alnum:]_.-]|$)|[[:alnum:]_][[:space:]]*\\([[:space:]]*\\)': [
        '\\$[\\(\\{A-Za-z_]',
        '`',
        '(^|[^A-Za-z0-9_\\.\\-])(g?xargs|alias|python[0-9\\.]*|perl|ruby|node|nodejs|php|deno|bun|osascript|sh|bash|zsh|dash|ksh|fish|pwsh|powershell)(\\.exe)?([^A-Za-z0-9_\\.\\-]|\\Z)',
        '[A-Za-z0-9_][ \\t\\n\\r\\f\\v]*\\([ \\t\\n\\r\\f\\v]*\\)',
    ],
    # PATTERN_PAROLA_PERICOLOSA
    'E:(^|[^[:alnum:]_.$-])(rm|unlink|shred|push|reset|clean|curl|wget|bw|gh)([^[:alnum:]_-]|$)': [
        '(^|[^A-Za-z0-9_\\.\\$\\-])(rm|unlink|shred|push|reset|clean|curl|wget|bw|gh)([^A-Za-z0-9_\\-]|\\Z)',
    ],
    # PATTERN_REMOTE
    'E:(^|[[:space:];&|(])(ssh|docker[[:space:]]+exec|kubectl[[:space:]]+exec)[[:space:]]|<<': [
        '(^|[ \\t\\n\\r\\f\\v;\\&\\|\\(])(ssh|docker[ \\t\\n\\r\\f\\v]+exec|kubectl[ \\t\\n\\r\\f\\v]+exec)[ \\t\\n\\r\\f\\v]',
        '<<',
    ],
    # PATTERN_SCRIVE
    'L:(^|[^-0-9&>])[0-9]?>[>|]?[[:space:]]*[^&>([:space:]]|&>|(^|[^[:alnum:]_.-])(cp|mv|tee|dd|install|ln|rsync|touch|truncate|sponge|tar|gtar|bsdtar|unzip|patch|gpatch|ditto|chmod|chown|chgrp)([[:space:]]|$)|(^|[^[:alnum:]_.-])git([[:space:]][^;&|]*)?[[:space:]](checkout|restore|reset)([[:space:]]|$)': [
        '(^|[^\\-0-9\\&>])[0-9]?>[>\\|]?[ \\t\\n\\r\\f\\v]*[^\\&>\\( \\t\\n\\r\\f\\v]',
        '&>',
        '(^|[^A-Za-z0-9_\\.\\-])(cp|mv|tee|dd|install|ln|rsync|touch|truncate|sponge|tar|gtar|bsdtar|unzip|patch|gpatch|ditto|chmod|chown|chgrp)([ \\t\\n\\r\\f\\v]|\\Z)',
        '(^|[^A-Za-z0-9_\\.\\-])git([ \\t\\n\\r\\f\\v](?:(?!(^|[^A-Za-z0-9_\\.\\-])git[ \\t\\n\\r\\f\\v])[^;\\&\\|])*)?[ \\t\\n\\r\\f\\v](checkout|restore|reset)([ \\t\\n\\r\\f\\v]|\\Z)',
    ],
    # PATTERN_SUBST
    'E:\\$\\(|`|<\\(|>\\(': [
        '\\$\\(',
        '`',
        '<\\(',
        '>\\(',
    ],
    # PATTERN_TIMEOUT
    'E:(^|[;&|(`\n])[[:space:]]*((sudo|env|command|exec)[[:space:]]+)?timeout[[:space:]]+(-[^[:space:]]+[[:space:]]+([A-Z]+[[:space:]]+)?)*[0-9]': [
        '(^|[;\\&\\|\\(`\\\n])[ \\t\\n\\r\\f\\v]*((sudo|env|command|exec)[ \\t\\n\\r\\f\\v]+)?timeout[ \\t\\n\\r\\f\\v]+(-[^ \\t\\n\\r\\f\\v]+[ \\t\\n\\r\\f\\v]+([A-Z]+[ \\t\\n\\r\\f\\v]+)?)*[0-9]',
    ],
    # RE_CWD_CLAUDE
    'E:"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\\\]\\.claude': [
        '"cwd"[ \\t\\n\\r\\f\\v]*:[ \\t\\n\\r\\f\\v]*"[^"]*[/\\\\\\\\]\\.claude',
    ],
    # RE_CWD_GIT
    'E:"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\\\]\\.git(["/\\\\])': [
        '"cwd"[ \\t\\n\\r\\f\\v]*:[ \\t\\n\\r\\f\\v]*"[^"]*[/\\\\\\\\]\\.git(["/\\\\\\\\])',
    ],
    # RE_CWD_SEGRETI
    'E:"cwd"[[:space:]]*:[[:space:]]*"[^"]*[/\\\\]\\.(ssh|aws|gnupg|secrets)(["/\\\\])': [
        '"cwd"[ \\t\\n\\r\\f\\v]*:[ \\t\\n\\r\\f\\v]*"[^"]*[/\\\\\\\\]\\.(ssh|aws|gnupg|secrets)(["/\\\\\\\\])',
    ],
    # _p
    'E:(^|[^[:alnum:]_.$-])(rm|unlink|shred|push|reset|clean|curl|wget|bw|gh)([^[:alnum:]_-]|$)': [
        '(^|[^A-Za-z0-9_\\.\\$\\-])(rm|unlink|shred|push|reset|clean|curl|wget|bw|gh)([^A-Za-z0-9_\\-]|\\Z)',
    ],
}
