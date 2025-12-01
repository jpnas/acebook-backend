from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.text import slugify
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Club, Coach, Court, Reservation
from .permissions import IsClubAdmin, IsClubStaffOrReadOnly, IsOwnerOrClubAdmin
from .serializers import CoachSerializer, CourtSerializer, ReservationSerializer, UserSerializer

User = get_user_model()
password_reset_token = PasswordResetTokenGenerator()


class ClubTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(write_only=True, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username_field = self.fields[self.username_field]
        username_field.required = False
        username_field.allow_blank = True

    def validate(self, attrs):
        identifier = (attrs.get("email") or attrs.get(self.username_field) or "").strip()
        if not identifier:
            raise serializers.ValidationError({"email": "Informe o email cadastrado."})

        try:
            user = User.objects.get(email__iexact=identifier)
            attrs[self.username_field] = user.username
        except User.DoesNotExist:
            attrs[self.username_field] = identifier

        attrs.pop("email", None)

        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class ClubTokenObtainPairView(TokenObtainPairView):
    serializer_class = ClubTokenObtainPairSerializer


class ClubSlugAvailabilityView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raw_slug = (request.query_params.get("slug") or "").strip()
        normalized_slug = slugify(raw_slug)
        is_valid = bool(normalized_slug)
        available = is_valid and not Club.objects.filter(slug=normalized_slug).exists()
        return Response({"slug": normalized_slug, "valid": is_valid, "available": available})


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")
        username = email
        desired_role_raw = (data.get("role") or User.Roles.PLAYER).lower()
        allowed_roles = {User.Roles.ADMIN, User.Roles.PLAYER}
        desired_role = desired_role_raw if desired_role_raw in allowed_roles else User.Roles.PLAYER
        full_name = (data.get("name") or "").strip()

        if not email or not password:
            return Response({"detail": "Informe email e senha."}, status=status.HTTP_400_BAD_REQUEST)

        if not username:
            base_username = email.split("@")[0]
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{suffix}"
                suffix += 1

        if User.objects.filter(email__iexact=email).exists():
            return Response({"detail": "Email já cadastrado."}, status=status.HTTP_400_BAD_REQUEST)

        if desired_role == User.Roles.ADMIN:
            club_name = (data.get("club_name") or "").strip()
            if not club_name:
                return Response({"detail": "Informe o nome do clube."}, status=status.HTTP_400_BAD_REQUEST)
            requested_slug = slugify(data.get("club_slug") or "")
            if not requested_slug:
                return Response({"detail": "Informe um código do clube."}, status=status.HTTP_400_BAD_REQUEST)
            if Club.objects.filter(slug=requested_slug).exists():
                return Response({"detail": "Código de clube indisponível."}, status=status.HTTP_400_BAD_REQUEST)
            club = Club.objects.create(slug=requested_slug, name=club_name)
            role = User.Roles.ADMIN
        else:
            club_slug = slugify(data.get("club_slug") or "")
            if not club_slug:
                return Response({"detail": "Informe o código do clube."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                club = Club.objects.get(slug=club_slug)
            except Club.DoesNotExist:
                return Response({"detail": "Clube não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            role = User.Roles.PLAYER

        user = User(username=username, email=email, role=role, club=club)
        if role == User.Roles.ADMIN:
            user.is_staff = True
        if role != User.Roles.ADMIN and full_name:
            parts = full_name.split()
            user.first_name = parts[0]
            user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        user.set_password(password)
        user.save()

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response({"detail": "Informe o email cadastrado."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({"detail": "Se o email existir, enviaremos as instruções em instantes."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        reset_link = f"{settings.FRONTEND_RESET_URL}?uid={uid}&token={token}"
        send_mail(
            subject="Redefinição de senha - AceBook",
            message=(
                "Recebemos sua solicitação de redefinição de senha.\n\n"
                f"Use o link seguro: {reset_link}\n\n"
                f"Ou insira UID: {uid}\nToken: {token}\n\n"
                "Se não foi você, ignore esta mensagem."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response({"detail": "Se o email existir, enviamos as instruções em instantes."})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("password")

        if not uid or not token or not password:
            return Response({"detail": "Preencha uid, token e nova senha."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if not password_reset_token.check_token(user, token):
            return Response({"detail": "Token expirado ou inválido."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response({"detail": "Senha atualizada com sucesso."})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class CourtViewSet(viewsets.ModelViewSet):
    serializer_class = CourtSerializer
    permission_classes = [IsClubStaffOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        return Court.objects.filter(club=self.request.user.club)

    def perform_create(self, serializer):
        serializer.save(club=self.request.user.club)

    def perform_update(self, serializer):
        serializer.save(club=self.request.user.club)


class CoachViewSet(viewsets.ModelViewSet):
    serializer_class = CoachSerializer
    permission_classes = [IsClubStaffOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        return Coach.objects.filter(club=self.request.user.club)

    def perform_create(self, serializer):
        serializer.save(club=self.request.user.club)

    def perform_update(self, serializer):
        serializer.save(club=self.request.user.club)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrClubAdmin]
    pagination_class = None

    def get_queryset(self):
        queryset = Reservation.objects.filter(club=self.request.user.club)
        if self.request.user.role != "admin":
            queryset = queryset.filter(player=self.request.user)
        return queryset.select_related("court", "player")

    def perform_create(self, serializer):
        serializer.save(
            club=self.request.user.club,
            player=serializer.validated_data.get("player"),
        )

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=["get"])
    def availability(self, request):
        court_id = request.query_params.get("court")
        date = request.query_params.get("date")
        if not court_id or not date:
            return Response({"detail": "Informe court e date no formato YYYY-MM-DD."}, status=400)

        start = timezone.datetime.fromisoformat(f"{date}T00:00:00+00:00")
        end = timezone.datetime.fromisoformat(f"{date}T23:59:59+00:00")
        reservations = Reservation.objects.filter(
            club=request.user.club,
            court_id=court_id,
            start_time__range=(start, end),
        )
        occupied = []
        for res in reservations:
            kickoff = res.start_time
            if timezone.is_naive(kickoff):
                kickoff = timezone.make_aware(kickoff, timezone.get_current_timezone())
            occupied.append(timezone.localtime(kickoff).strftime("%H:%M"))
        return Response({"occupied": occupied})


class ClubUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsClubAdmin]
    pagination_class = None
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = User.objects.filter(club=self.request.user.club)
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)
        return queryset.order_by("username")

    def perform_destroy(self, instance):
        if instance == self.request.user:
            raise serializers.ValidationError({"detail": "Você não pode remover seu próprio usuário."})
        instance.delete()
