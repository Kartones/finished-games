from django.contrib.auth import views as auth_views
from django.urls import path

from web.views import (base, game, platform, user)

urlpatterns = [
    path("", base.index, name="index"),
    path("help/", base.help, name="help"),

    path('accounts/login/', auth_views.LoginView.as_view(), name="login"),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page="index"), name="logout"),

    path("games/", game.games, name="games"),
    path("games/<int:game_id>/", game.GameDetailsView.as_view(), name="game_details"),

    path("platforms/", platform.platforms, name="platforms"),
    path("platforms/<int:platform_id>/", platform.platform_details, name="platform_details"),
    path("platforms/<int:platform_id>/games/", game.GamesByPlatformView.as_view(), name="games_by_platform"),

    path("users/", user.users, name="users"),
    path("users/<slug:username>/", user.public_profile, name="user_public_profile"),
    path("users/<slug:username>/profile/", user.profile, name="user_profile"),
    path("users/<slug:username>/catalog/", user.catalog, name="user_catalog"),
    path("users/<slug:username>/games/", user.GamesView.as_view(), name="user_games"),
    path("users/<slug:username>/platforms/", user.platforms, name="user_platforms"),
    path(
        "users/<slug:username>/games/currently-playing/",
        user.GamesCurrentlyPlayingView.as_view(),
        name="user_currently_playing_games"
    ),
    path("users/<slug:username>/games/finished/", user.GamesFinishedView.as_view(), name="user_finished_games"),
    path("users/<slug:username>/games/wishlisted/", user.GamesWishlistedView.as_view(), name="user_wishlisted_games"),
    path(
        "users/<slug:username>/platforms/<int:platform_id>/games/",
        user.GamesByPlatformView.as_view(),
        name="user_games_by_platform"
    ),
    path(
        "users/<slug:username>/games/no-longer-owned/",
        user.NoLongerOwnedGamesView.as_view(),
        name="user_no_longer_owned_games"
    ),
    path("users/<slug:username>/games/new/", user.add_game, name="user_add_game"),
]
