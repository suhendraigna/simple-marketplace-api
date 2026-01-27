from django.db import models
from core.models import TimeStampedModel
from customers.models import Customer
from products.models import Product

class Cart(TimeStampedModel):
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"

    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (CHECKED_OUT, "Checked out"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )

    def __str__(self):
        return f"Cart {self.id} - {self.customer.email}"
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("cart", "product")