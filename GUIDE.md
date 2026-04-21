# Serveur Volant Manager — Guide utilisateur

## Avant de lancer l'app

Assure-toi que **Syncthing** et **Tailscale** sont lancés sur ton PC. Sans eux, l'app fonctionnera mais tu ne pourras pas jouer avec les autres.

---

## Première utilisation — Configuration

Clique sur **Parametres** en haut à droite et remplis ces champs :

| Champ | Quoi mettre |
|---|---|
| **Pseudo** | Ton pseudo Minecraft — garde-le toujours identique |
| **Chemin du dossier serveur** | Le chemin vers ton dossier de serveur synchronisé (fourni par l'hôte) |
| **URL Syncthing** | Laisse la valeur par défaut |
| **Clé API Syncthing** | Dans Syncthing → Actions → Configuration → Clé d'API |
| **ID dossier Syncthing** | L'identifiant du dossier partagé (fourni par l'hôte) |
| **Arguments Java** | Laisse la valeur par défaut |
| **Nom du JAR** | Laisse la valeur par défaut |

Clique **Sauvegarder**. Cette configuration est à faire **une seule fois** sur ton PC.

---

## Rejoindre le groupe Syncthing (première fois seulement)

Avant de pouvoir jouer, ton PC doit être synchronisé avec le groupe. Demande l'ID Syncthing à l'hôte, puis :

1. Clique sur **Rejoindre le groupe** dans le header
2. Entre ton pseudo et l'ID Syncthing de l'hôte
3. Clique **Rejoindre**

Syncthing va télécharger automatiquement le dossier serveur sur ton PC. Attends que SYNCHRONISATION passe à **A jour** avant de faire quoi que ce soit.

---

## Les indicateurs

L'app se rafraîchit automatiquement toutes les 3 secondes.

**SYNCHRONISATION** — état de tes fichiers :
- `A jour` → tout est synchronisé, tu peux jouer
- `Synchronisation...` → attends, ne fais rien
- `Syncthing offline` → lance Syncthing

**SERVEUR** — qui héberge :
- `Hors ligne` → personne, le serveur est libre
- `En ligne chez [Pseudo]` → quelqu'un héberge, tu peux rejoindre

---

## Héberger le serveur

1. Vérifie que SYNCHRONISATION affiche **A jour**
2. Clique **Heberger**
3. Connecte-toi dans Minecraft sur **`localhost:25565`**

Les autres verront le serveur apparaître dans leur app quelques secondes après.

---

## Rejoindre une session

1. Attends que SYNCHRONISATION affiche **A jour**
2. Clique **Rejoindre**
3. Copie l'IP affichée dans la popup
4. Dans Minecraft : Multijoueur → Connexion directe → colle l'IP

---

## Arrêter le serveur

1. Clique **Arreter le serveur**
2. Attends le message *"Sauvegarde synchronisee"* dans la console avant de fermer l'app

> Ne ferme **jamais** la fenêtre brutalement pendant que tu héberges — ça peut corrompre la sauvegarde.

---

## Passer la main à quelqu'un d'autre

1. L'hôte clique **Arreter le serveur** et attend la fin de la sync
2. Tout le monde attend **A jour**
3. Le nouvel hôte clique **Heberger**

---

## En cas de problème

**Le bouton Heberger est grisé** → Quelqu'un héberge déjà, ou un `lock.json` fantôme traîne. Supprime `lock.json` manuellement dans le dossier serveur.

**Syncthing offline** → Lance Syncthing, attends qu'il affiche **A jour**.

**IP Tailscale introuvable** → Vérifie que Tailscale est connecté.

**Java introuvable** → Installe Java 17+ et redémarre ton PC.

**Un ami ne peut pas rejoindre** → Vérifiez que vous êtes bien sur le même réseau Tailscale.

**La sync ne se termine pas** → Vérifie dans Syncthing que le dossier serveur est bien partagé avec toi.
