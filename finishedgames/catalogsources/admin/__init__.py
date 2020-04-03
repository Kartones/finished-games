from catalogsources.admin.models import FetchedGameAdmin, FetchedPlatformAdmin
from catalogsources.models import FetchedGame, FetchedPlatform
from django.contrib import admin

# I don't fancy placing logic into init files but by convention django searches for an admin package/file so...

admin.site.register(FetchedGame, FetchedGameAdmin)
admin.site.register(FetchedPlatform, FetchedPlatformAdmin)
