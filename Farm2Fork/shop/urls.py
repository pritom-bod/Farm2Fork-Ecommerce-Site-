from django.urls import path
from shop import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', views.ProductView.as_view(), name='home'),
    path('shop/', views.shop, name='shop'),
    path('shop/<slug:data>', views.shop, name='shop-items'),
    path('cart/', views.cart, name='cart'),
    path('chackout/', views.chackout, name='chackout'),
    path('product-details/<int:pk>', views.ProductDetails.as_view(), name='productdetails'),
    path('contact/', views.contact, name='contact'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('404-page/', views.E_page, name='404-page'),
    path('Registration/', views.userregistration.as_view(), name='registration'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
