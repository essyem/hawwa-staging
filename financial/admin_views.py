from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import admin

from .services.reports import trial_balance
from django.http import HttpResponse
import csv
from django.core.paginator import Paginator
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.formats import number_format
from django.utils import timezone


def trial_balance_view(request):
    tb = trial_balance()
    # Add filtering and sorting via GET params
    order = request.GET.get('order', 'code')
    q_type = request.GET.get('type')

    rows = tb.get('rows', [])
    if q_type:
        rows = [r for r in rows if r['account'].account_type == q_type]

    reverse = False
    if order.startswith('-'):
        reverse = True
        order = order[1:]

    if order == 'code':
        rows = sorted(rows, key=lambda r: r['account'].code, reverse=reverse)
    elif order == 'name':
        rows = sorted(rows, key=lambda r: r['account'].name, reverse=reverse)
    elif order == 'balance':
        rows = sorted(rows, key=lambda r: r['balance'], reverse=reverse)

    # CSV export when requested - operate on full filtered/sorted rows (no pagination)
    fmt = request.GET.get('format')
    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="trial_balance.csv"'
        # Excel-friendly UTF-8 BOM
        response.write('\ufeff')
        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        # Metadata header rows
        generated = timezone.now().isoformat()
        filters = f"type={q_type or 'all'}; order={order}"
        writer.writerow([f"Report: Trial Balance"])
        writer.writerow([f"Generated: {generated}"])
        writer.writerow([f"Filters: {filters}"])
        writer.writerow([])
        # Column header
        writer.writerow(['account_code', 'account_name', 'account_type', 'balance_qat', 'balance_raw'])
        for r in rows:
            acct = r.get('account')
            bal = r.get('balance')
            bal_fmt = f"QAR {number_format(bal, use_l10n=True, decimal_pos=2)}"
            writer.writerow([acct.code, acct.name, acct.account_type, bal_fmt, str(bal)])
        return response

    # Pagination
    page = int(request.GET.get('page', '1') or 1)
    paginator = Paginator(rows, 25)
    page_obj = paginator.get_page(page)

    context = dict(
        admin.site.each_context(request),
        title='Trial Balance',
        trial_balance={'rows': page_obj.object_list, 'total': tb.get('total')},
        page_obj=page_obj,
        order=order,
        q_type=q_type,
    )
    return TemplateResponse(request, 'admin/financial/trial_balance.html', context)

