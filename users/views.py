"""Auth and user-profile endpoints."""
import logging

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from audit import services as audit_svc
from audit.models import AuditEventType
from core.exceptions import AuthenticationError, NotFoundError, ValidationError
from core.renderers import NyayaRenderer
from core.throttles import AuthThrottle
from .models import User
from .serializers import (
    RegistrationSerializer, LoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, UserUpdateSerializer,
)

logger = logging.getLogger("nyayapath.users")


def _tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = RegistrationSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        user = ser.save()
        audit_svc.record(AuditEventType.USER_REGISTERED, request=request, user=user,
                         description=f"New registration: {user.email}")
        return Response({"user": UserProfileSerializer(user).data, "tokens": _tokens(user)},
                        status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        user = authenticate(email=ser.validated_data["email"], password=ser.validated_data["password"])
        if not user or not user.is_active:
            raise AuthenticationError("Invalid credentials or inactive account.")
        audit_svc.record(AuditEventType.USER_LOGIN, request=request, user=user, description="Login")
        return Response({"user": UserProfileSerializer(user).data, "tokens": _tokens(user)})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get("refresh", ""))
            token.blacklist()
        except Exception:
            pass
        audit_svc.record(AuditEventType.USER_LOGOUT, request=request, description="Logout")
        return Response({"detail": "Logged out."})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        ser = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        ser.save()
        return Response(UserProfileSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data, context={"request": request})
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        request.user.set_password(ser.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        audit_svc.record(AuditEventType.USER_PASSWORD_CHANGE, request=request, description="Password changed")
        return Response({"detail": "Password updated."})


class PasswordResetRequestView(APIView):
    """POST {email}: always answers the same way (no account enumeration). Sends a reset link to FRONTEND_PASSWORD_RESET_URL."""
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]

    def post(self, request):
        from django.conf import settings
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        email = (request.data.get("email") or "").strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first() if email else None
        if user:
            link = settings.FRONTEND_PASSWORD_RESET_URL.format(uid=urlsafe_base64_encode(force_bytes(user.pk)),
                                                               token=default_token_generator.make_token(user))
            send_mail("NyayaPath password reset", f"Use this link to reset your password:\n{link}", settings.DEFAULT_FROM_EMAIL, [user.email])
        return Response({"message": "If an account exists for this email, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]

    def post(self, request):
        from django.contrib.auth.password_validation import validate_password
        from django.contrib.auth.tokens import default_token_generator
        from django.core.exceptions import ValidationError as DjangoVE
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(request.data.get("uid", ""))))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise ValidationError("Invalid or expired reset link.", code="INVALID_RESET_TOKEN")
        if not default_token_generator.check_token(user, request.data.get("token", "")):
            raise ValidationError("Invalid or expired reset link.", code="INVALID_RESET_TOKEN")
        try:
            validate_password(request.data.get("new_password", ""), user)
        except DjangoVE as e:
            raise ValidationError(" ".join(e.messages))
        user.set_password(request.data["new_password"]); user.save()
        audit_svc.record(AuditEventType.PASSWORD_RESET, request=request, user=user, description="Password reset")
        return Response({"message": "Password updated."})
