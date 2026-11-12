# Rapport de validation — 12 novembre 2026

## Périmètre livré

Site Flask/Jinja rendu côté serveur, administration SQLite, pages publiques, fiches de réalisations, filtres, galerie avec agrandissement, pages de services, atelier, conseils, parcours projet, formulaire, pages légales de travail, sitemap et redirections. Logo existant et 30 variantes WebP locales issues de 10 photographies.

## Tests serveur

18 tests automatisés passent avec `python -m unittest discover -s tests -v` :

- Toutes les pages du sitemap répondent, avec un H1 et des ressources locales accessibles.
- Filtres rendus côté serveur, pages absentes en 404 et redirections permanentes.
- Protection CSRF, validation des champs et conservation des valeurs en cas d’erreur.
- SMTP absent ou indisponible : statut 503, aucune fausse confirmation.
- Acceptation SMTP simulée : STARTTLS demandé, Reply-To correct, PDF et image joints, confirmation autorisée une seule fois. Ce test ne réalise pas de connexion SMTP externe.
- Rejet des faux PDF/images, fichiers trop volumineux, formats interdits, PDF actifs et excès de pièces jointes.
- Protection antispam et limitation des tentatives.
- Authentification, édition persistante, création et suppression après redémarrage.
- Validation des structures éditoriales, import et distribution des médias.
- Échappement des textes, en-têtes de sécurité et désactivation de l’indexation en préproduction.

## Navigateur Chromium

Exécuté avec Playwright sur le serveur Gunicorn local :

- Accueil aux largeurs 360, 390, 768 et 1440 px : aucun débordement horizontal, photographies effectivement chargées après défilement.
- Menu mobile : ouverture, fermeture avec Échap et restitution du focus.
- FAQ, filtres, accès aux fiches et agrandissement des photos ; fermeture du dialogue avec Échap.
- Pages principales : liens internes, H1 et absence de débordement sur mobile.
- Formulaire sans SMTP : erreur honnête et textes saisis conservés.
- Aucune erreur JavaScript capturée.

Captures : `apercu-ordinateur.png` et `apercu-mobile.png`. Rapport machine : `browser-report.json`.

## Mesures locales, pas des performances terrain

Dernière mesure via PerformanceObserver dans Chromium, sur la machine locale, écran 1440 × 1000, sans ralentissement réseau/CPU :

- LCP : 56 ms.
- CLS : 0.
- INP : non mesuré.

Ces valeurs ne démontrent pas le respect des Core Web Vitals en production. Aucun score Lighthouse ni audit d’accessibilité exhaustif n’est revendiqué. Les objectifs doivent être vérifiés sur l’hébergement cible et avec des appareils réels.

## Limites externes explicites

Aucun message n’a été envoyé à AMH. SMTP réel, remise finale en boîte, domaine, HTTPS public, sauvegarde/restauration de production, contenus légaux, validité des certifications et droits photographiques restent à configurer ou valider. L’administration exige un hash de mot de passe fourni par le propriétaire. La version reste en noindex par défaut.

Aucune publication, modification DNS ou modification du site AMH existant n’a été effectuée.
