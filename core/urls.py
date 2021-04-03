from . import views
from django.urls import path

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order-summary/', views.OrderSummaryView.as_view(), name='order-summary'),    
    path('product/<slug>/', views.ItemDetailView.as_view(), name='product'),
    path('about/', views.about, name='about'),
    path('add_coupon/', views.AddCouponView.as_view(), name = 'add_coupon'),
    path('add_to_cart/<slug>/', views.add_to_cart,name = 'add_to_cart'),
    path('remove_from_cart/<slug>/', views.remove_from_cart,name = 'remove_from_cart'),
    path('remove_item_from_cart/<slug>/', views.remove_single_item_from_cart,name = 'remove_single_item_from_cart'),
    path('add_item_to_cart/<slug>/', views.add_single_item_to_cart,name = 'add_single_item_to_cart'),
    path('payment/<payment_option>/', views.PaymentView.as_view(), name='payment'),
    path('request-refund/', views.RequestRefundFunds.as_view(), name='request-refund')

]