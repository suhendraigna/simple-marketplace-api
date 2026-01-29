from django.test import TestCase
from decimal import Decimal

from customers.models import Customer
from products.models import Category, Product
from cart.models import Cart, CartItem
from inventory.models import Inventory
from orders.services import OrderService
from orders.models import Order
from core.exceptions import(
    DomainError,
    EmptyCartError,
    InsufficientStockError
)

class OrderServiceCheckoutTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            email="hen@test.com",
            name="Hen"
        )

        self.category = Category.objects.create(
            name="Sepatu",
            slug="sepatu"
        )

        self.product = Product.objects.create(
            name="Sepatu Lari X",
            sku="SKU-001",
            price=Decimal("500000"),
            category=self.category
        )

        Inventory.objects.create(
            product=self.product,
            quantity_available=10
        )

        self.cart = Cart.objects.create(
            customer=self.customer
        )

        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

    def test_checkout_success(self):
        order = OrderService.checkout(self.cart)

        #order created
        self.assertIsInstance(order, Order)
        self.assertEqual(order.total_amount, Decimal("1000000"))
        self.assertEqual(order.status, Order.PENDING)

        #order item snapshot
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product_name.strip(), "Sepatu Lari X")
        self.assertEqual(item.product_price, Decimal("500000"))
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.product_sku, self.product.sku)

        #update cart
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, Cart.CHECKED_OUT)

        #reduce stok
        inventory = Inventory.objects.get(product=self.product)
        self.assertEqual(inventory.quantity_available, 8)

    
    def test_checkout_empty_cart_raises_error(self):
        empty_cart = Cart.objects.create(customer=self.customer)

        with self.assertRaises(EmptyCartError):
            OrderService.checkout(empty_cart)

    
    def test_checkout_isufficient_stock_raises_error(self):
        inventory = Inventory.objects.get(product=self.product)
        inventory.quantity_available = 1
        inventory.save()

        with self.assertRaises(InsufficientStockError):
            OrderService.checkout(self.cart)

        self.assertEqual(Order.objects.count(), 0)

        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, Cart.ACTIVE)

    def test_mark_order_as_paid_success(self):
        order = OrderService.checkout(self.cart)

        paid_order = OrderService.mark_as_paid(order)

        self.assertEqual(paid_order.status, Order.PAID)

    def test_mark_order_as_paid_non_pending_raises_error(self):
        order = OrderService.checkout(self.cart)
        OrderService.mark_as_paid(order)

        with self.assertRaises(DomainError):
            OrderService.mark_as_paid(order)

    def test_complete_order_success(self):
        order = OrderService.checkout(self.cart)
        OrderService.mark_as_paid(order)

        completed_order = OrderService.complete(order)
        
        self.assertEqual(completed_order.status, Order.COMPLETED)

    def test_complete_non_paid_order_raises_error(self):
        order = OrderService.checkout(self.cart)

        with self.assertRaises(DomainError):
            OrderService.complete(order)

    def test_cancel_order_success(self):
        order = OrderService.checkout(self.cart)

        inventory_before = Inventory.objects.get(product=self.product).quantity_available

        canceled_order = OrderService.cancel(order)

        self.assertEqual(canceled_order.status, Order.CANCELLED)

        inventory_after = Inventory.objects.get(product=self.product).quantity_available
        self.assertEqual(
            inventory_after,
            inventory_before+2
        )

    def test_cancel_non_pending_order_raises_error(self):
        order = OrderService.checkout(self.cart)
        OrderService.cancel(order)

        with self.assertRaises(DomainError):
            OrderService.cancel(order)

    def test_cancel_order_after_product_name_changed(self):
        order = OrderService.checkout(self.cart)

        self.product.name = "Sepatu Lari X - New Name"
        self.product.save()

        inventory_before = Inventory.objects.get(product=self.product).quantity_available

        OrderService.cancel(order)

        inventory_after = Inventory.objects.get(product=self.product).quantity_available
        self.assertEqual(inventory_after, inventory_before + 2)