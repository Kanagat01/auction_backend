from django.urls import path, include
from .views import *

auth = [
    path('register_transporter/', RegisterTransporterCompanyView.as_view()),
    path('register_customer/', RegisterCustomerCompanyView.as_view()),
    path('login/', Login.as_view()),
    path('reset_password/', PasswordResetView.as_view()),
    path('reset_password_confirm/<str:token>/',
         PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]

common = [
    path('get_user/', GetUser.as_view()),
    path('edit_user/', EditUser.as_view()),
    path('register_manager/', RegisterManagerForCompany.as_view()),
]

customer = [
    path('add_transporter_to_allowed_companies/',
         AddTransporterToAllowedCompanies.as_view()),
    path('delete_transporter_from_allowed_companies/',
         DeleteTransporterFromAllowedCompanies.as_view()),
]

transporter = [

]

urlpatterns = [
    path('auth/', include(auth)),
    path('common/', include(common)),
    path('customer/', include(customer)),
    path('transporter/', include(transporter)),
]
