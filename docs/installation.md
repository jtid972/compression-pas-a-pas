# Installation

Deux façons de faire, sur toutes les plateformes :

- **Sans Docker** : Python + ffmpeg, et un script qui s'occupe du reste. Le plus simple sur un poste de travail.
- **Avec Docker** : rien à installer à part Docker. Pratique pour un serveur ou un PC partagé.

Deux programmes sont utilisés : **ffmpeg** (vidéos, obligatoire) et **Tesseract** (reconnaissance du
texte des PDF scannés, facultatif : sans lui, seule la conversion des PDF scannés est désactivée).
L'image Docker contient les deux.

Avec Docker, préférez `scripts/verifier-et-lancer` : l'image est construite, **analysée par Trivy**,
et lancée seulement si elle est saine.

---

## Windows

### Sans Docker

1. Ouvrir un terminal (PowerShell) et installer les prérequis :
   ```powershell
   winget install Python.Python.3.13
   winget install Gyan.FFmpeg
   winget install UB-Mannheim.TesseractOCR
   ```
2. **Fermer puis rouvrir** le terminal (pour que `ffmpeg` soit reconnu).
3. Double-cliquer sur `scripts\lancer.bat`. Le premier lancement installe les dépendances
   (quelques minutes), puis le navigateur s'ouvre sur http://localhost:8081.

   Tesseract s'installe avec l'anglais ; pour le français, cocher *French* dans les langues
   supplémentaires pendant l'installation.

### Avec Docker

1. Installer [Docker Desktop](https://www.docker.com/products/docker-desktop/) (il active WSL 2).
2. Dans le dossier du projet : `.\scripts\verifier-et-lancer.ps1`
3. Ouvrir http://localhost:8081.

## macOS

Fonctionne sur Mac Intel et Apple Silicon (M1 à M4…).

### Sans Docker

```bash
brew install python ffmpeg tesseract tesseract-lang   # Homebrew : https://brew.sh
./scripts/lancer.sh
```

### Avec Docker

Installer Docker Desktop pour Mac, puis `./scripts/verifier-et-lancer.sh`.
L'image publiée `ghcr.io/<compte>/compression-pas-a-pas:latest` existe en version arm64 (Apple Silicon).

## Linux

### Sans Docker

```bash
sudo apt install python3 python3-venv ffmpeg tesseract-ocr tesseract-ocr-fra   # Debian / Ubuntu
# sudo dnf install python3 ffmpeg tesseract tesseract-langpack-fra   # Fedora (RPM Fusion pour ffmpeg)
./scripts/lancer.sh
```

### Avec Docker

```bash
./scripts/verifier-et-lancer.sh     # arrêt : docker compose down
```

---

## Accès depuis un autre poste du réseau

Par défaut, l'outil n'écoute que sur la machine elle-même (`127.0.0.1`).

- Sans Docker : `HOST=0.0.0.0 ./scripts/lancer.sh` (Windows : `$env:HOST="0.0.0.0"` avant `lancer.ps1`).
- Docker : dans `docker-compose.yml`, remplacer `"127.0.0.1:8081:8000"` par `"8081:8000"`.

**Activez alors un mot de passe** avec la variable `APP_PASSWORD` : le navigateur le
demandera (le nom d'utilisateur est libre).

## Réglages

Variables d'environnement (dans `docker-compose.yml`, ou avant de lancer le script) :

| Variable | Défaut | Rôle |
|---|---|---|
| `MIN_GAIN` | `10` | gain (%) en dessous duquel le traitement est déconseillé |
| `MAX_UPLOAD_MB` | `4096` | taille maximale d'un fichier envoyé |
| `KEEP_HOURS` | `24` | fichiers et résultats supprimés après ce délai |
| `APP_PASSWORD` | *(vide)* | mot de passe d'accès ; vide = pas de mot de passe |
| `SOURCE_URL` | adresse du dépôt | lien « Code source » du pied de page (obligation de l'AGPL) ; à faire pointer vers votre version si vous la modifiez |
| `TESSERACT_CMD` | *(détection auto)* | chemin de Tesseract s'il n'est pas trouvé automatiquement |
| `DATA_DIR` | `./data` | dossier de travail |
| `HOST` / `PORT` | `127.0.0.1` / `8081` (scripts) | adresse et port d'écoute |

Les réglages de compression eux-mêmes (définition, qualité, son, niveau des images…) se choisissent
dans la page, fichier par fichier. Détails : [fonctionnement.md](fonctionnement.md).
