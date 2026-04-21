Tu es un développeur logiciel Expert. Ta mission est de développer une application de bureau Windows de type "Launcher" pour un projet de Serveur Minecraft Décentralisé (P2P).

TECH STACK REQUIS :
- Langage et UI : [CHOISIS ICI : Python avec CustomTkinter OU C# avec WPF OU Node.js avec Electron]
- Environnement cible : Windows. L'application doit être un exécutable local.

CONTEXTE DU PROJET :
Le groupe de joueurs n'a pas de serveur central. Ils synchronisent un dossier de serveur Minecraft (PaperMC) via Syncthing. Ils utilisent Tailscale pour le réseau P2P. Le launcher doit s'assurer que jamais deux joueurs ne lancent le serveur en même temps, sous peine de corrompre la sauvegarde.

LES 3 MÉCANISMES CLÉS À CODER :

1. LE VERROU (Session Lock) :
Le système repose sur un fichier `lock.json` à la racine du dossier serveur.
- Format du fichier : {"status": "online", "host": "PseudoDuJoueur", "ip": "100.x.x.x:25565"}
- Si ce fichier existe, un autre joueur héberge déjà. Le bouton "Héberger" doit être grisé.
- Si le fichier n'existe pas, le serveur est libre.

2. L'API SYNCTHING (Sécurité des fichiers) :
L'application doit interroger l'API locale de Syncthing (URL: http://localhost:8384/rest/db/status?folder=MC_PROJET_SERVEUR). Il faut prévoir un champ dans les paramètres pour que l'utilisateur renseigne sa clé d'API Syncthing.
- Si l'état retourné est "syncing", TOUT doit être bloqué (risque de corruption).
- Si l'état retourné est "idle", les fichiers sont à jour.

3. LA GESTION DU PROCESSUS JAVA :
Lorsque l'utilisateur héberge, l'app doit exécuter la commande : `java -Xmx2G -Xms2G -jar paper.jar nogui` en arrière-plan, capturer l'output (stdout) pour l'afficher dans une console de l'UI, et pouvoir envoyer la commande `stop` via stdin pour l'éteindre proprement.

L'INTERFACE UTILISATEUR (UI) :
L'interface doit être moderne, sombre (Dark Mode) et contenir :
- Titre : "Serveur Volant Manager"
- Un indicateur d'état Syncthing (Ex: 🟢 À jour, ou 🟡 Synchronisation en cours).
- Un indicateur d'état du Serveur (Ex: 🔴 Hors ligne, ou 🔵 En ligne chez [Pseudo]).
- Bouton "Héberger" : Lance le processus Java ET crée le `lock.json`.
- Bouton "Rejoindre" : N'est cliquable que si `lock.json` existe. Affiche l'IP à rejoindre.
- Bouton "Arrêter le serveur" : N'apparaît que si l'utilisateur actuel héberge. Envoie 'stop' au serveur, attend la fin du processus, puis supprime `lock.json`.
- Une TextBox (Read-Only) en bas servant de console pour afficher les logs du serveur Java et de l'application.

INSTRUCTIONS DE DÉVELOPPEMENT :
1. Agis comme un architecte : génère d'abord la structure du code (classes, fonctions) avant de les remplir.
2. Gère les erreurs proprement (Timeout de l'API Syncthing, fichier Java introuvable, permissions d'écriture).
3. Le chemin du dossier serveur doit être configurable (par exemple stocké dans un petit fichier `config.ini` local à l'application).
4. Fournis le code complet et les instructions exactes pour que je puisse lancer et compiler ce projet sur ma machine.