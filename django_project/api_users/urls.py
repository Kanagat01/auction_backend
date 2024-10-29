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
    path('get_settings/', GetSettings.as_view()),
    path('get_landing_data/', GetLandingData.as_view()),
    path('create_application/', CreateApplicationForRegistration.as_view()),
    path('validate_token/', ValidateToken.as_view()),
    path('get_user/', GetUser.as_view()),
    path('edit_user/', EditUser.as_view()),
    path('change_password/', ChangePassword.as_view()),
    path('register_manager/', RegisterManagerForCompany.as_view()),
    path('edit_manager/', EditManager.as_view()),
    path('change_subscription/', ChangeSubscription.as_view()),
]

customer = [
    path('get_transporter_companies/', GetTransporterCompanies.as_view()),
    path('add_transporter_to_allowed_companies/',
         AddTransporterToAllowedCompanies.as_view()),
    path('delete_transporter_from_allowed_companies/',
         DeleteTransporterFromAllowedCompanies.as_view()),
]

transporter = []

driver = [
    path('auth_request/', DriverAuthRequestView.as_view()),
    path('auth_confirm/', DriverAuthConfirm.as_view()),
    path('set_profile_data/', SetDriverProfileData.as_view()),
    path('request_phone_change/', RequestPhoneNumberChangeView.as_view()),
    path('confirm_phone_change/', ConfirmPhoneNumberChangeView.as_view()),
]

urlpatterns = [
    path('auth/', include(auth)),
    path('common/', include(common)),
    path('customer/', include(customer)),
    path('transporter/', include(transporter)),
    path('driver/', include(driver)),
]
