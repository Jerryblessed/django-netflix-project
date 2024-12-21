from datetime import datetime, timedelta, timezone
from importlib import invalidate_caches
# from pyexpat.errors import messages
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from .forms import RegisterForm
from .forms import LoginForm
from .forms import SearchForm
from .models import Category, Movie, Notification, Profile, Subscription, WatchHistory, Wishlist
from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
import requests
from .models import Subscription
from django.db.models import Count
from django.utils.timezone import now


import stripe


from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from .forms import RegisterForm

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models  # Import models for Q
from .models import Movie, Wishlist, Profile, Subscription  # Your app-specific models


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Movie, Like


from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Subscription

import requests



PAGE_SIZE_PER_CATEGORY = 20

STRIPE_SECRET_KEY = "sk_test_51L8i0jDkGOBWyh471bK0YOEg5VQCiSHFsogH4mfytpAXQixAhGhIR47WImddmQya938dtTrpIadfnl3Aws8JVGys000VEv2oni"  # Replace with your Stripe secret key

stripe.api_key = STRIPE_SECRET_KEY

@login_required
def like_movie(request, movie_id):
    """Toggle like/unlike for a movie for the active profile."""
    movie = get_object_or_404(Movie, id=movie_id)
    profile_id = request.session.get('active_profile')  # Get active profile from the session
    if not profile_id:
        return JsonResponse({'error': 'No active profile selected.'}, status=400)
    
    profile = get_object_or_404(Profile, id=profile_id)
    like, created = Like.objects.get_or_create(profile=profile, movie=movie)

    if not created:
        like.is_liked = not like.is_liked  # Toggle like status
        like.save()

    return JsonResponse({
        'message': 'Movie liked' if like.is_liked else 'Movie unliked',
        'likes_count': movie.likes_count(),
    })

@login_required
def user_liked_movies_view(request):
    """Display movies liked by the active profile."""
    profile_id = request.session.get('active_profile')  # Get active profile from the session
    if not profile_id:
        return JsonResponse({'error': 'No active profile selected.'}, status=400)

    profile = get_object_or_404(Profile, id=profile_id)
    liked_movies = Movie.objects.filter(likes__profile=profile, likes__is_liked=True)
    return render(request, 'netflix/user_liked_movies.html', {'liked_movies': liked_movies})

def like_movie_view(request, movie_id):
    """Like or unlike a movie."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'You must be logged in to like a movie.'}, status=401)

    movie = get_object_or_404(Movie, id=movie_id)
    profile_id = request.session.get('active_profile')  # Use the active profile
    if not profile_id:
        return JsonResponse({'error': 'No active profile selected.'}, status=400)

    profile = get_object_or_404(Profile, id=profile_id)
    like, created = Like.objects.get_or_create(profile=profile, movie=movie)

    if not created:
        # If the profile already liked the movie, remove the like
        like.delete()
        return JsonResponse({'message': 'Movie unliked', 'likes_count': Like.objects.filter(movie=movie).count()})

    return JsonResponse({'message': 'Movie liked', 'likes_count': Like.objects.filter(movie=movie).count()})


 
def landing_view(request):
    """Landing page view."""
    return render(request, 'netflix/landing_page.html')  # Ensure this HTML exists
 
def settings_view(request):
    """Settings page view."""
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()

    if not profiles.exists() and request.method != "POST":
        return render(request, 'netflix/create_profile.html')

    if request.method == "POST":
        if len(profiles) < 4:  # Limit to max 4 profiles
            name = request.POST.get('profile_name')
            categories_input = request.POST.get('categories', '')  # Get categories or an empty string
            categories = [cat.strip() for cat in categories_input.split(',') if cat.strip()]  # Split and filter non-empty strings

            # Validate categories
            valid_categories = Category.objects.filter(name__in=categories)
            profile = Profile.objects.create(subscription=subscription, name=name)
            profile.preferred_categories.set(valid_categories)  # Assign validated categories
            profile.save()

            Notification.objects.create(
                user=request.user,
                message=f"Profile '{profile.name}' created with categories: {', '.join(cat.name for cat in valid_categories)}."
            )

    return render(request, 'netflix/settings_page.html', {'profiles': profiles})  # Ensure this HTML exists

def watch_movie(request):
    movie_id = request.GET.get('movie_pk')
    movie = Movie.objects.get(pk=movie_id)
    profile_id = request.session.get('active_profile')
    profile = Profile.objects.get(pk=profile_id)

    # Update or create watch history
    watch_history, created = WatchHistory.objects.update_or_create(
        profile=profile,
        movie=movie,
        defaults={'watched_at': now()},
    )

    # Render or redirect to the movie player
    return render(request, 'netflix/watch_movie.html', {'movie': movie})

@login_required
def index_view(request):
    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.is_active or subscription.date_expired <= timezone.now():
            subscription.is_active = False
            subscription.save()
            return redirect('subscription_view')
    except Subscription.DoesNotExist:
        return redirect('subscription_view')

    profile_id = request.session.get('active_profile')
    profile = Profile.objects.filter(id=profile_id, subscription=subscription).first()
    
    
    # wishlist
    wishlist = Wishlist.objects.filter(profile=profile)
    wishlist_movies = [item.movie for item in wishlist]
    categories = wishlist_movies and [movie.category for movie in wishlist_movies]
    tags = wishlist_movies and [tag for movie in wishlist_movies for tag in movie.tags.all()]

    if not profile:
        return redirect('profile_view')

    allowed_resolutions = {
        'HD': ['HD'],
        'FHD': ['HD', 'FHD'],
        'UHD': ['HD', 'FHD', 'UHD'],
    }
    resolutions = allowed_resolutions.get(subscription.subscription_type, ['HD'])

    preferred_categories = profile.preferred_categories.all()
    search_text = request.GET.get('search_text', '')
    if search_text:
        movies = Movie.objects.filter(name__icontains=search_text, resolution__in=resolutions)
    else:
        movies = Movie.objects.filter(
            category__in=preferred_categories,
            resolution__in=resolutions
        )

    others = Movie.objects.filter(
        resolution__in=resolutions
    ).exclude(category__in=preferred_categories)

    wishlist_movies = Wishlist.objects.filter(profile=profile).values_list('movie', flat=True)
    recommended_movies = Movie.objects.filter(
        models.Q(category__in=preferred_categories) |
        models.Q(tags__in=Movie.objects.filter(id__in=wishlist_movies).values_list('tags', flat=True))
    ).exclude(id__in=wishlist_movies).distinct()

    most_viewed_movie = Movie.objects.filter(resolution__in=resolutions).order_by('-watch_count').first()
    most_liked_movie = (
        Movie.objects.filter(resolution__in=resolutions)
        .annotate(like_count=Count('likes'))
        .order_by('-like_count')
        .first()
    )
    # Get the last 10 watched movies for the profile
    watch_history = WatchHistory.objects.filter(profile=profile).select_related('movie')[:10]

    categories = Category.objects.all()
    movies_by_category = {
        category.name: Movie.objects.filter(category=category, resolution__in=resolutions)
        for category in categories
    }
    
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()

    if not profiles.exists() and request.method != "POST":
        return render(request, 'netflix/create_profile.html')

    if request.method == "POST":
        if len(profiles) < 4:  # Limit to max 4 profiles
            name = request.POST.get('profile_name')
            categories_input = request.POST.get('categories', '')  # Get categories or an empty string
            categories = [cat.strip() for cat in categories_input.split(',') if cat.strip()]  # Split and filter non-empty strings

            # Validate categories
            valid_categories = Category.objects.filter(name__in=categories)
            profile = Profile.objects.create(subscription=subscription, name=name)
            profile.preferred_categories.set(valid_categories)  # Assign validated categories
            profile.save()

            Notification.objects.create(
                user=request.user,
                message=f"Profile '{profile.name}' created with categories: {', '.join(cat.name for cat in valid_categories)}."
            )
            
    return render(request, 'netflix/index.html', {
        'wishlist': wishlist,
        'movies': movies,
        'other_movies': others,
        'recommended_movies': recommended_movies,
        'active_profile': profile,
        'search_text': search_text,
        'most_viewed_movie': most_viewed_movie,
        'most_liked_movie': most_liked_movie,
        'movies_by_category': movies_by_category,
        'categories': categories,
        'watch_history': watch_history,
        'profiles': profiles
    })


@login_required
def movie_view(request):
    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.is_active or subscription.date_expired <= timezone.now():
            subscription.is_active = False
            subscription.save()
            return redirect('subscription_view')
    except Subscription.DoesNotExist:
        return redirect('subscription_view')

    profile_id = request.session.get('active_profile')
    profile = Profile.objects.filter(id=profile_id, subscription=subscription).first()
    
    # wishlist
    wishlist = Wishlist.objects.filter(profile=profile)
    wishlist_movies = [item.movie for item in wishlist]
    categories = wishlist_movies and [movie.category for movie in wishlist_movies]
    tags = wishlist_movies and [tag for movie in wishlist_movies for tag in movie.tags.all()]

    if not profile:
        return redirect('profile_view')

    allowed_resolutions = {
        'HD': ['HD'],
        'FHD': ['HD', 'FHD'],
        'UHD': ['HD', 'FHD', 'UHD'],
    }
    resolutions = allowed_resolutions.get(subscription.subscription_type, ['HD'])

    preferred_categories = profile.preferred_categories.all()
    search_text = request.GET.get('search_text', '')
    if search_text:
        movies = Movie.objects.filter(name__icontains=search_text, resolution__in=resolutions)
    else:
        movies = Movie.objects.filter(
            category__in=preferred_categories,
            resolution__in=resolutions
        )

    others = Movie.objects.filter(
        resolution__in=resolutions
    ).exclude(category__in=preferred_categories)

    wishlist_movies = Wishlist.objects.filter(profile=profile).values_list('movie', flat=True)
    recommended_movies = Movie.objects.filter(
        models.Q(category__in=preferred_categories) |
        models.Q(tags__in=Movie.objects.filter(id__in=wishlist_movies).values_list('tags', flat=True))
    ).exclude(id__in=wishlist_movies).distinct()

    most_viewed_movie = Movie.objects.filter(resolution__in=resolutions).order_by('-watch_count').first()
    most_liked_movie = (
        Movie.objects.filter(resolution__in=resolutions)
        .annotate(like_count=Count('likes'))
        .order_by('-like_count')
        .first()
    )
    # Get the last 10 watched movies for the profile
    watch_history = WatchHistory.objects.filter(profile=profile).select_related('movie')[:10]

    categories = Category.objects.all()
    movies_by_category = {
        category.name: Movie.objects.filter(category=category, resolution__in=resolutions)
        for category in categories
    }
    
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()

    if not profiles.exists() and request.method != "POST":
        return render(request, 'netflix/create_profile.html')

    if request.method == "POST":
        if len(profiles) < 4:  # Limit to max 4 profiles
            name = request.POST.get('profile_name')
            categories_input = request.POST.get('categories', '')  # Get categories or an empty string
            categories = [cat.strip() for cat in categories_input.split(',') if cat.strip()]  # Split and filter non-empty strings

            # Validate categories
            valid_categories = Category.objects.filter(name__in=categories)
            profile = Profile.objects.create(subscription=subscription, name=name)
            profile.preferred_categories.set(valid_categories)  # Assign validated categories
            profile.save()

            Notification.objects.create(
                user=request.user,
                message=f"Profile '{profile.name}' created with categories: {', '.join(cat.name for cat in valid_categories)}."
            )
            
    return render(request, 'netflix/movie.html', {
        'wishlist': wishlist,
        'movies': movies,
        'other_movies': others,
        'recommended_movies': recommended_movies,
        'active_profile': profile,
        'search_text': search_text,
        'most_viewed_movie': most_viewed_movie,
        'most_liked_movie': most_liked_movie,
        'movies_by_category': movies_by_category,
        'categories': categories,
        'watch_history': watch_history,
        'profiles': profiles
    })



@login_required
def category_movies_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    movies = Movie.objects.filter(category=category)

    return render(request, 'netflix/category_movies.html', {
        'category': category,
        'movies': movies,
    })

@login_required
def watch_movie(request, movie_pk):
    movie = get_object_or_404(Movie, pk=movie_pk)
    movie.watch_count = models.F('watch_count') + 1
    movie.save(update_fields=['watch_count'])

    profile_id = request.session.get('active_profile')
    profile = Profile.objects.filter(id=profile_id).first()
    if not profile:
        return redirect('profile_view')

    # Update or create a watch history entry
    WatchHistory.objects.update_or_create(
        profile=profile,
        movie=movie,
        defaults={'watched_at': timezone.now()},
    )

    return render(request, 'netflix/watch_movie.html', {'movie': movie})


@login_required
def watch_movie_view(request):
    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.is_active or subscription.date_expired <= timezone.now():
            subscription.is_active = False
            subscription.save()
            return redirect('subscription_view')
    except Subscription.DoesNotExist:
        return redirect('subscription_view')

    allowed_resolutions = {
        'HD': ['HD'],
        'FHD': ['HD', 'FHD'],
        'UHD': ['HD', 'FHD', 'UHD'],
    }
    resolutions = allowed_resolutions.get(subscription.subscription_type, ['HD'])

    profile_id = request.session.get('active_profile')
    profile = Profile.objects.filter(id=profile_id, subscription=subscription).first()

    if not profile:
        return redirect('profile_selection')

    movie_pk = request.GET.get('movie_pk')
    movie = get_object_or_404(Movie, pk=movie_pk, resolution__in=resolutions)

    # Increment the watch count
    movie.watch_count = models.F('watch_count') + 1
    movie.save(update_fields=['watch_count'])

    # Update or create watch history
    watch_history, created = WatchHistory.objects.update_or_create(
        profile=profile,
        movie=movie,
        defaults={'watched_at': timezone.now()},
    )
    
    profile.movies_watched = models.F('movies_watched') + 1
    profile.save(update_fields=['movies_watched'])

    # Check if the profile liked the movie
    user_liked = Like.objects.filter(profile=profile, movie=movie, is_liked=True).exists()

    return render(request, 'netflix/watch_movie.html', {
        'movie': movie,
        'user_liked': user_liked,
        'watch_count': movie.watch_count,
    })


@login_required
def notification_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'netflix/notifications.html', {'notifications': notifications})


def send_welcome_notification(user):
    """Send a welcome notification to the user."""
    Notification.objects.create(
        user=user,
        message=f"Welcome, {user.username}! Your subscription is active until {user.subscription.date_expired}. Enjoy our services!"
    )

def send_renewal_notification(user):
    """Send a notification after subscription renewal."""
    Notification.objects.create(
        user=user,
        message=f"Thank you for renewing, {user.username}! Your subscription is extended until {user.subscription.date_expired}."
    )


@login_required
def delete_profile_view(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id, subscription__user=request.user)
    profile_name = profile.name
    profile.delete()

    Notification.objects.create(
        user=request.user,
        message=f"Profile '{profile_name}' was deleted."
    )
    return redirect('profile_view')


@login_required
def import_profiles_view(request):
    if request.method == "POST" and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']

        # Read CSV file
        import csv
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            name = row['name']
            categories = row['categories'].split(',')
            profile = Profile.objects.create(
                subscription=Subscription.objects.get(user=request.user),
                name=name
            )
            profile.preferred_categories.set(categories)
            profile.save()

        Notification.objects.create(
            user=request.user,
            message="Profiles were imported successfully via CSV."
        )
        return redirect('profile_view')

    return render(request, 'netflix/import_profiles.html')




def generate_subscription_notifications(subscription):
    # Check if a notification for this event already exists
    if not Notification.objects.filter(user=subscription.user, message__icontains="Your subscription expires").exists():
        expiration_message = f"Your subscription expires on {subscription.date_expired.strftime('%Y-%m-%d')}."
        Notification.objects.create(user=subscription.user, message=expiration_message)

    days_left = (subscription.date_expired - timezone.now()).days
    if days_left <= 3 and not Notification.objects.filter(user=subscription.user, message__icontains="about to expire").exists():
        reminder_message = "Your subscription is about to expire in 3 days. Renew now to continue enjoying our service."
        Notification.objects.create(user=subscription.user, message=reminder_message)


@login_required
def profile_view(request):
    # category
    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.is_active or subscription.date_expired <= timezone.now():
            subscription.is_active = False
            subscription.save()
            return redirect('subscription_view')
    except Subscription.DoesNotExist:
        return redirect('subscription_view')

    profile_id = request.session.get('active_profile')
    profile = Profile.objects.filter(id=profile_id, subscription=subscription).first()

    allowed_resolutions = {
        'HD': ['HD'],
        'FHD': ['HD', 'FHD'],
        'UHD': ['HD', 'FHD', 'UHD'],
    }
    resolutions = allowed_resolutions.get(subscription.subscription_type, ['HD'])

    categories = Category.objects.all()
    movies_by_category = {
        category.name: Movie.objects.filter(category=category, resolution__in=resolutions)
        for category in categories
    }
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()


    # end category
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()

    if not profiles.exists() and request.method != "POST":
        return render(request, 'netflix/create_profile.html', {'profiles': profiles, 'movies_by_category': movies_by_category,'categories': categories,})

    if request.method == "POST":
        if len(profiles) < 4:  # Limit to max 4 profiles
            name = request.POST.get('profile_name')  # Retrieve the profile name
            categories_ids = request.POST.getlist('categories')  # Retrieve selected category IDs as a list
            valid_categories = Category.objects.filter(id__in=categories_ids)  # Validate category IDs

            # Create the profile and assign the selected categories
            profile = Profile.objects.create(subscription=subscription, name=name)
            profile.preferred_categories.set(valid_categories)  # Assign validated categories
            profile.save()

            # Create a notification for the user
            Notification.objects.create(
                user=request.user,
                message=f"Profile '{profile.name}' created with categories: {', '.join(cat.name for cat in valid_categories)}."
            )
        return redirect('index')

    return render(request, 'netflix/profile.html', {'profiles': profiles, 'movies_by_category': movies_by_category,'categories': categories,})


@login_required
def choose_profile_view(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id, subscription__user=request.user)
    request.session['active_profile'] = profile.id
    return redirect('home')    

def register_view(request):
    """Registration View with Email Autofill and Messages."""
    email_autofill = request.GET.get('email', '')  # Fetch email from landing page query param
    
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_conf = request.POST.get('password_conf')

        # Validation
        if password != password_conf:
            messages.error(request, "Passwords do not match!")
            return render(request, 'netflix/register.html', {'email_autofill': email})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered!")
            return render(request, 'netflix/register.html', {'email_autofill': email})
        
        # Create user
        user = User.objects.create(
            first_name=firstname,
            last_name=lastname,
            email=email,
            username=email,
            password=make_password(password)
        )
        messages.success(request, "Registration successful! Redirecting...")
        
        # Auto-login and redirect
        login(request, user)
        return redirect('/index')

    return render(request, 'netflix/register.html', {'email_autofill': email_autofill})

def login_view(request):
    """Login view."""
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'GET':
        # executed to render the login page
        login_form = LoginForm()
        # Get the 'next' parameter from the URL, default to '/browse'
        next_url = request.GET.get('next', '/browse')
        return render(request, 'netflix/login.html', {'login_form': login_form, 'next': next_url})
    else:
        # get user credentials input
        username = request.POST['email']
        password = request.POST['password']
        # If the email provided by user exists and match the
        # password he provided, then we authenticate him.
        user = authenticate(username=username, password=password)
        if user is not None:
            # if the credentials are good, we login the user
            login(request, user)
            # Redirect to the 'next' parameter or default to '/browse'
            next_url = request.POST.get('next', '/browse')
            return HttpResponseRedirect(next_url)
        # if the credentials are wrong, we redirect him to login and let him know
        return render(
            request,
            'netflix/login.html',
            {
                'wrong_credentials': True,
                'login_form': LoginForm(request.POST),
                'next': request.POST.get('next', '/browse'),
            }
        )

def logout_view(request):
    """Logout view."""
    # logout the request
    logout(request)
    # redirect user to home page
    return HttpResponseRedirect('/login')




@login_required
def movie_choice_view(request):
    """Restrict access to the movie page to active subscribers."""
    try:
        # Fetch the user's subscription
        subscription = Subscription.objects.get(user=request.user)

        # Check if subscription is active and not expired
        if subscription.is_active and subscription.date_expired and subscription.date_expired > timezone.now():
            return render(request, 'netflix/movie_choice.html')
        
        # If the subscription is inactive or expired, redirect to subscription page
        subscription.is_active = False  # Mark subscription as inactive if expired
        subscription.save()
        return redirect('subscription_view')

    except Subscription.DoesNotExist:
        # If no subscription exists, redirect to subscription page
        return redirect('subscription_view')


STRIPE_SECRET_KEY = "sk_test_51L8i0jDkGOBWyh471bK0YOEg5VQCiSHFsogH4mfytpAXQixAhGhIR47WImddmQya938dtTrpIadfnl3Aws8JVGys000VEv2oni"  # Replace with your Stripe secret key

@login_required
def subscription_failure(request):
    """Show the subscription failure page."""
    return render(request, 'netflix/subscription_failure.html')

@login_required
def subscription_view(request):
    user_subscription, created = Subscription.objects.get_or_create(user=request.user)

    # Check if subscription has expired
    if user_subscription.date_expired and user_subscription.date_expired < timezone.now():
        user_subscription.is_active = False
        user_subscription.plan = None  # Reset plan
        user_subscription.save()

    plans = sorted([
        {'name': 'Basic', 'price': 500},  # Example prices in cents
        {'name': 'Standard', 'price': 1000},
        {'name': 'Premium', 'price': 1500},
    ], key=lambda x: x['price'])

    if request.method == "POST":
        plan = request.POST.get('plan')
        for p in plans:
            if p['name'] == plan:
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{plan} Plan Subscription",
                            },
                            'unit_amount': p['price'],
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri('/subscription/callback/'),
                    cancel_url=request.build_absolute_uri('/subscription/failure/'),
                )
                # Update subscription details
                user_subscription.plan = plan
                user_subscription.is_active = True
                user_subscription.date_expired = timezone.now() + timezone.timedelta(days=30)
                user_subscription.save()
                return redirect(session.url, code=303)

    return render(request, 'netflix/subscription.html', {
        'subscription': user_subscription,
        'plans': plans,
    })

@login_required
def subscription_callback(request):
    user_subscription = Subscription.objects.get(user=request.user)
    user_subscription.is_active = True
    user_subscription.date_subscribed = timezone.now()
    user_subscription.date_expired = timezone.now() + timedelta(days=30)

    # Map plans to resolutions
    plan_to_resolution = {
        'Basic': 'HD',
        'Standard': 'FHD',
        'Premium': 'UHD',
    }
    user_subscription.subscription_type = plan_to_resolution.get(user_subscription.plan, 'HD')
    user_subscription.save()

    return redirect('index')


@login_required
def view_wishlist(request):
    profile_id = request.session.get('active_profile')
    profile = get_object_or_404(Profile, id=profile_id, subscription__user=request.user)
    wishlist = Wishlist.objects.filter(profile=profile)

    # Extract categories and tags from wishlist movies
    wishlist_movies = [item.movie for item in wishlist]
    categories = wishlist_movies and [movie.category for movie in wishlist_movies]
    tags = wishlist_movies and [tag for movie in wishlist_movies for tag in movie.tags.all()]

    # Generate recommendations: movies in the same categories or with similar tags
    recommended_movies = Movie.objects.filter(
        models.Q(category__in=categories) |
        models.Q(tags__in=tags)
    ).exclude(id__in=[movie.id for movie in wishlist_movies]).distinct()

    # Notify the user about new recommendations
    if recommended_movies.exists():
        Notification.objects.create(
            user=request.user,
            message=f"New recommendations based on your wishlist for {profile.name} are available!"
        )

    return render(request, 'netflix/view_wishlist.html', {
        'wishlist': wishlist,
        'recommended_movies': recommended_movies,
        'active_profile': profile,
    })

@login_required
def add_to_wishlist(request, movie_id):
    profile_id = request.session.get('active_profile')
    profile = get_object_or_404(Profile, id=profile_id, subscription__user=request.user)
    movie = get_object_or_404(Movie, id=movie_id)

    # Check if movie already exists in wishlist
    if not Wishlist.objects.filter(profile=profile, movie=movie).exists():
        Wishlist.objects.create(profile=profile, movie=movie)

        Notification.objects.create(
            user=request.user,
            message=f"Movie '{movie.name}' was added to {profile.name}'s wishlist."
        )

    return redirect('view_wishlist')


@login_required
def remove_from_wishlist(request, wishlist_id):
    profile_id = request.session.get('active_profile')
    profile = get_object_or_404(Profile, id=profile_id, subscription__user=request.user)
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, profile=profile)

    wishlist_item.delete()

    Notification.objects.create(
        user=request.user,
        message=f"A movie was removed from {profile.name}'s wishlist."
    )

    return redirect('view_wishlist')



@login_required
def manage_profiles_view(request):
    """Manage user profiles (up to 4 per subscription)."""
    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.is_active:
            return redirect('subscription_view')

        profiles = subscription.profiles.all()
        if request.method == "POST":
            if "delete_profile" in request.POST:
                profile_id = request.POST.get("profile_id")
                Profile.objects.filter(id=profile_id, subscription=subscription).delete()
                messages.success(request, "Profile deleted successfully.")
            elif len(profiles) < 4 and "profile_name" in request.POST:
                profile_name = request.POST.get("profile_name")
                if profile_name:
                    Profile.objects.create(subscription=subscription, name=profile_name)
                    messages.success(request, "Profile added successfully.")

        return render(request, 'netflix/manage_profiles.html', {'profiles': profiles})

    except Subscription.DoesNotExist:
        return redirect('subscription_view')



    
@login_required
def renew_subscription(request):
    """Renew the user's subscription."""
    try:
        subscription = Subscription.objects.get(user=request.user)
        subscription.date_expired += timezone.timedelta(days=30)  # Extend by 30 days
        subscription.is_active = True
        subscription.save()

        send_renewal_notification(request.user)  # Notify user of renewal
        messages.success(request, "Subscription renewed successfully.")
        return redirect('subscription_view')
    except Subscription.DoesNotExist:
        messages.error(request, "No active subscription found.")
        return redirect('subscription_view')

@login_required
def delete_profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Profile deleted successfully.')
        return redirect('index')  # Redirect to appropriate page

    return render(request, 'netflix/delete_profile_confirm.html', {'profile': profile})



@login_required
def edit_profile_view(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id, subscription__user=request.user)
    all_categories = Category.objects.all()

    if request.method == "POST":
        name = request.POST.get('profile_name')
        categories_input = request.POST.get('categories')  # Comma-separated IDs
        category_ids = [int(cat_id) for cat_id in categories_input.split(',') if cat_id.isdigit()]
        
        # Validate categories
        valid_categories = Category.objects.filter(id__in=category_ids)
        profile.name = name
        profile.preferred_categories.set(valid_categories)  # Assign validated categories
        profile.save()

        Notification.objects.create(
            user=request.user,
            message=f"Profile '{profile.name}' was updated with categories: {', '.join(cat.name for cat in valid_categories)}."
        )
        return redirect('profile_view')

    existing_categories = ",".join(map(str, profile.preferred_categories.values_list('id', flat=True)))
    return render(request, 'netflix/edit_profile.html', {
        'profile': profile,
        'all_categories': all_categories,
        'existing_categories': existing_categories,
    })



@login_required
def search_view(request):
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()

    if not profiles.exists() and request.method != "POST":
        return render(request, 'netflix/create_profile.html')

    if request.method == "POST":
        if len(profiles) < 4:  # Limit to max 4 profiles
            name = request.POST.get('profile_name')
            categories_input = request.POST.get('categories', '')  # Get categories or an empty string
            categories = [cat.strip() for cat in categories_input.split(',') if cat.strip()]  # Split and filter non-empty strings

            # Validate categories
            valid_categories = Category.objects.filter(name__in=categories)
            profile = Profile.objects.create(subscription=subscription, name=name)
            profile.preferred_categories.set(valid_categories)  # Assign validated categories
            profile.save()

            Notification.objects.create(
                user=request.user,
                message=f"Profile '{profile.name}' created with categories: {', '.join(cat.name for cat in valid_categories)}."
            )
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')


    search_text = request.GET.get('search_text', '')
    results = []
    
    if search_text:
        results = Movie.objects.filter(name__icontains=search_text)  # Adjust filter as needed
    
    return render(request, 'netflix/search.html', {'search_text': search_text, 'results': results, 'profiles': profiles, 'notifications': notifications})

@login_required
def category_view(request):
    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.is_active or subscription.date_expired <= timezone.now():
            subscription.is_active = False
            subscription.save()
            return redirect('subscription_view')
    except Subscription.DoesNotExist:
        return redirect('subscription_view')

    profile_id = request.session.get('active_profile')
    profile = Profile.objects.filter(id=profile_id, subscription=subscription).first()

    allowed_resolutions = {
        'HD': ['HD'],
        'FHD': ['HD', 'FHD'],
        'UHD': ['HD', 'FHD', 'UHD'],
    }
    resolutions = allowed_resolutions.get(subscription.subscription_type, ['HD'])

    categories = Category.objects.all()
    movies_by_category = {
        category.name: Movie.objects.filter(category=category, resolution__in=resolutions)
        for category in categories
    }
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()

    if not profiles.exists() and request.method != "POST":
        return render(request, 'netflix/create_profile.html')

    if request.method == "POST":
        if len(profiles) < 4:  # Limit to max 4 profiles
            name = request.POST.get('profile_name')
            categories_input = request.POST.get('categories', '')  # Get categories or an empty string
            categories = [cat.strip() for cat in categories_input.split(',') if cat.strip()]  # Split and filter non-empty strings

            # Validate categories
            valid_categories = Category.objects.filter(name__in=categories)
            profile = Profile.objects.create(subscription=subscription, name=name)
            profile.preferred_categories.set(valid_categories)  # Assign validated categories
            profile.save()

            Notification.objects.create(
                user=request.user,
                message=f"Profile '{profile.name}' created with categories: {', '.join(cat.name for cat in valid_categories)}."
            )
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')


    
    return render(request, 'netflix/category_view.html', { 'profiles': profiles, 'notifications': notifications, 'categories': categories}, )




def latest_movies(request):
    
    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.is_active or subscription.date_expired <= timezone.now():
            subscription.is_active = False
            subscription.save()
            return redirect('subscription_view')
    except Subscription.DoesNotExist:
        return redirect('subscription_view')

    profile_id = request.session.get('active_profile')
    profile = Profile.objects.filter(id=profile_id, subscription=subscription).first()

    allowed_resolutions = {
        'HD': ['HD'],
        'FHD': ['HD', 'FHD'],
        'UHD': ['HD', 'FHD', 'UHD'],
    }
    resolutions = allowed_resolutions.get(subscription.subscription_type, ['HD'])

    categories = Category.objects.all()
    movies_by_category = {
        category.name: Movie.objects.filter(category=category, resolution__in=resolutions)
        for category in categories
    }
    subscription = get_object_or_404(Subscription, user=request.user)
    profiles = subscription.profiles.all()

    if not profiles.exists() and request.method != "POST":
        return render(request, 'netflix/create_profile.html')

    if request.method == "POST":
        if len(profiles) < 4:  # Limit to max 4 profiles
            name = request.POST.get('profile_name')
            categories_input = request.POST.get('categories', '')  # Get categories or an empty string
            categories = [cat.strip() for cat in categories_input.split(',') if cat.strip()]  # Split and filter non-empty strings

            # Validate categories
            valid_categories = Category.objects.filter(name__in=categories)
            profile = Profile.objects.create(subscription=subscription, name=name)
            profile.preferred_categories.set(valid_categories)  # Assign validated categories
            profile.save()

            Notification.objects.create(
                user=request.user,
                message=f"Profile '{profile.name}' created with categories: {', '.join(cat.name for cat in valid_categories)}."
            )
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    
    # Fetch the latest 10 movies
    movies = Movie.objects.order_by('-date_created')[:10]
    return render(request, 'netflix/latest_movies.html', { 'profiles': profiles, 'notifications': notifications, 'movies_by_category': movies_by_category,'categories': categories, 'movies': movies})