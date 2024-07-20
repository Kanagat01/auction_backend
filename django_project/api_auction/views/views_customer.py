# def get_orders_view_decorator(cls):
#     class GetOrdersView(APIView):
#         permission_classes = [
#             IsCustomerCompanyAccount | IsCustomerManagerAccount]

#         def get(self, request: Request):
#             orders = cls().get_orders(request)
#             page = PaginationClass().paginate_queryset(orders, request)
#             return success_with_text(OrderSerializer(page, many=True).data)

#     return GetOrdersView


# @get_orders_view_decorator
# class GetUnpublishedOrdersView:
#     def get_orders(self, request: Request):
#         return OrderModel.objects.filter(customer_manager=request.user.customer_manager,
#                                          status=OrderStatus.unpublished)
