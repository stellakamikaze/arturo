"""Le cinque pagine di ricerca. Ogni affermazione tecnica ha la sua fonte nel commento accanto."""
from base import voce

GH = "https://github.com/stellakamikaze/arturo"
GH_FILE = GH + "/blob/main/"
DOCS_IT = "https://code.claude.com/docs/it/overview"


def messaggio(esito, testo, didascalia, blocca=False):
    classe = "messaggio messaggio--blocca" if blocca else "messaggio"
    return f"""          <figure class="{classe}">
            <div class="messaggio__finestra">
              <p class="messaggio__barra">Messaggio della guardia</p>
              <div class="messaggio__esito"><b>{esito}</b><p>{testo}</p></div>
            </div>
            <figcaption>{didascalia}</figcaption>
          </figure>"""


# ---------------------------------------------------------------------------------------------
# 1. Claude Code in italiano
# ---------------------------------------------------------------------------------------------
P1 = {
    "slug": "claude-code-in-italiano",
    "lang": "it",
    "title": "Claude Code in italiano: guida per chi non programma · Arturo",
    "desc": "Cos'è Claude Code, perché conviene configurarlo in italiano e cosa aggiunge Arturo, l'harness gratuito e open source per chi non programma.",
    "h1": "Claude Code in italiano",
    "briciola": "Claude Code in italiano",
    "lead": "Arturo è un harness per il lavoro della conoscenza, pensato per chi usa già l'intelligenza artificiale in chat e non ha mai aperto un terminale. Questa guida spiega che cos'è Claude Code e che cosa cambia quando lo configuri in italiano, con le regole e i comandi che Arturo aggiunge, come /inizio e /fine.",
    "indice": [("cos-e", "Cos'è Claude Code"), ("perche", "Perché configurarlo in italiano"),
               ("cosa-aggiunge", "Cosa aggiunge Arturo"), ("serve", "Cosa ti serve, e cosa resta uguale"),
               ("domande", "Domande")],
}
P1["main"] = '\n<section class="sezione">\n  <div class="dentro">\n    <div class="voci">' + \
    voce("cos-e", "Cos'è Claude Code", f"""          <p class="voce__attacco">Claude Code è l'IA di Anthropic che lavora sui file del tuo computer: legge e scrive i documenti, cerca sul web, esegue i passi che gli chiedi e riprende il lavoro dal punto in cui l'avevi lasciato.</p>
          <p>La <a href="{DOCS_IT}">documentazione ufficiale</a> lo presenta come uno strumento per chi scrive codice, perché legge un progetto, modifica i file ed esegue comandi. Le stesse capacità servono a chi lavora con le parole e con le informazioni, dato che un capitolo o una cartella di appunti sono file come gli altri. In chat incolli un testo e ricevi una risposta da copiare altrove. In Claude Code chiedi di rileggere quel capitolo o di preparare la bozza di una email, e Claude apre i file, li legge e scrive il risultato dove serve.</p>
          <p>Claude Code gira nel terminale, la finestra dove si scrivono i comandi al computer, e Anthropic lo offre anche come app desktop, nelle estensioni per gli editor di codice e nel browser. Per usarlo serve un abbonamento a pagamento: Pro, Max, Team, Enterprise oppure la Console di Anthropic. Il piano gratuito di claude.ai non lo include.</p>""") + \
    voce("perche", "Perché configurarlo in italiano", """          <p class="voce__attacco">Claude ti risponde in italiano se gli scrivi in italiano, e la documentazione di Anthropic ha una versione italiana. Le impostazioni, gli avvisi di permesso e le istruzioni di partenza, invece, sono pensati per chi programma.</p>
          <p>Claude Code legge da un file di impostazioni che cosa può fare senza chiederti niente, e da un file chiamato <code>CLAUDE.md</code> le istruzioni con cui comincia ogni sessione. Chi arriva dalla chat di solito non sa che questi file esistono, quindi non li scrive e lavora con le impostazioni di partenza, che decidono al posto suo che cosa chiedere e che cosa no.</p>
          <p>Una configurazione in italiano fa queste scelte per te e te le spiega nella tua lingua. In Arturo l'impostazione <code>language</code> di Claude Code vale <code>italian</code>, i messaggi delle guardie che ti chiedono conferma sono scritti in italiano e i comandi hanno nomi come <code>/inizio</code>, <code>/fine</code> e <code>/diagnosi</code>. Quando una guardia ti ferma, quindi, leggi subito che cosa sta per succedere e che cosa perdi se confermi, senza dover decifrare un avviso tecnico.</p>""") + \
    voce("cosa-aggiunge", "Cosa aggiunge Arturo", f"""          <p class="voce__attacco">Arturo è un harness per Claude Code, cioè l'insieme di regole, comandi e automazioni che gli sta attorno e ne guida il lavoro. È gratuito e open source, con licenza MIT.</p>
          <p>Nasce dalla configurazione con cui Federico Nejrotti lavora ogni giorno in Claude Code, ripulita dai suoi dati, dalle credenziali e dai riferimenti alle sue macchine. Il <a href="{GH}">README del progetto</a> conta 23 guardie e automazioni, 11 slash command, 8 subagent e 7 skill: gli slash command sono i comandi che si scrivono con la barra davanti, i subagent sono assistenti che Claude manda a fare un compito a parte, le skill sono istruzioni che Claude carica quando gli serve un certo lavoro. Per chi non programma pesano soprattutto tre parti.</p>
          <ul class="puntata">
            <li><strong>Le guardie</strong>: prima di un gesto che non si annulla, come cancellare una cartella, mandare un messaggio o mettere una password in un commit, Arturo ferma Claude e chiede a te. La pagina <a href="../claude-code-sicurezza/">Claude Code in sicurezza</a> le racconta una per una, con i loro messaggi.</li>
            <li><strong>Le sessioni in ordine</strong>: <code>/inizio</code> riprende il contesto di un progetto, i todo aperti e le scadenze, mentre <code>/fine</code> salva il lavoro e lascia un appunto per la volta dopo, con quello che resta da fare e chi lo deve fare. Il giorno dopo non rispieghi tutto da capo.</li>
            <li><strong>Un CLAUDE.md sul tuo lavoro</strong>: <code>/setup</code> controlla i programmi e poi, se gli dici sì, legge le tue conversazioni passate con Claude Code e guarda le tue cartelle di lavoro. Da lì scrive la bozza del tuo <code>CLAUDE.md</code>, e la salva solo dopo il tuo ok.</li>
          </ul>
          <p>Accanto ci sono un curriculum di principi in italiano (<code>docs/principi/</code>), che spiega come lavorare con un'IA che agisce sui tuoi file, e <code>/novita</code>, che a ogni aggiornamento racconta che cosa è cambiato e perché.</p>""") + \
    voce("serve", "Cosa ti serve, e cosa resta uguale", """          <p class="voce__attacco">Ti servono un Mac, un PC Windows o un computer Linux, e un abbonamento Anthropic che includa Claude Code.</p>
          <p>Gli altri programmi che usa Arturo, cioè git, Python 3.8 o successivo e node 18 o successivo, li controlla Claude e li installa col tuo sì. Su Windows Arturo lavora dentro Git Bash, la finestra dei comandi che arriva con Git: senza, Claude Code esegue i comandi con PowerShell e le guardie non li vedono.</p>
          <p>Alcune cose Arturo non le cambia, e conviene saperle prima. Claude Code è un servizio a pagamento di un'azienda privata, che ne decide prezzi e limiti. Quello che scrivi passa dai server di Anthropic, come in chat: le guardie chiedono conferma prima che Claude legga un file segreto, ma non filtrano quello che scrivi tu. Un aggiornamento di Arturo è codice scritto da altri che gira sul tuo computer, e per questo Arturo installa da solo soltanto i rilasci firmati da chi lo mantiene. Infine Arturo manda a chi lo mantiene dati d'uso da un elenco chiuso, accesi di default: il <a href="../confronto/#limiti">confronto con Claude Code da solo</a> dice che cosa esce e come si spengono.</p>""") + \
    "    </div>\n  </div>\n</section>\n"
P1["faq"] = [
    ("Claude Code parla italiano?",
     "Sì. Claude risponde nella lingua in cui gli scrivi, e la documentazione di Anthropic ha una versione italiana. Arturo aggiunge l'impostazione della lingua, i messaggi delle guardie, i comandi e un curriculum scritti in italiano."),
    ("Serve saper programmare per usare Claude Code?",
     "No. Con Arturo il terminale serve per installare Claude Code e per aprirlo scrivendo <code>claude</code>. Il resto lo chiedi a Claude a parole, e prima dei passi che non si annullano ti chiede un sì."),
    ("Arturo costa qualcosa?",
     "Arturo è gratuito e open source, con licenza MIT. Claude Code invece richiede un abbonamento Anthropic a pagamento: Pro, Max, Team, Enterprise o Console."),
    ("Arturo esiste in inglese?",
     "No. Uno degli impegni del progetto è che Arturo resta in italiano: comandi, messaggi e documenti sono scritti in italiano. C'è soltanto una <a href=\"../en/\" hreflang=\"en\">pagina di presentazione in inglese</a>."),
]


# ---------------------------------------------------------------------------------------------
# 2. Claude Code senza terminale
# ---------------------------------------------------------------------------------------------
P2 = {
    "slug": "claude-code-senza-terminale",
    "lang": "it",
    "title": "Usare Claude Code senza saper usare il terminale · Arturo",
    "desc": "Quanto terminale serve davvero per usare Claude Code: installarlo, incollare un link, scrivere claude. Il resto lo fa Claude, e prima ti chiede un sì.",
    "h1": "Usare Claude Code senza saper usare il terminale",
    "briciola": "Claude Code senza terminale",
    "lead": "Claude Code vive nel terminale, ma i comandi li scrive Claude. A te resta qualche riga da incollare il primo giorno, e un sì da dare prima dei passi che cambiano il computer.",
    "indice": [("perche", "Perché il terminale, anche se non scrivi codice"), ("terminale", "Cos'è il terminale"), ("quanto", "Quanto terminale serve davvero"),
               ("cosa-fa", "Cosa fa Claude al posto tuo"), ("dove-chiede", "Dove ti chiede un sì"),
               ("inceppa", "Se qualcosa si inceppa"), ("domande", "Domande")],
}
P2["main"] = '\n<section class="sezione">\n  <div class="dentro">\n    <div class="voci">' + \
    voce("perche", "Perché il terminale, anche se non scrivi codice", """
          <p>Faccio l'autore, non il programmatore, e sono passato dalla chat al terminale per due motivi. In chat il materiale lo raccoglievo io: aprivo i file, copiavo i pezzi che servivano, li incollavo nella conversazione e alla fine riportavo la risposta in un documento. In Claude Code l'IA lavora dentro le mie cartelle, quindi va a prendere da sola appunti, trascrizioni e fogli di calcolo, li mette a confronto e scrive il risultato in un file. L'altro motivo è la durata: quando chiudo la sessione, Arturo lascia un riepilogo con le cose da fare, e la mattina dopo il lavoro riparte da lì invece che da una conversazione nuova.</p>
          <p>Anthropic ha visto lo stesso uso crescere nelle sessioni di Claude Code. Fra ottobre 2025 e aprile 2026 la scrittura e l'analisi dei dati sono passate da circa il 10 al 20% delle sessioni, e chi non lavora nel software arriva a un risultato verificato nel 26% delle sessioni, contro il 30% di chi ci lavora. La distanza è di quattro punti, e secondo la ricerca conta più conoscere il proprio mestiere che saper programmare. La <a href="https://www.anthropic.com/research/claude-code-expertise">ricerca</a> conclude che quello che succede su Claude Code può essere un'anteprima di dove va il lavoro della conoscenza. Due persone che non lavorano per Anthropic arrivano a una conclusione vicina. Simon Willison, programmatore indipendente che da anni scrive di questi strumenti, ha scritto che Claude Code <a href="https://simonwillison.net/2025/Oct/16/claude-skills/">ha un nome sbagliato</a>, perché serve ad automatizzare il computer in generale e non solo a scrivere codice. Ethan Mollick, che alla Wharton studia l'IA nel lavoro, indica <a href="https://www.oneusefulthing.org/p/claude-code-and-what-comes-next">la stessa ragione</a> che ho trovato io: Claude Code è potente perché lavora sul tuo computer e sui tuoi file, e serve a chi fa lavoro della conoscenza di ogni tipo, anche se oggi è costruito per i programmatori. Per questo ho costruito Arturo, che prepara Claude Code per chi non programma.</p>
          <p>Le prove indipendenti però mostrano anche dove l'IA sbaglia. In un <a href="https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged">esperimento</a> del 2023 di Harvard e Boston Consulting Group su 758 consulenti, chi usava GPT-4 su compiti alla portata dell'IA ne finiva il 12,2% in più, il 25,1% più in fretta e con una qualità più alta del 40%; su un compito costruito per sfuggirle, invece, chi usava l'IA dava la risposta giusta fra il 60 e il 70% delle volte, contro l'84% di chi lavorava senza. Uno <a href="https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/">studio</a> di Microsoft Research su 319 persone che fanno lavoro della conoscenza ha trovato che chi si fida di più dell'IA dichiara di esercitare meno il pensiero critico. E Willison avverte che un agente che legge i tuoi dati, incontra testi scritti da altri e può comunicare all'esterno <a href="https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/">può essere usato per rubarli</a>, perché quei testi possono contenere istruzioni che l'agente esegue come se venissero da te.</p>
          <p>A questi rischi Arturo risponde in due modi diversi. Contro il furto dei dati ha regole che chiedono un sì prima di ogni gesto che non si annulla, come cancellare una cartella o mandare un messaggio; la stessa conferma per le pagine web che portano fuori un dato è ancora in lavorazione. Contro una risposta sbagliata accettata per fiducia non basta una regola: il risultato lo controlla chi lavora, ed è per questo che conta conoscere il proprio mestiere, come dice anche la ricerca di Anthropic.</p>""") + \
    voce("terminale", "Cos'è il terminale", """          <p class="voce__attacco">Il terminale è la finestra dove si danno ordini al computer scrivendo invece di cliccare: su Mac si chiama Terminale, su Windows PowerShell.</p>
          <p>Claude Code lavora lì perché da quella finestra può fare quello che fai tu con mouse e tastiera, cioè aprire una cartella, leggere un file o lanciare un programma, e lo fa scrivendo comandi. Quei comandi però li scrive lui. Tu gli dici in italiano che cosa ti serve, Claude sceglie i comandi, ti mostra che cosa sta per fare e, nei passi delicati, aspetta la tua risposta. Per questo a chi usa Claude Code basta saper aprire la finestra e incollarci una riga.</p>
          <p>Anthropic offre Claude Code anche come app desktop e nel browser. Arturo si installa nella cartella <code>~/.claude</code> ed è scritto per Claude Code nel terminale: la guida e questa pagina parlano di quello.</p>""") + \
    voce("quanto", "Quanto terminale serve davvero", """          <p class="voce__attacco">Il primo giorno il terminale serve in quattro momenti, e dal giorno dopo per una parola sola.</p>
          <ol class="giorno">
            <li><div><p><strong>Installi Claude Code.</strong> Apri il Terminale su Mac (<kbd>Cmd</kbd> + <kbd>Spazio</kbd>, poi scrivi "Terminale") o PowerShell su Windows (il tasto <kbd>Windows</kbd>, poi "PowerShell") e incolli la riga di Anthropic. Per qualche minuto l'installazione non scrive niente, e va lasciata finire.</p>
              <p class="riga__nome">Su Mac, nel Terminale</p>
              <pre class="riga" tabindex="0">curl -fsSL https://claude.ai/install.sh | bash</pre>
              <p class="riga__nome">Su Windows, in PowerShell</p>
              <pre class="riga" tabindex="0">irm https://claude.ai/install.ps1 | iex</pre></div></li>
            <li><p><strong>Apri Claude Code.</strong> Scrivi <code>claude</code> e premi <kbd>Invio</kbd>. La prima volta si apre il browser per entrare nel tuo account Anthropic, poi Claude Code ti chiede se ti fidi della cartella.</p></li>
            <li><div><p><strong>Incolli la frase.</strong> Dentro Claude Code incolli questa frase. Da qui in avanti i comandi del lavoro li scrive Claude, e a te restano i tre del passo dopo.</p>
              <pre class="frase frase--chiara">Installa Arturo: https://<wbr>arturo.stellakamikaze.org/<wbr>inizia/</pre></div></li>
            <li><p><strong>Riparti con Arturo.</strong> Quando Claude ha finito scrivi <code>/exit</code>, poi <code>claude</code>, poi <code>/setup</code>, uno per volta e ognuno seguito da <kbd>Invio</kbd>.</p></li>
          </ol>
          <p>Dal giorno dopo apri il terminale, scrivi <code>claude</code> e poi <code>/inizio</code> con il nome del progetto. Se non hai mai aperto un terminale, la <a href="https://code.claude.com/docs/it/terminal-guide">guida al terminale</a> di Anthropic lo mostra con le immagini, e la <a href="../installa/">guida d'installazione di Arturo</a> ha ogni comando già scritto, per Mac e per Windows.</p>""") + \
    voce("cosa-fa", "Cosa fa Claude al posto tuo", """          <p class="voce__attacco">Quando incolli il link, Claude legge la pagina <code>/inizia/</code>, scritta apposta per lui, e ne segue i passi uno per volta.</p>
          <p>Scarica lo script di installazione di Arturo in un file e lo confronta con la copia pubblicata su GitHub, così una pagina manomessa non basta a farti installare altro. Se le due copie non coincidono si ferma e te lo dice; se coincidono te lo riassume in cinque righe e ti chiede il permesso di lanciarlo. Se manca un programma che serve ad Arturo, come git o Python, te lo dice e lo installa col tuo sì.</p>
          <p>La stessa pagina gli dà dei divieti precisi: non usare <code>sudo</code> e non chiedere la password di amministratore, non cambiare i permessi di Claude Code, non leggere password, chiavi o file <code>.env</code>, non aprire le tue cartelle durante l'installazione. Le cartelle le guarda più tardi <code>/setup</code>, e solo dopo che hai detto sì.</p>""") + \
    voce("dove-chiede", "Dove ti chiede un sì", """          <p class="voce__attacco">Claude si ferma e aspetta te in due situazioni: mentre installa, e quando sta per fare qualcosa che non si annulla.</p>
          <p>Durante l'installazione chiede il permesso di leggere il sito di Arturo, di lanciare lo script e di installare i programmi che mancano. Su Mac può aprirsi una finestra di Apple dove cliccare "Installa", su Windows una conferma di sistema dove cliccare "Sì". Poi <code>/setup</code> chiede un sì per leggere le tue conversazioni passate e un altro per guardare le cartelle di lavoro, e prima di salvare il tuo <code>CLAUDE.md</code> te ne mostra la bozza.</p>
          <p>Nel lavoro di tutti i giorni chiedono le <a href="../claude-code-sicurezza/">guardie di Arturo</a>: prima di cancellare una cartella, di mandare una email o un messaggio, di fare un commit con dentro qualcosa che somiglia a una password, di caricare un tuo file su un sito esterno. Il messaggio dice che cosa sta per succedere e che cosa perdi se confermi. Se invece è un permesso di Claude Code a bloccare un comando, Claude non cerca altre strade e ti propone una riga che comincia con <code>!</code>, da scrivere tu in Claude Code. In qualunque momento premi <kbd>Esc</kbd> e Claude si ferma.</p>""") + \
    voce("inceppa", "Se qualcosa si inceppa", """          <p>Scrivi <code>/diagnosi</code>: Claude controlla che Arturo regga, poi guarda lo stato del progetto e cerca il guasto con te prima di correggerlo. Con <code>/segnala</code> mandi a chi mantiene Arturo un problema o un'idea: la bozza la scrive Claude, tu la leggi e dici sì. Il <a href="../feedback/">modulo di feedback</a> del sito funziona anche senza Claude Code, con due righe e senza account.</p>""") + \
    "    </div>\n  </div>\n</section>\n"
P2["faq"] = [
    ("Devo imparare i comandi del terminale?",
     "No. Il primo giorno incolli la riga che installa Claude Code e scrivi <code>claude</code>, poi <code>/exit</code>, <code>claude</code> e <code>/setup</code>. Dal giorno dopo scrivi <code>claude</code> e <code>/inizio</code>. I comandi del lavoro li scrive Claude."),
    ("Claude Code può fare danni sul mio computer?",
     "Può cancellare o inviare quello che gli chiedi, come ogni programma che lavora sui file. Le guardie di Arturo lo fermano prima dei gesti che non si annullano, come cancellare una cartella o mandare un messaggio, e ti chiedono conferma. Per fermarlo in qualunque momento premi Esc."),
    ("Posso usare Claude Code nell'app desktop invece che nel terminale?",
     "Anthropic offre Claude Code anche come app desktop e nel browser. Arturo e la sua guida sono scritti per la versione da terminale, che si apre scrivendo <code>claude</code>."),
    ("Quanto tempo ci vuole?",
     "La guida d'installazione ha cinque passi, dal computer vuoto al primo lavoro, e il README di Arturo stima circa un'ora. Ogni comando è già scritto: lo copi e lo incolli."),
]


# ---------------------------------------------------------------------------------------------
# 3. Claude Code in sicurezza
# ---------------------------------------------------------------------------------------------
P3 = {
    "slug": "claude-code-sicurezza",
    "lang": "it",
    "title": "Claude Code in sicurezza: le guardie di Arturo",
    "desc": "Cosa controllano le guardie di Arturo per Claude Code: cancellazioni, invii, password nei commit, dati verso l'esterno. Con i messaggi veri e i limiti.",
    "h1": "Claude Code in sicurezza: le guardie di Arturo",
    "briciola": "Claude Code in sicurezza",
    "lead": "Claude Code lavora sui tuoi file con i tuoi permessi, quindi può cancellare, inviare e pubblicare. Le guardie di Arturo sono regole scritte nel codice che lo fermano prima dei gesti che non si annullano, e chiedono a te.",
    "indice": [("come", "Come funzionano"), ("cancellazioni", "Le cancellazioni"),
               ("segreti", "Password e chiavi"), ("invii", "Email, messaggi e dati che escono"),
               ("dati", "Database, GitHub e la configurazione"), ("limiti", "Cosa le guardie non fanno"),
               ("domande", "Domande")],
}
P3["main"] = '\n<section class="sezione">\n  <div class="dentro">\n    <div class="voci">' + \
    voce("come", "Come funzionano", "\n".join([
        """          <p class="voce__attacco">Claude Code ha già un suo sistema di permessi, e le guardie di Arturo si aggiungono sopra con un criterio diverso: regole fisse invece di un giudizio.</p>
          <p>Arturo fa partire Claude Code nella modalità auto, in cui un secondo modello di Anthropic, il classificatore, guarda ogni azione prima che parta e blocca quelle che giudica pericolose. È un giudizio, quindi può bloccare un'azione innocua o lasciarne passare una pericolosa. Le guardie invece sono programmi brevi, scritti in Python, che leggono il comando e lo confrontano con regole precise, e lo stesso comando riceve sempre la stessa risposta. Come funzionano i permessi di Claude Code lo spiega la <a href="https://code.claude.com/docs/it/security">documentazione di Anthropic sulla sicurezza</a>.</p>
          <p>Ogni comando passa da uno smistatore, <code>bash-dispatcher.sh</code>, che lo manda soltanto alle guardie che lo riguardano. Una guardia può lasciar passare, chiedere conferma o bloccare, e se si rompe la decisione diventa una richiesta di conferma, mai un via libera.</p>""",
        messaggio("Chiede a te", "Una guardia non ha prodotto una decisione valida. Conferma prima di eseguire il comando.",
                  f'Il messaggio dello smistatore quando una guardia non decide, da <a href="{GH_FILE}hooks/bash-dispatcher.sh">hooks/bash-dispatcher.sh</a>.'),
        """          <p>I messaggi di questa pagina sono quelli che le guardie scrivono davvero, copiati dal codice. Dove compaiono un percorso o il nome di un programma, sono un esempio.</p>"""])) + \
    voce("cancellazioni", "Le cancellazioni", "\n".join([
        """          <p class="voce__attacco">Dal terminale un file cancellato non passa dal cestino, e chi non programma tiene nelle cartelle capitoli, fatture e documenti che valgono quanto il codice.</p>
          <p>Per questo <code>block-dangerous.py</code> chiede conferma prima di ogni cancellazione ricorsiva, cioè di una cartella con tutto quello che contiene. La riconosce anche quando arriva da <code>find</code>, da <code>git clean -f</code> o da uno script Python, e la giudica sulla cartella vera, seguendo i cambi di cartella che la precedono. Tace soltanto sulle cartelle che si ricreano da sole, come <code>node_modules</code>, <code>dist</code> o <code>build</code>, e sui file temporanei.</p>""",
        messaggio("Chiede a te", "rm ricorsivo su una cartella (/Users/maria/Documents/capitoli). Dal terminale non passa dal cestino: se dentro c'è lavoro tuo, lo perdi. Conferma solo se vuoi davvero cancellarla.",
                  f'Da <a href="{GH_FILE}hooks/block-dangerous.py">hooks/block-dangerous.py</a>. Il percorso è un esempio.'),
        """          <p>Cancellare la radice del disco, la tua cartella utente o un disco intero è bloccato, senza domanda, e la guardia dice a Claude di non proporti di lanciarlo a mano.</p>"""])) + \
    voce("segreti", "Password e chiavi", "\n".join([
        """          <p class="voce__attacco">Una password finita in un commit e poi pubblicata non si ritira più: chi ha scaricato il repository la tiene.</p>
          <p><code>commit-secret-gate.py</code> legge le modifiche pronte per il commit prima di ogni <code>git commit</code> e di ogni <code>gh pr create</code>, e cerca le forme note di chiavi e credenziali, dalle chiavi private ai token di GitHub e alle chiavi delle API di Anthropic, Google e AWS. Se trova qualcosa chiede conferma. Se la scansione non riesce a partire te lo dice e spiega come ripararla, invece di lasciar passare il commit senza controllo.</p>""",
        messaggio("Chiede a te", "Possibile secret nel diff staged: GitHub token. Un leak pushato è irreversibile. Conferma solo dopo aver verificato che non sia una credenziale reale.",
                  f'Da <a href="{GH_FILE}hooks/commit-secret-gate.py">hooks/commit-secret-gate.py</a>. Il tipo di segreto è un esempio.'),
        """          <p><code>block-dangerous.py</code> chiede conferma anche prima che Claude legga da terminale un file segreto, come una chiave privata in <code>~/.ssh</code>, le credenziali in <code>~/.aws</code> o un file <code>.env</code>, perché il contenuto finirebbe nella conversazione. Se una chiave compare comunque nell'output di un comando, <code>credential-leak-scanner.py</code> avvisa Claude, e la parte del mod di Arturo chiamata <code>redazione-segreti</code> la sostituisce con la sua forma, cioè tipo, lunghezza e impronta, prima che Claude la legga.</p>"""])) + \
    voce("invii", "Email, messaggi e dati che escono", "\n".join([
        """          <p class="voce__attacco">Un'email o un messaggio inviati non si ritirano, e nemmeno un file caricato su un sito esterno.</p>
          <p>Per questo <code>comms-guard.py</code> chiede conferma prima di ogni invio di email o messaggi da riga di comando: <code>sendmail</code>, la CLI <code>gws</code> di Google, <code>smtplib</code> di Python, Mail e Messaggi via AppleScript e altri. La regola è la bozza prima: una bozza creata con un collegamento, come quello a Gmail, non chiede niente, perché è il momento in cui leggi il testo; l'invio sì.</p>""",
        messaggio("Chiede a te", "Questo comando invia una comunicazione esterna via AppleScript Mail/Messages. Bozza prima: conferma solo se hai già letto il testo e vuoi inviarlo così com'è.",
                  f'Da <a href="{GH_FILE}hooks/comms-guard.py">hooks/comms-guard.py</a>, per un invio con l\'app Mail.'),
        """          <p><code>exfil-guard.py</code> chiede conferma quando un comando carica un file del tuo computer su un indirizzo esterno con <code>curl</code> o <code>wget</code>, o manda dati attraverso <code>nc</code> o <code>/dev/tcp</code>. Leggere una pagina web non chiede: lo giudica il classificatore, che legge il codice. <code>web-egress-guard.py</code> chiede conferma quando Claude apre un indirizzo esterno che si porta dietro una coda di dati lunga e illeggibile, il modo di far uscire un'informazione dentro un link.</p>"""])) + \
    voce("dati", "Database, GitHub e la configurazione", """          <p><code>data-guard.py</code> chiede conferma prima delle operazioni che cancellano dati in blocco: <code>DROP</code> e <code>TRUNCATE</code> su un database, un <code>DELETE</code> senza <code>WHERE</code>, che svuota la tabella intera, <code>docker compose down -v</code> e <code>rsync --delete</code>.</p>
          <p><code>gh-destructive-guard.py</code> blocca l'eliminazione di un repository o di una release su GitHub e la modifica dei secret, e chiede conferma per il merge di una pull request o per l'avvio di un workflow. <code>block-dangerous.py</code> blocca anche gli script scaricati e lanciati al volo (<code>curl ... | bash</code>): per questo, quando installa Arturo, Claude scarica prima lo script in un file, lo confronta con GitHub e lo lancia col tuo sì.</p>
          <p>Le guardie proteggono anche sé stesse: <code>protect_claude_md.py</code> chiede conferma a ogni modifica di un <code>CLAUDE.md</code>, che cambierebbe le istruzioni delle sessioni future, e protegge le impostazioni e i file delle guardie, perché una modifica lì le potrebbe spegnere.</p>""") + \
    voce("limiti", "Cosa le guardie non fanno", f"""          <p class="voce__attacco">Le guardie fermano soltanto i gesti per cui esiste una regola, e ci sono cinque cose che non fanno.</p>
          <ul class="puntata">
            <li><strong>Leggono la forma dei comandi.</strong> Un gesto pericoloso scritto in una forma che nessuna regola riconosce passa al classificatore di Claude Code, che può fermarlo o no. Le regole si correggono di rilascio in rilascio, e lo raccontano <a href="../novita/">le novità</a>.</li>
            <li><strong>Non filtrano la conversazione.</strong> Quello che scrivi e quello che Claude legge passano comunque dai server di Anthropic.</li>
            <li><strong>Su Windows vedono soltanto Git Bash.</strong> Senza Git Bash, Claude Code esegue i comandi con PowerShell e le guardie non li vedono. Claude e <code>/setup</code> controllano che ci sia.</li>
            <li><strong>Si possono spegnere.</strong> <code>claude --safe-mode</code> apre Claude Code senza guardie, e una modifica ai loro file le può spegnere: all'avvio Arturo te lo segnala con una riga <code>DERIVA</code>.</li>
            <li><strong>Dopo il tuo sì non c'è un secondo controllo.</strong> Se confermi, il comando parte: il messaggio serve a farti decidere sapendo che cosa perdi.</li>
          </ul>""") + \
    "    </div>\n  </div>\n</section>\n"
P3["faq"] = [
    ("Le guardie rallentano Claude Code?",
     "Un comando innocuo non fa partire nessuna guardia, perché lo smistatore manda ogni comando solo alle guardie che lo riguardano. Le conferme arrivano soltanto prima dei gesti che non si annullano."),
    ("Posso spegnere una guardia?",
     "Sì. Una guardia che passa dallo smistatore si spegne commentando la sua riga in <code>hooks/bash-dispatcher.sh</code>, le altre togliendo il loro blocco da <code>settings.json</code>. All'avvio Arturo ti avvisa con una riga <code>DERIVA</code> quando una guardia è stata cambiata o tolta."),
    ("Con Arturo Claude Code è sicuro al cento per cento?",
     "No. Le guardie fermano i gesti che riconoscono, quello che scrivi passa comunque dai server di Anthropic, e su Windows le guardie funzionano soltanto dentro Git Bash."),
    ("Come segnalo un modo per aggirare una guardia?",
     f"In privato, seguendo <a href=\"{GH_FILE}SECURITY.md\">SECURITY.md</a> nel repository di Arturo, e non con una issue pubblica."),
]


# ---------------------------------------------------------------------------------------------
# 4. Confronto
# ---------------------------------------------------------------------------------------------
COLONNE = ("La chat", "Claude Code da solo", "Claude Code con Arturo")
RIGHE = [
    ("Dove lavora",
     "Nella conversazione: i file li carichi o li incolli tu, e il risultato lo copi dove serve.",
     "Nelle cartelle del tuo computer: legge e scrive i file ed esegue comandi.",
     "Come Claude Code, con regole, comandi e istruzioni già impostati in italiano."),
    ("Come si comincia",
     "Apri il sito o l'app ed entri nel tuo account.",
     "Una riga nel terminale per installarlo, poi l'accesso al tuo account Anthropic.",
     "Dopo Claude Code, una frase da incollare e <code>/setup</code>, che ti guida una cosa per volta."),
    ("Costo",
     "Claude e ChatGPT hanno anche un piano gratuito.",
     "Un abbonamento Anthropic a pagamento: Pro, Max, Team, Enterprise o Console.",
     "Arturo è gratuito, con licenza MIT. L'abbonamento a Claude Code serve lo stesso."),
    ("Lingua",
     "Risponde nella lingua in cui scrivi.",
     "Risponde nella lingua in cui scrivi, e la documentazione di Anthropic ha una versione italiana.",
     "Impostazione della lingua, comandi, messaggi delle guardie e curriculum in italiano. Solo in italiano."),
    ("Prima di un gesto che non si annulla",
     "Lavora dentro la conversazione: i tuoi file li tocchi tu.",
     "Dipende dalla modalità di permesso: in auto un classificatore di Anthropic giudica ogni azione, in manuale Claude chiede prima di modificare file ed eseguire comandi.",
     "In più le guardie, regole scritte nel codice che chiedono conferma prima di cancellazioni, invii e password nei commit, e bloccano i gesti più gravi."),
    ("Il giorno dopo",
     "Riapri la conversazione, o un progetto con i suoi documenti.",
     "Puoi riprendere una conversazione passata.",
     "<code>/fine</code> lascia un appunto con i todo e chi li deve fare, e <code>/inizio</code> lo rilegge prima di ripartire."),
    ("Aggiornamenti",
     "Li fa il fornitore, sui suoi server.",
     "L'installazione nativa di Anthropic si aggiorna da sola, in background.",
     "Arturo si aggiorna alla chiusura della sessione, solo con rilasci firmati da chi lo mantiene. Si può tornare al sì per ogni aggiornamento."),
    ("Dati d'uso",
     "Li regolano le condizioni del fornitore.",
     "Claude Code manda ad Anthropic la sua telemetria, che secondo Anthropic non contiene codice, percorsi dei file o comandi.",
     "In più, eventi da un elenco chiuso a chi mantiene Arturo, accesi di default, mai testi o file. Si spengono con un comando."),
    ("Sistemi",
     "Browser e app.",
     "macOS, Linux e Windows.",
     "macOS e Linux; su Windows dentro Git Bash."),
    ("Chi lo mantiene",
     "Un'azienda: Anthropic per Claude, OpenAI per ChatGPT.",
     "Anthropic.",
     "Una persona, Federico Nejrotti, senza promessa di risposta né di correzione."),
]


def tabella():
    testa = "".join(f'<th scope="col">{c}</th>' for c in COLONNE)
    righe = []
    for nome, *celle in RIGHE:
        td = "".join(f'<td data-colonna="{c}">{v}</td>' for c, v in zip(COLONNE, celle))
        righe.append(f'          <tr><th scope="row">{nome}</th>{td}</tr>')
    return f"""      <table class="confronto">
        <caption>La chat, Claude Code da solo e Claude Code con Arturo, una riga per differenza.</caption>
        <colgroup><col style="width:16%"><col style="width:28%"><col style="width:28%"><col style="width:28%"></colgroup>
        <thead><tr><td></td>{testa}</tr></thead>
        <tbody>
{chr(10).join(righe)}
        </tbody>
      </table>"""


P4 = {
    "slug": "confronto",
    "lang": "it",
    "title": "Arturo, Claude Code da solo o la chat: il confronto",
    "desc": "Differenze tra la chat, Claude Code da solo e Claude Code con Arturo: dove lavorano, quanto costano, quando chiedono. Con i limiti di Arturo.",
    "h1": "Arturo, Claude Code da solo o la chat",
    "briciola": "Il confronto",
    "lead": "La chat, Claude Code da solo e Claude Code con Arturo servono a lavori diversi. La tabella li mette uno accanto all'altro, e sotto ci sono i limiti di Arturo, che conviene leggere prima di installarlo.",
    "indice": [("tabella", "Le differenze, riga per riga"), ("quando-chat", "Quando basta la chat"),
               ("quando-solo", "Quando basta Claude Code da solo"), ("limiti", "I limiti di Arturo"),
               ("domande", "Domande")],
}
P4["main"] = f"""
<section class="sezione">
  <div class="dentro">
    <div class="blocco" id="tabella">
      <h2 id="t-tabella">Le differenze, riga per riga</h2>
{tabella()}
    </div>
    <div class="voci">""" + \
    voce("quando-chat", "Quando basta la chat", """          <p class="voce__attacco">Se il lavoro sta tutto in una conversazione, come una domanda, un testo da rileggere o un'idea da discutere, la chat basta e costa meno.</p>
          <p>Claude Code comincia a servire quando il lavoro sta in molti file o si ripete: rileggere i capitoli di un libro, tenere in ordine i documenti di un progetto, preparare ogni settimana lo stesso riepilogo. In quei casi Claude apre i file da solo invece di aspettare che tu li incolli, e scrive il risultato dove serve, quindi il tempo che risparmi cresce con il numero dei file.</p>""") + \
    voce("quando-solo", "Quando basta Claude Code da solo", """          <p class="voce__attacco">Chi programma, conosce git e sa già scrivere il proprio <code>CLAUDE.md</code> e le proprie regole di permesso ha poco da guadagnare da Arturo.</p>
          <p>Claude Code ha i suoi permessi, e le guardie aggiungono conferme che una persona esperta può non volere. Lo stesso vale per chi lavora in un'altra lingua, perché Arturo parla soltanto italiano. Arturo serve a chi arriva dalla chat e non sa ancora quali scelte fare: le fa al posto suo, gliele spiega e gli lascia la possibilità di cambiarle, con <code>/setup</code> e con i file in <code>personale/</code> che nessun aggiornamento tocca.</p>""") + \
    voce("limiti", "I limiti di Arturo", """                    <ul class="puntata">
            <li><strong>Serve un abbonamento a pagamento.</strong> Arturo è gratuito, Claude Code no. Anthropic decide prezzi, limiti e funzioni, e li può cambiare; il piano gratuito di claude.ai non include Claude Code.</li>
            <li><strong>La telemetria è accesa di default.</strong> Arturo manda a chi lo mantiene eventi da un elenco chiuso: nomi di comandi, skill e guardie, esiti e numeri, con un id casuale che resta lo stesso nel tempo, e per questo i dati non sono anonimi. Mai prompt, file tuoi, percorsi del tuo computer o nomi. Il server non salva l'indirizzo IP e tiene gli eventi 12 mesi. <code>python3 ~/.claude/bin/arturo telemetria mostra</code> fa vedere che cosa parte; <code>python3 ~/.claude/bin/arturo telemetria spegni</code>, <code>ARTURO_TELEMETRIA=0</code> o <code>DO_NOT_TRACK=1</code> la spengono. <code>DO_NOT_TRACK=1</code> spegne anche la telemetria di Claude Code e le funzioni che ne dipendono. Il dettaglio sta nella pagina della <a href="../privacy/">privacy</a>.</li>
            <li><strong>Parla soltanto italiano.</strong> È uno degli impegni del progetto: comandi, messaggi e documenti restano in italiano.</li>
            <li><strong>Lo mantiene una persona.</strong> Arturo è un progetto di Federico Nejrotti. Le segnalazioni vengono lette, ma non c'è promessa di risposta né di correzione. Se lo sviluppo si ferma, lo dicono l'ultima voce di <code>NOVITA.md</code> e la cima del README; la copia che hai continua a funzionare, e puoi farne un fork.</li>
            <li><strong>Gli aggiornamenti sono codice di altri.</strong> Si installano da soli solo se portano la firma di chi mantiene Arturo, controllata con la chiave che hai già. Con <code>python3 ~/.claude/bin/arturo aggiornamenti manuali</code> torni a dire sì a ogni aggiornamento.</li>
          </ul>""") + \
    "    </div>\n  </div>\n</section>\n"
P4["faq"] = [
    ("Che differenza c'è tra Claude in chat e Claude Code?",
     "In chat Claude risponde nella conversazione, e i file li porti tu. Claude Code lavora nelle cartelle del tuo computer: legge e scrive i file ed esegue comandi, chiedendo i permessi che hai impostato."),
    ("Arturo sostituisce Claude Code?",
     "No, si appoggia sopra. Arturo è una configurazione di Claude Code, che va installato a parte e richiede un abbonamento Anthropic."),
    ("Posso spegnere la telemetria di Arturo?",
     "Sì, con <code>python3 ~/.claude/bin/arturo telemetria spegni</code>, oppure con <code>ARTURO_TELEMETRIA=0</code> o <code>DO_NOT_TRACK=1</code>. Prima di decidere, <code>python3 ~/.claude/bin/arturo telemetria mostra</code> fa vedere che cosa parte."),
    ("Cosa succede se Arturo smette di essere sviluppato?",
     "Lo dichiarano l'ultima voce di <code>NOVITA.md</code> e la cima del README. La copia che hai continua a funzionare, il repository resta pubblico con licenza MIT e puoi farne un fork."),
]


# ---------------------------------------------------------------------------------------------
# 5. English
# ---------------------------------------------------------------------------------------------
P5 = {
    "slug": "en",
    "lang": "en",
    "title": "Arturo: a free, open source Claude Code harness in Italian",
    "desc": "Arturo is a harness for knowledge work, made for people who already use AI in chat but have never opened a terminal. Free, open source (MIT), in Italian.",
    "h1": "Arturo, a Claude Code harness in Italian",
    "briciola": "In English",
    "lead": "Arturo is a harness for knowledge work, made for people who already use AI in chat but have never opened a terminal. It is free and open source, and it speaks Italian.",
    "faq_titolo": "Questions.",
}
P5["main"] = '\n<section class="sezione">\n  <div class="dentro">\n    <div class="voci">' + \
    voce("what", "What it is", f"""          <p>Claude Code is Anthropic's AI that works on the files on your computer: it reads and writes documents, runs commands and picks up the work where you left it (<a href="https://code.claude.com/docs/en/overview">official documentation</a>). Arturo is a harness for it, the set of rules, commands and automations around Claude Code that guide its work. The <a href="{GH}">README</a> counts 23 guards and automations, 11 slash commands, 8 subagents and 7 skills. The guards stop Claude before actions that cannot be undone, such as deleting a folder, sending a message or committing a password, and ask you first.</p>""") + \
    voce("who", "Who it is for", """          <p>I'm a writer, not a programmer, and I moved from the chat window to the terminal for two reasons. In a chat I collected the material myself: I opened the files, copied the parts I needed, pasted them into the conversation and then carried the answer back into a document. Claude Code works inside my folders, so it fetches notes, transcripts and spreadsheets on its own, compares them and writes the result to a file. The other reason is continuity: when I close a session, Arturo leaves a summary with what's left to do, and the next morning the work picks up from there instead of from a blank conversation.</p>
          <p>Anthropic saw the same use grow across Claude Code sessions. Between October 2025 and April 2026, writing and data analysis roughly doubled, from about 10% to 20% of sessions, and people outside software reached verified success in about 26% of their sessions, against 30% for software occupations. The gap is four points, and according to the study knowing your field matters more than knowing how to code. The <a href="https://www.anthropic.com/research/claude-code-expertise">study</a> concludes that what happens on Claude Code may be a preview of where knowledge work is headed. Two people who don't work for Anthropic reach a similar conclusion. Simon Willison, an independent programmer who has written about these tools for years, wrote that Claude Code <a href="https://simonwillison.net/2025/Oct/16/claude-skills/">is poorly named</a>, because it is a tool for general computer automation and not only for writing code. Ethan Mollick, who studies AI at work at Wharton, points to <a href="https://www.oneusefulthing.org/p/claude-code-and-what-comes-next">the same reason</a> I found: Claude Code is powerful because it works on your computer and your files, and it is useful to knowledge workers of all types, even though it is built for programmers. That is why I built Arturo, which sets Claude Code up for people who don't code.</p>
          <p>Independent evidence also shows where AI gets things wrong. In a 2023 <a href="https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged">experiment</a> by Harvard and Boston Consulting Group with 758 consultants, those using GPT-4 on tasks within the AI's reach finished 12.2% more of them, 25.1% faster and at 40% higher quality; on a task built to fall outside it, those using AI got the right answer 60 to 70% of the time, against 84% for those working without it. A Microsoft Research <a href="https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/">study</a> of 319 knowledge workers found that knowledge workers with higher confidence in AI report using less critical thinking. And Willison warns that an agent that reads your private data, meets text written by others and can communicate externally <a href="https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/">can be used to steal it</a>, because that text can carry instructions the agent follows as if they came from you.</p>
          <p>Arturo answers these risks in two different ways. Against data theft it has rules that ask for a yes before any step that can't be undone, such as deleting a folder or sending a message; the same check for web pages that carry data out is still being built. Against a wrong answer accepted on trust no rule is enough: the person doing the work checks the result, which is why knowing your field matters, as Anthropic's study also says.</p>
          <p>People who already use ChatGPT or Claude in chat, mostly for writing, research and keeping documents in order, and want the AI to work inside their folders without learning the terminal. Arturo speaks Italian: its commands, guard messages, setup and documentation are in Italian, and staying in Italian is one of the project's commitments. This is its only page in English.</p>""") + \
    voce("install", "How to install", f"""          <p>Install Claude Code, which needs a paid Anthropic plan that includes it (Pro, Max, Team, Enterprise or Console). Open it and paste this sentence, Italian for "Install Arturo":</p>
          <pre class="frase frase--chiara">Installa Arturo: https://<wbr>arturo.stellakamikaze.org/<wbr>inizia/</pre>
          <p>Claude reads the linked page, downloads Arturo's install script, compares it with the copy on GitHub and runs it after you say yes. Then type <code>/exit</code>, <code>claude</code> and <code>/setup</code>. The <a href="../installa/" hreflang="it">step-by-step guide</a> is in Italian, and the code is on <a href="{GH}">GitHub</a>.</p>
          <p>Before you start: Claude Code is a paid service, and what you write goes through Anthropic's servers. Arturo sends usage events from a closed list to its maintainer, on by default and never your texts or files; <code>python3 ~/.claude/bin/arturo telemetria spegni</code> turns them off. Arturo is maintained by one person, Federico Nejrotti.</p>""") + \
    "    </div>\n  </div>\n</section>\n"
P5["faq"] = [
    ("Does Arturo work in English?",
     "No. Its commands, guard messages and documents are in Italian, and the project has committed to staying in Italian. Claude itself answers in the language you write in."),
    ("What does it cost?",
     "Arturo is free and MIT-licensed. Claude Code needs a paid Anthropic plan: Pro, Max, Team, Enterprise or Console."),
    ("Where is the source code?",
     f"On GitHub, at <a href=\"{GH}\">github.com/stellakamikaze/arturo</a>, under the MIT license."),
]

PAGINE = [P1, P2, P3, P4, P5]
