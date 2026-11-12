# AMH — direction V6

La V5 reste disponible dans la branche `backup-v5` (commit `33add65`) et dans `AMH-PREMIUM-V5.zip`. Son empreinte est conservée dans `v5-backup.json`. L’archive V5 n’est ni remplacée ni reconstruite.

## Composition

Une navigation symétrique avec le logo d’origine centré, un premier écran marine associé à une photographie claire de la salle à manger rue de Rivoli, un titre court et un double accès contact / réalisations. La sélection photographique utilise deux grands portraits décalés puis une composition paysage. Les savoir-faire se parcourent avec un aperçu sensible au survol et au focus clavier. Le parcours se poursuit par les matières, l’accompagnement, les questions fréquentes et la prise de contact.

La direction est définie dans `static/css/atelier.css`, qui remplace la feuille V5. Les deux polices locales restent Cormorant Garamond et Manrope. Le bleu `#061D32`, le bleu profond `#0E1A2E` et le doré `#C9A25E` de l’atelier structurent l’ensemble.

## Contenus et administration

Le grand titre est éditable dans `hero_display_title` (une partie par ligne). La présentation de l’accueil, son introduction et son image principale restent éditables. Les anciens réglages héritent des nouveaux champs sans effacement des valeurs existantes. Les photographies ajoutées proviennent du site AMH d’origine ; sources dans `media-sources.json`. Aucun avis, label, nom de client ou chiffre commercial n’a été inventé.

Une sauvegarde locale de la base et des fichiers de données V5 a été créée dans `/workspace/AMH-backups/V5`, hors du dépôt. Elle contient la configuration de session et ne doit pas être publiée. Pour un retour complet sur cette machine, arrêter le serveur, sauvegarder l’état courant, restaurer ces données puis reprendre le code de `backup-v5`. L’archive hors connexion V5 suffit à retrouver exactement son aperçu visuel, sans toucher au serveur.

## Livraison

L’archive `AMH-ATELIER-V6.zip` contient `AMH-ATELIER-V6/OUVRIR-V6.html`. Cette entrée embarque styles, polices, photos jusqu’à 1600 px et interactions. Elle a été testée en bloquant toutes les requêtes réseau. Les autres pages sont incluses dans les sous-dossiers. Le formulaire reste désactivé dans l’export hors connexion. Aucun site public n’a été déployé.
