import random
from django.shortcuts import render
from .models import Video, Reussite, Defi
import requests  # À ajouter avec les autres imports en haut

# AJOUTE CELLE-CI À LA PLACE :
from decouple import config
from google import genai  # Assure-toi d'avoir fait : pip install google-genai
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib import colors
import json
import io


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
    mes_reussites = Reussite.objects.filter(
        active=True, type='moi'
    ).prefetch_related('medias')

    reussites_visiteurs = Reussite.objects.filter(
        active=True, type='visiteur'
    ).prefetch_related('medias')

    return render(request, 'reussites.html', {
        'mes_reussites': mes_reussites,
        'reussites_visiteurs': reussites_visiteurs,
    })

# 1. Enlève l'import de csrf_exempt s'il n'est plus utilisé ailleurs
# from django.views.decorators.csrf import csrf_exempt 

# 2. Modifie la vue en enlevant le décorateur @csrf_exempt
def generer_plan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)

        objectif = data.get('objectif', '')
        contraintes = data.get('contraintes', '')

        if not objectif:
            return JsonResponse({'success': False, 'error': 'Objectif manquant'}, status=400)

        try:
            client = genai.Client(api_key=config('GEMINI_API_KEY'))

            prompt = f"""
Tu es un coach de bien-être et fitness professionnel.
Un utilisateur veut atteindre l'objectif suivant sur 1 mois : "{objectif}"
Contraintes ou problèmes de santé : "{contraintes if contraintes else 'Aucune'}"

Génère un plan détaillé sur 1 mois avec exactement cette structure :

INTRODUCTION
[2-3 phrases motivantes personnalisées selon l'objectif]

OBJECTIF GLOBAL
[Reformule l'objectif de manière claire et mesurable]

CHALLENGE SEMAINE 1 : [Nom du challenge]
Objectif : [objectif spécifique]
Description : [description du challenge]
- Lundi : [activité - durée - intensité]
- Mardi : [activité - durée - intensité]
- Mercredi : [activité - durée - intensité]
- Jeudi : [activité - durée - intensité]
- Vendredi : [activité - durée - intensité]
- Samedi : [activité - durée - intensité]
- Dimanche : [repos ou activité légère]

CHALLENGE SEMAINE 2 : [Nom du challenge]
[même structure]

CHALLENGE SEMAINE 3 : [Nom du challenge]
[même structure]

CHALLENGE SEMAINE 4 : [Nom du challenge]
[même structure]

CONSEILS PERSONNALISÉS
[3-5 conseils adaptés aux contraintes mentionnées]

MESSAGE DE MOTIVATION
[Message final encourageant]

Réponds en français. Adapte TOUS les exercices aux contraintes mentionnées.
"""

            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
            )

            plan_texte = response.text
            if not plan_texte:
                return JsonResponse({'success': False, 'error': "Réponse vide de l'IA."}, status=500)

        except Exception as e:
            print(f"--- ERREUR GEMINI : {str(e)} ---")
            return JsonResponse({'success': False, 'error': f"Erreur : {str(e)}"}, status=500)

        # Détecte le prix
        mots_fitness = ['fitness', 'sport', 'kilo', 'poids', 'musculation',
                        'cardio', 'course', 'marche', 'yoga', 'bien-être',
                        'bien être', 'minceur', 'forme', 'courir', 'perdre',
                        'prendre', 'muscle', 'souple', 'stretching']
        est_fitness = any(mot in objectif.lower() for mot in mots_fitness)
        prix = 500 if est_fitness else 1000

        # Stocke en session
        request.session['plan_complet'] = plan_texte
        request.session['plan_objectif'] = objectif
        request.session['plan_prix'] = prix

        # Aperçu 30 premières lignes
        lignes = plan_texte.split('\n')
        apercu = '\n'.join(lignes[:30])

        return JsonResponse({
            'success': True,
            'apercu': apercu,
            'total_lignes': len(lignes),
            'prix': prix,
        })

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


def telecharger_pdf(request):
    """Génère et retourne le PDF après vérification de la redirection ou de la session"""
    
    # 1. On regarde si FedaPay nous envoie un statut directement dans l'URL de redirection
    status_payment = request.GET.get('status')
    transaction_id = request.GET.get('id')
    
    plan_texte = request.session.get('plan_complet')
    objectif = request.session.get('plan_objectif', 'Mon objectif')

    # Si on revient de FedaPay avec un succès, ou si la session est toujours valide
    paiement_valide = (status_payment in ['approved', 'successful']) or (plan_texte is not None)

    if not paiement_valide:
        return HttpResponse(
            'Validation du paiement échouée. Si vous avez été débité, contactez le support avec votre ID de transaction.', 
            status=403
        )

    # Sécurité : Si la session a expiré à cause du temps de paiement mais que le paiement est OK,
    # on évite un crash en mettant un texte par défaut (ou idéalement, tu pourrais sauvegarder le plan en BDD)
    if not plan_texte:
        plan_texte = "Félicitations pour votre achat ! Votre plan est en cours de rechargement. Veuillez nous contacter si ce message persiste."

    # --- RESTE DE TON CODE GÉNÉRATION PDF (REPORTLAB) ---
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('Titre', parent=styles['Title'], fontSize=20, textColor=colors.HexColor('#3aaa5c'), spaceAfter=20)
    style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1a1a1a'), spaceBefore=15, spaceAfter=8)
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, leading=18, spaceAfter=6)

    contenu = []
    contenu.append(Paragraph("1 Kilo en Moins", style_titre))
    contenu.append(Paragraph(f"Mon Plan Personnalisé — {objectif}", style_h2))
    contenu.append(Spacer(1, 0.5*cm))

    for ligne in plan_texte.split('\n'):
        ligne = ligne.strip()
        if not ligne:
            contenu.append(Spacer(1, 0.3*cm))
        elif ligne.isupper() or any(ligne.startswith(x) for x in ['CHALLENGE', 'INTRODUCTION', 'CONSEILS', 'MESSAGE', 'OBJECTIF']):
            contenu.append(Paragraph(ligne, style_h2))
        else:
            contenu.append(Paragraph(ligne, style_normal))

    doc.build(contenu)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="mon_plan_1kilo.pdf"'
    return response