# Ce que fait Compression pas à pas

## Le principe : estimer d'abord, compresser ensuite

1. Vous choisissez un fichier : il est analysé (type, dimensions, durée, pages, images intégrées…).
2. Les réglages adaptés à ce type de fichier s'affichent, avec des valeurs par défaut raisonnables.
3. **Le gain est estimé** et se recalcule à chaque changement de réglage :
   - **images, documents bureautiques, PDF** : la compression est réellement faite pendant
     l'estimation, donc le chiffre affiché est **exact**, et le lancement est ensuite immédiat ;
   - **vidéos** : trois extraits de 6 secondes (à 15 %, 50 % et 85 % de la durée) sont encodés avec
     les réglages choisis, et la taille finale est extrapolée (affichée avec « ≈ »). En test, l'écart
     était d'environ 1 %. Les vidéos de moins de 40 secondes sont encodées en entier.
4. **Si le gain est inférieur à 10 %** (réglable avec `MIN_GAIN`), l'outil conseille de ne pas lancer
   le traitement ; le bouton devient « Lancer quand même » et demande une confirmation.
5. Si le résultat n'est pas plus léger que l'original, **l'original est rendu tel quel**.

## Vidéos

| Réglage | Choix |
|---|---|
| Définition maximale | **Full HD** (tient dans 1920 × 1080), **HD Ready** (1280 × 720), ou définition d'origine. Les vidéos verticales (téléphone) sont traitées dans le bon sens. Jamais d'agrandissement. |
| Qualité de l'image | Haute, Équilibrée, Compacte |
| Son | Normal (128 kbit/s), Réduit (96 kbit/s), Mono (64 kbit/s), Sans son. Masqué si la vidéo est muette. |
| MP3 séparé | fournit en plus le son seul en MP3 (64 kbit/s mono si « Mono » est choisi, 128 kbit/s sinon) |

Le **format est conservé** : MP4 reste MP4 (H.264 + AAC), MOV reste MOV, MKV reste MKV, WEBM reste WEBM
(VP9 + Opus), AVI reste AVI (H.264 + MP3). Seuls les anciens formats (WMV, FLV, MPG, OGV) sont
convertis en MP4, ce qui est signalé avant le lancement. Les sous-titres intégrés et les pistes audio
secondaires ne sont pas conservés.

## Images

- Réduction pour tenir dans **Full HD** (1920 × 1080) ou **HD Ready** (1280 × 720), dans le sens de
  l'image ; jamais d'agrandissement.
- Compression dans le **même format** : JPEG, PNG, WEBP, HEIC/HEIF (photos d'iPhone), AVIF, TIFF, BMP, GIF.
- Options : **convertir en JPEG** (le plus léger ; la transparence devient un fond blanc) et, pour les
  PNG, **réduire à 256 couleurs** (très efficace sur les logos et captures d'écran).
- La rotation de l'appareil photo est appliquée, puis les **métadonnées sont retirées** (dont la
  position GPS) ; le profil de couleurs est conservé.
- Les images animées ou multipages ne sont pas encore prises en charge.

## Documents bureautiques

Formats : Word (.docx, .docm, .dotx), PowerPoint (.pptx, .pptm, .potx, .ppsx), Excel (.xlsx, .xlsm, .xltx),
LibreOffice / OpenDocument (.odt, .odp, .ods, .odg et leurs modèles). OnlyOffice enregistre dans ces mêmes
formats : ses fichiers sont donc pris en charge.

Seules les **images intégrées** sont recompressées ; le texte, la mise en page, les styles et les
formules ne sont pas touchés. Le document **reste modifiable, au même format**.

| Niveau | Plus grand côté des images | Usage |
|---|---|---|
| Impression | 2480 px (≈ 300 dpi sur une pleine page A4) | impression de qualité |
| **Entre web et impression** (défaut) | 1754 px (≈ 150 dpi sur A4) | écran confortable, impression correcte |
| Écran uniquement | 1280 px | diffusion par mail ou web |

Option (activée par défaut) : les **photos enregistrées en PNG** sont converties en JPEG **à l'intérieur**
du document, quand c'est nettement plus léger et qu'elles n'ont pas de transparence ; les références
internes sont mises à jour automatiquement.

Les anciens formats binaires (.doc, .xls, .ppt, .rtf) ne sont pas pris en charge : ouvrez-les et
enregistrez-les au format actuel.

## PDF

**Compression** (le PDF reste un PDF) :
- images ramenées à la résolution choisie : Impression **200 dpi**, Entre web et impression **150 dpi**
  (défaut), Écran **110 dpi**, en tenant compte de leur taille réelle sur la page ;
- polices intégrées réduites aux seuls caractères utilisés ;
- structure du fichier réécrite au format **PDF 1.5** (« flux d'objets »), plus compact, et objets
  inutilisés supprimés.

**Version modifiable** (en option) : Word (.docx), PowerPoint (.pptx), ou les deux. Le résultat est un
ZIP contenant le PDF compressé et les versions modifiables, dont les images sont elles aussi compressées.

| PDF | Word | PowerPoint |
|---|---|---|
| **Créé par un logiciel** (texte sélectionnable) | paragraphes, styles, tableaux et images reconstitués | une diapositive par page : le fond reprend les images et dessins de la page, chaque bloc de texte devient une **zone de texte modifiable** à sa place (police, taille, couleur, gras, italique) |
| **Scanné** (images de pages) | texte reconnu par **OCR** (français et anglais), un paragraphe par paragraphe détecté, un saut de page par page | fond = page scannée **dont le texte est effacé**, et texte reconnu placé en zones de texte modifiables |

Limites à connaître : la conversion est une **reconstitution**. Sur les mises en page complexes
(colonnes multiples, tableaux imbriqués, formulaires), une relecture et des retouches sont à prévoir.
Sur un scan, la qualité dépend de la netteté du document ; dans Word, les illustrations des pages
scannées ne sont pas reprises (elles restent dans le PDF compressé et dans la version PowerPoint).

La reconnaissance de texte nécessite **Tesseract** : il est inclus dans l'image Docker ; sans Docker,
voir [installation.md](installation.md).
