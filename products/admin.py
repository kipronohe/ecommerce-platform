from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from .models import Product, Order, OrderItem
from django.db.models import Sum
from django.contrib.auth.models import User  # for managing users

# Custom AdminSite
class MyAdminSite(admin.AdminSite):
    site_header = "MyShop Admin"
    site_title = "MyShop Admin Portal"
    index_title = "Welcome to MyShop Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        # Aggregate dashboard data
        total_sales = Order.objects.filter(payment_status=True).aggregate(total=Sum('total_price'))['total'] or 0
        total_orders = Order.objects.count()
        total_customers = User.objects.count()  # using built-in User

        # Top products
        top_products = (
            OrderItem.objects.values('product__name')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:5]
        )

        # Sales over time
        orders = Order.objects.filter(payment_status=True).order_by('created_at')
        dates = [o.created_at.strftime('%Y-%m-%d') for o in orders]
        totals = [o.total_price for o in orders]

        context = {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'top_products': top_products,
            'dates': dates,
            'totals': totals
        }
        return render(request, 'admin/dashboard.html', context)
# Instantiate Custom AdminSite
admin_site = MyAdminSite(name='myadmin')

# Register models
admin_site.register(Product)
admin_site.register(Order)
admin_site.register(User)