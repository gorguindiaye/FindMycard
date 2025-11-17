from django.db.models import Q
from difflib import SequenceMatcher
from datetime import datetime, date
from .models import LostItem, FoundItem, Match, Notification
import logging

logger = logging.getLogger(__name__)

class MatchingService:
    @staticmethod
    def find_matches(item):
        """
        Trouve les correspondances potentielles pour un objet perdu ou trouvé
        """
        logger.info(f"Starting matching for {type(item).__name__}: {item.id}")
        if isinstance(item, LostItem):
            # Chercher dans les objets trouvés
            found_items = FoundItem.objects.filter(
                document_type=item.document_type,
                status__in=['pending', 'processed']
            )
            logger.info(f"Found {found_items.count()} potential found items for lost item {item.id}")
            for found_item in found_items:
                confidence = MatchingService.calculate_confidence(item, found_item)
                logger.info(f"Confidence for lost {item.id} and found {found_item.id}: {confidence}")
                if confidence > 0.5:  # Seuil de confiance
                    match, created = Match.objects.get_or_create(
                        lost_item=item,
                        found_item=found_item,
                        defaults={
                            'confidence_score': confidence,
                            'match_criteria': {'method': 'basic'}
                        }
                    )
                    if created:
                        logger.info(f"Created match: {match.id}")
                        # Créer une notification
                        Notification.objects.create(
                            user=found_item.user,
                            match=match,
                            notification_type='match_found',
                            title='Correspondance trouvée',
                            message=f'Une correspondance a été trouvée pour votre objet trouvé.'
                        )
                        logger.info(f"Created notification for user {found_item.user.id}")
                    else:
                        logger.info(f"Match already exists: {match.id}")
        elif isinstance(item, FoundItem):
            # Chercher dans les objets perdus
            lost_items = LostItem.objects.filter(
                document_type=item.document_type,
                status='active'
            )
            logger.info(f"Found {lost_items.count()} potential lost items for found item {item.id}")
            for lost_item in lost_items:
                confidence = MatchingService.calculate_confidence(lost_item, item)
                logger.info(f"Confidence for lost {lost_item.id} and found {item.id}: {confidence}")
                if confidence > 0.5:
                    match, created = Match.objects.get_or_create(
                        lost_item=lost_item,
                        found_item=item,
                        defaults={
                            'confidence_score': confidence,
                            'match_criteria': {'method': 'basic'}
                        }
                    )
                    if created:
                        logger.info(f"Created match: {match.id}")
                        # Créer une notification
                        Notification.objects.create(
                            user=lost_item.user,
                            match=match,
                            notification_type='match_found',
                            title='Correspondance trouvée',
                            message=f'Une correspondance a été trouvée pour votre objet perdu.'
                        )
                        logger.info(f"Created notification for user {lost_item.user.id}")
                    else:
                        logger.info(f"Match already exists: {match.id}")
        else:
            logger.warning(f"Unknown item type: {type(item)}")

    @staticmethod
    def calculate_confidence(lost_item, found_item):
        """Calcule le score de confiance entre deux pièces"""
        scores = []
        
        # Comparaison des noms
        if lost_item.first_name and found_item.first_name:
            first_name_score = SequenceMatcher(
                None, 
                lost_item.first_name.lower(), 
                found_item.first_name.lower()
            ).ratio()
            scores.append(first_name_score * 0.3)  # Poids 30%
        
        if lost_item.last_name and found_item.last_name:
            last_name_score = SequenceMatcher(
                None, 
                lost_item.last_name.lower(), 
                found_item.last_name.lower()
            ).ratio()
            scores.append(last_name_score * 0.3)  # Poids 30%
        
        # Comparaison des dates de naissance
        if lost_item.date_of_birth and found_item.date_of_birth:
            if lost_item.date_of_birth == found_item.date_of_birth:
                scores.append(1.0 * 0.25)  # Poids 25%
            else:
                scores.append(0.0)
        
        # Comparaison des numéros de document
        if lost_item.document_number and found_item.document_number:
            if lost_item.document_number == found_item.document_number:
                scores.append(1.0 * 0.15)  # Poids 15%
            else:
                doc_score = SequenceMatcher(
                    None, 
                    lost_item.document_number, 
                    found_item.document_number
                ).ratio()
                scores.append(doc_score * 0.15)
        
        return sum(scores) if scores else 0.0
