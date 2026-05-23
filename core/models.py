from django.db import models

# ── Catégories de vidéos ──────────────────────────────────────────
class Categorie(models.Model):
    NOM_CHOICES = [
        ('fitness', 'Fitness'),
        ('dance', 'Dance'),
    ]
    nom = models.CharField(max_length=20, choices=NOM_CHOICES, unique=True)

    def __str__(self):
        return self.nom.capitalize()


# ── Vidéos TikTok ─────────────────────────────────────────────────
class Video(models.Model):
    titre = models.CharField(max_length=200)
    tiktok_url = models.URLField(help_text="URL de la vidéo TikTok")
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    ordre = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return self.titre


# ── Réussites ─────────────────────────────────────────────────────
# ── Médias d'une réussite (photos ou vidéos TikTok) ───────────────
class ReussiteMedia(models.Model):
    TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('tiktok', 'Vidéo TikTok'),
    ]
    reussite = models.ForeignKey(
        'Reussite',
        on_delete=models.CASCADE,
        related_name='medias'
    )
    type_media = models.CharField(max_length=10, choices=TYPE_CHOICES)
    photo = models.ImageField(
        upload_to='reussites/',
        blank=True, null=True
    )
    tiktok_url = models.URLField(
        blank=True, null=True,
        help_text="URL TikTok si type = vidéo"
    )
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"{self.type_media} — {self.reussite.titre}"


# ── Réussites ─────────────────────────────────────────────────────
class Reussite(models.Model):
    TYPE_CHOICES = [
        ('moi', 'Ma réussite'),
        ('visiteur', 'Réussite visiteur'),
    ]

    # Infos générales
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='moi')
    nom = models.CharField(max_length=100, help_text="Ton nom ou celui du visiteur")
    titre = models.CharField(max_length=200, help_text="Ex: J'ai perdu 2kg !")
    description = models.TextField(blank=True)
    date_reussite = models.DateField()

    # Pour les réussites visiteurs uniquement
    lien_post = models.URLField(
        blank=True, null=True,
        help_text="Lien vers leur post (Instagram, Facebook, LinkedIn...)"
    )
    reseau_social = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('instagram', 'Instagram'),
            ('facebook', 'Facebook'),
            ('linkedin', 'LinkedIn'),
            ('tiktok', 'TikTok'),
            ('autre', 'Autre'),
        ]
    )

    # Gestion
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_reussite']

    def __str__(self):
        return f"{self.nom} — {self.titre}"
    
    # ── Défis de la semaine ───────────────────────────────────────────
class Defi(models.Model):
    texte = models.CharField(max_length=200)
    accompli = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return self.texte