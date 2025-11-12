from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def promote_amenities_task():
    """
    Celery task to run amenity promotion logic
    This should be scheduled to run nightly
    """
    try:
        logger.info("Starting automated amenity promotion...")
        
        # Run the promotion command with default thresholds
        call_command('promote_amenities')
        
        logger.info("Amenity promotion completed successfully")
        return "Amenity promotion completed successfully"
        
    except Exception as e:
        logger.error(f"Amenity promotion failed: {str(e)}")
        raise


@shared_task
def update_user_reputations_task():
    """
    Celery task to update all user reputations and account ages
    This should be scheduled to run daily
    """
    try:
        from gymapp.models import User
        
        logger.info("Starting user reputation update...")
        
        updated_count = 0
        for user in User.objects.all():
            user.update_reputation()
            user.update_account_age()
            updated_count += 1
        
        logger.info(f"Updated {updated_count} user reputations")
        return f"Updated {updated_count} user reputations"
        
    except Exception as e:
        logger.error(f"User reputation update failed: {str(e)}")
        raise
