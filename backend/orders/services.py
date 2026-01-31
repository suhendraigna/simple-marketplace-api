from django.db import transaction
from orders.models import Order, OrderItem
from orders.state_machine import OrderStateMachine
from inventory.services import InventoryService
from core.exceptions import (
    DomainError,
    CartNotActiveError,
    EmptyCartError,
)
import re

class OrderService:

    @staticmethod
    def checkout(cart):
        with transaction.atomic():
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
    
    @staticmethod
    def mark_as_paid(order_id):
        with transaction.atomic():
            order = (
                Order.objects.select_for_update().get(id=order_id)
            )

            if order.status == Order.PAID:
                return order 
        
            new_status = OrderStateMachine.next_state(
                order.status,
                "pay"
            )

            order.status = new_status
            order.save()
            return order
        
    @staticmethod
    def complete(order_id):
        with transaction.atomic():
            order = (
                Order.objects.select_for_update().get(id=order_id)
            )

            if order.status == Order.COMPLETED:
                return order

            new_status = OrderStateMachine.next_state(
                order.status, "complete"
            )

            order.status = new_status
            order.save()
            return order
        
    @staticmethod
    def cancel(order_id):
        with transaction.atomic():
            order = (
                Order.objects.select_for_update().get(id=order_id)
            )
            
            if order.status == Order.CANCELED:
                return order

            new_status = OrderStateMachine.next_state(
                order.status, "cancel"
            )
            
            order.status = new_status
            order.save()
            return order