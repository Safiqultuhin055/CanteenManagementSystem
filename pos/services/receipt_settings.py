"""POS receipt header/footer from system_settings."""
from core.models import SystemSetting

_SETTING_KEYS = (
    'RECEIPT_HEADER',
    'RECEIPT_ADDRESS',
    'RECEIPT_PHONE',
    'RECEIPT_FOOTER',
)

_DEFAULTS = {
    'RECEIPT_HEADER': 'Canteen Management System',
    'RECEIPT_ADDRESS': 'Staff Canteen',
    'RECEIPT_PHONE': '',
    'RECEIPT_FOOTER': 'THANK YOU!',
}


def get_receipt_settings():
    """Return shop lines for customer/kitchen slips (editable in System settings)."""
    values = dict(_DEFAULTS)
    try:
        rows = SystemSetting.objects.filter(
            setting_key__in=_SETTING_KEYS,
            is_active=True,
            is_deleted=False,
        ).values_list('setting_key', 'setting_value')
        for key, val in rows:
            if val is not None and str(val).strip():
                values[key] = str(val).strip()
    except Exception:
        pass

    return {
        'business_name': values['RECEIPT_HEADER'],
        'business_address': values['RECEIPT_ADDRESS'],
        'business_phone': values['RECEIPT_PHONE'],
        'footer_text': values['RECEIPT_FOOTER'],
    }
