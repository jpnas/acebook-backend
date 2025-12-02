from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Club, Coach, Court, Reservation

User = get_user_model()


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ("id", "name", "slug")


class UserSerializer(serializers.ModelSerializer):
    club = ClubSerializer(read_only=True, allow_null=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "first_name", "last_name", "username", "email", "role", "club")
        read_only_fields = ("id", "username", "role", "club")

    def get_name(self, obj):
        full_name = obj.get_full_name()
        return full_name or obj.username

    def update(self, instance, validated_data):
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        email = validated_data.pop("email", None)

        if first_name is not None:
            instance.first_name = first_name
        if last_name is not None:
            instance.last_name = last_name
        if email is not None:
            email = email.strip().lower()
            if User.objects.filter(email__iexact=email).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({"email": "Email já cadastrado."})
            instance.email = email
            instance.username = email

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = (
            "id",
            "name",
            "surface",
            "covered",
            "lights",
            "status",
            "opens_at",
            "closes_at",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        club = self.context["request"].user.club
        name = attrs.get("name", "")
        if club and Court.objects.filter(club=club, name=name).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError({"name": "Já existe uma quadra com esse nome no clube."})
        return attrs


class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = ("id", "name", "phone")
        read_only_fields = ("id",)

    def validate_name(self, value):
        club = self.context["request"].user.club
        if club and Coach.objects.filter(club=club, name__iexact=value).exclude(
            id=self.instance.id if self.instance else None
        ).exists():
            raise serializers.ValidationError("Já existe um coach com esse nome no clube.")
        return value


class ReservationSerializer(serializers.ModelSerializer):
    player = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    player_name = serializers.SerializerMethodField()
    court_name = serializers.CharField(source="court.name", read_only=True)

    class Meta:
        model = Reservation
        fields = (
            "id",
            "court",
            "court_name",
            "player",
            "player_name",
            "start_time",
            "end_time",
            "status",
            "type",
        )
        read_only_fields = ("id", "status")

    def validate(self, attrs):
        start = attrs.get("start_time")
        end = attrs.get("end_time")
        court = attrs.get("court")
        request_user = self.context["request"].user
        player = attrs.get("player") or request_user
        current_tz = timezone.get_current_timezone()

        if start and timezone.is_naive(start):
            start = timezone.make_aware(start, current_tz)
        if end and timezone.is_naive(end):
            end = timezone.make_aware(end, current_tz)

        if not start or not end:
            raise serializers.ValidationError("Informe início e fim da reserva.")
        if end <= start:
            raise serializers.ValidationError("Horário final deve ser maior que o inicial.")
        if start < timezone.now():
            raise serializers.ValidationError("Não é possível criar reservas retroativas.")
        local_start_date = start.astimezone(current_tz).date()
        if request_user.role == User.Roles.PLAYER and local_start_date != timezone.localdate():
            raise serializers.ValidationError("Jogadores só podem criar reservas para o dia atual.")
        if not court:
            raise serializers.ValidationError({"court": "Selecione uma quadra."})
        if player.club_id != court.club_id:
            raise serializers.ValidationError("Quadra e jogador precisam pertencer ao mesmo clube.")
        if court.status == Court.Status.MAINTENANCE:
            raise serializers.ValidationError({"court": "Quadra em manutenção. Escolha outra quadra."})

        qs = Reservation.objects.filter(court=court, start_time__lt=end, end_time__gt=start)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Já existe uma reserva para essa quadra nesse horário.")

        daily_reservations = Reservation.objects.filter(
            player=player,
            start_time__date=local_start_date,
        )
        if self.instance:
            daily_reservations = daily_reservations.exclude(id=self.instance.id)
        if daily_reservations.exists():
            raise serializers.ValidationError("Cada jogador pode ter no máximo uma reserva por dia.")

        attrs["player"] = player
        attrs["start_time"] = start
        attrs["end_time"] = end
        return attrs

    def get_player_name(self, obj):
        full_name = obj.player.get_full_name()
        return full_name or obj.player.username or obj.player.email
