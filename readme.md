# 🚀 Projet : Serveur Minecraft Décentralisé ("Floating Host")

## 1. Contexte et Objectifs
Le but du projet est de créer un serveur Minecraft multijoueur qui répond à des contraintes strictes :
* **100% Gratuit et sans hébergeur :** Pas de serveur allumé 24h/24, le serveur tourne directement sur le PC du joueur qui veut jouer.
* **Décentralisé (Hôte Volant) :** N'importe quel joueur du groupe peut "lancer" le serveur et inviter les autres. Quand il s'arrête, un autre peut prendre le relais.
* **Accessibilité "Crack" :** Le serveur doit accepter les versions non-officielles de Minecraft (`online-mode=false`).
* **Sécurité des Inventaires :** Résoudre le bug du mode Solo où le changement d'hôte écrase les inventaires. Tout le monde doit garder son corps et ses items.
* **Simplicité finale :** Créer une application de type "Launcher" pour cacher la complexité technique aux joueurs et automatiser les connexions.

---

## 2. L'Architecture Technique (Les 3 Piliers)

Pour que la magie opère sans serveur centralisé, le projet s'appuie sur trois technologies distinctes qui travaillent ensemble :

| Couche | Technologie utilisée | Rôle dans le projet |
| :--- | :--- | :--- |
| **Le Moteur de Jeu** | **PaperMC (1.21.11)** | Un vrai serveur dédié local. Il stocke les joueurs dans `playerdata` pour éviter les conflits d'inventaire, et sépare les dimensions (`world_nether`, `world_the_end`). |
| **Le Réseau P2P** | **Tailscale** | Remplace l'ouverture de ports (Port Forwarding). Crée un tunnel direct (WireGuard) entre les joueurs. Géré via le "Node Sharing" pour éviter les conflits de comptes. |
| **La Synchronisation**| **Syncthing** | Maintient le dossier du serveur (`MC_PROJET_SERVEUR`) identique sur tous les PC en temps réel. Ne transfère que les fichiers modifiés pour une vitesse maximale. |

---

## 3. Le Mécanisme de "Verrou" (Session Lock)

C'est le cœur de la logique de protection des données que ton application devra gérer. Si deux joueurs lancent le serveur en même temps, la sauvegarde est corrompue.
* **Le Fichier Témoin :** L'application utilise un fichier texte nommé `lock.json`, placé à la racine du serveur.
* **Le Contenu :** Lorsqu'un joueur héberge, l'app y écrit ses infos : `{"status": "online", "host": "Pseudo", "ip": "100.x.x.x:25565"}`.
* **La Diffusion :** Syncthing partage instantanément ce fichier chez tous les autres joueurs.
* **La Sécurité :** Si l'application détecte que ce fichier existe, elle **interdit** de lancer le serveur localement et force le mode "Rejoindre".

---

## 4. Spécifications de l'Application "Manager" (À développer)

Ton application sera l'interface unique pour tes amis. Elle doit agir comme une surcouche intelligente qui automatise les tâches ingrates.

### A. Interface Utilisateur (UI)
* **État du Réseau :** Un indicateur visuel de l'état de Syncthing (ex: 🟢 *À jour*, 🟡 *Synchronisation en cours...*).
* **État du Serveur :** Un indicateur lisant le `lock.json` (ex: 🔴 *Hors ligne*, 🔵 *En ligne chez [Pseudo]*).
* **Bouton "Héberger" :** Démarre le serveur local.
* **Bouton "Rejoindre" :** Lance directement le jeu avec la bonne IP.
* **Console d'événement :** Une petite zone de texte pour afficher ce que fait l'application ("Vérification des fichiers...", "Lancement de PaperMC...").

### B. Logique Interne (Le Code)

L'application doit exécuter des scénarios précis selon l'action de l'utilisateur.

#### Scénario 1 : Le joueur clique sur "Héberger"
1.  **Vérification de Syncthing :** L'app interroge l'API locale de Syncthing (`http://localhost:8384/rest/db/status`).
    * *Si la réponse n'est pas "idle" (À jour) -> Bloquer l'action avec un message d'erreur.*
2.  **Vérification du Verrou :** L'app cherche la présence de `lock.json`.
    * *Si présent -> Bloquer l'action.*
3.  **Prise de contrôle :** L'app crée le fichier `lock.json` avec l'IP Tailscale du joueur.
4.  **Lancement serveur :** L'app exécute silencieusement le `start.bat` (ou la commande Java directement) et garde le processus actif.
5.  **Lancement jeu :** L'app lance le client Minecraft du joueur pour qu'il se connecte à `localhost`.

#### Scénario 2 : Le joueur clique sur "Rejoindre"
1.  **Lecture du Verrou :** L'app lit le fichier `lock.json` pour récupérer l'IP Tailscale de l'hôte actuel.
2.  **Connexion :** (Optionnel/Avancé) L'app lance le client Minecraft du joueur et injecte l'IP pour rejoindre directement, ou indique simplement au joueur l'IP à copier/coller.

#### Scénario 3 : Le joueur arrête le serveur (Fermeture)
1.  **Arrêt propre :** L'app envoie la commande `stop` à la console Java cachée du serveur.
2.  **Libération du verrou :** Une fois le processus Java terminé, l'app supprime le fichier `lock.json`.
3.  **Attente Syncthing :** L'app affiche "Envoi de la sauvegarde aux autres joueurs..." et surveille l'API Syncthing jusqu'à ce que la synchronisation soit terminée.

---

## 5. Obstacles Techniques Déjà Résolus
Pour mémoire, voici les éléments cruciaux qui ont été paramétrés en amont et qui rendent ce projet viable aujourd'hui :
* **Le problème des GUID (UUID) en crack :** Réglé par le fait d'avoir des pseudos uniques dans le launcher.
* **Le vol d'inventaire de l'Hôte :** Réglé par l'abandon du système "Ouvrir au LAN" au profit d'un vrai `server.jar`.
* **La suppression des dimensions (Nether/End) par Paper :** Réglé par la migration manuelle des dossiers `DIM-1` et `DIM1` hors du dossier `world`.
* **Le blocage de la double authentification Tailscale :** Réglé en utilisant la fonctionnalité de partage de machine ("Share Node") plutôt qu'un compte commun.

En développant cette application, tu vas relier tous ces concepts complexes avec du code (Python, C#, ou JS) pour offrir une expérience "Plug & Play" à tes amis.