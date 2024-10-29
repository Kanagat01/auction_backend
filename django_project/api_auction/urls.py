from django.urls import path, include
from .views import *

customer = [
    path('pre_create_order/', PreCreateOrderView.as_view()),
    path('create_order/', CreateOrderView.as_view()),
    path('edit_order/', EditOrderView.as_view()),

    path('add_document/', AddDocumentView.as_view()),
    path('delete_document/', DeleteDocumentView.as_view()),

    path('accept_offer/', AcceptOffer.as_view()),
    path('reject_offer/', RejectOffer.as_view()),
    path('cancel_order/', CancelOrderView.as_view()),
    path('unpublish_order/', UnpublishOrderView.as_view()),
    path('publish_order/', PublishOrderToView.as_view()),
    path('complete_order/', CompleteOrderView.as_view()),
    path('cancel_order_completion/', CancelOrderCompletionView.as_view()),
]

transporter = [
    path('get_offers/', GetOffers.as_view()),
    path('add_order_offer/', AddOrderOfferView.as_view()),
    path('accept_offer/', AcceptOfferTransporter.as_view()),
    path('reject_offer/', RejectOfferTransporter.as_view()),

    path('add_document/', AddDocumentView.as_view()),
    path('add_driver_data/', views_transporter.AddDriverData.as_view())
]

driver = [
    path('get_orders/', views_driver.GetOrders.as_view()),
    path('add_document/', AddDocumentView.as_view()),
    path('delete_document/', DeleteDocumentView.as_view()),
    path('make_order_stage_completed/',
         views_driver.MakeOrderStageCompleted.as_view()),
]

urlpatterns = [
    path("find_cargo/<int:transportation_number>/<str:machine_number>/",
         views_common.FindCargoView.as_view()),
    path("get_orders/", views_common.GetOrdersView.as_view()),
    path('customer/', include(customer)),
    path('transporter/', include(transporter)),
    path('driver/', include(driver)),
]
