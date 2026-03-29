from django.shortcuts import render,redirect, get_object_or_404
from .models import Order, OrderItem
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Product
from django.contrib.auth.decorators import login_required
import requests
import base64
from datetime import datetime
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})


@login_required(login_url='/accounts/login/')
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1

    request.session['cart'] = cart
    request.session.modified = True  

    return redirect('home')

def view_cart(request):
    cart = request.session.get('cart', {})

    # 🔥 FIX HERE
    products = Product.objects.filter(id__in=[int(id) for id in cart.keys()])

    cart_items = []
    total = 0

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'total': total
    })
def increase_quantity(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)] += 1

 
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('view_cart')

def decrease_quantity(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)] -= 1

        # remove if quantity becomes 0
        if cart[str(product_id)] <= 0:
            del cart[str(product_id)]

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('view_cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('view_cart')
@login_required(login_url='/accounts/login/')
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('home')

    products = Product.objects.filter(id__in=cart.keys())

    total = 0
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        total_price=0
    )

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )


    order.total_price = total
    order.save()

    # clear cart
    request.session['cart'] = {}

    return render(request, 'products/checkout_success.html', {'order': order})



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'products/register.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'products/order_history.html', {
        'orders': orders
    })

def get_access_token():
    consumer_key = "tAcZ2XdPmkgRh4wb6wVW4jBehMFGieslumM57YL3a6WpAasE"
    consumer_secret = "mTEk80xxrZjFBx7e4cAY2ra25Igd6shPGzbA1fj4MRzywBcG0mxtFKG3Bfgz8wGZ"

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(url, auth=(consumer_key, consumer_secret))

        print("TOKEN STATUS:", response.status_code)
        print("TOKEN RESPONSE:", response.text)

        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            return None

    except Exception as e:
        print("TOKEN ERROR:", e)
        return None

def stk_push(phone, amount, order_id):
    access_token = get_access_token()

    if not access_token:
        print("❌ No access token")
        return None

    shortcode = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": "https://example.com/callback/",  # TEMP
        "AccountReference": f"Order{order_id}",
        "TransactionDesc": "Payment"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.text:
            return response.json()
        else:
            print("❌ Empty response from Safaricom")
            return None

    except Exception as e:
        print("❌ ERROR:", e)
        return None

def pay_order(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        phone = request.POST.get('phone')

        response = stk_push(phone, order.total_price, order.id)

        if response:
            print("MPESA RESPONSE:", response)
        else:
            print("❌ Payment failed")

        return render(request, 'products/payment_pending.html', {'order': order})

    return render(request, 'products/pay.html', {'order': order})

def home(request):
    query = request.GET.get('q')

    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()

    return render(request, 'products/home.html', {'products': products})

def search_products(request):
    query = request.GET.get('q')

    products = []

    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

        products = [
            {
                'id': p.id,
                'name': p.name,
                'price': str(p.price),
                'image': p.image.url if p.image else ''
            }
            for p in results
        ]

    return JsonResponse({'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/detail.html', {'product': product})