from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nickname = models.CharField('昵称', max_length=64, blank=True)

    def __str__(self):
        return self.nickname or self.username
