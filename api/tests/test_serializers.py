from django.test import TestCase
from django.utils import timezone

from api.serializers import BookingSerializer, ServiceSerializer
from bookings.models import Booking
from services.models import Service, ServiceCategory


class BookingSerializerTests(TestCase):
    def test_booking_serializer_accepts_shorthand_fields_and_note_alias(self):
        """BookingSerializer should accept booking_date/booking_time and 'note' alias for notes."""
        data = {
            "customer_name": "Alice",
            "service": None,
            "booking_date": timezone.now().date().isoformat(),
            "booking_time": "09:30",
            "note": "Needs wheelchair access",
        }

        serializer = BookingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        booking = serializer.save()
        self.assertIsInstance(booking, Booking)
        # note alias maps to notes
        self.assertIn("wheelchair", (booking.notes or "").lower())


class ServiceSerializerTests(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(name="Cleaning")

    def test_service_serializer_accepts_category_pk_and_returns_category_details(self):
        data = {
            "name": "Standard Clean",
            "price": "25.00",
            "category": self.category.pk,
        }

        serializer = ServiceSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        service = serializer.save()
        self.assertIsInstance(service, Service)
        # Ensure nested category details available on serialized output
        out = ServiceSerializer(service)
        self.assertIn("category_details", out.data)
        self.assertEqual(out.data["category_details"]["name"], "Cleaning")
