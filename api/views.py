from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (
    UserSerializer,
    ServiceSerializer,
    ServiceCategorySerializer,
    ServiceReviewSerializer,
    BookingSerializer,
    BookingItemSerializer
)
from accounts.models import User
from services.models import Service, ServiceCategory, ServiceReview
from bookings.models import Booking, BookingItem


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access it
    """
    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.is_staff or request.user.user_type == 'ADMIN':
            return True
        
        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type == 'ADMIN':
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the authenticated user's details
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows service categories to be viewed or edited
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows services to be viewed or edited
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'featured']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['name', 'price', 'created_at']
    lookup_field = 'slug'
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_review(self, request, slug=None):
        """
        Add a review to a service
        """
        service = self.get_object()
        user = request.user
        
        # Check if user already reviewed this service
        if ServiceReview.objects.filter(service=service, user=user).exists():
            return Response(
                {'detail': 'You have already reviewed this service.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ServiceReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(service=service, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """
        Get all reviews for a service
        """
        service = self.get_object()
        reviews = service.reviews.filter(is_public=True)
        serializer = ServiceReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows bookings to be viewed or edited
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'start_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type == 'ADMIN':
            return Booking.objects.all()
        return Booking.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking
        """
        booking = self.get_object()
        
        # Only allow cancellation of pending or confirmed bookings
        if booking.status not in ['pending', 'confirmed']:
            return Response(
                {'detail': 'Only pending or confirmed bookings can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.notes = request.data.get('notes', booking.notes)
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """
        Add an item to a booking
        """
        booking = self.get_object()
        
        # Only allow adding items to pending bookings
        if booking.status != 'pending':
            return Response(
                {'detail': 'Items can only be added to pending bookings.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BookingItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(booking=booking)
            
            # Update booking total price
            booking.total_price += serializer.validated_data['price'] * serializer.validated_data['quantity']
            booking.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows booking items to be viewed or edited
    """
    serializer_class = BookingItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type == 'ADMIN':
            return BookingItem.objects.all()
        return BookingItem.objects.filter(booking__user=user)