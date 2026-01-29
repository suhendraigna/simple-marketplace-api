class DomainError(Exception):
    """Base class for domain-level errors"""
    pass

class CartNotActiveError(DomainError):
    pass

class EmptyCartError(DomainError):
    pass

class InsufficientStockError(DomainError):
    def __init__(self, product_name):
        self.product_name = product_name
        super().__init__(f"Insufficient stock for product: {product_name}")