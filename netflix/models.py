from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Manager

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
    RESOLUTION_CHOICES = [
        ('HD', 'HD'),
        ('FHD', 'Full HD'),
        ('UHD', 'Ultra HD'),
    ]

    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag')
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES)
    watch_count = models.IntegerField(default=0)
    file = models.FileField(upload_to='movies/')
    thumbnail = models.ImageField(upload_to='thumbnail/')
    preview_image = models.ImageField(upload_to='preview_images/')
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_resolution_display()})"

    def likes_count(self):
        """Count the total likes for this movie."""
        return self.likes.filter(is_liked=True).count()


class Profile(models.Model):
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=50)
    preferred_categories = models.ManyToManyField('Category', blank=True)  # Multiple categories
    created_at = models.DateTimeField(default=timezone.now)
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    movies_watched = models.IntegerField(default=0)
    liked_movies = models.ManyToManyField(Movie, related_name='liked_profiles', blank=True)

    def __str__(self):
        return f"{self.name} ({self.subscription.user.username})"

class Like(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='likes')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='likes')
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'movie')

# class Tag(models.Model):
#     """Tag model class."""
#     name = models.CharField(max_length=CHARS_MAX_LENGTH, blank=True)
#     description = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.name


    
class SubscriptionManager(Manager):
    def get_queryset(self):
        # Deactivate expired subscriptions before returning them
        queryset = super().get_queryset()
        queryset.filter(is_active=True, date_expired__lt=timezone.now()).update(is_active=False)
        return queryset

    
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
    subscription_type = models.CharField(max_length=50, default='HD')

    # Use the custom manager
    
    objects = SubscriptionManager()

    def check_and_deactivate(self):
        """Deactivate subscription if the expiration date has passed."""
        if self.is_active and self.date_expired and self.date_expired < timezone.now():
            self.is_active = False
            self.save()

# Signal to check subscription status after save
@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, **kwargs):
    """Check and deactivate expired subscriptions."""
    instance.check_and_deactivate()
 



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


class WatchHistory(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-watched_at']
        unique_together = ('profile', 'movie')  # Ensures a profile cannot have duplicate history entries for the same movie