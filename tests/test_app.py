import io
import json
import re
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
from pypdf import PdfWriter
from werkzeug.security import generate_password_hash
from app import create_app


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_app({'TESTING':True,'DATA_DIR':self.tmp.name,'DATABASE':str(Path(self.tmp.name)/'test.sqlite3'),
                             'SECRET_KEY':'test-session-only','ADMIN_PASSWORD_HASH':generate_password_hash('test-password'),
                             'SMTP_HOST':'','SMTP_FROM':''})
        self.client=self.app.test_client()

    def tearDown(self):self.tmp.cleanup()

    def form(self):
        self.client.get('/contact/')
        with self.client.session_transaction() as s:
            s['form_started']=time.time()-10
            token=s['csrf']
        return dict(csrf=token,name='Camille',email='camille@example.com',phone='',type='menuiserie',town='Paris',message='Une bibliothèque pour notre salon.',budget='',timing='')

    def admin(self):
        self.client.get('/admin/connexion/')
        with self.client.session_transaction() as s:token=s['csrf']
        return self.client.post('/admin/connexion/',data={'csrf':token,'password':'test-password'})

    def test_all_public_pages_sitemap_and_assets(self):
        result=self.client.get('/sitemap.xml');self.assertEqual(result.status_code,200)
        root=ET.fromstring(result.data)
        locations=root.findall('{*}url/{*}loc')
        self.assertGreaterEqual(len(locations),19)
        for loc in locations:
            path=loc.text.replace('https://amh-agencement.com','')
            response=self.client.get(path)
            with self.subTest(path=path):
                self.assertEqual(response.status_code,200)
                html=response.data.decode()
                self.assertEqual(html.count('<h1'),1)
                for asset in re.findall(r'(?:src|href)="(/static/[^\"]+)"',html):
                    with self.client.get(asset) as asset_response:
                        self.assertEqual(asset_response.status_code,200,asset)

    def test_filter_is_server_rendered(self):
        text=self.client.get('/realisations/?categorie=menuiserie').data.decode()
        self.assertIn('Une bibliothèque, un lieu de vie',text)
        self.assertNotIn('Lumière sur Rivoli',text)

    def test_redirects_and_404(self):
        for path,target in [('/?page_id=24','/contact/'),('/sitemap_index.xml','/sitemap.xml'),('/wp-sitemap.xml','/sitemap.xml'),('/atelier/','/la-societe/')]:
            r=self.client.get(path);self.assertEqual(r.status_code,301);self.assertEqual(r.location,target)
        self.assertEqual(self.client.get('/inexistant/').status_code,404)
        self.assertEqual(self.client.get('/realisations/inexistant/').status_code,404)

    def test_csrf_rejected(self):
        data=self.form();data['csrf']='bad'
        self.assertEqual(self.client.post('/contact/',data=data).status_code,400)

    def test_invalid_form_preserves_fields(self):
        data=self.form();data['email']='not-an-email'
        response=self.client.post('/contact/',data=data)
        self.assertEqual(response.status_code,422);self.assertIn(b'Camille',response.data)

    def test_absent_smtp_never_claims_success(self):
        r=self.client.post('/contact/',data=self.form())
        self.assertEqual(r.status_code,503)
        self.assertIn('n’a pas été envoyée',r.data.decode())
        with self.client.session_transaction() as state:
            self.assertNotIn('contact_sent',state)
        self.assertEqual(self.client.get('/contact/merci/').status_code,302)

    def test_smtp_acceptance_and_real_attachments(self):
        data=self.form()
        pdf=io.BytesIO();writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.write(pdf);pdf.seek(0)
        image=io.BytesIO();Image.new('RGB',(20,20),'red').save(image,'PNG');image.seek(0)
        data['files']=[(pdf,'plan.pdf'),(image,'salon.png')]
        self.app.config.update(SMTP_HOST='smtp.example.com',SMTP_FROM='site@example.com')
        with patch('app.smtplib.SMTP') as smtp:
            smtp.return_value.__enter__.return_value=smtp.return_value
            smtp.return_value.send_message.return_value={}
            r=self.client.post('/contact/',data=data,content_type='multipart/form-data')
            self.assertEqual(r.status_code,303)
            smtp.return_value.starttls.assert_called_once()
            message=smtp.return_value.send_message.call_args.args[0]
            self.assertEqual(message['Reply-To'],'camille@example.com')
            self.assertEqual(len(list(message.iter_attachments())),2)
        self.assertEqual(self.client.get('/contact/merci/').status_code,200)
        self.assertEqual(self.client.get('/contact/merci/').status_code,302)

    def test_smtp_failure_preserves_content(self):
        self.app.config.update(SMTP_HOST='smtp.example.com',SMTP_FROM='site@example.com')
        with patch('app.smtplib.SMTP',side_effect=OSError('offline')):
            r=self.client.post('/contact/',data=self.form())
        self.assertEqual(r.status_code,503);self.assertIn(b'Camille',r.data)

    def test_bad_files_rejected(self):
        for name,data in [('plan.pdf',b'%PDF-fake %%EOF'),('photo.png',b'fake'),('script.svg',b'<svg/>'),('large.png',b'x'*(5*1024*1024+1))]:
            with self.subTest(name=name):
                form=self.form();form['files']=(io.BytesIO(data),name)
                with self.client.post('/contact/',data=form,content_type='multipart/form-data') as r:
                    self.assertEqual(r.status_code,422)

    def test_more_than_three_files_rejected(self):
        data=self.form();data['files']=[(io.BytesIO(b'x'),f'{i}.png') for i in range(4)]
        self.assertEqual(self.client.post('/contact/',data=data).status_code,422)

    def test_antispam_and_rate_limit(self):
        data=self.form();data['website']='bot.example'
        self.assertEqual(self.client.post('/contact/',data=data).status_code,400)
        data.pop('website')
        for _ in range(4):self.client.post('/contact/',data=data)
        self.assertEqual(self.client.post('/contact/',data=data).status_code,429)

    def test_admin_auth_and_persistence(self):
        self.assertEqual(self.client.get('/admin/').status_code,302)
        self.assertEqual(self.admin().status_code,302)
        self.assertEqual(self.client.get('/admin/').status_code,200)
        response=self.client.get('/admin/edit/project/appartement-rivoli/')
        self.assertEqual(response.status_code,200)
        import content
        data=dict(content.PROJECTS[0]);data['title']='Un nouveau regard'
        data['gallery']=json.dumps(data['gallery'])
        with self.client.session_transaction() as s:data['csrf']=s['csrf']
        self.assertEqual(self.client.post('/admin/edit/project/appartement-rivoli/',data=data).status_code,302)
        self.assertIn(b'Un nouveau regard',self.client.get('/realisations/appartement-rivoli/').data)
        other=create_app(dict(self.app.config))
        self.assertIn(b'Un nouveau regard',other.test_client().get('/realisations/appartement-rivoli/').data)

    def test_admin_rejects_broken_nested_data(self):
        self.admin()
        import content
        data=dict(content.PROJECTS[0]);data['gallery']='[{}]'
        with self.client.session_transaction() as s:data['csrf']=s['csrf']
        r=self.client.post('/admin/edit/project/appartement-rivoli/',data=data)
        self.assertIn('liste de noms',r.data.decode())
        self.assertIn(b'Lumi',self.client.get('/realisations/appartement-rivoli/').data)

    def test_admin_create_and_delete_persist_across_restart(self):
        self.admin()
        import content
        data=dict(content.PROJECTS[0]);data.update(slug='nouveau-projet',title='Nouveau projet',gallery='["rivoli"]')
        with self.client.session_transaction() as state:data['csrf']=state['csrf']
        self.assertEqual(self.client.post('/admin/edit/project/nouveau/',data=data).status_code,302)
        self.assertEqual(self.client.get('/realisations/nouveau-projet/').status_code,200)
        r=self.client.post('/admin/delete/project/appartement-rivoli/',data={'csrf':data['csrf'],'confirm':'supprimer'})
        self.assertEqual(r.status_code,302)
        restarted=create_app(dict(self.app.config))
        self.assertEqual(restarted.test_client().get('/realisations/appartement-rivoli/').status_code,404)

    def test_pdf_with_active_elements_rejected(self):
        from pypdf.generic import NameObject,TextStringObject,DictionaryObject
        pdf=io.BytesIO();writer=PdfWriter();writer.add_blank_page(width=100,height=100)
        writer._root_object.update({NameObject('/OpenAction'):DictionaryObject({NameObject('/S'):NameObject('/JavaScript'),NameObject('/JS'):TextStringObject('app.alert(1)')})})
        writer.write(pdf);pdf.seek(0)
        data=self.form();data['files']=(pdf,'active.pdf')
        self.assertEqual(self.client.post('/contact/',data=data).status_code,422)

    def test_draft_not_indexed_and_production_switch(self):
        self.assertIn('noindex',self.client.get('/').headers['X-Robots-Tag'])
        self.app.config['INDEXING_ENABLED']=True
        self.assertNotIn('X-Robots-Tag',self.client.get('/').headers)
        self.assertIn('noindex',self.client.get('/admin/connexion/').headers['X-Robots-Tag'])

    def test_admin_upload_and_served_media(self):
        self.admin()
        image=io.BytesIO();Image.new('RGB',(32,24),'blue').save(image,'PNG');image.seek(0)
        with self.client.session_transaction() as state:token=state['csrf']
        with self.client.post('/admin/upload/',data={'csrf':token,'image':(image,'photo.png')},content_type='multipart/form-data') as result:
            self.assertEqual(result.status_code,302)
        files=list((Path(self.tmp.name)/'media').glob('*.webp'))
        self.assertEqual(len(files),3)
        with self.client.get('/media/'+files[0].name) as response:
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.mimetype,'image/webp')
        self.assertEqual(self.client.get('/media/session.key').status_code,404)

    def test_headers_and_escaped_content(self):
        r=self.client.get('/');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
        self.assertIn("object-src 'none'",r.headers['Content-Security-Policy'])
        data=self.form();data['name']='<script>alert(1)</script>';data['email']='bad'
        r=self.client.post('/contact/',data=data)
        self.assertNotIn(b'<script>alert(1)</script>',r.data)
        self.assertIn(b'&lt;script&gt;',r.data)

if __name__=='__main__':unittest.main()
