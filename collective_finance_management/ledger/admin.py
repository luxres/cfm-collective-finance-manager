from django.contrib import admin

from .models import AccountHolder, AccountHolderMembership

admin.site.register(AccountHolder)
admin.site.register(AccountHolderMembership)