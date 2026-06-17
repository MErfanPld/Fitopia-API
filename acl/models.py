from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100)


class UserRole(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)