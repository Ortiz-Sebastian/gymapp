from django.db import models
from django.contrib.auth.models import User

class Gym(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    description = models.TextField()
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
