from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from orders.services import OrderService
from orders.serializers import OrderSerializer
from cart.models import Cart


class CheckoutAPIView(APIView):
    def post(self, request):
        """
        checkout active cart for current customer
        """
        customer = request.user.customer
        cart = Cart.objects.filter(
            customer=customer,
            status=Cart.ACTIVE
        ).first()

        if not cart:
            return Response(
                {"error": "Active cart not found"},
                status = status.HTTP_404_NOT_FOUND
            )
        
        order = OrderService.checkout(cart)
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)