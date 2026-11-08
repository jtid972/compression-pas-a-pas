# Sécurité

## Signaler une faille

Merci de **ne pas** ouvrir de ticket public. Utilisez le signalement privé de GitHub :
onglet *Security* → *Report a vulnerability*. Une réponse est donnée dès que possible.

## Bonnes pratiques d'utilisation

- Par défaut, l'outil n'est accessible que depuis la machine elle-même.
- Dès qu'il est ouvert au réseau ou à Internet (Scaleway), définissez `APP_PASSWORD`.
- Les fichiers envoyés et les résultats sont supprimés après `KEEP_HOURS` (24 h par défaut).
- Le traitement est local : aucun contenu n'est envoyé à un service tiers.

## Suivi des vulnérabilités

Analyse Trivy chaque semaine, alertes et mises à jour Dependabot : voir [docs/maintenance.md](docs/maintenance.md).
