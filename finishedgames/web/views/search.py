from dal import autocomplete
from django.db.models.functions import Lower
from django.db.models.query import QuerySet

from core.models import Game


class GameAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self) -> QuerySet:
        if not self.request.user.is_authenticated:
            return Game.objects.none()

        queryset = Game.objects.all()
        if self.q:
            queryset = queryset.filter(name__istartswith=self.q)
        queryset = queryset.order_by(Lower("name"))

        return queryset
