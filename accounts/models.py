from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """유저의 최근 로그인 세션을 저장하기 위한 프로필 모델"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    last_session_key = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return self.user.username


# 유저 생성 시 자동으로 프로필도 생성되게 하는 신호(Signal)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
