from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('api_users.urls')),
    path('auction/', include('api_auction.urls')),
]
