from django.contrib.auth.models import AbstractUser
from django.db import models


class Club(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class ClubUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Administrador"
        PLAYER = "player", "Atleta"

    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.PLAYER)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="users", null=True, blank=True)

    @property
    def club_name(self) -> str:
        return self.club.name if self.club else ""


class Coach(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="coaches")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Court(models.Model):
    class Surface(models.TextChoices):
        SAIBRO = "saibro", "Saibro"
        RAPIDA = "rápida", "Rápida"

    class Status(models.TextChoices):
        AVAILABLE = "disponível", "Disponível"
        MAINTENANCE = "manutenção", "Em manutenção"

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="courts")
    name = models.CharField(max_length=120)
    surface = models.CharField(max_length=20, choices=Surface.choices)
    covered = models.BooleanField(default=False)
    lights = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    opens_at = models.TimeField(default="06:00")
    closes_at = models.TimeField(default="22:00")

    class Meta:
        unique_together = ("club", "name")

    def __str__(self) -> str:
        return self.name


class Reservation(models.Model):
    class Status(models.TextChoices):
        APPROVED = "aprovada", "Aprovada"
        CANCELED = "cancelada", "Cancelada"

    class Type(models.TextChoices):
        TRAINING = "treino", "Treino"
        RECREATIONAL = "recreativo", "Recreativo"
        TOURNAMENT = "torneio", "Torneio"
        PERFORMANCE = "performance", "Performance"

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="reservations")
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="reservations")
    player = models.ForeignKey(ClubUser, on_delete=models.CASCADE, related_name="reservations")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPROVED)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.TRAINING)

    class Meta:
        ordering = ("-start_time",)
        constraints = [
            models.CheckConstraint(check=models.Q(end_time__gt=models.F("start_time")), name="reservation_end_gt_start"),
        ]

    def __str__(self) -> str:
        return f"{self.court.name} - {self.start_time:%d/%m %H:%M}"
