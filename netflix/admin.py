from django.contrib import admin
from django.utils.html import format_html
from netflix.models import Movie, Notification, Profile, Subscription, Category, Tag, Like, Wishlist

# Register Category and Tag models
admin.site.register(Category)
admin.site.register(Tag)

class LikeInline(admin.TabularInline):
    """Inline to display likes for a movie in the admin."""
    model = Like
    extra = 0  # No extra blank rows
    readonly_fields = ('user', 'get_movie', 'timestamp')

    def get_movie(self, obj):
        """Get the liked movie for the inline display."""
        return obj.movie  # Assuming 'movie' is the field in Like model.
    get_movie.short_description = 'Movie'

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Admin view for movies with likes, preview, and video."""

    def preview(self, movie):
        """Render preview image as HTML."""
        return format_html(
            f'<img style="height: 200px" src="/media/{movie.preview_image}" />'
        )

    def video(self, movie):
        """Render movie video as HTML."""
        return format_html(
            f"""
            <video width="320" height="240" controls>
                <source src="/media/{movie.file}" type="video/mp4">
                Your browser does not support the video tag.
            </video>"""
        )

    preview.short_description = 'Movie Image'
    video.short_description = 'Movie Video'

    list_display = ['name', 'preview', 'video', 'description', 'get_likes_count', 'resolution']
    inlines = [LikeInline]

    def get_likes_count(self, obj):
        """Returns the number of likes for a movie."""
        return obj.likes.count()
    get_likes_count.short_description = 'Likes Count'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Admin view for managing likes."""
    list_display = ('user', 'get_movie', 'timestamp')
    search_fields = ('user__username', 'movie__name')
    list_filter = ('timestamp',)

    def get_movie(self, obj):
        """Get the liked movie for admin display."""
        return obj.movie  # Assuming 'movie' is the field in Like model.
    get_movie.short_description = 'Movie'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'subscription_type', 'date_subscribed', 'date_expired')
    list_filter = ('is_active', 'subscription_type')
    
    
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'subscription', 'get_preferred_categories', 'created_at']

    # Custom method to display preferred categories as a comma-separated string
    def get_preferred_categories(self, obj):
        return ", ".join(category.name for category in obj.preferred_categories.all())

    get_preferred_categories.short_description = 'Preferred Categories'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['profile', 'movie', 'added_at']
    list_filter = ['profile', 'added_at']
    search_fields = ['profile__name', 'movie__name']