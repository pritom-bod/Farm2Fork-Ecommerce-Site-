from django.urls import path
from shop import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_view
from .forms import LoginForm, PassChangeForm, MyPasswordResetForm, MySetPasswordForm

urlpatterns = [
    path('', views.ProductView.as_view(), name='home'),
    path('shop/', views.shop, name='shop'),
    path('shop/<slug:data>/', views.shop, name='shop-items'),
    path('cart/', views.cart, name='cart'),
    path('chackout/', views.chackout, name='chackout'),
    path('order-confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('order-detail/<str:order_number>/', views.order_detail, name='order_detail'),
    # THIS IS THE CRITICAL CHANGE: use the correct name for product detail below!
    path('product-details/<int:pk>/', views.ProductDetails.as_view(), name='product_detail'),

    path('contact/', views.contact, name='contact'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('profile/', views.profile, name='profile'),
    path('404-page/', views.E_page, name='404-page'),

    # Authentication URLs
    path('Registration/', views.userregistration.as_view(), name='registration'),
    path('account/Login/', views.CustomLoginView.as_view(template_name='shop/login.html', authentication_form=LoginForm), name='login'),
    path('logout/', auth_view.LogoutView.as_view(next_page='login'), name='logout'),

    # Password management URLs
    path('password-change/', auth_view.PasswordChangeView.as_view(template_name='shop/passwordchange.html', form_class=PassChangeForm, success_url='/passwordchangedone/'), name='passwordchange'),
    path('passwordchangedone/', auth_view.PasswordChangeDoneView.as_view(template_name='shop/passwordchangedone.html'), name='passwordchangedone'),
    path('password-reset/', auth_view.PasswordResetView.as_view(template_name='shop/password_reset.html', form_class=MyPasswordResetForm), name='password_reset'),
    path('password-reset/done/', auth_view.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_view.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html', form_class=MySetPasswordForm), name='password_reset_confirm'),
    path('password-reset-complete/', auth_view.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'), name='password_reset_complete'),

    # Fixed: regular post add-to-cart, not only AJAX
    path('add-to-cart/<int:pk>/', views.add_to_cart_view, name='add_to_cart'),

    # AJAX URLs for Cart
    path('add-to-cart/', views.add_to_cart, name='ajax_add_to_cart'),  # Renamed to avoid clash
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
