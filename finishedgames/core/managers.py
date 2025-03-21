from core.models import UserGame, WishlistedUserGame
from django.conf import settings


class CatalogManager:
    @staticmethod
    def mark_as_no_longer_owned(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        CatalogManager.unmark_as_currently_playing(user=user, game_id=game_id, platform_id=platform_id)
        CatalogManager.unmark_as_abandoned(user=user, game_id=game_id, platform_id=platform_id)

        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.no_longer_owned = True
        user_game.save(update_fields=["no_longer_owned"])


    @staticmethod
    def unmark_as_no_longer_owned(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.no_longer_owned = False
        user_game.save(update_fields=["no_longer_owned"])

    @staticmethod
    def mark_as_finished(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int, year_finished: int) -> None:
        CatalogManager.unmark_as_abandoned(user=user, game_id=game_id, platform_id=platform_id)

        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.year_finished = year_finished
        user_game.save(update_fields=["year_finished"])


    @staticmethod
    def unmark_as_finished(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.year_finished = None
        user_game.save(update_fields=["year_finished"])

    @staticmethod
    def mark_as_currently_playing(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        CatalogManager.unmark_as_no_longer_owned(user=user, game_id=game_id, platform_id=platform_id)
        CatalogManager.unmark_as_abandoned(user=user, game_id=game_id, platform_id=platform_id)

        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.currently_playing = True
        user_game.save(update_fields=["currently_playing"])


    @staticmethod
    def unmark_as_currently_playing(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.currently_playing = False
        user_game.save(update_fields=["currently_playing"])

    @staticmethod
    def mark_as_wishlisted(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        wishlist_game = WishlistedUserGame(user_id=user.id, game_id=game_id, platform_id=platform_id)
        wishlist_game.full_clean()
        wishlist_game.save()

    @staticmethod
    def unmark_as_wishlisted(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        WishlistedUserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).delete()

    @staticmethod
    def add_to_catalog(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        CatalogManager.unmark_as_wishlisted(user=user, game_id=game_id, platform_id=platform_id)

        user_game = UserGame(user_id=user.id, game_id=game_id, platform_id=platform_id)
        user_game.full_clean()
        user_game.save()


    @staticmethod
    def remove_from_catalog(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).delete()

    @staticmethod
    def mark_as_abandoned(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int, year_finished: int) -> None:

        CatalogManager.unmark_as_currently_playing(user=user, game_id=game_id, platform_id=platform_id)
        CatalogManager.unmark_as_finished(user=user, game_id=game_id, platform_id=platform_id)

        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.abandoned = True
        user_game.year_finished = year_finished
        user_game.save(update_fields=["abandoned", "year_finished"])

    @staticmethod
    def unmark_as_abandoned(user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int) -> None:
        user_game = UserGame.objects.filter(user=user, game_id=game_id, platform_id=platform_id).get()
        user_game.abandoned = False
        user_game.year_finished = None
        user_game.save(update_fields=["abandoned", "year_finished"])
