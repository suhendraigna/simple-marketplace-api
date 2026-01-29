from inventory.models import Inventory
from core.exceptions import InsufficientStockError
from products.models import Product

class InventoryService:
    def check_availability(product, qty):
        inventory = Inventory.objects.select_for_update().get(product=product)
        if inventory.quantity_available < qty:
            raise InsufficientStockError(product.name)
        
    def reduce(product, qty):
        inventory = Inventory.objects.select_for_update().get(product=product)
        if inventory.quantity_available < qty:
            raise InsufficientStockError(product.name)
        inventory.quantity_available -= qty
        inventory.save()
    
    def restore(product_sku, qty):
        product = Product.objects.get(sku=product_sku)
        inventory = Inventory.objects.select_for_update().get(product=product)
        inventory.quantity_available += qty
        inventory.save()