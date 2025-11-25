# 📱 FindMyCard – Retrouvons vos pièces

## 🔰 Introduction
La perte d'une pièce d'identité ou d'un document officiel est une expérience frustrante et stressante. FindMyCard est une application web intelligente qui facilite la déclaration, l'identification et la restitution des pièces perdues grâce à l'intelligence artificielle.

## 🎯 Objectifs du projet
- Permettre aux citoyens de déclarer une pièce perdue de façon simple et rapide
- Offrir un espace sécurisé pour enregistrer les pièces retrouvées avec photo
- Utiliser un modèle de deep learning pour l'extraction intelligente des informations (OCR avancé)
- Comparer les données déclarées avec celles extraites automatiquement par l'IA
- Notifier les utilisateurs en cas de correspondance positive

## 🧱 Architecture technique
- **Frontend**: React.js avec TypeScript  
- **Backend**: Django REST Framework (Python)  
- **Base de données**: PostgreSQL  
- **OCR**: Modèle de deep learning pour l'extraction d'informations  
- **Authentification**: JWT tokens  

## 📁 Structure du projet
FindMyCard/
├── backend/ # API Django
│ ├── findmyid/ # Configuration Django
│ ├── api/ # API endpoints
│ ├── ocr/ # Module OCR/Deep Learning
│ └── requirements.txt # Dépendances Python
├── frontend/ # Application React
│ ├── src/
│ ├── public/
│ └── package.json
└── README.md

## 🚀 Installation et démarrage

### Backend (Django)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
Frontend (React)
cd frontend
npm install
npm start

### Comptes administrateurs par défaut

| Rôle | Email | Mot de passe |
| --- | --- | --- |
| Admin plateforme | `admin.platform@findmycard.local` | `AdminPlateforme123!` |
| Admin public | `admin.public@findmycard.local` | `AdminPublic123!` |

> ⚠️ Pensez à modifier ces accès lors du passage en production.
🔐 Fonctionnalités principales

Déclaration de perte de pièces d'identité

Prise de photo et analyse automatique des pièces retrouvées

Système de matching intelligent

Notifications en temps réel

Interface sécurisée et intuitive


---

# 🟢 Maintenant, fais ces commandes :

```bash
git add README.md
git commit -m "Fix: Résolution du conflit README complet"
git push origin main
