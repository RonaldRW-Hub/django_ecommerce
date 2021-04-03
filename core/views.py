import random
import string

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone

from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund
from .forms import CheckoutForms, CouponForm, RefundForm

import random 
import string
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

# creating a random sequence of characters for the reference code
def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForms()
            context = {
                'form': form, 
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user = self.request.user,
                address_type = 'S',
                default = True
            )
            if shipping_address_qs.exists():
                context.update({'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user = self.request.user,
                address_type = 'B',
                default = True
            )
            if billing_address_qs.exists():
                context.update({'default_billing_address': billing_billing_qs[0]})

            return render(self.request, "core/checkout.html", context)
        except:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForms(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                #Shipping address code
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    print('Using the default shipping address')
                    address_qs = Address.objects.filter(
                        user = self.request.user,
                        address_type = 'S',
                        default = True
                    )
                    if address_qs.exist():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new address for the operations")
                    shipping_address = form.cleaned_data.get('street_address')
                    shipping_address2 = form.cleaned_data.get('apartment_address')
                    shipping_country = form.cleaned_data.get('country')
                    shipping_zip_code = form.cleaned_data.get('zip_code')
                    payment_option = form.cleaned_data.get('payment_option')

                    if is_valid_form([shipping_address, shipping_country, shipping_zip_code]):
                        shipping_address = Address(
                            user = self.request.user,
                            street_address = shipping_address,
                            apartment_address = shipping_address2,
                            country = shipping_country,
                            zip = shipping_zip_code,
                            address_type = 'S'
                        )
                        shipping_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get('same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip_code = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip_code,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment-option')

                if payment_option == "S":
                    return redirect('core:payment', payment_option="Stripe")
                elif payment_option == "P":
                    return redirect('core:payment', payment_option="Paypal")
                elif payment_option == "D":
                    return redirect('core:payment', payment_option="Debit card")
                else:
                    messages.warning(self.request, "Failed checkout")
                    return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "you don't have items in your cart")
            return redirect('core:order-summary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, 'core/payment.html', context)
        else: 
            messages.warning(self.request, "you don't have a billing address")
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total_amount() * 100)

        try:
            # Use Stripe's library to make requests...
            charge = stripe.Charge.create(
                amount = amount,
                currency="usd",
                source=token,
            )

            # Creating payment order 
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amoun = order.get_total_amount()
            payment.save()

            # adding the order to the payment but first updating after each order
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            messages.warning(self.request, "Yout Order has been successful")
            return redirect("/")

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}") 
            return redirect("/")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, 'Rate Limit Error.')
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, 'Invalid Parameters.')
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, 'Not Aunthenticated.')
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, 'Network Error.')
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(self.request, 'Something went wrong. You were not charged please try again.')
            return redirect("/")

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.warning(self.request, 'Serious error has occur, we have been notified.')
            return redirect("/")


def about(request):
    context = {}
    return render(request, 'core/about.html', context)


def login(request):
    context = {}
    return render(request, 'core/account/login.html', context)


class HomeView(ListView):
    '''
    try to add a function for picking a dynamic order to the list, like the examples from the page.
    https://stackoverflow.com/questions/42698197/is-there-django-list-view-model-sort
    '''
    model = Item
    paginate_by = 25
    template_name = 'core/home.html'
    ordering = ['-id']


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'core/order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "you don't have items in your cart")
            return redirect("/")



class ItemDetailView(DetailView):
    model = Item
    template_name = 'core/product.html'

# Function to add items to the cart based on the user      
@login_required  
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    #this logic is for avoiding duplicate orders 
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user = request.user,
        ordered=False
        )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    # this is going to check if the order exists
    if order_qs.exists():
        order = order_qs[0]
        # this is going to check if the order item is inside the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
        else:
            messages.info(request, "This item was added to your cart.")
            order.items.add(order_item)
    # if the order does not exist
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
    return redirect("core:product", slug=slug)

# Function to remove element from the cart 
@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item , slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order.")
        return redirect("core:product", slug=slug)


# Function to remove single item from cart
@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item , slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
                order_item.delete()
            messages.info(request, "This quantity has been updated")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order.")
        return redirect("core:product", slug=slug)

# Function to add single item to cart
def add_single_item_to_cart(request, slug):
    item = get_object_or_404(Item , slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This quantity has been updated")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order.")
        return redirect("core:product", slug=slug) 

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")

class RequestRefundFunds(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form 
        }
        return render(self.request, "core/request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            messages = form.cleaned_data.get('messages')
            email = form.cleaned_data.get('email')
            # Edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

            # Store the refund 
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your refund request has been received")
                return redirect ("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist")
                return redirect("core:request-refund")