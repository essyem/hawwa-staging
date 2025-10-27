from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import (
    ServiceCategory, 
    Service, 
    AccommodationService, 
    HomeCareService, 
    WellnessService, 
    ServiceReview,
    ServiceImage
)

# Custom admin actions
@admin.action(description='Mark selected services as active')
def mark_as_active(modeladmin, request, queryset):
    """Mark selected services as active."""
    updated = queryset.update(status='active')
    messages.success(request, f"Successfully activated {updated} services.")

@admin.action(description='Mark selected services as inactive')
def mark_as_inactive(modeladmin, request, queryset):
    """Mark selected services as inactive."""
    updated = queryset.update(status='inactive')
    messages.success(request, f"Successfully deactivated {updated} services.")

@admin.action(description='Mark selected services as featured')
def mark_as_featured(modeladmin, request, queryset):
    """Mark selected services as featured."""
    updated = queryset.update(featured=True)
    messages.success(request, f"Successfully featured {updated} services.")

@admin.action(description='Remove featured status')
def remove_featured(modeladmin, request, queryset):
    """Remove featured status from selected services."""
    updated = queryset.update(featured=False)
    messages.success(request, f"Successfully removed featured status from {updated} services.")

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ('image', 'caption', 'display_order')
    readonly_fields = ()

class ServiceReviewInline(admin.TabularInline):
    model = ServiceReview
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    can_delete = False
    max_num = 5  # Show only latest 5 reviews
    ordering = ('-created_at',)
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'service_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('name',)
    readonly_fields = ('service_count',)
    
    def service_count(self, obj):
        """Display number of services in this category."""
        count = obj.services.count()
        return format_html('<strong>{}</strong> services', count)
    service_count.short_description = 'Services'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).prefetch_related('services')

class BaseServiceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'price_formatted', 
        'status_colored', 'featured_icon', 'rating_display', 'created_at'
    )
    list_filter = ('status', 'featured', 'category', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ServiceImageInline, ServiceReviewInline]
    readonly_fields = ('created_at', 'updated_at', 'rating_display')
    list_per_page = 25
    actions = [mark_as_featured, remove_featured]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'short_description')
        }),
        ('URL & SEO', {
            'fields': ('slug',),
            'classes': ('collapse',)
        }),
        ('Service Details', {
            'fields': ('price', 'duration', 'image', 'status', 'featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def price_formatted(self, obj):
        """Display formatted price."""
        return format_html('<strong>QAR {}</strong>', f'{obj.price:.2f}')
    price_formatted.short_description = 'Price'
    price_formatted.admin_order_field = 'price'
    
    def status_colored(self, obj):
        """Display status with color coding."""
        colors = {
            'available': 'green',
            'unavailable': 'red',
            'limited': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    status_colored.admin_order_field = 'status'
    
    def featured_icon(self, obj):
        """Display featured status as icon."""
        if obj.featured:
            return format_html('<span style="color: gold; font-size: 16px;">★</span>')
        return format_html('<span style="color: lightgray;">☆</span>')
    featured_icon.short_description = 'Featured'
    featured_icon.admin_order_field = 'featured'
    
    def rating_display(self, obj):
        """Display average rating with stars."""
        if hasattr(obj, 'reviews'):
            avg_rating = obj.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
            if avg_rating:
                stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
                return format_html(
                    '<span style="color: gold;">{}</span> ({})',
                    stars, f'{avg_rating:.1f}'
                )
        return 'No ratings'
    rating_display.short_description = 'Rating'
    
    def get_queryset(self, request):
        """Optimize queryset with related fields."""
        return super().get_queryset(request).select_related('category').prefetch_related('reviews')

@admin.register(Service)
class ServiceAdmin(BaseServiceAdmin):
    """Enhanced admin interface for base Service model."""
    pass

@admin.register(AccommodationService)
class AccommodationServiceAdmin(BaseServiceAdmin):
    """Enhanced admin interface for AccommodationService model."""
    list_display = BaseServiceAdmin.list_display + ('capacity', 'room_type')
    list_filter = BaseServiceAdmin.list_filter + ('room_type', 'amenities')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'short_description')
        }),
        ('URL & SEO', {
            'fields': ('slug',),
            'classes': ('collapse',)
        }),
        ('Service Details', {
            'fields': ('price', 'duration', 'image', 'status', 'featured')
        }),
        ('Accommodation Details', {
            'fields': ('location', 'address', 'capacity', 'amenities', 'room_type', 'check_in_time', 'check_out_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(HomeCareService)
class HomeCareServiceAdmin(BaseServiceAdmin):
    """Enhanced admin interface for HomeCareService model."""
    list_display = BaseServiceAdmin.list_display + ('service_area', 'min_hours')
    list_filter = BaseServiceAdmin.list_filter + ('service_area',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'short_description')
        }),
        ('URL & SEO', {
            'fields': ('slug',),
            'classes': ('collapse',)
        }),
        ('Service Details', {
            'fields': ('price', 'duration', 'image', 'status', 'featured')
        }),
        ('Home Care Details', {
            'fields': ('service_area', 'min_hours')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(WellnessService)
class WellnessServiceAdmin(BaseServiceAdmin):
    """Enhanced admin interface for WellnessService model."""
    list_display = BaseServiceAdmin.list_display + ('service_type', 'is_virtual')
    list_filter = BaseServiceAdmin.list_filter + ('service_type', 'is_virtual')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'short_description')
        }),
        ('URL & SEO', {
            'fields': ('slug',),
            'classes': ('collapse',)
        }),
        ('Service Details', {
            'fields': ('price', 'duration', 'image', 'status', 'featured')
        }),
        ('Wellness Details', {
            'fields': ('service_type', 'is_virtual')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )



@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = (
        'get_service_info', 'get_user_info', 'rating_stars', 
        'is_public', 'created_at'
    )
    list_filter = ('rating', 'is_public', 'created_at', 'service__category')
    search_fields = (
        'comment', 'user__email', 'user__first_name', 'user__last_name', 
        'service__name'
    )
    readonly_fields = ('created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('service', 'user', 'rating', 'comment')
        }),
        ('Status', {
            'fields': ('is_public',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_service_info(self, obj):
        """Display service information with link."""
        service_url = reverse('admin:services_service_change', args=[obj.service.id])
        return format_html(
            '<a href="{}">{}</a>',
            service_url,
            obj.service.name
        )
    get_service_info.short_description = 'Service'
    get_service_info.admin_order_field = 'service__name'
    
    def get_user_info(self, obj):
        """Display user information with link."""
        user_url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>',
            user_url,
            obj.user.get_full_name() or obj.user.email,
            obj.user.email
        )
    get_user_info.short_description = 'Reviewer'
    get_user_info.admin_order_field = 'user__first_name'
    
    def rating_stars(self, obj):
        """Display rating as stars."""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        colors = {1: 'red', 2: 'orange', 3: 'yellow', 4: 'lightgreen', 5: 'green'}
        color = colors.get(obj.rating, 'black')
        return format_html(
            '<span style="color: {}; font-size: 16px;">{}</span>',
            color, stars
        )
    rating_stars.short_description = 'Rating'
    rating_stars.admin_order_field = 'rating'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('service', 'user')

@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ('get_service_info', 'caption', 'display_order', 'image_preview')
    list_filter = ('service__category', 'service__status')
    search_fields = ('caption', 'service__name')
    readonly_fields = ('image_preview',)
    
    def get_service_info(self, obj):
        """Display service information."""
        service_url = reverse('admin:services_service_change', args=[obj.service.id])
        return format_html(
            '<a href="{}">{}</a>',
            service_url,
            obj.service.name
        )
    get_service_info.short_description = 'Service'
    get_service_info.admin_order_field = 'service__name'
    
    def image_preview(self, obj):
        """Display image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Preview'
