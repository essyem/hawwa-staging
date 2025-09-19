from rest_framework import serializers
from accounts.models import User
from services.models import Service, ServiceCategory, ServiceReview
from bookings.models import Booking, BookingItem


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'user_type', 'profile_picture', 'date_joined']
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class ServiceCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the ServiceCategory model
    """
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'icon', 'slug']


class ServiceReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the ServiceReview model
    """
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceReview
        fields = ['id', 'service', 'user', 'rating', 'comment', 'created_at', 'is_public']
        read_only_fields = ['created_at']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'name': obj.user.get_full_name(),
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else None
        }


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for the Service model
    """
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), 
        source='category', 
        write_only=True
    )
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'short_description', 'price',
            'duration', 'category', 'category_id', 'image', 'status',
            'featured', 'created_at', 'updated_at', 'slug',
            'reviews', 'average_rating'
        ]
        read_only_fields = ['created_at', 'updated_at', 'slug']
    
    def get_reviews(self, obj):
        # Only return public reviews with limited fields
        reviews = obj.reviews.filter(is_public=True)[:3]
        return ServiceReviewSerializer(reviews, many=True).data
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_public=True)
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return None


class BookingItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the BookingItem model
    """
    class Meta:
        model = BookingItem
        fields = ['id', 'booking', 'name', 'description', 'quantity', 'price']


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model
    """
    service_details = serializers.SerializerMethodField()
    items = BookingItemSerializer(many=True, read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'service', 'service_details',
            'start_date', 'end_date', 'start_time', 'address',
            'total_price', 'status', 'created_at', 'updated_at',
            'notes', 'items'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']
    
    def get_service_details(self, obj):
        return {
            'id': obj.service.id,
            'name': obj.service.name,
            'price': obj.service.price,
            'image': obj.service.image.url if obj.service.image else None
        }
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'name': obj.user.get_full_name(),
            'email': obj.user.email
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)