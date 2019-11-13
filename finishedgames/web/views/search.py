from core.models import Game
from dal import autocomplete
from django.db.models.functions import Length, Lower
from django.db.models.query import QuerySet


class GameAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self) -> QuerySet:
        queryset = Game.objects.all()
        if self.q:
            queryset = queryset.filter(name__icontains=self.q)
        queryset = queryset.order_by(Length("name"), Lower("name"))

        return queryset
