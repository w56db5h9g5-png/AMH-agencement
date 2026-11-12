# Nouvelle direction visuelle — base de la première version

La première composition (commit `874abdf`) sert de base : fond clair, hero en deux colonnes et photographie à droite. Le reste du site est retravaillé dans une direction éditoriale : grandes photographies, galeries décalées, hiérarchie typographique et rythme des espaces.

## Couleurs de l’atelier

Le bleu nuit `#061D32`, le bleu profond `#0E1A2E`, le doré `#C9A25E` et son ton de texte sombre `#967100` proviennent des styles du site AMH d’origine. Le logo est conservé. Les couleurs neutres servent aux fonds et à la lecture. La direction est définie dans `static/css/premium.css`, sans les surcharges successives de l’ancienne version plein écran.

## Typographie

Cormorant Garamond pour les titres et Manrope pour les textes. Fichiers locaux WOFF2, caractères latins/français, deux préchargements prioritaires, aucune requête Google Fonts au navigateur. Voir `fonts.md` et les licences dans `static/fonts/`.

## Mise en page

- Hero claire en deux colonnes sur ordinateur, empilée sur mobile.
- Navigation issue de la première version, simplifiée ; menu mobile avec confinement du focus, fermeture par Échap et blocage du défilement de la page.
- Portfolio décalé et fiches projets avec grand format photographique.
- Savoir-faire présentés par des photographies et de courts textes.
- Atelier, conseils et contact harmonisés avec les mêmes grilles et styles.
- Micro-interactions limitées aux liens, boutons, photographies, champs et apparitions au défilement. Aucun contenu masqué dans l’attente du JavaScript ; réduction des mouvements respectée.

L’administration, les contenus et le traitement du formulaire sont préservés. Aucune publication du site web n’est réalisée.

## V5 — présence du bleu marine

Le bandeau éditorial et la légende photographique de la hero utilisent le bleu AMH `#061D32`, avec des textes clairs et des accents dorés. Les numéros d’étapes et les repères de savoir-faire sont également bleu marine. Les fonds clairs restent majoritaires. Contrôles navigateur sur l’entrée autonome V5 : couleurs calculées, texte blanc sur bandeau et absence de débordement à 1440 et 390 px ; aucune erreur JavaScript détectée.
