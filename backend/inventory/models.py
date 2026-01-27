from django.db import models
from products.models import Product

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity_available = models.PositiveIntegerField()

    def __str__(self):
        f"{self.product.name} - {self.quantity_available}"