from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Anonymous account settings
    is_anonymous_account = models.BooleanField(default=True, 
                                             help_text="If True, user's reviews will be shown as anonymous")
    display_name = models.CharField(max_length=50, blank=True,
                                  help_text="Display name for reviews (if not anonymous)")
    
    # Reputation system
    reputation_score = models.IntegerField(default=0, help_text="User reputation score")
    account_age_days = models.IntegerField(default=0, help_text="Account age in days")
    
    def __str__(self):
        return self.username
    
    @property
    def review_display_name(self):
        """Get the name to display for reviews"""
        if self.is_anonymous_account:
            return self.display_name or "Anon"
        return self.display_name or self.username
    
    def update_reputation(self):
        """Update user reputation based on various factors"""
        # Base reputation from reviews
        review_reputation = self.reviews.count() * 10
        
        # Bonus for helpful reviews
        helpful_bonus = sum(review.helpful_votes for review in self.reviews.all()) * 2
        
        # Bonus for verified amenities
        amenity_bonus = self.added_amenities.filter(is_verified=True).count() * 5
        
        # Penalty for reported content
        reported_penalty = PhotoReport.objects.filter(photo__uploaded_by=self).count() * -10
        
        self.reputation_score = max(0, review_reputation + helpful_bonus + amenity_bonus + reported_penalty)
        self.save(update_fields=['reputation_score'])
    
    def update_account_age(self):
        """Update account age in days"""
        if self.date_joined:
            delta = timezone.now().date() - self.date_joined.date()
            self.account_age_days = delta.days
            self.save(update_fields=['account_age_days'])

class Gym(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    # Using Google Places ID as primary key
    place_id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    google_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    google_user_ratings_total = models.IntegerField(null=True, blank=True)
    photo_reference = models.CharField(max_length=255, blank=True)
    types = models.JSONField(default=list, blank=True)  # Store Google Places types
    opening_hours = models.JSONField(null=True, blank=True)  # Store opening hours
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def avg_equipment_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(review.equipment_rating for review in reviews) / len(reviews), 1)
        return 0
    
    @property
    def avg_cleanliness_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(review.cleanliness_rating for review in reviews) / len(reviews), 1)
        return 0
    
    @property
    def avg_staff_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(review.staff_rating for review in reviews) / len(reviews), 1)
        return 0
    
    @property
    def avg_value_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(review.value_rating for review in reviews) / len(reviews), 1)
        return 0
    
    @property
    def avg_atmosphere_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(review.atmosphere_rating for review in reviews) / len(reviews), 1)
        return 0
    
    @property
    def overall_avg_rating(self):
        reviews = self.reviews.all()
        if reviews:
            total = sum(review.overall_rating for review in reviews)
            return round(total / len(reviews), 1)
        return 0


class GymPhoto(models.Model):
    MODERATION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    ]
    
    REJECTION_REASON_CHOICES = [
        ('inappropriate_content', 'Inappropriate Content'),
        ('nudity', 'Nudity or Sexual Content'),
        ('violence', 'Violence or Harmful Content'),
        ('spam', 'Spam or Irrelevant'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other Policy Violation'),
    ]
    
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='gym_photos/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_google_photo = models.BooleanField(default=False)  # Track if it's from Google
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption for the photo")
    likes_count = models.PositiveIntegerField(default=0)
    
    # Moderation fields
    moderation_status = models.CharField(max_length=20, choices=MODERATION_STATUS_CHOICES, default='pending')
    rejection_reason = models.CharField(max_length=30, choices=REJECTION_REASON_CHOICES, blank=True)
    moderation_notes = models.TextField(blank=True, help_text="Internal notes about moderation decision")
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_photos')
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    # Auto-moderation results
    auto_moderation_score = models.FloatField(null=True, blank=True, help_text="AI confidence score (0-1)")
    auto_moderation_flags = models.JSONField(default=list, blank=True, help_text="List of detected issues")
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_google_photo', 'moderation_status', '-likes_count', '-uploaded_at']  # Google photos first, then approved, then by popularity
    
    def __str__(self):
        return f"Photo for {self.gym.name}"


class Review(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Require user account
    
    # Specific ratings
    equipment_rating = models.IntegerField(choices=RATING_CHOICES)
    cleanliness_rating = models.IntegerField(choices=RATING_CHOICES)
    staff_rating = models.IntegerField(choices=RATING_CHOICES)
    value_rating = models.IntegerField(choices=RATING_CHOICES)
    atmosphere_rating = models.IntegerField(choices=RATING_CHOICES)
    
    # Review text (like Rate My Professor comments)
    review_text = models.TextField(blank=True, help_text="Share your detailed experience at this gym")
    
    # Review photos (users can attach photos to their review)
    review_photo = models.ImageField(upload_to='review_photos/', blank=True, null=True, 
                                   help_text="Optional photo to accompany your review")
    
    # Helpful voting system
    helpful_votes = models.PositiveIntegerField(default=0)
    not_helpful_votes = models.PositiveIntegerField(default=0)
    
    # Track if user would recommend this gym
    would_recommend = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Check if a review from this user for this gym already exists
        if self.pk is None:  # Only check on creation
            existing_review = Review.objects.filter(
                gym=self.gym, 
                user=self.user
            ).first()
            
            if existing_review:
                # Update the existing review instead of creating a new one
                existing_review.equipment_rating = self.equipment_rating
                existing_review.cleanliness_rating = self.cleanliness_rating
                existing_review.staff_rating = self.staff_rating
                existing_review.value_rating = self.value_rating
                existing_review.atmosphere_rating = self.atmosphere_rating
                existing_review.review_text = self.review_text
                existing_review.review_photo = self.review_photo
                existing_review.would_recommend = self.would_recommend
                existing_review.updated_at = timezone.now()
                existing_review.save()
                return existing_review
        
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_review(cls, user, gym, **kwargs):
        """
        Get existing review or create a new one if none exists.
        This method ensures only one review per user per gym.
        """
        review, created = cls.objects.get_or_create(
            user=user,
            gym=gym,
            defaults=kwargs
        )
        
        if not created:
            # Update existing review with new values
            for key, value in kwargs.items():
                setattr(review, key, value)
            review.save()
        
        return review, created

    def __str__(self):
        display_name = self.user.review_display_name
        return f"{display_name}'s review of {self.gym.name}"

    @property
    def overall_rating(self):
        ratings = [
            self.equipment_rating,
            self.cleanliness_rating,
            self.staff_rating,
            self.value_rating,
            self.atmosphere_rating
        ]
        return sum(ratings) / len(ratings)

# Comment model removed - reviews now include text directly


class ReviewVote(models.Model):
    """Track helpful/not helpful votes on reviews"""
    VOTE_CHOICES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
    ]
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']  # One vote per user per review
    
    def __str__(self):
        return f"{self.user.username} voted {self.vote_type} on {self.review}"


class PhotoLike(models.Model):
    """Track likes on gym photos"""
    photo = models.ForeignKey(GymPhoto, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['photo', 'user']  # One like per user per photo
    
    def __str__(self):
        return f"{self.user.username} liked {self.photo}"


class UserFavorite(models.Model):
    """Track user's favorite gyms"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_gyms')
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'gym']  # One favorite per user per gym
    
    def __str__(self):
        return f"{self.user.username} favorited {self.gym.name}"


class PhotoReport(models.Model):
    """Track user reports of inappropriate photos"""
    REPORT_REASON_CHOICES = [
        ('inappropriate_content', 'Inappropriate Content'),
        ('nudity', 'Nudity or Sexual Content'),
        ('violence', 'Violence or Harmful Content'),
        ('spam', 'Spam or Irrelevant'),
        ('copyright', 'Copyright Violation'),
        ('harassment', 'Harassment or Bullying'),
        ('other', 'Other'),
    ]
    
    photo = models.ForeignKey(GymPhoto, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_reports')
    reason = models.CharField(max_length=30, choices=REPORT_REASON_CHOICES)
    description = models.TextField(blank=True, help_text="Additional details about the report")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ], default='pending')
    
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['photo', 'reporter']  # One report per user per photo
    
    def __str__(self):
        return f"Report by {self.reporter.username} on {self.photo}"


class AmenityCategory(models.Model):
    """Categories for gym amenities (e.g., Equipment, Facilities, Services)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for frontend")
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Amenity Categories"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Amenity(models.Model):
    """Individual amenities that gyms can have - fully community-driven"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(AmenityCategory, on_delete=models.CASCADE, related_name='amenities')
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for frontend")
    is_active = models.BooleanField(default=True)
    
    # Community-driven suggestion system
    suggested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='suggested_amenities')
    suggestion_votes = models.PositiveIntegerField(default=0)
    is_community_suggested = models.BooleanField(default=False)
    
    # Community-driven approval (based on usage and votes)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Community Review'),
        ('approved', 'Approved by Community'),
        ('rejected', 'Rejected by Community'),
    ], default='approved')  # Start approved, community can reject if unused
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['category__sort_order', 'category__name', 'name']
        unique_together = ['name', 'category']
    
    def __str__(self):
        return f"{self.category.name}: {self.name}"


class GymAmenity(models.Model):
    """Many-to-many relationship between gyms and amenities - fully community-driven"""
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='gym_amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='gym_amenities')
    
    # Community-driven confidence system
    positive_votes = models.PositiveIntegerField(default=0)
    negative_votes = models.PositiveIntegerField(default=0)
    confidence_score = models.FloatField(default=0.0, help_text="Calculated confidence based on weighted assertions")
    
    # Community-driven status (no staff approval needed)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('approved', 'Approved by Community'),
        ('rejected', 'Rejected by Community'),
        ('flagged', 'Flagged for Review'),
    ], default='pending')
    
    # Community-driven verification (based on confidence thresholds)
    is_verified = models.BooleanField(default=False, help_text="Verified by community consensus")
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Additional details
    notes = models.TextField(blank=True, help_text="Additional details about this amenity")
    is_available = models.BooleanField(default=True, help_text="Currently available")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['gym', 'amenity']
        ordering = ['-confidence_score', 'amenity__category__sort_order', 'amenity__category__name', 'amenity__name']
    
    def __str__(self):
        return f"{self.gym.name} - {self.amenity.name}"
    
    def update_confidence_score(self):
        """Update confidence score based on weighted assertions"""
        from django.db.models import Sum, Case, When, FloatField, Count
        
        # Get weighted assertions for this gym-amenity combination
        assertions = GymAmenityAssertion.objects.filter(
            gym=self.gym,
            amenity=self.amenity
        ).aggregate(
            up=Sum(Case(When(has_amenity=True, then='weight'), default=0.0, output_field=FloatField())),
            down=Sum(Case(When(has_amenity=False, then='weight'), default=0.0, output_field=FloatField())),
            total_assertions=Count('id'),
            distinct_users=Count('user', distinct=True)
        )
        
        up_weight = assertions['up'] or 0.0
        down_weight = assertions['down'] or 0.0
        total_weight = up_weight + down_weight
        
        if total_weight == 0:
            self.confidence_score = 0.0
        else:
            # Calculate confidence as ratio of positive weighted votes
            self.confidence_score = up_weight / total_weight
        
        # Update vote counts for backward compatibility
        self.positive_votes = int(up_weight)
        self.negative_votes = int(down_weight)
        
        self.save(update_fields=['confidence_score', 'positive_votes', 'negative_votes'])
        
        return {
            'confidence': self.confidence_score,
            'up_weight': up_weight,
            'down_weight': down_weight,
            'total_assertions': assertions['total_assertions'],
            'distinct_users': assertions['distinct_users']
        }


class AmenityVote(models.Model):
    """User votes on gym amenities"""
    VOTE_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
    ]
    
    gym_amenity = models.ForeignKey(GymAmenity, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amenity_votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['gym_amenity', 'user']
    
    def __str__(self):
        return f"{self.user.username} voted {self.vote_type} on {self.gym_amenity}"


class GymAmenityAssertion(models.Model):
    """User assertions about gym amenities - the raw crowd data"""
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='amenity_assertions')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='gym_assertions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amenity_assertions')
    has_amenity = models.BooleanField(help_text="User's assertion: does this gym have this amenity?")
    weight = models.FloatField(default=1.0, help_text="Weight based on user reputation and account age")
    notes = models.TextField(blank=True, help_text="Optional notes about the assertion")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['gym', 'amenity', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} asserts {self.gym.name} {'has' if self.has_amenity else 'does not have'} {self.amenity.name}"
    
    def save(self, *args, **kwargs):
        # Calculate weight based on user reputation and account age
        self.weight = self.calculate_weight()
        super().save(*args, **kwargs)
    
    def calculate_weight(self):
        """Calculate assertion weight based on user reputation and account age"""
        # Base weight
        weight = 1.0
        
        # Account age bonus (older accounts are more trusted)
        if self.user.account_age_days >= 30:
            weight += 0.5
        elif self.user.account_age_days >= 7:
            weight += 0.2
        
        # Reputation bonus
        if self.user.reputation_score >= 100:
            weight += 1.0
        elif self.user.reputation_score >= 50:
            weight += 0.5
        elif self.user.reputation_score >= 20:
            weight += 0.2
        
        # Staff bonus
        if self.user.is_staff:
            weight += 2.0
        
        return max(0.1, weight)  # Minimum weight of 0.1


class AmenityReport(models.Model):
    """User reports about amenity accuracy"""
    REPORT_TYPE_CHOICES = [
        ('incorrect', 'Amenity Not Available'),
        ('missing', 'Amenity Missing'),
        ('outdated', 'Information Outdated'),
        ('other', 'Other'),
    ]
    
    gym_amenity = models.ForeignKey(GymAmenity, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amenity_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ], default='pending')
    
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='reviewed_amenity_reports')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['gym_amenity', 'reporter']  # One report per user per amenity
    
    def __str__(self):
        return f"Report by {self.reporter.username} on {self.gym_amenity}"


class GymClaim(models.Model):
    """Gym ownership claims by staff/owners"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revoked', 'Revoked'),
    ]
    
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='claims')
    claimant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gym_claims')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Claim details
    business_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    verification_documents = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    claim_notes = models.TextField(blank=True)
    
    # Review
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='reviewed_claims')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['gym', 'claimant']  # One claim per user per gym
    
    def __str__(self):
        return f"{self.claimant.username} claims {self.gym.name}"
