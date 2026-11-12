"""Export a navigable, offline preview without a Python server."""
import html
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urljoin,urlsplit,parse_qs
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app

output=Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/AMH-apercu-hors-ligne')
output.mkdir(parents=True,exist_ok=True)
with app.test_client() as client:
    root=ET.fromstring(client.get('/sitemap.xml').data)
    urls=[urlsplit(node.text).path for node in root.findall('{*}url/{*}loc')]
    urls+=[f'/realisations/?categorie={category}' for category in ['menuiserie','appartements','professionnels','coproprietes']]
    def filename(url):
        parsed=urlsplit(url)
        if parsed.query:
            category=parse_qs(parsed.query).get('categorie',[''])[0]
            return Path('realisations')/('filtre-'+category)/'index.html'
        return Path(parsed.path.lstrip('/'))/'index.html'
    mapping={url:filename(url) for url in urls}
    for url in urls:
        dest=output/mapping[url];dest.parent.mkdir(parents=True,exist_ok=True)
        page=client.get(url).data.decode()
        def local(value):
            if not value.startswith(('/','?')):return value
            parsed=urlsplit(urljoin('http://preview.local'+url,html.unescape(value)))
            if parsed.path.startswith('/static/'):
                target=Path(parsed.path.lstrip('/'))
            else:
                key=parsed.path+('?' + parsed.query if parsed.query else '')
                if key not in mapping:return value
                target=mapping[key]
            relative=os.path.relpath(output/target,dest.parent)
            return relative+('#'+parsed.fragment if parsed.fragment else '')
        page=re.sub(r'\b(href|src|action)="([^"]*)"',lambda m:f'{m[1]}="{html.escape(local(m[2]),quote=True)}"',page)
        page=re.sub(r'\bsrcset="([^"]*)"',lambda m:'srcset="'+', '.join(local(part.strip().split()[0])+' '+part.strip().split()[1] for part in m[1].split(','))+'"',page)
        if url=='/contact/':
            page=page.replace('<div class="form-heading">','<div class="notice"><strong>Aperçu hors connexion.</strong> Aucun message ne peut être envoyé depuis cette copie. Le formulaire sert ici à examiner la présentation.</div><div class="form-heading">')
            page=page.replace('<button class="button" type="submit">','<button class="button" type="button" disabled>')
        dest.write_text(page)
shutil.copytree(Path(app.root_path)/'static',output/'static',dirs_exist_ok=True)
(output/'LISEZ-MOI.txt').write_text('AMH Agencement — Aperçu hors connexion\n\n1. Décompressez cette archive.\n2. Ouvrez le fichier index.html dans Safari ou Chrome.\n3. Naviguez entre les pages, filtrez les réalisations et ouvrez les photographies.\n\nCette copie ne publie rien. Le formulaire est désactivé et aucune donnée ne peut être envoyée. L’administration et la sauvegarde des contenus exigent le serveur et ne font pas partie de cet aperçu. Les liens téléphone, email et réseaux sociaux restent des liens externes. Les informations légales restent à valider.\n')
archive=shutil.make_archive(str(output),'zip',root_dir=output.parent,base_dir=output.name)
print(archive)
print('Pages exported:',len(urls))
