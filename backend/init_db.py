#!/usr/bin/env python
"""
Script d'initialisation de la base de données
Créé les types de documents et un superutilisateur
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findmyid.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import DocumentType

def create_document_types():
    """Créé les types de documents supportés"""
    document_types = [
        {
            'name': 'Carte d\'identité',
            'description': 'Carte nationale d\'identité française'
        },
        {
            'name': 'Passeport',
            'description': 'Passeport français ou étranger'
        },
        {
            'name': 'Permis de conduire',
            'description': 'Permis de conduire français ou européen'
        },
        {
            'name': 'Carte d\'étudiant',
            'description': 'Carte d\'étudiant d\'établissement'
        },
        {
            'name': 'Carte vitale',
            'description': 'Carte d\'assurance maladie'
        },
        {
            'name': 'Carte bancaire',
            'description': 'Carte bancaire ou de crédit'
        },
        {
            'name': 'Autre',
            'description': 'Autre type de document'
        }
    ]
    
    for doc_type in document_types:
        DocumentType.objects.get_or_create(
            name=doc_type['name'],
            defaults={'description': doc_type['description']}
        )
        print(f"✓ Type de document créé: {doc_type['name']}")

def create_superuser():
    """Créé un superutilisateur par défaut"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@findmyid.com',
            password='admin123',
            first_name='Admin',
            last_name='FindMyID'
        )
        print("✓ Superutilisateur créé: admin/admin123")
    else:
        print("✓ Superutilisateur existe déjà")

def main():
    print("🚀 Initialisation de la base de données FindMyID...")
    
    try:
        # Créer les types de documents
        print("\n📋 Création des types de documents...")
        create_document_types()
        
        # Créer le superutilisateur
        print("\n👤 Création du superutilisateur...")
        create_superuser()
        
        print("\n✅ Initialisation terminée avec succès!")
        print("\n📝 Informations de connexion:")
        print("   - URL admin: http://localhost:8000/admin/")
        print("   - Utilisateur: admin")
        print("   - Mot de passe: admin123")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 