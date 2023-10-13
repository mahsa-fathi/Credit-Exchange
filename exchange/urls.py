from django.urls import path
from .views import SellerObtainJWTView, CreditSellingAPIView

urlpatterns = [
    path('token/', SellerObtainJWTView.as_view(), name='token'),
    path('sell/', CreditSellingAPIView.as_view(), name='sell')
]
