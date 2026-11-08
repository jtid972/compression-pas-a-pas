# Mentions — Compression pas à pas

## Droit d'auteur

Copyright (c) 2026 Johan TIDAS.

L'auteur conserve l'intégralité de ses droits d'auteur sur le projet (code, documentation,
visuels). La licence accorde des droits d'utilisation ; elle ne transfère aucun droit.

## Licence

L'ensemble du projet (code, documentation, visuels) est distribué sous la
**GNU Affero General Public License, version 3 ou ultérieure** (AGPL-3.0-or-later). Le texte
officiel complet est dans [`LICENSE`](LICENSE).

```
Compression pas à pas
Copyright (c) 2026 Johan TIDAS

This program is free software: you can redistribute it and/or modify it under the terms of
the GNU Affero General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.
```

### En résumé (non contractuel ; seul le texte de `LICENSE` fait foi)

- **Vous pouvez** utiliser, étudier, modifier et redistribuer le logiciel, y compris dans un
  cadre professionnel.
- **À condition de** fournir le code source complet, sous AGPL-3.0, de toute version que vous
  distribuez **ou que vous faites utiliser à distance** (réseau, service en ligne) ; de conserver
  les mentions de droit d'auteur et d'attribution ci-dessous ; et d'indiquer vos modifications.
- **Aucune garantie** : le logiciel est fourni « tel quel ».

## Conditions supplémentaires (article 7 de l'AGPL-3.0)

Conformément à l'article 7, paragraphes b) et e), de la licence :

1. **Attributions à conserver.** Toute copie ou version modifiée doit conserver, dans sa
   documentation et dans le pied de page de son interface web, les mentions suivantes :
   - « Compression pas à pas — Copyright (c) 2026 Johan TIDAS » ;
   - « Code réalisé avec l'assistance de Claude, l'IA d'Anthropic ».
2. **Nom.** La licence n'accorde aucun droit d'utiliser le nom « Compression pas à pas » pour
   désigner une version modifiée ou un service dérivé, sauf pour indiquer honnêtement l'origine
   du logiciel (« basé sur Compression pas à pas »).

## Licence commerciale

L'auteur, seul titulaire des droits, peut accorder une **licence commerciale séparée** à ceux
qui souhaitent utiliser ou intégrer Compression pas à pas **sans les obligations de l'AGPL**
(par exemple, garder leurs modifications fermées, ou l'intégrer dans un produit propriétaire).

> **Important — PyMuPDF.** Le traitement des PDF utilise PyMuPDF, lui-même distribué sous AGPL-3.0
> par Artifex (ou sous licence commerciale Artifex). Une licence commerciale de Compression pas à pas
> ne couvre **pas** PyMuPDF : un licencié commercial qui veut s'affranchir de l'AGPL doit aussi obtenir
> une licence commerciale auprès d'Artifex, ou utiliser une version sans traitement des PDF.
**Contact** : ouvrir un ticket **« Demande de licence commerciale »** sur le dépôt GitHub
(onglet *Issues* → *New issue*). Les tickets sont publics : n'y indiquez rien de confidentiel.
L'auteur vous répondra pour poursuivre l'échange en privé.

## Assistance par intelligence artificielle

Le code et la documentation de ce projet ont été réalisés **avec l'assistance de Claude,
l'IA d'Anthropic**, pour la génération de code. La conception, les choix fonctionnels, la
relecture, les tests et la maintenance sont assurés par l'auteur.

## Composants tiers

Compression pas à pas **utilise** les logiciels suivants, chacun sous sa propre licence, toutes
compatibles avec l'AGPL-3.0.

| Composant | Rôle | Licence |
|---|---|---|
| [FFmpeg](https://ffmpeg.org/) | vidéos, son, MP3 | LGPL 2.1+ / GPL 2+ selon la compilation ; appelé comme programme séparé |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | reconnaissance du texte des PDF scannés | Apache-2.0 ; appelé comme programme séparé |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (Artifex) | lecture, compression et analyse des PDF | **AGPL-3.0** ou licence commerciale Artifex |
| [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx) | conversion PDF → Word | MIT |
| [python-docx](https://github.com/python-openxml/python-docx) / [python-pptx](https://github.com/scanny/python-pptx) | création des documents Word / PowerPoint | MIT |
| [Pillow](https://github.com/python-pillow/Pillow) | images | MIT-CMU (HPND) |
| [pillow-heif](https://github.com/bigcat88/pillow_heif) | photos HEIC/HEIF | BSD-3-Clause (bibliothèques intégrées : libheif LGPL-3.0, x265 GPL-2.0+) |
| OpenCV, NumPy, fontTools, Fire (dépendances de pdf2docx) | analyse de mise en page | Apache-2.0 / BSD-3-Clause / MIT |
| [FastAPI](https://github.com/fastapi/fastapi) | serveur web | MIT |
| [Uvicorn](https://github.com/encode/uvicorn) | serveur HTTP | BSD-3-Clause |
| [python-multipart](https://github.com/Kludex/python-multipart) | réception des fichiers | Apache-2.0 |

**Images Docker** : elles contiennent Debian, Python et les paquets `ffmpeg` (GPL) et `tesseract-ocr`
de la distribution. Leur code source est disponible auprès de Debian :
<https://sources.debian.org/src/ffmpeg/> et <https://sources.debian.org/src/tesseract/>.
