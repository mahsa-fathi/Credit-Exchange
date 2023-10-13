from rest_framework import serializers
from .models import Transaction


class SellingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["amount", "receiver"]

    def validate(self, data):
        amount = data.get('amount')
        seller = self.instance

        if amount < 0:
            raise serializers.ValidationError("Amount cannot be negative.")

        if amount is not None and seller:
            if amount > seller.credit:
                raise serializers.ValidationError("Amount cannot exceed available credit.")

        return data
