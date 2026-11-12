import copy
import hmac
import io
import json
import os
import re
import secrets
import smtplib
import sqlite3
import ssl
import time
import warnings
from email.message import EmailMessage
from functools import wraps, lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, abort, flash, jsonify, make_response, redirect, render_template, request, session, url_for, send_from_directory
from PIL import Image, ImageOps
from pypdf import PdfReader
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash
import content

ROOT = Path(__file__).parent
Image.MAX_IMAGE_PIXELS = 20_000_000


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    data_dir = Path((test_config or {}).get('DATA_DIR') or os.environ.get('AMH_DATA_DIR', ROOT / 'instance'))
    data_dir.mkdir(parents=True, exist_ok=True)
    keyfile = data_dir / 'session.key'
    if not keyfile.exists():
        try:
            fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY') or keyfile.read_text(),
        DATABASE=str(data_dir / 'content.sqlite3'),
        DATA_DIR=str(data_dir),
        TEMPLATES_AUTO_RELOAD=os.environ.get('TEMPLATES_AUTO_RELOAD')=='1',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1',
        ADMIN_PASSWORD_HASH=os.environ.get('ADMIN_PASSWORD_HASH', ''),
        SITE_URL=os.environ.get('SITE_URL', 'https://amh-agencement.com').rstrip('/'),
        SMTP_HOST=os.environ.get('SMTP_HOST', ''),
        SMTP_PORT=int(os.environ.get('SMTP_PORT', '587')),
        SMTP_MODE=os.environ.get('SMTP_MODE', 'starttls'),
        SMTP_USERNAME=os.environ.get('SMTP_USERNAME', ''),
        SMTP_PASSWORD=os.environ.get('SMTP_PASSWORD', ''),
        SMTP_FROM=os.environ.get('SMTP_FROM', ''),
        CONTACT_TO=os.environ.get('CONTACT_TO', 'contact@amh-agencement.com'),
        INDEXING_ENABLED=os.environ.get('INDEXING_ENABLED')=='1',
    )
    if test_config:
        app.config.update(test_config)
    proxy_count=int(os.environ.get('TRUST_PROXY_COUNT','0'))
    if proxy_count:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=proxy_count,x_proto=proxy_count,x_host=0,x_port=0)

    def db():
        connection = sqlite3.connect(app.config['DATABASE'], timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS documents (kind TEXT NOT NULL, slug TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(kind,slug))')
        c.execute('CREATE TABLE IF NOT EXISTS seed_meta (kind TEXT PRIMARY KEY)')
        c.execute('CREATE TABLE IF NOT EXISTS limits (bucket TEXT NOT NULL, stamp REAL NOT NULL)')
        c.execute('CREATE INDEX IF NOT EXISTS limits_bucket ON limits(bucket,stamp)')
        for kind, docs in [('site', [dict(content.SITE, slug='settings')]), ('service', content.SERVICES), ('project', content.PROJECTS), ('article', content.ARTICLES), ('process', [{'slug':'steps','steps':content.STEPS}]), ('page',content.PAGES)]:
            if c.execute('SELECT 1 FROM seed_meta WHERE kind=?',(kind,)).fetchone():
                continue
            for item in docs:
                c.execute('INSERT OR IGNORE INTO documents VALUES (?,?,?)', (kind, item['slug'], json.dumps(item, ensure_ascii=False)))
            c.execute('INSERT INTO seed_meta VALUES(?)',(kind,))
        for kind,item in [('article',content.MIGRATED_ARTICLE),('project',content.MIGRATED_PROJECT)]:
            migration='import-v1:'+kind
            if not c.execute('SELECT 1 FROM seed_meta WHERE kind=?',(migration,)).fetchone():
                c.execute('INSERT OR IGNORE INTO documents VALUES(?,?,?)',(kind,item['slug'],json.dumps(item,ensure_ascii=False)))
                c.execute('INSERT INTO seed_meta VALUES(?)',(migration,))

    def get_doc(kind, slug):
        with db() as c:
            row = c.execute('SELECT data FROM documents WHERE kind=? AND slug=?', (kind, slug)).fetchone()
        return json.loads(row['data']) if row else None

    def get_docs(kind):
        with db() as c:
            rows = c.execute('SELECT data FROM documents WHERE kind=? ORDER BY rowid', (kind,)).fetchall()
        return [json.loads(r['data']) for r in rows]

    def save_doc(kind, slug, data):
        with db() as c:
            c.execute('INSERT INTO documents VALUES(?,?,?) ON CONFLICT(kind,slug) DO UPDATE SET data=excluded.data', (kind, slug, json.dumps(data, ensure_ascii=False)))

    def csrf():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(24)
        return session['csrf']

    def valid_csrf():
        return bool(session.get('csrf')) and hmac.compare_digest(session['csrf'], request.form.get('csrf', ''))

    def rate_limit(bucket, maximum, window):
        now = time.time()
        # Immediate transaction makes this shared across Gunicorn workers.
        with db() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DELETE FROM limits WHERE stamp<?', (now - 3600,))
            count = c.execute('SELECT count(*) FROM limits WHERE bucket=? AND stamp>?', (bucket, now-window)).fetchone()[0]
            if count >= maximum:
                return False
            c.execute('INSERT INTO limits VALUES (?,?)', (bucket, now))
        return True

    def image_path(key,width):
        return (data_dir/'media' if key.startswith('upload_') else ROOT/'static'/'images')/f'{key}-{width}.webp'

    def image_url(key, width=960):
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', key or ''):
            key = 'rivoli'
        if key.startswith('upload_'):
            return url_for('media',name=f'{key}-{width}.webp')
        return url_for('static', filename=f'images/{key}-{width}.webp')

    @lru_cache(maxsize=256)
    def image_info(key):
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', key or ''):
            key='rivoli'
        candidates=[];seen=set();dimensions=(1600,1067)
        for width in [480,960,1600]:
            path=image_path(key,width)
            if path.exists():
                with Image.open(path) as image:
                    dimensions=image.size
                if dimensions[0] not in seen:
                    seen.add(dimensions[0]);candidates.append((width,dimensions[0]))
        return dimensions,candidates

    def image_srcset(key):
        return ', '.join(f'{image_url(key,width)} {actual}w' for width,actual in image_info(key)[1])

    @app.context_processor
    def context():
        return dict(site=get_doc('site', 'settings'), services=get_docs('service'), categories=content.CATEGORIES,
                    csrf=csrf, image_url=image_url, image_info=image_info, image_srcset=image_srcset, current_year=time.strftime('%Y'),
                    canonical=app.config['SITE_URL'] + request.path,
                    site_origin=app.config['SITE_URL'],
                    meta_title='AMH Agencement — Menuiserie et agencement sur mesure à Paris',
                    meta_description='Menuiserie, mobilier sur mesure et rénovation à Paris. Découvrez les réalisations AMH et notre atelier de fabrication à Bagnolet.')

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if request.path.startswith(('/admin', '/contact')):
            response.headers['Cache-Control'] = 'no-store'
        if not app.config['INDEXING_ENABLED'] or request.path.startswith('/admin') or response.status_code >= 400:
            response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response

    @app.get('/')
    def home():
        if request.args.get('page_id') == '24':
            return redirect(url_for('contact'), 301)
        return render_template('home.html', projects=get_docs('project')[:3], steps=get_doc('process', 'steps')['steps'])

    @app.get('/realisations/')
    def projects():
        category = request.args.get('categorie', '')
        all_projects = get_docs('project')
        chosen = [p for p in all_projects if p['category'] == category] if category else all_projects
        return render_template('projects.html', projects=chosen, active_category=category,
                               meta_title='Réalisations — Menuiserie & rénovation | AMH Agencement',
                               meta_description='Parcourez nos réalisations de menuiserie, rénovation, bureaux, commerces et copropriétés.')

    @app.get('/realisations/<slug>/')
    def project(slug):
        doc = get_doc('project', slug)
        if not doc:
            abort(404)
        return render_template('project.html', project=doc, meta_title=doc['title']+' | Réalisations AMH', meta_description=doc['summary'])

    @app.get('/la-societe/')
    def atelier():
        return render_template('atelier.html', page=get_doc('page','atelier'), meta_title='L’Atelier — Fabrication à Bagnolet | AMH Agencement',
                               meta_description='Découvrez notre atelier de menuiserie à Bagnolet et notre approche de l’agencement sur mesure.')

    @app.get('/deroulement-projet/')
    def process():
        return render_template('process.html', steps=get_doc('process','steps')['steps'],
                               meta_title='Comment se déroule votre projet ? | AMH Agencement',
                               meta_description='Du premier échange à la réception : découvrez les étapes proposées pour préparer votre projet avec AMH.')

    @app.get('/<slug>/')
    def service(slug):
        doc = get_doc('service', slug)
        if not doc:
            abort(404)
        return render_template('service.html', service=doc, projects=[p for p in get_docs('project') if p['category']==doc['category']],
                               meta_title=doc['title']+' à Paris | AMH Agencement', meta_description=doc['intro'])

    @app.get('/blog/')
    def blog():
        return render_template('blog.html', articles=get_docs('article'), meta_title='Conseils pour votre intérieur | AMH Agencement',
                               meta_description='Préparer un projet sur mesure, choisir ses matières : les conseils pratiques de l’atelier.')

    @app.get('/blog/<slug>/')
    def article(slug):
        doc = get_doc('article', slug)
        if not doc:
            abort(404)
        return render_template('article.html', article=doc, meta_title=doc['title']+' | AMH Agencement', meta_description=doc['intro'])

    def validate_attachments(files):
        chosen = [f for f in files if f.filename]
        if len(chosen) > 3:
            raise ValueError('Vous pouvez joindre jusqu’à 3 fichiers.')
        attachments = []
        for number, upload in enumerate(chosen, 1):
            try:
                data = upload.read(5 * 1024 * 1024 + 1)
            finally:
                upload.close()
            if not data or len(data) > 5 * 1024 * 1024:
                raise ValueError('Chaque fichier doit contenir entre 1 octet et 5 Mo.')
            suffix = Path(upload.filename).suffix.lower()
            if suffix == '.pdf':
                if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-2048:]:
                    raise ValueError('Un fichier PDF est invalide.')
                try:
                    reader=PdfReader(io.BytesIO(data), strict=True)
                    if reader.is_encrypted or not len(reader.pages):
                        raise ValueError('PDF protégé ou sans page. Joignez une version lisible.')
                    reader.pages[0].mediabox
                except Exception as e:
                    raise ValueError('Le PDF est illisible ou protégé.') from e
                seen=set()
                def inspect_pdf(obj,depth=0):
                    if depth>40 or len(seen)>10000:
                        raise ValueError('PDF trop complexe. Joignez une version aplatie.')
                    if hasattr(obj,'get_object'):
                        obj=obj.get_object()
                    identity=id(obj)
                    if identity in seen:return
                    seen.add(identity)
                    if isinstance(obj,dict):
                        if any(key in obj for key in ['/JS','/JavaScript','/Launch','/EmbeddedFiles','/OpenAction','/AA']):
                            raise ValueError('PDF avec éléments actifs : joignez une version aplatie.')
                        for item in obj.values():inspect_pdf(item,depth+1)
                    elif isinstance(obj,list):
                        for item in obj:inspect_pdf(item,depth+1)
                inspect_pdf(reader.trailer)
                if any(marker in data for marker in [b'/JavaScript', b'/JS', b'/Launch', b'/EmbeddedFile', b'/OpenAction']):
                    raise ValueError('Les PDF contenant des éléments actifs ne sont pas acceptés. Joignez une version aplatie.')
                attachments.append((data, f'plan-{number}.pdf', 'application', 'pdf'))
            elif suffix in ['.jpg','.jpeg','.png','.webp']:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter('error', Image.DecompressionBombWarning)
                        with Image.open(io.BytesIO(data)) as image:
                            if image.format not in ['JPEG','PNG','WEBP']:
                                raise ValueError('Format d’image non accepté.')
                            image.load()
                            image = ImageOps.exif_transpose(image).convert('RGB')
                            image.thumbnail((2400,2400))
                            stream=io.BytesIO(); image.save(stream, format='JPEG', quality=88)
                    attachments.append((stream.getvalue(), f'photo-{number}.jpg', 'image', 'jpeg'))
                except (OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as e:
                    raise ValueError('Une image est illisible ou trop volumineuse.') from e
            else:
                raise ValueError('Formats acceptés : PDF, JPG, PNG et WebP.')
        return attachments

    def send_contact(values, attachments):
        cfg = app.config
        if not cfg['SMTP_HOST'] or not cfg['SMTP_FROM']:
            raise RuntimeError('SMTP not configured')
        for address in [cfg['SMTP_FROM'], cfg['CONTACT_TO']]:
            if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',address):
                raise RuntimeError('SMTP address invalid')
        msg=EmailMessage()
        msg['Subject']='Nouveau projet — AMH Agencement'
        msg['From']=cfg['SMTP_FROM']; msg['To']=cfg['CONTACT_TO']; msg['Reply-To']=values['email']
        labels={'name':'Nom','email':'Email','phone':'Téléphone','type':'Type de projet','town':'Commune','budget':'Budget','timing':'Échéance','message':'Description'}
        msg.set_content('\n\n'.join(f'{label} : {values.get(key, "")}' for key,label in labels.items()))
        for data, filename, main, sub in attachments:
            msg.add_attachment(data, maintype=main, subtype=sub, filename=filename)
        context=ssl.create_default_context()
        if cfg['SMTP_MODE']=='ssl':
            smtp=smtplib.SMTP_SSL(cfg['SMTP_HOST'],cfg['SMTP_PORT'],timeout=20,context=context)
        elif cfg['SMTP_MODE']=='starttls':
            smtp=smtplib.SMTP(cfg['SMTP_HOST'],cfg['SMTP_PORT'],timeout=20)
        else:
            raise RuntimeError('TLS SMTP required')
        with smtp:
            if cfg['SMTP_MODE']=='starttls':
                smtp.ehlo(); smtp.starttls(context=context); smtp.ehlo()
            if cfg['SMTP_USERNAME']:
                smtp.login(cfg['SMTP_USERNAME'],cfg['SMTP_PASSWORD'])
            refused=smtp.send_message(msg)
            if refused:
                raise RuntimeError('SMTP recipient refused')

    @app.route('/contact/', methods=['GET','POST'])
    def contact():
        values={key:request.form.get(key,'').strip() for key in ['name','email','phone','type','town','budget','timing','message']}
        errors={}; status=200
        if request.method=='POST':
            if not valid_csrf():
                errors['global']='Votre session a expiré. Rechargez la page avant de réessayer.';status=400
            elif not rate_limit('contact:'+request.remote_addr,5,900):
                errors['global']='Trop de tentatives. Réessayez dans 15 minutes ou appelez-nous.';status=429
            elif request.form.get('website') or time.time()-session.get('form_started',time.time())<2:
                errors['global']='Veuillez patienter quelques secondes avant de réessayer.';status=400
            else:
                for key,label in [('name','votre nom'),('type','le type de projet'),('message','votre description')]:
                    if not values[key]:errors[key]='Merci de renseigner '+label+'.'
                if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',values['email']) or len(values['email'])>254:
                    errors['email']='Indiquez une adresse email valide.'
                if values['type'] not in [*content.CATEGORIES, 'autre']:
                    errors['type']='Sélectionnez un type de projet.'
                for key,value in values.items():
                    if len(value)>(5000 if key=='message' else 300):errors[key]='Ce champ est trop long.'
                attachments=[]
                try:attachments=validate_attachments(request.files.getlist('files'))
                except ValueError as e:errors['files']=str(e)
                if not errors:
                    try:
                        send_contact(values,attachments)
                    except Exception as e:
                        app.logger.warning('Contact delivery failed (%s)',type(e).__name__)
                        errors['global']='Votre demande n’a pas été envoyée. Vos informations restent affichées. Contactez-nous par téléphone ou par email, ou réessayez plus tard.';status=503
                    else:
                        session.pop('form_started',None)
                        session['contact_sent']=True
                        return redirect(url_for('contact_thanks'),303)
                else:status=422
        session.setdefault('form_started',time.time())
        return render_template('contact.html',values=values,errors=errors,
                               meta_title='Parlons de votre projet | AMH Agencement',
                               meta_description='Présentez votre projet de menuiserie, d’agencement ou de rénovation à l’atelier AMH.'),status

    @app.get('/contact/merci/')
    def contact_thanks():
        if not session.pop('contact_sent',False):
            return redirect(url_for('contact'))
        return render_template('thanks.html',meta_title='Demande transmise | AMH Agencement')

    @app.get('/mentions-legales/')
    @app.get('/confidentialite/')
    def legal():
        return render_template('legal.html', privacy=request.path.startswith('/confidentialite'),
                               meta_title=('Confidentialité' if request.path.startswith('/confidentialite') else 'Mentions légales')+' | AMH Agencement')

    def admin_required(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            if not session.get('admin'):
                return redirect(url_for('admin_login'))
            return fn(*args,**kwargs)
        return wrapped

    @app.route('/admin/connexion/',methods=['GET','POST'])
    def admin_login():
        error='';status=200
        if not app.config['ADMIN_PASSWORD_HASH']:
            return render_template('login.html',error='L’administration doit être configurée par le responsable du site.'),503
        if request.method=='POST':
            if not valid_csrf():error='Session expirée.';status=400
            elif not rate_limit('login:'+request.remote_addr,5,900):error='Trop de tentatives. Réessayez dans 15 minutes.';status=429
            elif check_password_hash(app.config['ADMIN_PASSWORD_HASH'],request.form.get('password','')):
                session.clear();session['admin']=True;csrf()
                return redirect(url_for('admin'))
            else:error='Identifiants incorrects.';status=401
        return render_template('login.html',error=error),status

    @app.post('/admin/deconnexion/')
    def admin_logout():
        if not valid_csrf():abort(400)
        session.clear();return redirect(url_for('home'))

    @app.get('/admin/')
    @admin_required
    def admin():
        return render_template('admin.html',documents={k:get_docs(k) for k in ['site','project','service','article','process','page']})

    @app.route('/admin/edit/<kind>/<slug>/',methods=['GET','POST'])
    @admin_required
    def admin_edit(kind,slug):
        if kind not in ['site','project','service','article','process','page']:abort(404)
        doc=get_doc(kind,slug)
        if slug=='nouveau' and kind in ['project','article']:
            doc=copy.deepcopy(content.PROJECTS[0] if kind=='project' else content.ARTICLES[0])
            doc.update(slug='',title='',intro='' if kind=='article' else doc.get('intro',''))
        if doc is None:abort(404)
        error=''
        if request.method=='POST':
            if not valid_csrf():abort(400)
            updated=copy.deepcopy(doc)
            try:
                for key,old in doc.items():
                    value=request.form.get(key,'')
                    if isinstance(old,(list,dict)):
                        parsed=json.loads(value)
                        if not isinstance(parsed,type(old)):raise ValueError('Structure incorrecte : '+key)
                        updated[key]=parsed
                    else:updated[key]=value.strip()
                if 'title' in updated and not updated['title']:
                    raise ValueError('Le titre ne peut pas être vide.')
                for image_key in ['image','hero_image']:
                    if image_key in updated and (not re.fullmatch('[a-zA-Z0-9_-]+',updated[image_key]) or not image_path(updated[image_key],960).exists()):
                        raise ValueError('Nom d’image introuvable : '+image_key)
                if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',updated['slug']):raise ValueError('Adresse : lettres minuscules, chiffres et tirets uniquement.')
                if slug!='nouveau' and updated['slug']!=slug:raise ValueError('L’adresse existante doit être conservée pour préserver les liens.')
                if slug=='nouveau' and get_doc(kind,updated['slug']):raise ValueError('Cette adresse existe déjà.')
                if kind in ['project','service'] and updated['category'] not in content.CATEGORIES:raise ValueError('Catégorie invalide.')
                # Preserve the seed schema: templates rely on known field types.
                if kind=='site':
                    if not all(isinstance(q,dict) and isinstance(q.get('question'),str) and isinstance(q.get('answer'),str) for q in updated['faq']):raise ValueError('FAQ : question et answer sont obligatoires.')
                    for key in ['social_instagram','social_linkedin']:
                        if updated[key] and urlsplit(updated[key]).scheme!='https':raise ValueError('Les réseaux sociaux doivent utiliser HTTPS.')
                if kind=='project' and not all(isinstance(v,str) and re.fullmatch('[a-zA-Z0-9_-]+',v) for v in updated['gallery']):raise ValueError('Galerie : liste de noms d’images uniquement.')
                if kind in ['article','process']:
                    key='sections' if kind=='article' else 'steps'
                    if not all(isinstance(v,list) and len(v)==2 and all(isinstance(x,str) for x in v) for v in updated[key]):raise ValueError('Chaque section doit contenir un titre et un texte.')
                if kind=='page' and not all(isinstance(v,str) for v in updated['paragraphs']):raise ValueError('Paragraphes : liste de textes uniquement.')
                if kind=='service' and not all(isinstance(v,str) for v in updated['details']):raise ValueError('Détails : liste de textes uniquement.')
                save_doc(kind,updated['slug'],updated)
                flash('Modifications enregistrées.','success')
                return redirect(url_for('admin'))
            except (ValueError,TypeError,json.JSONDecodeError) as e:
                error=str(e);doc=updated
        return render_template('admin_edit.html',doc=doc,kind=kind,error=error)

    @app.post('/admin/delete/<kind>/<slug>/')
    @admin_required
    def admin_delete(kind,slug):
        if not valid_csrf():abort(400)
        if kind not in ['project','article']:abort(400)
        if request.form.get('confirm')!='supprimer':
            flash('Confirmez la suppression en saisissant « supprimer ».','error')
            return redirect(url_for('admin_edit',kind=kind,slug=slug))
        with db() as c:
            c.execute('DELETE FROM documents WHERE kind=? AND slug=?',(kind,slug))
        flash('Contenu supprimé. Prévoyez une redirection si cette adresse était déjà publiée.','success')
        return redirect(url_for('admin'))

    @app.post('/admin/upload/')
    @admin_required
    def admin_upload():
        if not valid_csrf():abort(400)
        upload=request.files.get('image')
        if not upload or not upload.filename:
            flash('Choisissez une image.','error');return redirect(url_for('admin'))
        try:
            data=validate_attachments([upload])
            if data[0][2]!='image':raise ValueError('Choisissez une image JPG, PNG ou WebP.')
            key='upload_'+secrets.token_hex(10)
            (data_dir/'media').mkdir(exist_ok=True)
            with Image.open(io.BytesIO(data[0][0])) as image:
                for width in [480,960,1600]:
                    resized=image.copy();resized.thumbnail((width,2000))
                    resized.save(image_path(key,width),'WEBP',quality=85)
            flash('Image ajoutée. Nom à utiliser dans les champs image ou galerie : '+key,'success')
        except ValueError as e:flash(str(e),'error')
        return redirect(url_for('admin'))

    @app.get('/media/<name>')
    def media(name):
        if not re.fullmatch(r'upload_[a-f0-9]{20}-(480|960|1600)\.webp',name):abort(404)
        return send_from_directory(data_dir/'media',name,max_age=31536000)

    @app.get('/robots.txt')
    def robots():
        return make_response('User-agent: *\nDisallow: /admin/\nSitemap: '+app.config['SITE_URL']+'/sitemap.xml\n',200,{'Content-Type':'text/plain; charset=utf-8'})

    @app.get('/sitemap.xml')
    def sitemap():
        paths=['/','/realisations/','/la-societe/','/deroulement-projet/','/blog/','/contact/','/mentions-legales/','/confidentialite/']
        paths += ['/'+s['slug']+'/' for s in get_docs('service')]
        paths += ['/realisations/'+p['slug']+'/' for p in get_docs('project')]
        paths += ['/blog/'+p['slug']+'/' for p in get_docs('article')]
        return make_response(render_template('sitemap.xml',paths=paths,base_url=app.config['SITE_URL']),200,{'Content-Type':'application/xml; charset=utf-8'})

    @app.get('/sitemap_index.xml')
    @app.get('/wp-sitemap.xml')
    def old_sitemap():
        return redirect(url_for('sitemap'),301)

    @app.get('/amenagement-securite-bebe-rambarde-meuble-sur-mesure/')
    def legacy_article():
        return redirect(url_for('article',slug=content.MIGRATED_ARTICLE['slug']),301)

    @app.get('/atelier/')
    def old_atelier():return redirect(url_for('atelier'),301)

    @app.get('/healthz')
    def health():
        with db() as c:c.execute('SELECT 1').fetchone()
        return jsonify(status='ok')

    @app.errorhandler(404)
    def not_found(error):return render_template('404.html',meta_title='Page introuvable | AMH Agencement'),404

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(error):
        return render_template('message.html',title='Vos fichiers sont trop volumineux',message='La demande dépasse 16 Mo. Revenez au formulaire avec 3 fichiers de 5 Mo maximum.',meta_title='Fichiers trop volumineux | AMH Agencement'),413

    return app


app=create_app()
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','3000')),debug=False)
