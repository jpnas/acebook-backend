from django.contrib import admin

from .models import Club, ClubUser, Coach, Court, Reservation


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(ClubUser)
class ClubUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "club")
    list_filter = ("role", "club")
    search_fields = ("username", "email")


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "surface", "status", "opens_at", "closes_at")
    list_filter = ("club", "surface", "status")
    search_fields = ("name",)


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "phone")
    list_filter = ("club",)
    search_fields = ("name", "phone")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("court", "player", "start_time", "end_time", "status")
    list_filter = ("status", "type", "club")
    search_fields = ("court__name", "player__username")
