"""Make a standalone visual entry point from an exported site (no local assets needed)."""
import base64
import mimetypes
from pathlib import Path
import re
import sys

root=Path(sys.argv[1]).resolve()
version=sys.argv[2] if len(sys.argv)>2 else 'V7'
if not re.fullmatch(r'V[0-9]+',version):raise ValueError('Invalid version')
output=root/f'OUVRIR-{version}.html'

def data_uri(path):
    path=path.resolve()
    if not path.is_relative_to(root):raise ValueError('Asset escapes export root')
    if path.name.endswith('-960.webp'):
        high=path.with_name(path.name.replace('-960.webp','-1600.webp'))
        if high.exists():path=high
    mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()

def css_embed(match):
    path=root/match[1]
    css=path.read_text()
    css=re.sub(r'url\([\'\"]?([^\)\'\"]+)[\'\"]?\)',lambda m:'url("'+data_uri(path.parent/m[1])+'")',css)
    return '<style>'+css+'</style>'

page=(root/'index.html').read_text()
page=re.sub(r'<link rel="stylesheet" href="([^"]+)">',css_embed,page)
page=re.sub(r'<link rel="preload"[^>]+>','',page)
page=re.sub(r'<link rel="icon"[^>]+>','',page)
page=re.sub(r'<script src="([^"]+)" defer></script>',lambda m:'<script>document.addEventListener("DOMContentLoaded", () => {\n'+(root/m[1]).read_text()+'\n});</script>',page)
page=re.sub(r'\s+srcset="[^"]*"','',page)
page=re.sub(r'\ssrc="(static/[^"]+)"',lambda m:' src="'+data_uri(root/m[1])+'"',page)
page=re.sub(r'<title>.*?</title>',f'<title>AMH — APERÇU PREMIUM {version} — ATELIER</title>',page,count=1)
page=page.replace('<head>',f'<head>\n<meta name="amh-preview-version" content="{version} — aperçu autonome — nouvelle direction artistique">',1)
licenses='\n\n'.join(p.read_text() for p in (root/'static'/'fonts').glob('LICENSE-*.txt'))
page=page.replace('</body>','<script type="text/plain" id="font-licenses">'+licenses+'</script>\n</body>')
assert 'premium-hero' in page and 'hero-full' not in page
assert '<link rel="stylesheet"' not in page
assert 'src="static/' not in page
output.write_text(page)
print(output,output.stat().st_size)
