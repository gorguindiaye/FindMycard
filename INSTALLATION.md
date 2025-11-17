# 📱 Guide d'installation - FindMyID

## 🎯 Vue d'ensemble
FindMyID est une application web complète pour retrouver les pièces d'identité perdues. Elle utilise React pour le frontend et Django pour le backend avec un système OCR intelligent.

## 📋 Prérequis

### Système
- Windows 10/11, macOS ou Linux
- Python 3.8 ou supérieur
- Node.js 16 ou supérieur
- npm ou yarn

### Outils recommandés
- Git
- Un éditeur de code (VS Code, PyCharm, etc.)
- Redis (optionnel, pour les tâches asynchrones)

## 🚀 Installation rapide

### 1. Cloner le projet
```bash
git clone <url-du-repo>
cd FindMyCard
```

### 2. Backend Django

#### Installation automatique (Windows)
```bash
start_backend.bat
```

#### Installation manuelle
```bash
cd backend

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# Initialiser la base de données
python init_db.py

# Démarrer le serveur
python manage.py runserver
```

### 3. Frontend React

#### Installation automatique (Windows)
```bash
start_frontend.bat
```

#### Installation manuelle
```bash
cd frontend

# Installer les dépendances
npm install

# Démarrer le serveur de développement
npm start
```

## 🔧 Configuration

### Variables d'environnement
Copiez le fichier `backend/env.example` vers `backend/.env` et configurez :

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
```

### Base de données
Par défaut, l'application utilise SQLite. Pour PostgreSQL :

1. Installer PostgreSQL
2. Créer une base de données
3. Modifier `DATABASES` dans `backend/findmyid/settings.py`

## 🌐 Accès à l'application

### Frontend
- URL: http://localhost:3000
- Interface utilisateur principale

### Backend API
- URL: http://localhost:8000/api/
- Documentation API: http://localhost:8000/api/

### Admin Django
- URL: http://localhost:8000/admin/
- Utilisateur: admin
- Mot de passe: admin123

## 📱 Fonctionnalités principales

### Pour les utilisateurs
1. **Inscription/Connexion** - Créer un compte et se connecter
2. **Déclarer une perte** - Signaler la perte d'une pièce d'identité
3. **Déclarer une trouvaille** - Signaler avoir trouvé une pièce
4. **Voir les correspondances** - Consulter les correspondances trouvées
5. **Notifications** - Recevoir des alertes en temps réel

### Pour les administrateurs
1. **Gestion des utilisateurs** - Via l'interface admin Django
2. **Suivi des déclarations** - Voir toutes les pertes et trouvailles
3. **Gestion des correspondances** - Valider ou rejeter les matches
4. **Statistiques** - Analyser l'utilisation de l'application

## 🔍 Système OCR

L'application utilise EasyOCR pour extraire automatiquement les informations des pièces d'identité :

- **Reconnaissance de texte** - Extraction du nom, prénom, date de naissance
- **Traitement d'image** - Amélioration automatique de la qualité
- **Confiance** - Score de confiance pour chaque extraction

## 🔐 Sécurité

- **Authentification JWT** - Tokens sécurisés pour l'API
- **Validation des données** - Vérification côté client et serveur
- **CORS configuré** - Protection contre les requêtes cross-origin
- **Chiffrement des mots de passe** - Hachage sécurisé avec Django

## 🐛 Dépannage

### Problèmes courants

#### Backend ne démarre pas
```bash
# Vérifier Python
python --version

# Vérifier les dépendances
pip list

# Vérifier les migrations
python manage.py showmigrations
```

#### Frontend ne démarre pas
```bash
# Vérifier Node.js
node --version
npm --version

# Nettoyer le cache
npm cache clean --force

# Supprimer node_modules et réinstaller
rm -rf node_modules package-lock.json
npm install
```

#### Problèmes de CORS
Vérifier que le backend est bien sur `http://localhost:8000` et le frontend sur `http://localhost:3000`.

### Logs
- Backend: Les logs apparaissent dans la console Django
- Frontend: Ouvrir les outils de développement du navigateur

## 📞 Support

Pour toute question ou problème :
1. Vérifier la documentation
2. Consulter les logs d'erreur
3. Créer une issue sur le repository

## 🚀 Déploiement

### Production
Pour déployer en production :

1. **Backend**
   - Configurer une base de données PostgreSQL
   - Configurer un serveur web (Nginx + Gunicorn)
   - Configurer les variables d'environnement
   - Activer HTTPS

2. **Frontend**
   - Build de production : `npm run build`
   - Servir les fichiers statiques
   - Configurer un CDN si nécessaire

### Docker (optionnel)
```bash
# Build des images
docker-compose build

# Démarrer les services
docker-compose up -d
```

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails. 