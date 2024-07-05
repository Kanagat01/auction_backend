from rest_framework import serializers
from api_auction.models import *
from api_users.serializers.model_serializers import CustomerManagerSerializer, TransporterManagerSerializer


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
    class Meta:
        model = OrderDocument
        exclude = ['order']
        read_only_fields = ['created_at']


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


class OrderSerializer(serializers.ModelSerializer):
    customer_manager = CustomerManagerSerializer(read_only=True)
    transporter_manager = TransporterManagerSerializer(read_only=True)
    # take offers that are not rejected
    offers = serializers.SerializerMethodField()
    tracking = OrderTrackingSerializer(read_only=True)
    documents = OrderDocumentSerializer(many=True, read_only=True)
    stages = OrderStageCoupleSerializer(many=True, read_only=True)

    def __init__(self, *args, with_offers=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not with_offers:
            # для перевозчика не надо видеть
            self.fields.pop('offers')

    class Meta:
        model = OrderModel
        fields = '__all__'
        read_only_fields = ['customer_manager', 'id', 'created_at', 'updated_at', 'transporter_manager', 'status',
                            'offers', 'tracking', 'documents']

    def create(self, validated_data):
        customer_manager = validated_data.get('customer_manager')
        if not customer_manager:
            raise serializers.ValidationError("customer_manager is required")
        return OrderModel.objects.create(**validated_data)

    def get_offers(self, obj):
        offers = OrderOffer.objects.filter(
            order=obj, status=OrderOfferStatus.none).order_by('price')
        return OrderOfferSerializer(offers, many=True).data


class OrderSerializerForTransporter(serializers.ModelSerializer):
    customer_manager = CustomerManagerSerializer(read_only=True)
    transporter_manager = TransporterManagerSerializer(read_only=True)
    documents = OrderDocumentSerializer(many=True, read_only=True)
    stages = OrderStageCoupleSerializer(many=True, read_only=True)
    price_data = serializers.SerializerMethodField()

    def __init__(self, *args, transporter_manager: TransporterManager, for_bidding: bool = False, **kwargs):
        """
        for_bidding = True, то цена показывается только если она от перевозчика а другие цены не показываются
        """
        super().__init__(*args, **kwargs)
        self.for_bidding = for_bidding
        if transporter_manager is None:
            raise serializers.ValidationError(
                "transporter_manager is required")
        if for_bidding:
            self.fields.pop('price_step')
            self.fields.pop('start_price')
        self.transporter_manager = transporter_manager

    class Meta:
        model = OrderModel
        fields = '__all__'
        read_only_fields = ['customer_manager', 'id', 'created_at', 'updated_at', 'transporter_manager', 'status',
                            'offers', 'tracking', 'documents', 'price_data']

    def get_price_data(self, obj: OrderModel):
        offer = obj.offers.filter(
            status=OrderOfferStatus.none).order_by('price').first()
        if offer is None:
            if self.for_bidding:
                return None
            return {
                "price": obj.start_price,
                "by_you": False,
            }
        if self.for_bidding:
            if offer.transporter_manager != self.transporter_manager:
                return None

        return {
            "offer_id": offer.id,
            "price": offer.price,
            "by_you": offer.transporter_manager == self.transporter_manager,
        }


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
