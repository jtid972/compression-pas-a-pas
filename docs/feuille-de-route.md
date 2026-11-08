# Feuille de route

## v1.1 — Traitement par lot (prévu)

- Déposer **plusieurs fichiers** (ou un dossier, ou un ZIP) en une fois, avec les mêmes réglages par type.
- Estimation globale : gain total, et liste des fichiers où le gain est inférieur à 10 %
  (proposés décochés par défaut).
- Résultat : un ZIP reprenant l'arborescence d'origine, avec un rapport (avant, après, gain par fichier).
- File d'attente visible et reprise possible si la page est fermée.

## Pistes ultérieures

- PDF scanné → **PDF recherchable** (texte reconnu invisible sous l'image, comme les scanners de bureau).
- Choix des langues de reconnaissance de texte dans la page (allemand, espagnol, italien…).
- Images animées (GIF, WEBP animés) et TIFF multipages.
- Conservation optionnelle des sous-titres et des pistes audio multiples des vidéos.
- Vidéo : encodage H.265/HEVC ou AV1 en option (plus léger, mais moins compatible).
- Stockage des résultats dans un bucket Scaleway Object Storage (S3), pour ne plus les perdre à la
  mise en veille de Serverless Containers.
- Mutualisation avec **Vidéo pas à pas** : compresser une vidéo avant d'en faire un dossier de préparation.
