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
    
    # Add any additional fields you want here
    
    def __str__(self):
        return self.username
    
    @property
    def review_display_name(self):
        """Get the name to display for reviews"""
        if self.is_anonymous_account:
            return self.display_name or "Anon"
        return self.display_name or self.username

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
