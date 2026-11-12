# AMH Agencement — refonte

Site rendu côté serveur avec **Flask, Jinja et SQLite**, CSS et JavaScript natifs. Ce choix garde l’installation légère, rend les contenus disponibles sans JavaScript et fournit une administration sans abonnement à un CMS externe. Les photographies existantes sont stockées localement en WebP. Les deux polices (Cormorant Garamond et Manrope) sont optimisées en WOFF2 et hébergées localement ; aucune ressource distante n’est demandée par le navigateur.

## Démarrer

Python 3.12 recommandé. Depuis la racine du dépôt :

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/gunicorn --bind 0.0.0.0:3000 --workers 2 --threads 2 --timeout 60 app:app
```

Développement avec rechargement : ajouter `--reload` et définir `TEMPLATES_AUTO_RELOAD=1` pour actualiser aussi les templates HTML. `python app.py` fonctionne également dans l’environnement virtuel, sans activer le débogueur public. Le point `/healthz` vérifie l’accès à SQLite.

Les dépendances directes sont décrites dans `requirements.txt`, les versions installées dans `requirements.lock.txt`. Aucun build Node n’est nécessaire. Les images optimisées sont déjà dans le dépôt.

## Configuration

Utiliser les variables du service d’hébergement. Pour un développement local, copier `.env.example` vers `.env`, renseigner les valeurs et les exporter dans le shell avant de démarrer. Le programme ne charge pas automatiquement les fichiers `.env`.

```bash
set -a
source .env
set +a
```

**Ne jamais committer `.env` ni `instance/`.** Une clé de session aléatoire est créée dans `instance/session.key` avec des permissions restrictives ; la conserver, ou définir `SECRET_KEY` dans le gestionnaire de secrets. Les processus ne survivent pas au redémarrage d’une machine : relancer le serveur avec la commande ci-dessus.

### Administration

L’administration est accessible à `/admin/`. Elle reste désactivée tant que `ADMIN_PASSWORD_HASH` est vide. Aucun compte ni mot de passe par défaut.

Générer le hash localement sans écrire le mot de passe dans l’historique :

```bash
.venv/bin/python -c 'from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass("Mot de passe administrateur : ")))'
```

Enregistrer le hash produit dans `ADMIN_PASSWORD_HASH` via la configuration sécurisée de l’hébergement, puis redémarrer le serveur. En cas d’utilisation d’un fichier `.env`, entourer le hash de guillemets simples : il contient des caractères `$`.

L’administration permet de :

- modifier l’identité, le premier écran, l’introduction, la FAQ et les informations légales ;
- modifier les contenus de l’atelier et des services ;
- créer, modifier et supprimer des réalisations et conseils ;
- importer des images, redimensionnées et débarrassées de leurs métadonnées ;
- modifier les étapes du parcours projet.

Les contenus structurés comme les galeries, paragraphes et FAQ utilisent des champs JSON validés. Exemple de galerie : `["rivoli", "bibliotheque"]`. Après import d’une photographie, son identifiant est affiché : le copier dans `image` ou dans la galerie. Les champs de projet vides sont masqués sur le site public. Les libellés de navigation et les compositions graphiques se modifient dans les templates.

### Formulaire et email

Renseigner `SMTP_HOST`, `SMTP_PORT`, `SMTP_MODE`, `SMTP_FROM`, `CONTACT_TO` et, si le prestataire les exige, `SMTP_USERNAME` et `SMTP_PASSWORD`. STARTTLS et TLS implicite sont pris en charge ; les certificats sont vérifiés. Les envois sans TLS ne sont pas proposés.

Le site affiche une confirmation **uniquement après acceptation du message par le serveur SMTP**. Cela ne garantit pas sa remise finale dans la boîte destinataire. Sans configuration ou si SMTP échoue, une erreur explicite est affichée et les textes saisis restent présents. Les pièces jointes doivent être resélectionnées après une réponse serveur, conformément au fonctionnement des navigateurs.

Limites : 3 fichiers, 5 Mo chacun, requête totale 16 Mo. PDF lisibles et non chiffrés, JPG/PNG/WebP décodés puis réencodés. Les PDF contenant des éléments actifs détectés sont refusés. Cette validation n’est pas un antivirus. Les pièces jointes ne sont pas conservées sur le site : elles sont transmises dans l’email.

Protection CSRF, champ piège, délai minimum de 2 secondes et 5 tentatives par adresse IP en 15 minutes. Limitation partagée entre les workers via SQLite. Les adresses IP de limitation sont purgées à la prochaine tentative après une heure. Pas de suivi marketing ni de notification commerciale automatique.

**Avant ouverture :** tester avec une vraie adresse autorisée, vérifier la réception des pièces jointes et les réglages SPF/DKIM/DMARC du prestataire. Ce test externe n’a pas été réalisé faute de configuration SMTP.

## Déployer

1. Utiliser un service Python persistant avec Python 3.12, disque local persistant et reverse proxy HTTPS.
2. Installer `requirements.lock.txt`, puis utiliser la commande Gunicorn de démarrage ci-dessus (adapter le port au fournisseur).
3. Définir `AMH_DATA_DIR` vers un répertoire absolu du disque persistant. Un chemin relatif est résolu depuis le répertoire de lancement : préférer un chemin absolu en production.
4. Configurer les secrets et SMTP. Mettre `COOKIE_SECURE=1` sous HTTPS.
5. Mettre `SITE_URL` à l’origine publique canonique. Faire rediriger HTTP et l’hôte secondaire vers cette origine au reverse proxy.
6. Derrière un proxy maîtrisé, définir `TRUST_PROXY_COUNT` au nombre exact de proxies fiables et empêcher l’accès direct au serveur. Sinon laisser `0`. Ne jamais faire confiance à des en-têtes transférés provenant directement d’Internet.
7. Valider le contenu et les points de `docs/validation-editoriale.md` avant de rendre le site public.
8. Garder `INDEXING_ENABLED=0` en préproduction : le site émet `X-Robots-Tag: noindex, nofollow`. Après autorisation de publication et vérifications, mettre `INDEXING_ENABLED=1` pour les pages publiques et soumettre `/sitemap.xml` à Search Console.

Ne pas utiliser le serveur de développement Flask en production. Une seule machine/volume SQLite est prévue : pour plusieurs instances indépendantes, migrer la base et la limitation vers des services partagés. Définir le délai du reverse proxy au-dessus du délai SMTP (20 s) et sa limite de requête à 16 Mo. Le serveur SMTP doit être joignable depuis l’hébergement.

### Sauvegardes et mises à jour

Sauvegarder l’intégralité de `AMH_DATA_DIR` : base éditoriale, clé de session et `media/`. Utiliser l’API de sauvegarde SQLite pour une base active, ou arrêter le service avant une copie cohérente. Sauvegarder les médias au même moment. Tester une restauration avant publication. Les fichiers de données sont initialisés une seule fois et ne sont pas écrasés par les mises à jour de code. Une réalisation supprimée ne revient pas au redémarrage.

## Vérifications

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Tests navigateur, avec le serveur démarré, Playwright et Chromium disponibles :

```bash
python3 tests/browser.py
```

Dans une autre machine, installer Playwright dans un environnement de test et son Chromium avec les instructions officielles ; `CHROMIUM_PATH` désigne l’exécutable et `TEST_BASE_URL` l’origine de test. Les dépendances de test navigateur sont dans `requirements-browser.txt`. Le script vérifie le comportement SMTP non configuré : le lancer sur un environnement de test sans SMTP réel. Les captures et le rapport JSON sont écrits dans `/tmp/amh-browser` (`TEST_ARTIFACTS` permet de changer ce chemin).

Voir `docs/rapport-validation.md`, `docs/redirections.csv` et `docs/validation-editoriale.md` pour les preuves et les limites. Aucun déploiement ou changement du site public n’a été effectué.
