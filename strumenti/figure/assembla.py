import re,os,sys
S=os.path.dirname(os.path.abspath(__file__))
pag=open(os.path.join(S,'pagina.html')).read()
for n,f in [(1,'cassettiera.svg.html'),(2,'guardie.svg.html'),(3,'ritmo.svg.html')]:
    p=os.path.join(S,f)
    if os.path.exists(p):
        pag=pag.replace(f'<!-- figura-{n} inizio -->\n<!-- figura-{n} fine -->', f'<!-- figura-{n} inizio -->\n'+open(p).read()+f'\n<!-- figura-{n} fine -->')
out='/Users/federico/Documents/ClaudeCode/arturo-landing/sito/prove/figure/index.html'
os.makedirs(os.path.dirname(out),exist_ok=True)
open(out,'w').write(pag); print('scritto',len(pag))
