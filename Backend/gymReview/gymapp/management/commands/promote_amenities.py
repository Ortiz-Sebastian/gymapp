from django.core.management.base import BaseCommand
from django.db.models import Sum, Case, When, FloatField, Count, Q
from django.utils import timezone
from gymapp.models import GymAmenity, GymAmenityAssertion, User


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
            default=7,
            help='Minimum account age in days (default: 7)'
        )
        parser.add_argument(
            '--min-reputation',
            type=int,
            default=10,
            help='Minimum reputation score (default: 10)'
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
        dry_run = options['dry_run']

        self.stdout.write(f'Starting amenity promotion with thresholds:')
        self.stdout.write(f'  Min confirmations: {min_confirmations}')
        self.stdout.write(f'  Min confidence: {min_confidence}')
        self.stdout.write(f'  Min account age: {min_account_age} days')
        self.stdout.write(f'  Min reputation: {min_reputation}')
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

        # Get assertions from qualified users only
        qualified_assertions = GymAmenityAssertion.objects.filter(
            user__account_age_days__gte=min_account_age,
            user__reputation_score__gte=min_reputation
        )

        self.stdout.write(f'Found {qualified_assertions.count()} assertions from qualified users')

        # Aggregate assertions by gym and amenity
        qs = (qualified_assertions
              .values('gym_id', 'amenity_id')
              .annotate(
                  up=Sum(Case(When(has_amenity=True, then='weight'), default=0.0, output_field=FloatField())),
                  down=Sum(Case(When(has_amenity=False, then='weight'), default=0.0, output_field=FloatField())),
                  total_assertions=Count('id'),
                  distinct_users=Count('user', distinct=True)
              ))

        promoted_count = 0
        rejected_count = 0
        verified_count = 0

        for row in qs:
            up_weight = row['up'] or 0.0
            down_weight = row['down'] or 0.0
            total_weight = up_weight + down_weight
            
            if total_weight == 0:
                continue
            
            confidence = up_weight / total_weight
            total_assertions = row['total_assertions']
            distinct_users = row['distinct_users']
            
            # Check if meets minimum thresholds
            meets_confirmations = up_weight >= min_confirmations
            meets_confidence = confidence >= min_confidence
            meets_users = distinct_users >= 3  # Require at least 3 different users
            
            # Get or create GymAmenity
            gym_amenity, created = GymAmenity.objects.get_or_create(
                gym_id=row['gym_id'],
                amenity_id=row['amenity_id'],
                defaults={
                    'status': 'pending',
                    'confidence_score': confidence,
                    'positive_votes': int(up_weight),
                    'negative_votes': int(down_weight)
                }
            )
            
            if not created:
                # Update existing
                gym_amenity.confidence_score = confidence
                gym_amenity.positive_votes = int(up_weight)
                gym_amenity.negative_votes = int(down_weight)
            
            # Determine new status
            if meets_confirmations and meets_confidence and meets_users:
                if confidence >= 0.9:  # Very high confidence
                    new_status = 'approved'
                    gym_amenity.is_verified = True
                    verified_count += 1
                else:
                    new_status = 'approved'
                    promoted_count += 1
            elif confidence < 0.3:  # Very low confidence
                new_status = 'rejected'
                rejected_count += 1
            else:
                new_status = 'pending'  # Keep pending for more data
            
            old_status = gym_amenity.status
            gym_amenity.status = new_status
            
            if not dry_run:
                gym_amenity.save()
            
            # Log the change
            self.stdout.write(
                f'{"[DRY RUN] " if dry_run else ""}'
                f'Gym {row["gym_id"]} - Amenity {row["amenity_id"]}: '
                f'{old_status} → {new_status} '
                f'(conf: {confidence:.3f}, up: {up_weight:.1f}, users: {distinct_users})'
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
