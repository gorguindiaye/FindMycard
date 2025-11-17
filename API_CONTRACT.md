# API Contract - FindMyID

## Vue d'ensemble
API REST pour la gestion des objets perdus et trouvés avec authentification JWT et OCR.

## Base URL
`http://localhost:8000/api/`

## Authentification
Utilise JWT (JSON Web Tokens). Tous les endpoints sauf inscription et connexion nécessitent un token Bearer.

### Inscription
- **Endpoint**: `POST /users/`
- **Body**:
  ```json
  {
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "password": "string",
    "password_confirm": "string"
  }
  ```
- **Response**: `201 Created` avec données utilisateur

### Connexion
- **Endpoint**: `POST /token/`
- **Body**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access": "string",
    "refresh": "string"
  }
  ```

### Rafraîchissement Token
- **Endpoint**: `POST /token/refresh/`
- **Body**:
  ```json
  {
    "refresh": "string"
  }
  ```
- **Response**: `200 OK` avec nouveau access token

## Endpoints Principaux

### Types de Documents
- **GET /document-types/**: Liste des types de documents
- **Auth**: Requise

### Objets Perdus
- **GET /lost-items/**: Liste des objets perdus de l'utilisateur
- **POST /lost-items/**: Créer un objet perdu
- **PATCH /lost-items/{id}/**: Modifier un objet perdu
- **DELETE /lost-items/{id}/**: Supprimer un objet perdu
- **POST /lost-items/{id}/close/**: Fermer une déclaration
- **GET /lost-items/active/**: Objets perdus actifs
- **Auth**: Requise pour tous

### Objets Trouvés
- **GET /found-items/**: Liste des objets trouvés de l'utilisateur
- **POST /found-items/**: Créer un objet trouvé (avec image)
- **PATCH /found-items/{id}/**: Modifier un objet trouvé
- **DELETE /found-items/{id}/**: Supprimer un objet trouvé
- **POST /found-items/{id}/process_ocr/**: Traiter l'image avec OCR
- **Auth**: Requise pour tous

### Correspondances
- **GET /matches/**: Liste des correspondances
- **POST /matches/{id}/confirm/**: Confirmer une correspondance
- **POST /matches/{id}/reject/**: Rejeter une correspondance
- **POST /matches/{id}/hand_over/**: Remettre l'objet
- **Auth**: Requise

### Notifications
- **GET /notifications/**: Liste des notifications
- **GET /notifications/unread_count/**: Nombre de notifications non lues
- **POST /notifications/{id}/mark_as_read/**: Marquer comme lue
- **POST /notifications/mark_all_as_read/**: Tout marquer comme lu
- **Auth**: Requise

### Utilisateur
- **GET /users/me/**: Informations utilisateur actuel
- **PATCH /users/me/**: Modifier profil
- **Auth**: Requise

## Codes d'Erreur
- `400 Bad Request`: Données invalides
- `401 Unauthorized`: Token manquant ou invalide
- `403 Forbidden`: Permissions insuffisantes
- `404 Not Found`: Ressource inexistante
- `500 Internal Server Error`: Erreur serveur

## Pagination
Utilise PageNumberPagination avec page_size=20.

## Formats de Données
- Dates: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- Images: Multipart/form-data pour upload
- Réponses: JSON

## Documentation Complète
Consultez `/api/docs/` pour la documentation interactive Swagger.
