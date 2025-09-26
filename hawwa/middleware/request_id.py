import uuid
from django.utils.deprecation import MiddlewareMixin

class RequestIDMiddleware(MiddlewareMixin):
    """Attach a request_id to each request for logging correlation."""
    def process_request(self, request):
        rid = request.META.get('HTTP_X_REQUEST_ID') or str(uuid.uuid4())
        request.request_id = rid
        # expose in META for templates or downstream
        request.META['REQUEST_ID'] = rid

    def process_response(self, request, response):
        rid = getattr(request, 'request_id', None)
        if rid:
            response['X-Request-ID'] = rid
        return response
