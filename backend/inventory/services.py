from django.db import transaction
from inventory.models import Inventory

class InventoryService:
    def check_availability(product, qty):
        inventory = Inventory.objects.select_for_update().get(product=product)
        if inventory.quantity_available < qty:
            raise ValueError("Insufficient stock")
        
    def reduce(product, qty):
        inventory = Inventory.objects.select_for_update().get(product=product)
        if inventory.quantity_available < qty:
            raise ValueError("Insufficient stock")
        inventory.quantity_available -= qty
        inventory.save()
    
    def restore(product, qty):
        inventory = Inventory.objects.select_for_update().get(product=product)
        inventory.quantity_available += qty
        inventory.save()