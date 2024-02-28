from django.urls import path
from account.views import *


urlpatterns = [
    path('register/',UserRegistrationView.as_view(),name='register'),
    path('login/',UserLoginView.as_view(),name='login'),
    path('profile/',UserProfileView.as_view(),name='profile'),
    path('changepassword/',UserChangePasswordView.as_view(),name='changepassword'),
    path('menu/',MenuView.as_view(),name='menu'),
    path('menuitem/<str:id>/',MenuDescriptionView.as_view(),name='menuitem'),
    path('cartitem/',CartItemCreateView.as_view(),name='cartitem'),
    path('api/save_address/', SaveAddress.as_view(), name='save_user_address'),
    # path('order/',OrderCreateListView.as_view(),name='order'),
   path('initiate-payment/', InitiatePayment.as_view(), name='initiate-payment'),
    path('handle-payment-callback/', HandlePayment.as_view(), name='handle-payment-callback'),
   path('receipt/<str:transaction_id>/', ReceiptData.as_view(), name='receipt-data'),
    path('search/<str:title>/', SearchView.as_view(), name='search'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('cartitem/<int:cart_item_id>/', CartItemDeleteView.as_view(), name='cart-item-delete'),
   # path('user/<int:user_id>/order/<int:order_id>',UserOrderDetail.as_view(),name='user_specific_detail'),
]