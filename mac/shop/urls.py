from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="ShopHome"),
    path("about/", views.about, name="AboutUs"),
    path("contact/", views.contact, name="ContactUs"),
    path("tracker/", views.tracker, name="TrackingStatus"),
    path("subscribe/", views.subscribe, name="Subscribe"),
    path("search/", views.search, name="Search"),
    path("products/<int:myid>", views.productView, name="ProductView"),
    path("checkout/", views.checkout, name="Checkout"),
    path("orders/", views.my_orders, name="MyOrders"),
    path("orders/<int:order_id>/invoice/", views.order_invoice, name="OrderInvoice"),
    path("signup/", views.signup, name="Signup"),
    path("login/", views.login_view, name="Login"),
    path("logout/", views.logout_view, name="Logout"),
]
