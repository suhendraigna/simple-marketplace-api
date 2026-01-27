from django.db import transaction
from orders.models import Order, OrderItem
from inventory.services import InventoryService

class OrderService:
    def checkout(cart):
        # 1. validate cart
        if cart.status != cart.ACTIVE:
            raise ValueError("Cart is not active")
        
        cart_items = cart.items.select_related("products")

        if not cart_items.exists():
            raise ValueError("Cart is empty")

        # 2. validate stock
        for item in cart_items:
            InventoryService.check_availability(
                product=item.product,
                qty=item.quantity
            )

        # 3. count total
        total_amount = 0
        for item in cart_items:
            total_amount += item.product.price * item.quantity

        # 4. create order
        order = Order.objects.create(
            customer=cart.customer,
            status=Order.PENDING,
            total_amount=total_amount
        )

        # 5. create order items (snapshot)
        order_items = []
        for item in cart_items:
            order_items.append(
                OrderItem(
                    order=order,
                    product_name=item.product.name,
                    product_price=item.product.price,
                    quantity=item.quantity
                )
            )
        OrderItem.objects.bulk_create(order_items)

        # 6. reduce stock
        for item in cart_items:
            InventoryService.reduce(
                product=item.product,
                qty=item.quantity
            )

        # 7. update cart status
        cart.status = cart.CHECKED_OUT
        cart.save()
        
        return order