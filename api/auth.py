from rest_framework import authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from services.models import Service, ServiceCategory, ServiceReview
from bookings.models import Booking, BookingItem
from .serializers import (
    UserSerializer,
    ServiceCategorySerializer,
    ServiceSerializer,
    ServiceReviewSerializer,
    BookingSerializer,
    BookingItemSerializer
)

User = get_user_model()

class CustomAuthToken(ObtainAuthToken):
    """Custom authentication token view"""
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Include user data in response
        user_serializer = UserSerializer(user)
        
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'user': user_serializer.data
        })


class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current authenticated user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """Update current authenticated user profile"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for service categories"""
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    lookup_field = 'slug'


class ServiceViewSet(viewsets.ModelViewSet):
    """API endpoint for services"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'featured']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['price', 'created_at', 'name']
    lookup_field = 'slug'
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def review(self, request, slug=None):
        """Add a review to a service"""
        service = self.get_object()
        
        # Check if user already reviewed this service
        existing_review = ServiceReview.objects.filter(
            service=service, 
            user=request.user
        ).first()
        
        if existing_review:
            # Update existing review
            serializer = ServiceReviewSerializer(
                existing_review, 
                data=request.data,
                context={'request': request}
            )
        else:
            # Create new review
            serializer = ServiceReviewSerializer(
                data=request.data,
                context={'request': request}
            )
        
        if serializer.is_valid():
            serializer.save(service=service, user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class BookingViewSet(viewsets.ModelViewSet):
    """API endpoint for bookings"""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'booking_date']
    search_fields = ['booking_number', 'note']
    ordering_fields = ['booking_date', 'created_at']
    
    def get_queryset(self):
        """Return bookings for current user or all bookings for staff"""
        user = self.request.user
        if user.is_staff or user.user_type in ['admin', 'provider', 'dispatcher']:
            return Booking.objects.all()
        return Booking.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Save the booking with the authenticated user"""
        serializer.save(user=self.request.user)


class BookingItemViewSet(viewsets.ModelViewSet):
    """API endpoint for booking items"""
    serializer_class = BookingItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return booking items for current user or all booking items for staff"""
        user = self.request.user
        if user.is_staff or user.user_type in ['admin', 'provider', 'dispatcher']:
            return BookingItem.objects.all()
            
        # Filter by booking's user
        return BookingItem.objects.filter(booking__user=user)
        
    def perform_create(self, serializer):
        """Save the booking item and update the booking total"""
        booking_item = serializer.save()
        booking = booking_item.booking
        
        # Recalculate booking total
        booking.calculate_total()
        booking.save()