# Compression pas à pas

**Allège vos vidéos, images, documents bureautiques et PDF, sans changer leur format,
avec une estimation du gain avant de lancer le traitement.**

| Type | Ce qui est fait | Le fichier reste |
|---|---|---|
| **Vidéo** (MP4, MOV, MKV, WEBM, AVI, 3GP, TS…) | réduction en **Full HD (1920 max)** ou **HD Ready (1280 max)**, réencodage efficace, **son réglable** (normal, réduit, mono, sans son), **MP3 séparé** en option | dans le même format |
| **Image** (JPEG, PNG, WEBP, HEIC, AVIF, TIFF, BMP, GIF) | réduction en Full HD ou HD Ready, compression ; option **conversion en JPEG** ; option PNG 256 couleurs | dans le même format (sauf option JPEG) |
| **Bureautique** : Word, PowerPoint, Excel, LibreOffice (Writer, Impress, Calc, Draw), OnlyOffice | recompression des **images à l'intérieur** du document, en qualité entre web et impression | modifiable, au même format |
| **PDF** (y compris scanné) | compression des images, polices réduites aux caractères utilisés, structure PDF 1.5 plus compacte ; **version Word et/ou PowerPoint modifiable** en option, avec **reconnaissance du texte** pour les PDF scannés | PDF, plus les versions modifiables dans un ZIP |

**Avant chaque traitement, le gain est estimé.** S'il est inférieur à 10 %, l'outil conseille
de ne pas lancer le traitement. Si le résultat n'est pas plus léger, l'original est rendu tel quel.

Tout est traité **sur votre machine ou votre serveur** : aucun fichier n'est envoyé à un service extérieur.

L'outil s'utilise **sur ordinateur et sur téléphone**. On peut l'**installer comme une application**
et lui **partager un fichier** depuis la galerie ou le gestionnaire de fichiers (voir [docs/mobile.md](docs/mobile.md)).

---

## Installation rapide

| Plateforme | Méthode conseillée | Détails |
|---|---|---|
| **Windows 10/11** | double-clic sur `scripts\lancer.bat`, ou Docker Desktop | [docs/installation.md](docs/installation.md#windows) |
| **macOS** (Intel et Apple Silicon) | `./scripts/lancer.sh`, ou Docker Desktop | [docs/installation.md](docs/installation.md#macos) |
| **Linux** | `./scripts/lancer.sh`, ou Docker | [docs/installation.md](docs/installation.md#linux) |
| **Scaleway Serverless Containers** | image `ghcr.io/<compte>/compression-pas-a-pas:latest` | [docs/scaleway.md](docs/scaleway.md) |

Avec Docker, **en vérifiant la sécurité avant chaque lancement** (construction, analyse Trivy, puis
lancement seulement si l'image est saine) :

```bash
./scripts/verifier-et-lancer.sh          # Windows : .\scripts\verifier-et-lancer.ps1
```

puis ouvrir **http://localhost:8081** (Vidéo pas à pas utilise le port 8080 : les deux peuvent tourner ensemble).

## Documentation

- [Installation sur Windows, macOS et Linux, réglages](docs/installation.md)
- [Ce que fait l'outil pour chaque type de fichier](docs/fonctionnement.md)
- [Utilisation sur téléphone : application installable et partage](docs/mobile.md)
- [Déploiement sur Scaleway Serverless Containers](docs/scaleway.md)
- [Maintenance : Trivy, mises à jour automatiques, versions mensuelles](docs/maintenance.md)
- [Feuille de route (traitement par lot…)](docs/feuille-de-route.md)
- [Sécurité](SECURITY.md) · [Journal des versions](CHANGELOG.md) · [Contribuer](CONTRIBUTING.md)

## Licence et droit d'auteur

Copyright (c) 2026 Johan TIDAS. L'auteur conserve l'intégralité de ses droits d'auteur.

Logiciel libre sous licence **[GNU AGPL-3.0](LICENSE)** (version 3 ou ultérieure), pour le code
comme pour la documentation. Vous pouvez l'utiliser, le modifier et le partager, à condition de
publier sous la même licence le code de toute version que vous distribuez **ou que vous
proposez en service en ligne**, et de conserver les mentions d'auteur.

Une **licence commerciale** est disponible auprès de l'auteur pour un usage sans ces obligations
(voir la remarque sur PyMuPDF dans [NOTICE.md](NOTICE.md)).

**Code réalisé avec l'assistance de Claude (IA d'Anthropic) et de Mistral Vibe (IA Mistral)**,
pour la génération de code.
