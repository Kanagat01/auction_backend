from django.db.models import Q
from rest_framework import serializers
from api_auction.models import *
from api_users.serializers.model_serializers import CustomerManagerSerializer, TransporterManagerSerializer, DriverProfileSerializer


class OrderApplicationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderApplicationType
        fields = '__all__'


class OrderOfferSerializer(serializers.ModelSerializer):
    transporter_manager = TransporterManagerSerializer()

    class Meta:
        model = OrderOffer
        exclude = ['order']


class OrderTrackingGeoPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTrackingGeoPoint
        fields = '__all__'


class OrderTrackingSerializer(serializers.ModelSerializer):
    geopoints = OrderTrackingGeoPointSerializer(many=True)

    class Meta:
        model = OrderTracking
        fields = '__all__'


class OrderDocumentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = OrderDocument
        exclude = ['order']
        read_only_fields = ['created_at']

    def get_user(self, obj: OrderDocument):
        return obj.user.full_name if obj.user else None


class OrderLoadStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLoadStage
        exclude = ['order_couple']


class OrderUnloadStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderUnloadStage
        exclude = ['order_couple']


class OrderStageCoupleSerializer(serializers.ModelSerializer):
    load_stage = OrderLoadStageSerializer()
    unload_stage = OrderUnloadStageSerializer()

    class Meta:
        model = OrderStageCouple
        read_only_fields = ['created_at']
        exclude = ['order']

    def create(self, validated_data):
        load_data = OrderLoadStageSerializer(
            data=validated_data.pop('load_stage', {}))
        load_data.is_valid(raise_exception=True)

        unload_data = OrderUnloadStageSerializer(
            data=validated_data.pop('unload_stage', {}))
        unload_data.is_valid(raise_exception=True)

        order_stage_couple = OrderStageCouple(**validated_data)
        load = OrderLoadStage(**load_data.validated_data,
                              order_couple=order_stage_couple)
        unload = OrderUnloadStage(
            **unload_data.validated_data, order_couple=order_stage_couple)

        order_stage_couple.save()
        load.save()
        unload.save()

        return order_stage_couple

    def update(self, instance, validated_data):
        load = OrderLoadStageSerializer(instance.load_stage, data=validated_data.pop('load_stage', {}),
                                        partial=True)
        load.is_valid(raise_exception=True)
        load.save()

        unload = OrderUnloadStageSerializer(instance.unload_stage, data=validated_data.pop('unload_stage', {}),
                                            partial=True)
        unload.is_valid(raise_exception=True)
        unload.save()

        instance.updated_at = timezone.now()
        return super().update(instance, validated_data)


class BaseOrderSerializer(serializers.ModelSerializer):
    customer_manager = CustomerManagerSerializer(read_only=True)
    transporter_manager = TransporterManagerSerializer(read_only=True)
    driver = DriverProfileSerializer(read_only=True)
    documents = OrderDocumentSerializer(many=True, read_only=True)
    stages = OrderStageCoupleSerializer(many=True, read_only=True)
    tracking = OrderTrackingSerializer(read_only=True)
    application_type = serializers.SerializerMethodField()

    class Meta:
        model = OrderModel
        fields = '__all__'
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 'customer_manager', 'transporter_manager', 'driver',
                            'tracking', 'documents']

    def get_application_type(self, obj):
        try:
            return obj.application_type.status
        except OrderApplicationType.DoesNotExist:
            return None


class OrderSerializer(BaseOrderSerializer):
    offers = serializers.SerializerMethodField()

    def __init__(self, *args, with_offers=True, for_order_viewer=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not with_offers:
            # для перевозчика не надо видеть
            self.fields.pop('offers')
        if for_order_viewer:
            self.fields.pop("offers")
            self.fields.pop("start_price")
            self.fields.pop("price_step")
            self.fields.pop("application_type")

    def create(self, validated_data):
        customer_manager = validated_data.get('customer_manager')
        if not customer_manager:
            raise serializers.ValidationError("customer_manager is required")
        return OrderModel.objects.create(**validated_data)

    def get_offers(self, obj: OrderModel):
        if obj.status in [OrderStatus.being_executed, OrderStatus.completed]:
            offers = [
                OrderOffer.objects.filter(
                    order=obj, status=OrderOfferStatus.accepted
                ).order_by('price').first()
            ]

        else:
            if obj.status == OrderStatus.in_direct:
                status_filter = Q(status=OrderOfferStatus.none) | Q(
                    status=OrderOfferStatus.rejected)
            elif obj.status == OrderStatus.cancelled:
                status_filter = Q(status=OrderOfferStatus.accepted)
            else:
                status_filter = Q(status=OrderOfferStatus.none)

            offers = OrderOffer.objects.filter(
                Q(order=obj) & status_filter).order_by('price')
        return OrderOfferSerializer(offers, many=True).data

    class Meta(BaseOrderSerializer.Meta):
        read_only_fields = BaseOrderSerializer.Meta.read_only_fields + \
            ['offers']


class OrderSerializerForTransporter(BaseOrderSerializer):
    price_data = serializers.SerializerMethodField()

    def __init__(self, *args, transporter_manager: TransporterManager, for_bidding: bool = False, **kwargs):
        """
        for_bidding = True, то цена показывается только если она от перевозчика а другие цены не показываются
        """
        super().__init__(*args, **kwargs)
        self.for_bidding = for_bidding
        if for_bidding:
            self.fields.pop('price_step')
            self.fields.pop('start_price')
        self.transporter_manager = transporter_manager

    def get_price_data(self, obj: OrderModel):
        if obj.status in [OrderStatus.being_executed, OrderStatus.completed, OrderStatus.cancelled]:
            offer = OrderOffer.objects.filter(
                order=obj,
                transporter_manager__in=self.transporter_manager.company.managers.all(),
                status=OrderOfferStatus.accepted
            ).order_by('price').first()
            return {
                "offer_id": offer.id,
                "price": offer.price,
                "current_price": offer.price,
                "is_best_offer": True,
            }

        offer = OrderOffer.objects.filter(
            order=obj,
            transporter_manager__in=self.transporter_manager.company.managers.all(),
            status=OrderOfferStatus.none
        ).order_by('price').first()

        if self.for_bidding:
            if offer is None:
                return None
            return {"offer_id": offer.id, "price": offer.price}

        best_offer = obj.offers.filter(
            status=OrderOfferStatus.none).order_by('price').first()

        if not best_offer:
            return None
        if not offer:
            return {"current_price": best_offer.price}
        return {
            "offer_id": offer.id,
            "price": offer.price,
            "current_price": best_offer.price,
            "is_best_offer": offer.price == best_offer.price,
        }

    class Meta(BaseOrderSerializer.Meta):
        read_only_fields = BaseOrderSerializer.Meta.read_only_fields + \
            ['price_data']


class OrderSerilizerForDriver(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    stages = OrderStageCoupleSerializer(many=True, read_only=True)

    def __init__(self, *args, driver: DriverProfile, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver

    class Meta:
        model = OrderModel
        fields = ['id', 'transportation_number', 'stages', 'documents']

    def get_documents(self, obj: OrderModel):
        documents = obj.documents.filter(user=self.driver.user)
        return OrderDocumentSerializer(documents, many=True).data


class OrderTransportBodyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTransportBodyType
        fields = '__all__'


class OrderTransportLoadTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTransportLoadType
        fields = '__all__'


class OrderTransportUnloadTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTransportUnloadType
        fields = '__all__'
