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

from api.models import DocumentType, CustomUser

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

def create_admin_accounts():
    """Créé les comptes administrateurs plateforme et public par défaut"""
    accounts = [
        {
            'email': 'admin.platform@findmycard.local',
            'password': 'AdminPlateforme123!',
            'first_name': 'Admin',
            'last_name': 'Plateforme',
            'role': 'admin_plateforme',
            'is_superuser': True,
            'is_staff': True,
        },
        {
            'email': 'admin.public@findmycard.local',
            'password': 'AdminPublic123!',
            'first_name': 'Admin',
            'last_name': 'Public',
            'role': 'admin_public',
            'is_superuser': False,
            'is_staff': True,
        },
    ]

    for account in accounts:
        user, created = CustomUser.objects.get_or_create(
            email=account['email'],
            defaults={
                'username': account['email'],
                'first_name': account['first_name'],
                'last_name': account['last_name'],
                'role': account['role'],
                'is_superuser': account['is_superuser'],
                'is_staff': account['is_staff'],
                'is_active': True,
            }
        )
        if created:
            user.set_password(account['password'])
            user.save()
            print(f"✓ Compte {account['role']} créé: {account['email']} / {account['password']}")
        else:
            print(f"✓ Compte {account['role']} existe déjà: {account['email']}")

def main():
    print("🚀 Initialisation de la base de données FindMyID...")
    
    try:
        # Créer les types de documents
        print("\n📋 Création des types de documents...")
        create_document_types()
        
        # Créer les comptes admin
        print("\n👤 Création des comptes administrateurs...")
        create_admin_accounts()
        
        print("\n✅ Initialisation terminée avec succès!")
        print("\n📝 Informations de connexion par défaut:")
        print("   - Admin plateforme: admin.platform@findmycard.local / AdminPlateforme123!")
        print("   - Admin public: admin.public@findmycard.local / AdminPublic123!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 