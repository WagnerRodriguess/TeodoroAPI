import logging
from django.conf import settings

# from rest_framework.exceptions import AuthenticationFailed
# from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that reads the access token from (HTTP-only in production) cookies
    instead of the Authorization header.
    """

    def authenticate(self, request):
        """
        Authenticate the request using JWT token from cookies.
        Returns a tuple of (user, validated_token) if successful, None otherwise.
        """
        jwt_settings = getattr(settings, "SIMPLE_JWT", {})
        cookie_name = jwt_settings.get("AUTH_COOKIE_NAME", "access_token")

        raw_token = request.COOKIES.get(cookie_name)

        if not raw_token:
            return super().authenticate(request)  # try Authorization header as fallback

        if not isinstance(raw_token, str) or not raw_token.strip():
            logger.warning("Invalid token format in cookie")
            return None

        token_parts = raw_token.split(".")
        if len(token_parts) != 3:
            logger.warning("Invalid JWT token structure in cookie")
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None
