from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from account.serializers import *
from django.contrib.auth import authenticate
from account.renders import UserRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from django.conf import settings
from django.contrib.auth import get_user_model
import razorpay
from django.db import transaction
import logging
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
# Initialize Razorpay client with your Razorpay API keys
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_KEY_SECRET))

class InitiatePayment(APIView):
    permission_classes = [IsAuthenticated | AllowAny]
    def get(self, request):
            payment = Payment.objects.all()
            serializer=PaymentSerializer(payment,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
            # Get all cart items for the authenticated user
        cart_items = CartItem.objects.filter(user=request.user)

        # Calculate the total amount for payment
        total_amount = 0
        for cart_item in cart_items:
            total_amount += cart_item.product.price * cart_item.quantity

        # Convert the total amount to integer paise (minimum value: 100 paise)
        total_amount_in_paise = int(total_amount * 100)
        total_amount_in_paise = max(total_amount_in_paise, 100)  # Ensure the minimum value is 100 paise (Rs. 1)

        # Create a Razorpay order
        order_response = razorpay_client.order.create({
            'amount': total_amount_in_paise,
            'currency': 'INR',
        })

        # Create a single Payment record in your database for the entire cart
        payment = Payment.objects.create(
            user=request.user,
            status='pending',
            transaction_id=order_response.get('id'),
            subtotal=total_amount,
        )

        # Assign all cart items to the payment record
        for cart_item in cart_items:
            cart_item.payment = payment
            cart_item.save()

        # Return the payment details to the frontend
        data = {
            'payment_amount': total_amount_in_paise,
            'payment_order_id': order_response.get('id'),
        }

        return Response(data)



class HandlePayment(APIView):
    permission_classes = [IsAuthenticated | AllowAny]
    def post(self, request):
        logger = logging.getLogger(__name__)

        # Assuming you have received the transaction_id and status from the payment gateway
        transaction_id = request.data.get('transaction_id')
        status = request.data.get('status')

        logger.info(f"Received transaction_id: {transaction_id}, status: {status}")


        # Retrieve the payment record using the transaction_id
        payment = get_object_or_404(Payment, transaction_id=transaction_id)

        # Update the payment status in the database
        payment.status = status
        payment.save()

        return Response({'status': 'success'})


class ReceiptData(APIView):
    permission_classes = [IsAuthenticated | AllowAny]

    def get(self, request, transaction_id):
        # Check if the user is authenticated before fetching the payment record
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        # Retrieve the payment record using the transaction_id
        try:
            payment = Payment.objects.get(transaction_id=transaction_id, user=request.user)
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found"}, status=404)

        # Fetch all cart items associated with the payment
        cart_items = CartItem.objects.filter(user=request.user, payment=payment)

        # Serialize cart items to retrieve their data
        cart_item_serializer = CartItemSerializer(cart_items, many=True)

        # Extract and add cart item details (title and image) to the serialized cart items
        cart_items_data = cart_item_serializer.data
        for i in range(len(cart_items_data)):
            cart_items_data[i]["product_title"] = cart_items[i].product.title
            cart_items_data[i]["product_image"] = cart_items[i].product.image.url

        # Here you can add any other relevant data you want to include in the receipt
        receipt_data = {
            "transaction_id": payment.transaction_id,
            "user_name": payment.user.name,
            "amount": payment.subtotal,
            "cartItems": cart_items_data,  # Add the serialized cart items to the receipt data
            # Add other relevant receipt details here
        }

        # Delete the cart items associated with the payment
        with transaction.atomic():
            cart_items.delete()

        return Response(receipt_data)

    
class SaveAddress(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new address for the authenticated user.
        """
        # Add the authenticated user to the request data before validating
        request.data['user'] = request.user.id
        
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # No need to explicitly pass the user, as it's already set in the data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


User=get_user_model()

# Create your views here.

# Generate Token Manually


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserRegistrationView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            token = get_tokens_for_user(user)
            return Response({'token': token, 'msg': 'Registration Successful'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.data.get('email')
            password = serializer.data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                token = get_tokens_for_user(user)
                return Response({'token': token, 'msg': 'Login Success'}, status=status.HTTP_200_OK)
            else:
                return Response({'errors': {'non_field_errors': ['Email or Password is not Valid']}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    renderer_classes=[UserRenderer]
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        serializer=UserProfileSerializer(request.user)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
class UserChangePasswordView(APIView):
     renderer_classes=[UserRenderer]
     permission_classes=[IsAuthenticated]
     def post(self,request,format=None):
         serializer=UserChangePasswordSerializer(data=request.data,context={'user':request.user})
         if serializer.is_valid(raise_exception=True):
             return Response({'msg':'Password change successfully'},status=status.HTTP_200_OK)
         return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
     
class MenuView(APIView):
    # renderer_classes=[UserRenderer]
    def get(self,request):
        menu_obj=Menu.objects.all()
        print(menu_obj)
        serializer=MenuSerializer(menu_obj,many=True)
        print(serializer.data)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
class MenuDescriptionView(APIView):
    def get(self, request, id):
        try:
           menu_item_obj = Menu.objects.get(id=id)
           serializer = MenuItemSerializer(menu_item_obj)
           return Response(serializer.data, status=status.HTTP_200_OK)
        except Menu.DoesNotExist:
             return Response({'status': 404, 'message': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'status': 403, 'message': 'Menu item doesnot exists'}, status=status.HTTP_403_FORBIDDEN)

class CartItemCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def get(self,request):
        cart_items = CartItem.objects.filter(user=self.request.user)

        serializer = CartItemSerializer(cart_items, many=True)

        return Response(serializer.data)
       


    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            # Extracting the product ID and quantity from the request data
            product_id = serializer.validated_data['product'].id
            quantity = serializer.validated_data['quantity']

            # Checking if the product exists in the Menu
            try:
                product = Menu.objects.get(pk=product_id)
            except Menu.DoesNotExist:
                return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check if the product is already in the cart for the authenticated user
            try:
                cart_item = CartItem.objects.get(product=product, user=request.user)
                # If the product exists in the cart, increase the quantity
                cart_item.quantity += quantity
            except CartItem.DoesNotExist:
                # If the product does not exist in the cart, create a new CartItem object
                cart_item = CartItem(
                    product=product,
                    quantity=quantity,
                    user=request.user  # The authenticated user instance
                )

            cart_item.save()

            # Return the serialized data of the updated/created CartItem
            return Response(CartItemSerializer(cart_item).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class CartItemDeleteView(APIView):
    def delete(self, request, cart_item_id):
        try:
            cart_item = CartItem.objects.get(pk=cart_item_id)
            cart_item.delete()
            return Response({"message": "Cart item deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"message": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    
class SearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, title): 
        try:
            results = Menu.objects.filter(title__icontains=title) 
            if results.exists():
                serializer = MenuSerializer(results, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Meals FOUND successfully",
                    "data": serializer.data,
                }, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No query provided"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save()

            # Sending a contact form confirmation email
            subject = "Contact Form Submission Confirmation"
            message = render_to_string('email.html', {'submission': submission})
            plain_message = strip_tags(message)

            send_mail(subject, plain_message, 'nirwalriya51@gmail.com', [submission.email], html_message=message)

            return Response({'message': 'Email sent successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)