import logging

class RequestContextFilter(logging.Filter):
    """Inject request-specific context (request_id, ip, url) into log records.

    This filter expects that the current thread has access to a request object
    via the record (passed from views or middleware). If not available, defaults
    to '-'.
    """
    def filter(self, record):
        # default values
        record.request_id = getattr(record, 'request_id', '-')
        record.ip = getattr(record, 'ip', '-')
        record.url = getattr(record, 'url', '-')
        # If a request object was attached to the record, prefer it
        req = getattr(record, 'request', None)
        if req is not None and hasattr(req, 'META') and hasattr(req, 'path'):
            record.request_id = getattr(req, 'request_id', record.request_id)
            record.ip = req.META.get('REMOTE_ADDR', record.ip)
            record.url = getattr(req, 'path', record.url)
        return True
