from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.generic import TemplateView
from web.views import base, game, platform, search, user

urlpatterns = [
    path("", base.index, name="index"),
    path("help/", base.help, name="help"),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),
    path("games/", game.games, name="games"),
    path("games/<int:game_id>/", game.GameDetailsView.as_view(), name="game_details"),
    path(
        "games/starting-with/<str:character>/",
        game.GamesStartingWithCharacterView.as_view(),
        name="games_filtered_by_starting_character",
    ),
    path("games/search/", game.GameSearch.as_view(), name="game_search"),
    path("platforms/", platform.platforms, name="platforms"),
    path("platforms/<int:platform_id>/", platform.platform_details, name="platform_details"),
    path("platforms/<int:platform_id>/games/", game.GamesByPlatformView.as_view(), name="games_by_platform"),
    path("search/game-autocomplete/", search.GameAutocompleteView.as_view(), name="game_autocomplete"),
    path("search/platform-autocomplete/", search.PlatformAutocompleteView.as_view(), name="platform_autocomplete"),
    path("users/", user.users, name="users"),
    path("users/<slug:username>/", user.catalog, name="user_catalog"),
    path("users/<slug:username>/games/", user.GamesView.as_view(), name="user_games"),
    path("users/<slug:username>/platforms/", user.platforms, name="user_platforms"),
    path(
        "users/<slug:username>/games/currently-playing/",
        user.GamesCurrentlyPlayingView.as_view(),
        name="user_currently_playing_games",
    ),
    path("users/<slug:username>/games/finished/", user.GamesFinishedView.as_view(), name="user_finished_games"),
    path("users/<slug:username>/games/pending/", user.GamesPendingView.as_view(), name="user_pending_games"),
    path("users/<slug:username>/games/abandoned/", user.GamesAbandonedView.as_view(), name="user_abandoned_games"),
    path("users/<slug:username>/games/wishlisted/", user.GamesWishlistedView.as_view(), name="user_wishlisted_games"),
    path(
        "users/<slug:username>/platforms/search/",
        user.WishlistedPlatformFilter.as_view(),
        name="wishlisted_games_platform_filter",
    ),
    path(
        "users/<slug:username>/platforms/<int:platform_id>/games/",
        user.GamesByPlatformView.as_view(),
        name="user_games_by_platform",
    ),
    path(
        "users/<slug:username>/games/no-longer-owned/",
        user.NoLongerOwnedGamesView.as_view(),
        name="user_no_longer_owned_games",
    ),
    path("users/<slug:username>/options/", user.Options.as_view(), name="user_options"),
    re_path(r"^google.*\.html$", TemplateView.as_view(template_name="google-validation.html")),
]
