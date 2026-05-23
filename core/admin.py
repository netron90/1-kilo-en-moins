from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Categorie, Video, Reussite, ReussiteMedia, Defi


@admin.register(Defi)
class DefiAdmin(admin.ModelAdmin):
    list_display = ['texte', 'accompli', 'ordre', 'active']
    list_editable = ['accompli', 'ordre', 'active']
    
@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom']


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'ordre', 'active']
    list_editable = ['ordre', 'active']
    list_filter = ['categorie', 'active']


class ReussiteMediaInline(admin.TabularInline):
    model = ReussiteMedia
    extra = 1


@admin.register(Reussite)
class ReussiteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'titre', 'type', 'date_reussite', 'active']
    list_editable = ['active']
    list_filter = ['type', 'active']
    inlines = [ReussiteMediaInline]