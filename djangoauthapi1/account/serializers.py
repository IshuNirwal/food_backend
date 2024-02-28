from rest_framework import serializers
from account.models import User
from .models import *
class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)
    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password2',]
        extra_kwargs = {
            'password': {'write_only': True}
        }
        # validating password & confirm password

    def validate(self, attrs):
        password = attrs.get('password')  
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError(
                "Password & confirm  Password doesn't match")
        return attrs
    def create(self, validate_data):
        return User.objects.create_user(**validate_data)
# class UserLoginSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         fields = ['email', 'password']
class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    class Meta:
        model = User
        fields = ['email', 'password']
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name']
        
class UserChangePasswordSerializer(serializers.Serializer):
    password=serializers.CharField(max_length=255,style={'input_type':'password'},write_only=True)
    password2=serializers.CharField(max_length=225,style={'input_type':'password'},write_only=True)
    class Meta:
        fields=['password','password2']
    def validate(self,attrs):
        password=attrs.get('password')
        password2=attrs.get('password2')
        user=self.context.get('user')
        if password != password2:
           raise serializers.ValidationError("Password & confirm  Password doesn't match")
        user.set_password(password)
        user.save()
        return attrs
    
class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model=Menu
        fields='__all__'
        
class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=Menu
        fields='__all__'
class CartItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    title = serializers.CharField(source='product.title', read_only=True)
    image = serializers.ImageField(source='product.image', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'user', 'product', 'quantity', 'title', 'price','image']
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

        
# class OrderSerializer(serializers.ModelSerializer):
#     order_status=serializers.HiddenField(default='PENDING')
#     quantity=serializers.IntegerField()
#     flavour=serializers.CharField(max_length=40)
#     class Meta:
#         model=Order
#         fields=['order_status','quantity','flavour']
        
# class OrderDetailSerializer(serializers.ModelSerializer):
#     order_status=serializers.CharField(default='PENDING')
#     quantity=serializers.IntegerField()
#     flavour=serializers.CharField(max_length=40)
#     created_at=serializers.DateTimeField()
#     updated_at=serializers.DateTimeField()
#     class Meta:
#         model=Order
#         fields=['id','order_status','quantity','flavour','created_at','updated_at']
        
# class OrderStatusUpdateSerializer(serializers.ModelSerializer):
#     order_status=serializers.CharField(default='PENDING')
    
#     class Meta:
#         model=Order
#         fields=['order_status']
        
