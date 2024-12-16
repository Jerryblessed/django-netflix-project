from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

CHARS_MAX_LENGTH = 150

class Category(models.Model):
    """Category model class."""
    name = models.CharField(max_length=CHARS_MAX_LENGTH, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag model class."""
    name = models.CharField(max_length=CHARS_MAX_LENGTH, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    """Unified Movie model class."""
    RESOLUTION_CHOICES = [
        ('HD', 'HD'),
        ('FHD', 'Full HD'),
        ('UHD', 'Ultra HD'),
    ]

    name = models.CharField(max_length=CHARS_MAX_LENGTH, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES)  # Resolution field
    watch_count = models.IntegerField(default=0)
    file = models.FileField(upload_to='movies/')
    preview_image = models.ImageField(upload_to='preview_images/')
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_resolution_display()})"

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    date_subscribed = models.DateTimeField(null=True, blank=True)
    date_expired = models.DateTimeField(null=True, blank=True)
    plan = models.CharField(max_length=50, choices=[
        ('Basic', 'Basic'),
        ('Standard', 'Standard'),
        ('Premium', 'Premium'),
    ], default='Basic')
    subscription_type = models.CharField(max_length=50, default='HD')  # Default to HD for Basic
    
class Like(models.Model):
    """Unified Like model class."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='likes')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} liked {self.movie.name}"



class Profile(models.Model):
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=50)
    preferred_categories = models.ManyToManyField('Category', blank=True)  # Multiple categories
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.subscription.user.username})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return f"Notification for {self.user.username} - {'Read' if self.is_read else 'Unread'}"
    
    
class Wishlist(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='wishlists')
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    added_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.movie.name} in {self.profile.name}'s wishlist"