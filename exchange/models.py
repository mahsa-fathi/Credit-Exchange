from django.db import models
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class SellerManager(BaseUserManager):
    def create_user(self, username, password=None, credit=0, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, credit=credit, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, credit=0, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, credit, **extra_fields)


class Seller(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    credit = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = SellerManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.username}: {self.credit}"


class Transaction(models.Model):
    class Type(models.TextChoices):
        CHARGE = "CH", _("Charge")
        SELL = "SE", _("Sell")

    user = models.ForeignKey(Seller, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=Type.choices)
    datetime = models.DateTimeField(default=timezone.now)
    receiver = models.CharField(max_length=14, null=True, blank=True)
    amount = models.IntegerField()

    def __str__(self):
        return f"Transaction {self.pk}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.type == self.Type.SELL:
                self.user.credit -= self.amount
            else:
                self.user.credit += self.amount
            self.user.save()
            super().save(*args, **kwargs)
