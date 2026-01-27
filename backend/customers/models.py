from django.db import models
from core.models import TimeStampedModel

class Customer(TimeStampedModel):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email