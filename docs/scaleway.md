# Déploiement sur Scaleway Serverless Containers

Compression pas à pas peut tourner sur [Scaleway Serverless Containers](https://www.scaleway.com/fr/serverless-containers/) :
l'instance démarre à la première visite et s'éteint quand elle ne sert plus (facturation à l'usage).

## Ce qu'il faut savoir avant

Contraintes de Scaleway (vérifiées en novembre 2026, à recontrôler dans la
[page des limites](https://www.scaleway.com/en/docs/serverless-containers/reference-content/containers-limitations/)) :

- **Architecture amd64 uniquement** : l'image publiée `latest` existe en amd64 ; pour construire
  depuis un Mac Apple Silicon, ajouter `--platform linux/amd64`.
- **Mémoire** : jusqu'à environ 12 Go par conteneur. Compter **2 à 4 Go** (vidéos Full HD et gros PDF : 4 Go).
- **Durée d'une requête** : de 10 s à 60 min. Mettre le maximum pour permettre l'envoi de gros fichiers.
- **Mise en veille** : l'instance s'arrête après 15 min sans requête. Le **résultat est alors perdu** :
  il faut le télécharger dès la fin du traitement.
- **Stockage temporaire** : le disque disparaît à l'arrêt de l'instance. Prévoir un stockage
  éphémère d'au moins 3 fois la taille des plus gros fichiers traités.

Conséquences pour Compression pas à pas :

- **Mettre `max-scale` à 1.** Le suivi des travaux est gardé en mémoire dans l'instance ;
  avec plusieurs instances, la page pourrait interroger une instance qui ne connaît pas le travail.
- **Garder l'onglet ouvert pendant le traitement** : la page interroge le serveur chaque
  seconde, ce qui maintient l'instance active.
- Les vidéos longues sont coûteuses en calcul : pour des vidéos de plus d'une heure, préférer un
  poste de travail.

## 1. Disposer de l'image

Le workflow GitHub `Image Docker` publie automatiquement `ghcr.io/<compte>/compression-pas-a-pas:latest`,
**après un contrôle Trivy**.

Scaleway ne sait lire que les images **publiques** des registres externes :

- **Option A, la plus simple** : rendre le paquet public (GitHub → *Packages* → `compression-pas-a-pas`
  → *Package settings* → *Change visibility* → *Public*), puis utiliser directement l'image ghcr.io.
- **Option B, recommandée par Scaleway** : la copier dans votre Scaleway Container Registry :
  ```bash
  docker login rg.fr-par.scw.cloud/<namespace> -u nologin --password-stdin <<< "$SCW_SECRET_KEY"
  docker pull --platform linux/amd64 ghcr.io/<compte>/compression-pas-a-pas:latest
  docker tag ghcr.io/<compte>/compression-pas-a-pas:latest rg.fr-par.scw.cloud/<namespace>/compression-pas-a-pas:latest
  docker push rg.fr-par.scw.cloud/<namespace>/compression-pas-a-pas:latest
  ```

## 2. Créer le conteneur (console Scaleway)

*Serverless* → *Containers* → créer un namespace (région `fr-par`, par exemple) → *Deploy container* :

| Paramètre | Valeur |
|---|---|
| Image | celle de l'étape 1 |
| Port | `8000` (l'application lit aussi la variable `PORT` fournie par Scaleway) |
| Mémoire | **4096 Mo** (le vCPU associé est fixé par Scaleway ; plus de vCPU = vidéos plus rapides) |
| Min scale / Max scale | **0 / 1** |
| Timeout | le maximum (3600 s) |
| Stockage éphémère | au moins 3 fois la taille des plus gros fichiers |
| Variable d'environnement | `SOURCE_URL=https://github.com/<compte>/compression-pas-a-pas` (lien « Code source » exigé par l'AGPL) |
| **Secret** | `APP_PASSWORD` = un mot de passe solide |
| Health check (HTTP) | chemin `/healthz` |

L'adresse publique du conteneur est accessible à tout Internet : **le mot de passe est indispensable**.

## 3. Mise à jour

À chaque nouvelle image (version mensuelle, ou reconstruction hebdomadaire avec les correctifs
de sécurité), relancer *Deploy* sur le conteneur pour qu'il récupère la dernière image.

## Sur téléphone

L'adresse Scaleway étant en **https**, l'application peut être installée sur l'écran d'accueil et
recevoir des fichiers partagés depuis Android : voir [mobile.md](mobile.md).
