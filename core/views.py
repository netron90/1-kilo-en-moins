import random
from django.shortcuts import render
from .models import Video, Reussite, Defi
import requests  # À ajouter avec les autres imports en haut

import json
import re

# AJOUTE CELLE-CI À LA PLACE :
from decouple import config
from google import genai  # Assure-toi d'avoir fait : pip install google-genai
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
import json
import io
import os
from django.conf import settings
BASE_DIR = settings.BASE_DIR
import urllib.parse
from django.contrib import messages
# Importe ton exception de sécurité Gemini si tu utilises le SDK google-generativeai
import google.api_core.exceptions


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

# YOUTUBE AVEC MOT CLE
# def generer_plan(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)

#         objectif = data.get('objectif', '')
#         contraintes = data.get('contraintes', '')

#         if not objectif:
#             return JsonResponse({'success': False, 'error': 'Objectif manquant'}, status=400)

#         try:
#             client = genai.Client(api_key=config('GEMINI_API_KEY'))

#             prompt = f"""
# Tu es un coach de bien-être et fitness professionnel.
# Un utilisateur veut atteindre l'objectif suivant sur 1 mois : "{objectif}"
# Contraintes ou problèmes de santé : "{contraintes if contraintes else 'Aucune'}"

# Génère un plan détaillé sur 1 mois avec exactement cette structure :

# INTRODUCTION
# [2-3 phrases motivantes personnalisées selon l'objectif]

# OBJECTIF GLOBAL
# [Reformule l'objectif de manière claire et mesurable]

# CHALLENGE SEMAINE 1 : [Nom du challenge]
# Objectif : [objectif spécifique]
# Description : [description du challenge]
# - Lundi : [activité - durée - intensité] | RECHERCHE: [mots-clés YouTube en français pour cette activité, ex: "pompes débutant technique"]
# - Mardi : [activité - durée - intensité] | RECHERCHE: [mots-clés YouTube]
# - Mercredi : [activité - durée - intensité] | RECHERCHE: [mots-clés YouTube]
# - Jeudi : [activité - durée - intensité] | RECHERCHE: [mots-clés YouTube]
# - Vendredi : [activité - durée - intensité] | RECHERCHE: [mots-clés YouTube]
# - Samedi : [activité - durée - intensité] | RECHERCHE: [mots-clés YouTube]
# - Dimanche : [repos ou activité légère] | RECHERCHE: [mots-clés YouTube si applicable]

# CHALLENGE SEMAINE 2 : [Nom du challenge]
# [même structure]

# CHALLENGE SEMAINE 3 : [Nom du challenge]
# [même structure]

# CHALLENGE SEMAINE 4 : [Nom du challenge]
# [même structure]

# CONSEILS PERSONNALISÉS
# [3-5 conseils adaptés aux contraintes mentionnées]

# MESSAGE DE MOTIVATION
# [Message final encourageant]

# Réponds en français. Adapte TOUS les exercices aux contraintes mentionnées.
# Pour chaque RECHERCHE, fournis des mots-clés précis et courts (3-5 mots max) pour trouver une vidéo YouTube démonstrative.
# """

#             response = client.models.generate_content(
#                 model='gemini-3.5-flash',
#                 contents=prompt,
#             )

#             plan_texte = response.text
#             if not plan_texte:
#                 return JsonResponse({'success': False, 'error': "Réponse vide de l'IA."}, status=500)

#         except Exception as e:
#             print(f"--- ERREUR GEMINI : {str(e)} ---")
#             return JsonResponse({'success': False, 'error': f"Erreur : {str(e)}"}, status=500)

#         # Détecte le prix
#         mots_fitness = ['fitness', 'sport', 'kilo', 'poids', 'musculation',
#                         'cardio', 'course', 'marche', 'yoga', 'bien-être',
#                         'bien être', 'minceur', 'forme', 'courir', 'perdre',
#                         'prendre', 'muscle', 'souple', 'stretching']
#         est_fitness = any(mot in objectif.lower() for mot in mots_fitness)
#         prix = 500 if est_fitness else 1000

#         # Stocke en session
#         request.session['plan_complet'] = plan_texte
#         request.session['plan_objectif'] = objectif
#         request.session['plan_prix'] = prix

#         # Aperçu 30 premières lignes
#         lignes = plan_texte.split('\n')
#         apercu = '\n'.join(lignes[:30])

#         return JsonResponse({
#             'success': True,
#             'apercu': apercu,
#             'total_lignes': len(lignes),
#             'prix': prix,
#         })

#     return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

# YOUTUBE AVEC LIEN VERS DES RECHERCHES VIDEOS
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
        
        # ==========================================================
        # SÉCURITÉ : FILTRAGE DES MOTS-CLÉS / THÈMES DÉPLACÉS
        # ==========================================================
        termes_interdits = [
            r"sexe", r"sexuel", r"porno", r"nude", r"insulte", r"connard", 
            r"pute", r"salope", r"baiser", r"penis", r"vagin", r"orgasme"
        ]
        
        contient_contenu_deplace = any(
            re.search(pattern, objectif, re.IGNORECASE) or re.search(pattern, contraintes, re.IGNORECASE)
            for pattern in termes_interdits
        )
        
        if contient_contenu_deplace:
            # On renvoie le message d'erreur au format JSON
            return JsonResponse({
                'success': False, 
                'message': "Désolé, votre objectif ou vos contraintes contiennent des termes inappropriés ou non conformes à nos règles d'utilisation. Veuillez formuler un objectif axé sur le bien-être, le sport ou le développement personnel."
            })

        try:
            client = genai.Client(api_key=config('GEMINI_API_KEY'))

            prompt = f"""
Tu es un expert et coach professionnel spécialisé dans le domaine lié à l'objectif suivant : "{objectif}".
Adapte ton rôle de coach selon cet objectif — si c'est du fitness sois un coach sportif, si c'est de la couture sois un expert en couture, si c'est l'apprentissage d'une langue sois un professeur de langue, etc.

Un utilisateur veut atteindre l'objectif suivant sur 1 mois : "{objectif}"
Contraintes ou limitations : "{contraintes if contraintes else 'Aucune'}"

Génère un plan détaillé sur 1 mois adapté au domaine de l'objectif, avec exactement cette structure :

INTRODUCTION
[2-3 phrases motivantes personnalisées selon l'objectif et le domaine]

OBJECTIF GLOBAL
[Reformule l'objectif de manière claire et mesurable]

CHALLENGE SEMAINE 1 : [Nom du challenge lié au domaine]
Objectif : [objectif spécifique de la semaine]
Description : [description du challenge]
- Lundi : [activité ou tâche - durée - niveau] | RECHERCHE: [SI une activité ou tâche physique est prévue, mots-clés YouTube précis pour cette activité si applicable. SI le jour est indiqué comme "Repos" ou sans tâche active, écris simplement "Aucune"]
- Mardi : [activité ou tâche - durée - niveau] | RECHERCHE: [SI une activité ou tâche physique est prévue, mots-clés YouTube précis pour cette activité si applicable. SI le jour est indiqué comme "Repos" ou sans tâche active, écris simplement "Aucune"]
- Mercredi : [activité ou tâche - durée - niveau] | RECHERCHE: [mots-clés YouTube pour cette activité si applicable et si il existe une activité ou tâche ce jour]
- Jeudi : [activité ou tâche - durée - niveau] | RECHERCHE: [mots-clés YouTube pour cette activité si applicable]
- Vendredi : [activité ou tâche - durée - niveau] | RECHERCHE: [mots-clés YouTube pour cette activité si applicable]
- Samedi : [activité ou tâche - durée - niveau] | RECHERCHE: [mots-clés YouTube pour cette activité si applicable]
- Dimanche : [repos, révision ou tâche légère] | RECHERCHE: [mots-clés YouTube pour cette activité si applicable]

CHALLENGE SEMAINE 2 : [Nom du challenge]
[même structure]

CHALLENGE SEMAINE 3 : [Nom du challenge]
[même structure]

CHALLENGE SEMAINE 4 : [Nom du challenge]
[même structure]

CONSEILS PERSONNALISÉS
[3-5 conseils adaptés aux contraintes et au domaine de l'objectif]

MESSAGE DE MOTIVATION
[Message final encourageant adapté au domaine]

Réponds en français.
Adapte TOUT le contenu au domaine spécifique de l'objectif.
Tiens compte des contraintes mentionnées pour adapter les tâches.

IMPORTANT SÉCURITÉ : Si l'objectif ou les contraintes contiennent des insultes, des demandes à caractère sexuel, déplacées, illégales ou haineuses, ne génère PAS la structure demandée. Réponds UNIQUEMENT et strictement par cette phrase exacte : "REFUS_CONTENU_INAPPROPRIE".
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
                        'muscle', 'souple', 'stretching', 'gym',
                        'natation', 'vélo', 'danse', 'pilates', 'crossfit',
                        'pompe', 'abdos', 'squat', 'saut', 'sprint']
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
    status_payment = request.GET.get('status')
    plan_texte = request.session.get('plan_complet')
    objectif = request.session.get('plan_objectif', 'Mon objectif')

    paiement_valide = (status_payment in ['approved', 'successful']) or (plan_texte is not None)

    if not paiement_valide:
        return HttpResponse('Validation du paiement échouée.', status=403)

    if not plan_texte:
        plan_texte = "Votre plan est en cours de rechargement. Contactez le support si ce message persiste."

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#3aaa5c'),
        spaceAfter=6,
    )

    style_titre_black = ParagraphStyle(
        'Titre',
        parent=styles['Title'],
        fontSize=14,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
    )

    style_sous_titre = ParagraphStyle(
        'SousTitre',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#555555'),
        spaceAfter=20,
        italic=True,
    )
    style_h2 = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1a1a1a'),
        spaceBefore=15,
        spaceAfter=8,
    )
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=18,
        spaceAfter=6,
    )

    style_objectif = ParagraphStyle(
    'Objectif',
    parent=styles['Title'],
    fontSize=16,
    textColor=colors.HexColor('#1a1a1a'),
    alignment=1,  # centré
    fontName='Helvetica-Bold',
    spaceBefore=10,
    spaceAfter=20,
)
    style_exercice = ParagraphStyle(
    'Exercice',
    parent=styles['Normal'],
    fontSize=11,
    leading=18,
    spaceAfter=4,
)

    contenu = []

    # ── En-tête avec logo ─────────────────────
    logo_path = os.path.join(BASE_DIR, 'static', 'images', 'logo.png')

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3*cm, height=3*cm)
        logo.hAlign = 'LEFT'

        titre_pdf = Paragraph("1 Kilo en Moins", style_titre)
        sous_titre = Paragraph(f"Ton coach fitness personnel", style_titre_black)

        # Tableau pour aligner logo à gauche et titre à droite
        header_data = [[logo, [titre_pdf, sous_titre]]]
        header_table = Table(header_data, colWidths=[3.5*cm, 13*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        contenu.append(header_table)
    else:
        # Si le logo n'est pas trouvé, affiche juste le titre
        contenu.append(Paragraph("1 Kilo en Moins", style_titre))
        contenu.append(Paragraph(f"Mon Plan Personnalisé — {objectif}", style_sous_titre))

    # Ligne de séparation verte
    from reportlab.platypus import HRFlowable
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(HRFlowable(
        width="100%",
        thickness=2,
        color=colors.HexColor('#3aaa5c'),
        spaceAfter=0.5*cm
    ))
    
    contenu.append(Paragraph(objectif, style_objectif))
    # ── Contenu du plan ───────────────────────

    #### PLAN MOT CLE YOUTUBE###
    # for ligne in plan_texte.split('\n'):
    #     ligne = ligne.strip()
    #     if not ligne:
    #         contenu.append(Spacer(1, 0.3*cm))
    #     elif any(ligne.startswith(x) for x in ['CHALLENGE', 'INTRODUCTION', 'CONSEILS', 'MESSAGE', 'OBJECTIF']) or ligne.isupper():
    #         contenu.append(Paragraph(ligne, style_h2))
    #     elif '| RECHERCHE:' in ligne:
    #         # Sépare l'activité des mots-clés de recherche
    #         parties = ligne.split('| RECHERCHE:')
    #         activite = parties[0].strip()
    #         mots_cles = parties[1].strip() if len(parties) > 1 else ''

    #         # Construit le lien YouTube Search
            
    #         mots_cles_encoded = urllib.parse.quote(mots_cles)
    #         lien_youtube = f"https://www.youtube.com/results?search_query={mots_cles_encoded}"

    #         # Texte avec lien cliquable
    #         texte_html = f'{activite} &nbsp;<a href="{lien_youtube}" color="#FF0000"><b>🎥 Voir sur YouTube</b></a>'
    #         contenu.append(Paragraph(texte_html, style_exercice))
    #     else:
    #         contenu.append(Paragraph(ligne, style_normal))


    # #### PLAN RECHERCHE VIDEO YOUTUBE###
    # for ligne in plan_texte.split('\n'):
    #     ligne = ligne.strip()
    #     if not ligne:
    #         contenu.append(Spacer(1, 0.3*cm))
    #     elif any(ligne.startswith(x) for x in ['CHALLENGE', 'INTRODUCTION', 'CONSEILS', 'MESSAGE', 'OBJECTIF']) or ligne.isupper():
    #         contenu.append(Paragraph(ligne, style_h2))
    #     elif '| RECHERCHE:' in ligne:
    #         # Sépare l'activité des mots-clés de recherche
    #         parties = ligne.split('| RECHERCHE:')
    #         activite = parties[0].strip()
    #         mots_cles = parties[1].strip() if len(parties) > 1 else ''

    #         # Construit le lien YouTube Search
            
    #         mots_cles_encoded = urllib.parse.quote(mots_cles)
    #         lien_youtube = f"https://www.youtube.com/results?search_query={mots_cles_encoded}"

    #         # Texte avec lien cliquable
    #         texte_html = f'{activite} &nbsp;<a href="{lien_youtube}" color="#FF0000"><b>🎥 Voir sur YouTube</b></a>'
    #         contenu.append(Paragraph(texte_html, style_exercice))
    #     else:
    #         contenu.append(Paragraph(ligne, style_normal))
            
    
    #### PLAN RECHERCHE VIDEO YOUTUBE###
    # Variable témoin pour savoir si on vient de passer l'introduction
    sous_introduction = False

    for ligne in plan_texte.split('\n'):
        ligne = ligne.strip()
        if not ligne:
            contenu.append(Spacer(1, 0.3*cm))
            continue  # On passe à la ligne suivante
            
        elif any(ligne.startswith(x) for x in ['CHALLENGE', 'INTRODUCTION', 'CONSEILS', 'MESSAGE', 'OBJECTIF']) or ligne.isupper():
            contenu.append(Paragraph(ligne, style_h2))
            # Si la section qui commence est l'Introduction, on active notre témoin
            if 'INTRODUCTION' in ligne:
                sous_introduction = True
            else:
                sous_introduction = False
                
        elif '| RECHERCHE:' in ligne:
            sous_introduction = False  # Sécurité
            # Sépare l'activité des mots-clés de recherche
            parties = ligne.split('| RECHERCHE:')
            activite = parties[0].strip()
            mots_cles = parties[1].strip() if len(parties) > 1 else ''

            if not mots_cles or "aucune" in mots_cles.lower():
                contenu.append(Paragraph(activite, style_exercice))
            else:
                mots_cles_encoded = urllib.parse.quote(mots_cles)
                lien_youtube = f"https://www.youtube.com/results?search_query={mots_cles_encoded}"
                texte_html = f'{activite} &nbsp;<a href="{lien_youtube}" color="#FF0000"><b>🎥 Voir sur YouTube</b></a>'
                contenu.append(Paragraph(texte_html, style_exercice))
                
        else:
            # C'est un paragraphe de texte normal
            contenu.append(Paragraph(ligne, style_normal))
            
            # ==========================================
            # INJECTION DU NB JUSTE APRÈS L'INTRODUCTION
            # ==========================================
            if sous_introduction:
                contenu.append(Spacer(1, 0.2*cm))
                
                # Définition d'un style discret pour le NB (en italique et gris foncé)
                style_nb = ParagraphStyle(
                    'NotaBene', 
                    parent=style_normal, 
                    fontSize=9.5, 
                    leading=14, 
                    textColor=colors.HexColor('#555555')
                )
                
                texte_nb = (
                    "<b>NB :</b> <i>Les liens YouTube sont générés automatiquement sur la base de mots-clés. "
                    "Si certaines vidéos suggérées ne cadrent pas parfaitement avec l'activité précisée, "
                    "n'hésitez pas à modifier vous-même les termes de votre recherche sur YouTube pour l'adapter "
                    "exactement à l'exercice que vous devez effectuer.</i>"
                )
                contenu.append(Paragraph(texte_nb, style_nb))
                contenu.append(Spacer(1, 0.2*cm))
                
                # On désactive le témoin pour ne pas répéter le NB sur les paragraphes suivants
                sous_introduction = False

    doc.build(contenu)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="mon_plan_1kilo.pdf"'
    return response