"""django_netflix_clone URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings            # Add this line
from django.conf.urls.static import static  # Add this line

from netflix.views import add_to_wishlist, choose_profile_view, edit_profile_view, index_view, landing_view, movie_choice_view, notification_view, profile_view, remove_from_wishlist, view_wishlist # Add this line
from netflix.views import register_view # Add this line
from netflix.views import login_view # Add this line
from netflix.views import logout_view # Add this line
from netflix.views import watch_movie_view

from netflix.views import like_movie_view
from netflix.views import user_liked_movies_view


from netflix.views import subscription_view, subscription_callback, subscription_failure


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_view, name='landing'),  # Landing page
    path('browse/', index_view, name='home'),  # Home page
    path('watch/', watch_movie_view, name='watch_movie'), # Add this line
    path('register', register_view, name='register'), # Add this line
    path('login', login_view, name='login'), # Add this line
    path('logout/', logout_view, name='logout'), # Add this line
    path('like/<int:movie_id>/', like_movie_view, name='like_movie'),
    path('liked-movies/', user_liked_movies_view, name='user_liked_movies'),
    
    path('subscription/', subscription_view, name='subscription_view'),
    
    # path('profile/', profile_view, name='profile_view'),
    path('edit_profile/<int:profile_id>/', edit_profile_view, name='profile_view'),
    path('create_profile/', profile_view, name='profile_view'),
    
    path('profile/choose/<int:profile_id>/', choose_profile_view, name='choose_profile'),
    path('notifications/', notification_view, name='notification_view'),

    path('subscription/callback/', subscription_callback, name='subscription_callback'),
    path('index/', movie_choice_view, name='index'),
    path('subscription/failure/', subscription_failure, name='subscription_failure'),
    
    
    path('wishlist/', view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:movie_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:wishlist_id>/', remove_from_wishlist, name='remove_from_wishlist'),



]
# Add the lines below
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)