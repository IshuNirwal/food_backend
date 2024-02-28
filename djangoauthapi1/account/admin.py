from django.contrib import admin
from account.models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.

class UserModelAdmin(BaseUserAdmin):
     list_display=('id','email','name','is_admin')
     list_filter=('is_admin',)
     fieldsets=(
        ('User Credentials',{'fields':('email','password')}),
        ('Permissions',{'fields':('is_admin',)}),
        
    )
     add_fieldsets=(
        (None,{
            'classes':('wide',),
            'fields':('email','name','password1','password2'),
        }),
    )
     search_fields=('email',)
     ordering=('email','id')
     filter_horizontal=()
admin.site.register(User, UserModelAdmin)
class MenuModelAdmin(admin.ModelAdmin):
    list_display=('id','title','description','image','price','energy','carbs','protein','fibre','fat')
    
admin.site.register(Menu,MenuModelAdmin)

class CartItemAdmin(admin.ModelAdmin):
    list_display=('id','product','quantity','user','processed')
admin.site.register(CartItem,CartItemAdmin)
# class OrderAdmin(admin.ModelAdmin):
#     list_display=('id','customer','order_status','quantity','created_at','flavour','updated_at')
#     list_filter=['created_at','order_status']
# admin.site.register(Order,OrderAdmin)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'subtotal', 'status', 'transaction_id')
    list_filter = ('status',)
    
admin.site.register(Payment,PaymentAdmin)

class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_line_1', 'city', 'state', 'postal_code', 'country')
admin.site.register(Address,AddressAdmin)   

class ContactAdmin(admin.ModelAdmin):
    list_display=('id','name','email','message')
admin.site.register(Contact,ContactAdmin) 