from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework.decorators import authentication_classes
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from .serializers import SellingSerializer
from .models import Transaction


class SellerObtainJWTView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        response = super(SellerObtainJWTView, self).post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = request.user
            if user:
                response.data['user_id'] = user.id
        return response


@authentication_classes([JSONWebTokenAuthentication])
class CreditSellingAPIView(APIView):
    def post(self, request):
        serializer = SellingSerializer(data=request.data, instance=request.user)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            receiver = serializer.validated_data['receiver']

            try:
                Transaction.objects.create(
                    user=request.user,
                    type=Transaction.Type.SELL,
                    amount=amount,
                    receiver=receiver
                )

                return Response({"message": "Credit added successfully."}, status=status.HTTP_201_CREATED)

            except ValidationError as e:
                return Response({"detail": str(e)},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"detail": str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
