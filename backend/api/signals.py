from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FoundItem, LostItem
from .services import MatchingService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=FoundItem)
def trigger_matching_on_found_item(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Triggering matching for new FoundItem: {instance.id}")
        try:
            MatchingService.find_matches(instance)
        except Exception as e:
            logger.error(f"Error in matching for FoundItem {instance.id}: {e}")

@receiver(post_save, sender=LostItem)
def trigger_matching_on_lost_item(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Triggering matching for new LostItem: {instance.id}")
        try:
            MatchingService.find_matches(instance)
        except Exception as e:
            logger.error(f"Error in matching for LostItem {instance.id}: {e}")
