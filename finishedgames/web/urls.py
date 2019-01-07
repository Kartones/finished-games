from django.contrib.auth import views as auth_views
from django.urls import path

from web.views import (base, game, platform, user)

urlpatterns = [
    path("", base.index, name="index"),

    path('accounts/login/', auth_views.LoginView.as_view(), name="login"),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page="index"), name="logout"),

    path("games/", game.games, name="games"),
    path("games/<int:game_id>/", game.game_details, name="game_details"),

    path("platforms/", platform.platforms, name="platforms"),
    path("platforms/<int:platform_id>/", platform.platform_details, name="platform_details"),
    path("platforms/<int:platform_id>/games/", game.games_by_platform, name="games_by_platform"),

    path("users/", user.users, name="users"),
    path("users/<slug:username>/", user.public_profile, name="user_public_profile"),
    path("users/<slug:username>/profile/", user.profile, name="user_profile"),
    path("users/<slug:username>/catalog/", user.catalog, name="user_catalog"),
    path("users/<slug:username>/games/", user.games, name="user_games"),
    path("users/<slug:username>/platforms/", user.platforms, name="user_platforms"),
    path(
        "users/<slug:username>/games/currently-playing/",
        user.currently_playing_games,
        name="user_currently_playing_games"
    ),
    path("users/<slug:username>/games/finished/", user.finished_games, name="user_finished_games"),
    path("users/<slug:username>/games/wishlisted/", user.wishlisted_games, name="user_wishlisted_games"),
    path(
        "users/<slug:username>/platforms/<int:platform_id>/games/",
        user.user_games_by_platform,
        name="user_games_by_platform"
    ),
    path("users/<slug:username>/games/new/", user.add_game, name="user_add_game"),
]
