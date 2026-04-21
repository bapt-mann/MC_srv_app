# ⛏ Serveur Volant Manager — Guide utilisateur

## Avant de lancer l'app

Assure-toi que **Syncthing** et **Tailscale** sont lancés sur ton PC. Sans eux, l'app fonctionnera mais tu ne pourras pas jouer avec les autres.

---

## Première utilisation — Configuration

Clique sur **⚙️** en haut à droite et remplis ces champs :

| Champ | Quoi mettre |
|---|---|
| **Pseudo** | Ton pseudo Minecraft (garde-le toujours identique) |
| **Chemin du dossier serveur** | Le chemin vers ton dossier `MC_PROJET_SERVEUR` synchronisé |
| **Clé API Syncthing** | Dans Syncthing → Actions → Paramètres → Clé API GUI |
| **ID dossier Syncthing** | L'identifiant du dossier dans Syncthing (ex: `MC_PROJET_SERVEUR`) |

Laisse les autres champs par défaut. Clique **Sauvegarder**.

> Cette configuration est à faire **une seule fois** sur ton PC.

---

## Les indicateurs en haut

L'app se rafraîchit automatiquement toutes les 3 secondes.

**SYNCHRONISATION** — état de tes fichiers :
- 🟢 À jour → tout est bon
- 🟡 Synchronisation... → attends avant de faire quoi que ce soit
- ⚫ Hors ligne → lance Syncthing

**SERVEUR** — qui héberge :
- 🔴 Hors ligne → personne, le serveur est libre
- 🔵 En ligne chez [Pseudo] → quelqu'un héberge, tu peux rejoindre

---

## Héberger le serveur

1. Vérifie que SYNCHRONISATION affiche 🟢 À jour
2. Clique **🟢 Héberger**
3. Connecte-toi dans Minecraft sur **`localhost:25565`**

Les autres joueurs verront ton serveur apparaître dans leur app quelques secondes après.

---

## Rejoindre une session

1. Attends que SYNCHRONISATION affiche 🟢 À jour
2. Clique **🔵 Rejoindre**
3. Copie l'IP affichée dans la popup
4. Dans Minecraft : Multijoueur → Connexion directe → colle l'IP

---

## Arrêter le serveur

1. Clique **🔴 Arrêter le serveur**
2. Attends le message *"Sauvegarde synchronisée"* dans la console avant de fermer l'app

> ⚠️ Ne ferme **jamais** la fenêtre brutalement pendant que tu héberges — ça peut corrompre la sauvegarde.

---

## Passer la main à quelqu'un d'autre

1. L'hôte actuel clique **Arrêter le serveur** et attend la fin de la sync
2. Tout le monde attend le 🟢 À jour
3. Le nouvel hôte clique **Héberger**

---

## En cas de problème

**Le bouton Héberger est grisé** → Quelqu'un héberge déjà, ou un `lock.json` fantôme est bloqué. Dans ce cas, supprime `lock.json` manuellement dans le dossier serveur.

**IP Tailscale introuvable** → Vérifie que Tailscale est connecté sur ton PC.

**Java introuvable** → Installe Java 17+ depuis [adoptium.net](https://adoptium.net) et redémarre ton PC.

**Un ami ne peut pas rejoindre** → Vérifiez que vous êtes bien connectés au même réseau Tailscale (Node Sharing).
