@echo off
title Serveur Volant Manager

:: Vérifie que Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
    echo Telecharge Python sur https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Installe les dépendances si besoin
echo Installation / vérification des dépendances...
pip install -r requirements.txt --quiet

:: Lance l'application
echo Lancement de Serveur Volant Manager...
python main.py

pause
