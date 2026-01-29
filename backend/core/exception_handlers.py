from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from core.exceptions import(
    DomainError,
    CartNotActiveError,
    EmptyCartError,
    InsufficientStockError,
)

def custom_exeption_handler(exc, context):
    """
    Global DRF exeption handler from domain errors
    """
    if isinstance(exc, CartNotActiveError):
        return Response(
            {"error": str(s)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, EmptyCartError):
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, InsufficientStockError):
        return Response(
            {"error": str(e)},
            status=status.HTTP_409_CONFLICT
        )
    
    return exception_handler(exc, context)