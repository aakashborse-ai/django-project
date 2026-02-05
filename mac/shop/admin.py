from django.contrib import admin


from .models import Product, Contact, Orders, OrderUpdate, Subscription

admin.site.register(Product)
admin.site.register(Contact)
admin.site.register(Orders)
admin.site.register(OrderUpdate)
admin.site.register(Subscription)
