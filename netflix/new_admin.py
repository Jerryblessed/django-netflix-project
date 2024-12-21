from django.contrib import admin
from django.utils.html import format_html
from netflix.models import Movie, Notification, Profile, Subscription, Category, Tag, Like, Wishlist

# Register Category and Tag models
admin.site.register(Category)
admin.site.register(Tag)




@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'subscription_type', 'date_subscribed', 'date_expired')
    list_filter = ('is_active', 'subscription_type')
    search_fields = ('user__username',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'movies_watched', 'subscription', 'get_preferred_categories', 'created_at']

    def get_preferred_categories(self, obj):
        """Display preferred categories as a comma-separated string."""
        return ", ".join(category.name for category in obj.preferred_categories.all())
    get_preferred_categories.short_description = 'Preferred Categories'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['profile', 'movie', 'added_at']
    list_filter = ['profile', 'added_at']
    search_fields = ['profile__name', 'movie__name']




@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    search_fields = ('user__username', 'message')
    list_filter = ('created_at', 'is_read')


class LikeInline(admin.TabularInline):
    """Inline to display likes for a movie in the admin."""
    model = Like
    extra = 0
    readonly_fields = ('user', 'created_at')


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Admin view for movies with likes, preview, and video."""

    def get_preview(self, obj):
        """Render preview image as HTML."""
        if obj.preview_image:
            return format_html('<img style="height: 200px;" src="{}" />', obj.preview_image.url)
        return "No preview available"
    get_preview.short_description = 'Preview Image'

    def get_thumbnail(self, obj):
        """Render thumbnail as HTML."""
        if obj.thumbnail:
            return format_html('<img style="height: 200px;" src="{}" />', obj.thumbnail.url)
        return "No thumbnail available"
    get_thumbnail.short_description = 'Thumbnail Image'

    def get_video(self, obj):
        """Render movie video as HTML."""
        if obj.file:
            return format_html(
                '<video width="320" height="240" controls>'
                '<source src="{}" type="video/mp4">'
                'Your browser does not support the video tag.</video>',
                obj.file.url
            )
        return "No video available"
    get_video.short_description = 'Preview Video'

    list_display = ['name', 'get_preview', 'get_thumbnail', 'get_video', 'description', 'get_likes_count', 'resolution']
    inlines = [LikeInline]

    def get_likes_count(self, obj):
        """Returns the number of likes for a movie."""
        return obj.likes.count()
    get_likes_count.short_description = 'Likes Count'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'is_liked', 'created_at')
    search_fields = ('user__username', 'movie__name')
    list_filter = ('created_at', 'is_liked')
