import random
from django.shortcuts import render
from .models import Video, Reussite, Defi

def reorder_around_active(videos, active_index):
    """Réorganise la liste pour que la vidéo active soit au centre"""
    if not videos:
        return videos, 0
    n = len(videos)
    # Réorganise : les vidéos avant l'active, l'active, les vidéos après
    reordered = videos[active_index:] + videos[:active_index]
    # L'active est maintenant à l'index 0, on la met au milieu
    half = n // 2
    reordered = reordered[n - half:] + reordered[:n - half]
    new_active = half
    return reordered, new_active

def home(request):
    def get_tiktok_id(url):
        try:
            return url.split('/video/')[-1].split('?')[0]
        except:
            return ''

    videos_fitness = list(Video.objects.filter(categorie__nom='fitness', active=True))
    videos_dance = list(Video.objects.filter(categorie__nom='dance', active=True))

    videos_fitness_data = [
        {'titre': v.titre, 'tiktok_id': get_tiktok_id(v.tiktok_url)}
        for v in videos_fitness
    ]
    videos_dance_data = [
        {'titre': v.titre, 'tiktok_id': get_tiktok_id(v.tiktok_url)}
        for v in videos_dance
    ]

    # Sélection aléatoire
    fitness_random = random.randint(0, len(videos_fitness_data) - 1) if videos_fitness_data else 0
    dance_random = random.randint(0, len(videos_dance_data) - 1) if videos_dance_data else 0

    # Réorganisation autour de l'active
    videos_fitness_data, fitness_start = reorder_around_active(videos_fitness_data, fitness_random)
    videos_dance_data, dance_start = reorder_around_active(videos_dance_data, dance_random)
    defis = Defi.objects.filter(active=True)

    context = {
        'videos_fitness': videos_fitness_data,
        'videos_dance': videos_dance_data,
        'fitness_start': fitness_start,
        'dance_start': dance_start,
        'defis': defis,
    }
    return render(request, 'home.html', context)


def reussites(request):
    def get_tiktok_id(url):
        try:
            return url.split('/video/')[-1].split('?')[0]
        except:
            return ''

    mes_reussites_qs = Reussite.objects.filter(
        active=True, type='moi'
    ).prefetch_related('medias')

    reussites_visiteurs_qs = Reussite.objects.filter(
        active=True, type='visiteur'
    ).prefetch_related('medias')

    # Prépare les données avec les IDs TikTok déjà extraits
    mes_reussites = []
    for r in mes_reussites_qs:
        medias = []
        for m in r.medias.all():
            medias.append({
                'type_media': m.type_media,
                'photo_url': m.photo.url if m.photo else None,
                'tiktok_id': get_tiktok_id(m.tiktok_url) if m.tiktok_url else '',
            })
        mes_reussites.append({
            'titre': r.titre,
            'date_reussite': r.date_reussite,
            'medias': medias,
        })

    reussites_visiteurs = []
    for r in reussites_visiteurs_qs:
        media = r.medias.first()
        reussites_visiteurs.append({
            'nom': r.nom,
            'titre': r.titre,
            'lien_post': r.lien_post,
            'media': {
                'type_media': media.type_media if media else None,
                'photo_url': media.photo.url if media and media.photo else None,
                'tiktok_id': get_tiktok_id(media.tiktok_url) if media and media.tiktok_url else '',
            } if media else None,
        })

    return render(request, 'reussites.html', {
        'mes_reussites': mes_reussites,
        'reussites_visiteurs': reussites_visiteurs,
    })