from django import forms
from django.contrib import admin
from .models import Transaction, Seller
from django.contrib.auth.admin import UserAdmin


class SellerAdmin(UserAdmin):
    list_display = ['username', 'credit', 'created_at', 'updated_at']
    fields = ['username', 'password', 'credit', 'is_active', 'is_staff']
    fieldsets = None

    def get_readonly_fields(self, request, obj=None):
        return ['credit']


class TransactionAdminForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'

    def clean(self):
        amount = self.cleaned_data.get('amount')
        credit = self.cleaned_data.get('user').credit
        if amount + credit < 0:
            self.add_error('amount', 'User credit is not sufficient.')
        return self.cleaned_data


class TransactionAdmin(admin.ModelAdmin):
    form = TransactionAdminForm
    list_display = ['user', 'type', 'amount', 'receiver', 'datetime']
    fields = ['user', 'amount']

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def formfield_for_dbfield(self, *args, **kwargs):
        formfield = super().formfield_for_dbfield(*args, **kwargs)

        formfield.widget.can_delete_related = False
        formfield.widget.can_change_related = False
        formfield.widget.can_add_related = False
        formfield.widget.can_view_related = False
        return formfield

    def save_model(self, request, obj, form, change):
        obj.type = Transaction.Type.CHARGE
        super().save_model(request, obj, form, change)


admin.site.register(Seller, SellerAdmin)
admin.site.register(Transaction, TransactionAdmin)
