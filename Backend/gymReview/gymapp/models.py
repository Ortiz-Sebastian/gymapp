from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Add any additional fields you want here
    
    def __str__(self):
        return self.username

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

class Review(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Specific ratings
    equipment_rating = models.IntegerField(choices=RATING_CHOICES)
    cleanliness_rating = models.IntegerField(choices=RATING_CHOICES)
    staff_rating = models.IntegerField(choices=RATING_CHOICES)
    value_rating = models.IntegerField(choices=RATING_CHOICES)
    atmosphere_rating = models.IntegerField(choices=RATING_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s review of {self.gym.name}"

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

class Comment(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s comment on {self.gym.name}"
