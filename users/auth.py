from django.contrib.auth.models import User
from users.models import BusinessUser


class BusinessUserBackend(object):
    def authenticate(self, username=None, password=None):
        try:
            user = BusinessUser.objects.get(phone=username)
        except BusinessUser.DoesNotExist:
            pass
        else:
            if user.check_password(password):
                return user
        return None

    def get_user(self, user_id):
        try:
            return BusinessUser.objects.get(pk=user_id)
        except BusinessUser.DoesNotExist:
            return None