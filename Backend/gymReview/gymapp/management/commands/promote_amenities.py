from django.core.management.base import BaseCommand
from gymapp.models import User, GymAmenityAssertion
from gymapp.services import promote_amenities_for_gym_amenity


class Command(BaseCommand):
    help = 'Promote crowd data to truth - aggregate assertions and update gym amenities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-confirmations',
            type=int,
            default=5,
            help='Minimum weighted confirmations required (default: 5)'
        )
        parser.add_argument(
            '--min-confidence',
            type=float,
            default=0.85,
            help='Minimum confidence threshold (default: 0.85)'
        )
        parser.add_argument(
            '--min-account-age',
            type=int,
            default=0,
            help='Minimum account age in days (default: 0 - no threshold, age affects weight only)'
        )
        parser.add_argument(
            '--min-reputation',
            type=int,
            default=0,
            help='Minimum reputation score (default: 0 - no threshold, reputation affects weight only)'
        )
        parser.add_argument(
            '--min-users',
            type=int,
            default=1,
            help='Minimum number of distinct users required (default: 1)'
        )
        parser.add_argument(
            '--verify-confidence',
            type=float,
            default=0.7,
            help='Confidence threshold for verification (default: 0.7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )

    def handle(self, *args, **options):
        min_confirmations = options['min_confirmations']
        min_confidence = options['min_confidence']
        min_account_age = options['min_account_age']
        min_reputation = options['min_reputation']
        min_users = options['min_users']
        verify_confidence = options['verify_confidence']
        dry_run = options['dry_run']

        self.stdout.write(f'Starting amenity promotion with thresholds:')
        self.stdout.write(f'  Min confirmations: {min_confirmations}')
        self.stdout.write(f'  Min confidence: {min_confidence}')
        self.stdout.write(f'  Min account age: {min_account_age} days')
        self.stdout.write(f'  Min reputation: {min_reputation}')
        self.stdout.write(f'  Min users: {min_users}')
        self.stdout.write(f'  Verify confidence: {verify_confidence}')
        self.stdout.write(f'  Dry run: {dry_run}')
        self.stdout.write('')

        # First, update all user reputations and account ages
        self.stdout.write('Updating user reputations and account ages...')
        users_updated = 0
        for user in User.objects.all():
            user.update_reputation()
            user.update_account_age()
            users_updated += 1
        
        self.stdout.write(f'Updated {users_updated} users')
        
        # Recalculate assertion weights for all assertions (since user reputations changed)
        # This ensures assertion weights reflect current user reputation/account age.
        # We need to recalculate because assertion weights depend on user reputation/account age,
        # which we just updated. The endpoint also updates user reputation when creating assertions,
        # but this batch recalculation ensures all assertion weights are up-to-date.
        self.stdout.write('Recalculating assertion weights...')
        assertions_updated = 0
        
        # Use iterator() for memory efficiency with large datasets
        # Note: We use select_related('user') to avoid N+1 queries when calculating weights.
        # Since we just updated all users in the database, select_related will fetch the updated values
        # from the database (which we just saved).
        for assertion in GymAmenityAssertion.objects.all().select_related('user').iterator(chunk_size=1000):
            old_weight = assertion.weight
            # Trigger weight recalculation (save() calls calculate_weight() which reads user reputation/account_age)
            # The user object is already loaded via select_related and reflects the updated DB values
            assertion.save()  # Save triggers calculate_weight() which uses the user's updated reputation/account_age
            if assertion.weight != old_weight:
                assertions_updated += 1
        
        self.stdout.write(f'Updated {assertions_updated} assertion weights')
        self.stdout.write('')

        # Use the shared promotion function to process all gym-amenity combinations
        result = promote_amenities_for_gym_amenity(
            gym=None,  # Process all gyms
            amenity=None,  # Process all amenities
            min_confirmations=min_confirmations,
            min_confidence=min_confidence,
            min_account_age=min_account_age,
            min_reputation=min_reputation,
            min_users=min_users,
            verify_confidence=verify_confidence,
            dry_run=dry_run
        )
        
        promoted_count = result['promoted_count']
        verified_count = result['verified_count']
        rejected_count = result['rejected_count']
        
        # Log the changes
        for item in result['processed']:
            self.stdout.write(
                f'{"[DRY RUN] " if dry_run else ""}'
                f'Gym {item["gym_id"]} - Amenity {item["amenity_id"]}: '
                f'{item["old_status"]} → {item["new_status"]} '
                f'(conf: {item["confidence"]:.3f}, up: {item["up_weight"]:.1f}, users: {item["users"]})'
            )

        self.stdout.write('')
        self.stdout.write(f'Promotion complete:')
        self.stdout.write(f'  Promoted to approved: {promoted_count}')
        self.stdout.write(f'  Verified: {verified_count}')
        self.stdout.write(f'  Rejected: {rejected_count}')
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('This was a dry run - no changes were made'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Amenity promotion completed successfully!'))
