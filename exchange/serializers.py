from rest_framework import serializers
from .models import Transaction


class SellingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["amount", "receiver"]
