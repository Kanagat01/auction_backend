from django.urls import path, include
from .views import *

customer = [
    path('get_orders/', views_customer.get_orders_view),  # uses paginator

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
]

transporter = [
    path('get_offers/', GetOffers.as_view()),
    path('add_order_offer/', AddOrderOfferView.as_view()),
    path('accept_offer/', AcceptOfferTransporter.as_view()),
    path('reject_offer/', RejectOfferTransporter.as_view()),

    path('add_document/', AddDocumentView.as_view()),
    path('add_driver_data/', views_transporter.AddDriverData.as_view()),
    path('get_orders/', views_transporter.get_orders_view),  # uses paginator
]

urlpatterns = [
    path('customer/', include(customer)),
    path('transporter/', include(transporter)),
]

# path('add_order_stage/', AddStageToOrderView.as_view()),
# path('edit_order_stage/', EditStageView.as_view()),
# path('delete_order_stage/', DeleteStageView.as_view()),

# path('get_cancelled_orders/',
#         views_transporter.GetCancelledOrdersView.as_view()),  # uses paginator
# path('get_orders_in_auction/',
#         views_transporter.GetOrdersInAuctionView.as_view()),  # uses paginator
# path('get_orders_in_bidding/',
#         views_transporter.GetOrdersInBiddingView.as_view()),  # uses paginator
# path('get_orders_in_direct/',
#         views_transporter.GetOrdersInDirectView.as_view()),  # uses paginator
# path('get_being_executed_orders/',
#         views_transporter.GetBeingExecutedOrdersViews.as_view()),  # uses paginator
# path('get_completed_orders/',
#         views_transporter.GetCompletedOrdersView.as_view()),  # uses paginator
