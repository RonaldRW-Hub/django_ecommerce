from django.contrib import admin

# Register your models here.
from .models import Item, OrderItem, Order, Payment, Coupon, Refund, Address

def make_refund_requested_granted(ModelAdmin, request, queryet):
    queryet.update(refund_requested=False, refund_granted=True)

make_refund_requested_granted.description = 'Update selected orders to refund granted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 
                    'ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted',
                    'shipping_address',
                    'billing_address',
                    'payment',
                    'coupon']
    list_diplay_links = [
                    'user',
                    'shipping_address',
                    'billing_address',
                    'payment',
                    'coupon']
    list_filter = ['ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted']
    search_fields = [
                    'user__username',
                    'ref_code']
    actions = [make_refund_requested_granted]

class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']

admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Address, AddressAdmin)