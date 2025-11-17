@echo off
echo 🚀 Démarrage du backend FindMyID...

cd backend

echo 📦 Installation des dépendances Python...
pip install -r requirements.txt

echo 🗄️  Application des migrations...
python manage.py makemigrations
python manage.py migrate

echo 🔧 Initialisation de la base de données...
python init_db.py

echo 🌐 Démarrage du serveur Django...
python manage.py runserver

pause 