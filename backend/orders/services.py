from django.db import transaction
from orders.models import Order, OrderItem
from inventory.services import InventoryService
from core.exceptions import (
    DomainError,
    CartNotActiveError,
    EmptyCartError,
)
import re

class OrderService:
    def checkout(cart):
        # 1. validate cart
        if cart.status != cart.ACTIVE:
            raise CartNotActiveError("Cart is not active")
        
        cart_items = cart.items.select_related("product")

        if not cart_items.exists():
            raise EmptyCartError("Cart is empty")

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
            clean_name = re.sub(r"\s+", " ", item.product.name).strip()

            order_items.append(
                OrderItem(
                    order=order,
                    product_name=clean_name,
                    product_sku=item.product.sku,
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
    
    def mark_as_paid(order: Order):
        if order.status == Order.PAID:
            return order
        
        if order.status == Order.COMPLETED:
            return order
        
        if order.status != Order.PENDING:
            raise DomainError("Order cannot be marked as paid")
        
        order.status = Order.PAID
        order.save()
        
        return order
    
    def complete(order: Order):
        if order.status != Order.PAID:
            raise DomainError("Only paid orders can be completed")
        
        order.status = Order.COMPLETED
        order.save()
        return order
    
    def cancel(order: Order):
        if order.status != order.PENDING:
            raise DomainError("Only pending orders can be canceled")
        
        for item in order.items.select_related():
            InventoryService.restore(
                product_sku = item.product_sku,
                qty=item.quantity
            )

        order.status = Order.CANCELLED
        order.save()

        return order