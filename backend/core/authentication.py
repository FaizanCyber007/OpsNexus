from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model

class DummyAdminAuthentication(BaseAuthentication):
    """
    A dummy authentication class for development/demo purposes.
    Automatically authenticates all API requests as a superuser.
    """
    def authenticate(self, request):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username="demo_admin",
            defaults={"is_superuser": True, "is_staff": True}
        )
        return (user, None)
