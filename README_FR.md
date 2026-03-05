# 🎵 Music-Off : Suppresseur de Musique par IA

Supprimez la musique des fichiers audio et vidéo grâce à l'IA, tout en préservant la voix et les effets sonores.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Demucs](https://img.shields.io/badge/AI-Demucs%20by%20Meta-purple)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)

## ✨ Fonctionnalités

- 🧠 **Intelligence Artificielle** — Utilise le modèle Demucs de Meta pour une séparation audio de pointe
- 🎬 **Vidéo + Audio** — Prend en charge MP4, MKV, AVI, MOV, MP3, WAV, FLAC et plus
- ⏱️ **Jusqu'à 30 minutes** — Traitement de fichiers média jusqu'à 30 minutes (jusqu'à 1 Go)
- 🎯 **Préserve la voix** — Supprime uniquement la musique tout en conservant le dialogue
- 📂 **Sortie personnalisée** — Parcourez ou saisissez un chemin pour enregistrer les résultats n'importe où
- ⚡ **Accélération GPU** — Utilise automatiquement votre GPU (NVIDIA CUDA) si disponible
- 🌗 **Thèmes sombre et clair** — Basculez entre un thème sombre premium et un thème clair bleu ciel
- 🌍 **Multilingue** — Disponible en anglais, arabe (avec RTL) et français
- 🔧 **Configuration FFmpeg** — Détection automatique de FFmpeg, ou navigation manuelle pour définir son emplacement
- 🖥️ **Belle interface** — Design premium avec glisser-déposer et effets de glassmorphisme

---

## 🚀 Démarrage rapide (Étape par étape)

Suivez ces instructions attentivement — aucune expérience en programmation n'est nécessaire !

### Étape 1 : Installer Python

1. Allez sur **[python.org/downloads](https://python.org/downloads)**
2. Cliquez sur le gros bouton jaune **« Download Python »**
3. Exécutez le programme d'installation téléchargé
4. ⚠️ **IMPORTANT :** Cochez la case **« Add Python to PATH »** en bas de l'installateur avant de cliquer sur « Install Now »
5. Cliquez sur **« Install Now »** et attendez la fin de l'installation

> **Pour vérifier :** Ouvrez le menu Démarrer, tapez `cmd`, appuyez sur Entrée, puis tapez `python --version` et appuyez sur Entrée. Vous devriez voir quelque chose comme `Python 3.12.x`.

### Étape 2 : Installer FFmpeg (Requis pour les fichiers vidéo)

FFmpeg est nécessaire pour traiter les fichiers vidéo (MP4, MKV, etc.). Si vous ne prévoyez d'utiliser que des fichiers audio (MP3, WAV), vous pouvez ignorer cette étape.

1. Allez sur **[ffmpeg.org/download.html](https://ffmpeg.org/download.html)**
2. Sous **« Get packages & executable files »**, cliquez sur l'icône **Windows**
3. Cliquez sur **« Windows builds from gyan.dev »**
4. Téléchargez le fichier **ffmpeg-release-essentials.zip**
5. Extrayez le fichier dans un dossier, par exemple : `C:\ffmpeg`
6. **Ajoutez FFmpeg au PATH système :**
   - Appuyez sur `Win + R`, tapez `sysdm.cpl`, puis appuyez sur Entrée
   - Allez dans l'onglet **« Advanced »** → Cliquez sur **« Environment Variables »**
   - Sous **« System variables »**, trouvez **« Path »** → Cliquez sur **« Edit »**
   - Cliquez sur **« New »** et ajoutez le chemin du dossier `bin` de FFmpeg, ex. : `C:\ffmpeg\bin`
   - Cliquez sur **OK** dans toutes les fenêtres

> **Pour vérifier :** Ouvrez une **nouvelle** fenêtre d'invite de commandes, tapez `ffmpeg -version` et appuyez sur Entrée.

### Étape 3 : Télécharger Music-Off

**Option A — Télécharger en ZIP (le plus simple) :**
1. Sur cette page GitHub, cliquez sur le bouton vert **« Code »**
2. Cliquez sur **« Download ZIP »**
3. Extrayez le ZIP dans un dossier, par exemple : `C:\Users\VotreNom\music-off`

**Option B — Avec Git (si Git est installé) :**
```
git clone https://github.com/daoudz/music-off.git
```

### Étape 4 : Exécuter le script d'installation

1. Ouvrez le dossier où vous avez extrait Music-Off
2. **Double-cliquez** sur le fichier **`setup.bat`**
3. Une fenêtre de commande s'ouvrira et installera tout automatiquement
4. Attendez la fin — cela peut prendre **5 à 10 minutes**
5. Quand vous voyez **« Setup complete! »**, appuyez sur une touche pour fermer

### Étape 5 : Lancer l'application

1. **Double-cliquez** sur le fichier **`start.py`**
   - Si cela ne fonctionne pas, ouvrez l'invite de commandes dans le dossier Music-Off et exécutez :
     ```
     venv\Scripts\activate
     python start.py
     ```
2. Votre navigateur s'ouvrira automatiquement sur **http://127.0.0.1:8765**
3. L'application est maintenant en marche ! 🎉

---

## 🎬 Comment utiliser

1. **Définir le dossier de sortie** — Cliquez sur **📁 Parcourir** (ou saisissez un chemin)
2. **Téléverser un fichier** — Glissez-déposez un fichier ou cliquez pour parcourir
3. **Attendre le traitement IA** — L'IA sépare l'audio. Cela prend **1 à 5 minutes** selon la durée du fichier
4. **Télécharger** — Cliquez sur **Télécharger** pour récupérer le fichier sans musique

---

## 📋 Formats pris en charge

| Type | Formats |
|------|---------|
| **Audio** | MP3, WAV, FLAC, OGG, AAC, M4A, WMA |
| **Vidéo** | MP4, MKV, AVI, MOV, WebM, FLV, WMV |

**Limites :** Taille maximale **1 Go** et durée maximale **30 minutes**.

---

## 🛠️ Technologies

| Composant | Technologie |
|-----------|-------------|
| Modèle IA | Demucs (htdemucs) par Meta |
| Backend | Python + FastAPI |
| Traitement média | FFmpeg |
| Frontend | HTML / CSS / JS |

---

## ❓ Dépannage

### « Python is not recognized as a command »
Installez Python et assurez-vous d'avoir coché **« Add Python to PATH »**. Réinstallez Python si nécessaire.

### « FFmpeg not found »
FFmpeg n'est pas dans le PATH système. Suivez l'étape 2 ci-dessus. Après l'ajout, **fermez et rouvrez** toutes les fenêtres de commande.

### « AI separation failed »
- Vérifiez que le script d'installation (`setup.bat`) s'est terminé sans erreur
- Réexécutez le script d'installation
- Assurez-vous d'avoir au moins **2 Go d'espace libre** pour le modèle IA

### L'application est lente
- La vitesse dépend de la durée du fichier et de votre matériel
- Un fichier d'**1 minute** prend généralement **1 à 3 minutes** sur CPU
- Avec un GPU NVIDIA, installez [PyTorch avec CUDA](https://pytorch.org/get-started/locally/) pour un traitement beaucoup plus rapide

---

## 📄 Licence

MIT
