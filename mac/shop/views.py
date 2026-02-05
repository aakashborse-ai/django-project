from django.shortcuts import render
from .models import Product, Contact, Orders, OrderUpdate, Subscription
from math import ceil
from django.db.models import Q
import json
import re
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


@login_required(login_url='/shop/login/')
def index(request):
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password1:
            messages.error(request, 'All fields are required')
            return redirect('Signup')
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('Signup')

        # Strong password: min 8 chars, include upper, lower, digit and special char
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
        if not re.match(pattern, password1):
            messages.error(request, 'Password must be at least 8 characters and include uppercase, lowercase, a number, and a special character')
            return redirect('Signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('Signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('Signup')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, 'Account created successfully. Please login.')
        return redirect('Login')
    return render(request, 'shop/signup.html')


def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        # allow login by username or email
        user = authenticate(request, username=identifier, password=password)
        if user is None:
            # try to find by email
            try:
                u = User.objects.get(email=identifier)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None
        if user is not None:
            login(request, user)
            from django.urls import reverse
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('ShopHome')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('Login')
    # GET
    return render(request, 'shop/login.html', {'next': request.GET.get('next','')})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('Login')

@login_required(login_url='/shop/login/')
def about(request):
    return render(request, 'shop/about.html')


@login_required(login_url='/shop/login/')
def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank = True
    return render(request, 'shop/contact.html' , {'thank':thank})



def tracker(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId', '').strip()
        email = request.POST.get('email', '').strip()

        try:
            order_id = int(orderId)
        except ValueError:
            return JsonResponse({'status': 'noitem'})

        # First try: order id + email
        order_qs = Orders.objects.filter(order_id=order_id, email__iexact=email)

        # If logged in, allow user-based lookup
        if not order_qs.exists() and request.user.is_authenticated:
            order_qs = Orders.objects.filter(order_id=order_id, user=request.user)

        if not order_qs.exists():
            return JsonResponse({'status': 'noitem'})

        order = order_qs.first()

        updates_qs = OrderUpdate.objects.filter(order_id=order_id).order_by('timestamp')
        updates = [
            {'text': u.update_desc, 'time': u.timestamp.strftime('%Y-%m-%d')}
            for u in updates_qs
        ]

        return JsonResponse({
            'status': 'success',
            'updates': updates,
            'itemsJson': order.items_json
        })

    return render(request, 'shop/tracker.html')

# def searchMatch(query, item):
#     '''return true only if query matches the item'''
#     if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
#         return True
#     else:
#         return False

@login_required(login_url='/shop/login/')
def search(request):
    query = request.GET.get('search', '').strip()

    if len(query) < 3:
        return render(request, 'shop/search.html', {
            'msg': "Please enter at least 3 characters to search"
        })

    allProds = []

    # Get unique categories
    cats = Product.objects.values_list('category', flat=True).distinct()

    for cat in cats:
        products = Product.objects.filter(
            Q(category=cat) &
            (
                Q(product_name__icontains=query) |
                Q(desc__icontains=query) |
                Q(category__icontains=query) |
                Q(price__icontains=query)
            )
        )

        n = products.count()
        if n > 0:
            nSlides = n // 4 + ceil((n / 4) - (n // 4))
            allProds.append([products, range(1, nSlides), nSlides])

    if not allProds:
        return render(request, 'shop/search.html', {
            'msg': "No products found matching your search"
        })

    return render(request, 'shop/search.html', {
        'allProds': allProds
    })


@login_required(login_url='/shop/login/')
def productView(request, myid):

    # Fetch the product using the id
    product = Product.objects.filter(id=myid)
    return render(request, 'shop/prodView.html', {'product':product[0]})


@login_required(login_url='/shop/login/')
def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '0')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '').strip()
        phone = request.POST.get('phone', '').strip()

        # Validate phone: must be exactly 10 digits
        # Validate zip_code: must be numeric and at most 6 digits
        errors = []
        if not phone.isdigit() or len(phone) != 10:
            errors.append("Phone number must be exactly 10 digits")
        if zip_code and (not zip_code.isdigit() or len(zip_code) > 6):
            errors.append("Zip code must be at most 6 digits and numeric")
        if errors:
            return render(request, 'shop/checkout.html', {'thank': False, 'error': ' ; '.join(errors)})

        # create order and attach user if logged in
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone, amount=amount)
        if request.user.is_authenticated:
            order.user = request.user
        order.save()

        # build invoice JSON and set invoice_number
        try:
            parsed_items = json.loads(items_json) if items_json else {}
        except Exception:
            parsed_items = {}
        invoice_items = []
        subtotal = 0
        for key, val in parsed_items.items():
            # keys like pr<id> and val = [qty, name, price]
            try:
                qty = int(val[0])
                name_item = val[1]
                price_item = float(val[2])
            except Exception:
                continue
            total_line = qty * price_item
            subtotal += total_line
            invoice_items.append({'sku': key, 'name': name_item, 'qty': qty, 'unit_price': price_item, 'total': total_line})
        invoice = {
            'invoice_no': f"INV{order.order_id}",
            'items': invoice_items,
            'subtotal': subtotal,
            'total': float(amount),
            'customer': {'name': name, 'email': email, 'phone': phone, 'address': address, 'city': city, 'state': state, 'zip': zip_code},
            'order_id': order.order_id,
            'created_at': str(order.created_at)
        }
        order.invoice_json = json.dumps(invoice)
        order.invoice_number = invoice['invoice_no']
        order.save()

        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        return render(request, 'shop/checkout.html', {'thank':thank, 'id': id})
    return render(request, 'shop/checkout.html')




@login_required(login_url='/shop/login/')
@require_POST
def subscribe(request):
    email = request.POST.get('email', '').strip()
    if not email:
        return JsonResponse({'status':'error','message':'Email is required'}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'status':'error','message':'Invalid email address'}, status=400)

    sub, created = Subscription.objects.get_or_create(email=email)
    if created:
        return JsonResponse({'status':'ok','message':'Subscribed'})
    else:
        return JsonResponse({'status':'exists','message':'Email already subscribed'})


@login_required(login_url='/shop/login/')
def my_orders(request):
    orders = Orders.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})


@login_required(login_url='/shop/login/')
def order_invoice(request, order_id):
    try:
        order = Orders.objects.get(order_id=order_id)
    except Orders.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('ShopHome')
    # ensure this order belongs to the user
    if order.user and order.user != request.user:
        messages.error(request, 'You are not authorized to view this invoice')
        return redirect('ShopHome')
    # fall back to email match if user not linked
    if not order.user and order.email != request.user.email:
        messages.error(request, 'You are not authorized to view this invoice')
        return redirect('ShopHome')
    invoice = {}
    try:
        invoice = json.loads(order.invoice_json) if order.invoice_json else {}
    except Exception:
        invoice = {}
    return render(request, 'shop/invoice.html', {'order': order, 'invoice': invoice})
