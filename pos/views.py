import json
import logging

import requests
from django.contrib.auth.decorators import login_required
from django.db.models import BooleanField, Case, Value, When
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from balance.models import EmployeeBalance
from employee.models import EmployeeCard
from inventory.models import FoodCategory, MenuItem

from .services.checkout import CheckoutError, process_checkout
from .services.menu_stock import build_pos_menu_stock
from .services.receipt_settings import get_receipt_settings
from .services.voice_agent import VoiceAgentError, run_voice_turn

logger = logging.getLogger(__name__)


def _normalize_card_number(raw: str) -> str:
    """Strip whitespace and common HID keyboard-wedge prefixes."""
    s = (raw or '').strip()
    while s and s[0] in '%;?':
        s = s[1:].strip()
    while s and s[-1] in '?;':
        s = s[:-1].strip()
    return s


def _find_employee_card(card_number: str):
    """Resolve card by exact UID, case-insensitive, or suffix (partial UID)."""
    base = EmployeeCard.objects.select_related('employee', 'employee__department').filter(
        is_active=True,
        is_deleted=False,
        card_status='ACTIVE',
    )
    card = base.filter(card_number=card_number).first()
    if card:
        return card
    card = base.filter(card_number__iexact=card_number).first()
    if card:
        return card
    if len(card_number) >= 6:
        card = base.filter(card_number__iendswith=card_number).first()
        if card:
            return card
        card = base.filter(card_number__icontains=card_number).first()
    return card


@login_required
def pos_dashboard(request):
    categories = FoodCategory.objects.filter(is_active=True, is_deleted=False).order_by('category_name')
    menu_items = (
        MenuItem.objects.filter(
            is_active=True, is_available=True, is_deleted=False,
        )
        .annotate(
            _has_image=Case(
                When(image_data__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
        .defer('image_data')
        .select_related('category')
        .order_by('category__category_name', 'item_name')
    )
    menu_stock = build_pos_menu_stock(menu_items)
    from core.api_registry import get_active_llm
    # Voice ordering is on whenever ANY LLM provider is configured — DB-driven
    # (admin → API integrations), with .env as fallback. Do NOT gate on a single
    # provider's env key: that hides the button even when Gemini/local is active.
    return render(request, 'pos/pos_dashboard.html', {
        'categories': categories,
        'menu_items': menu_items,
        'menu_stock': menu_stock,
        'receipt_defaults': get_receipt_settings(),
        'voice_enabled': get_active_llm().is_configured,
    })


@login_required
@require_POST
def api_scan_card(request):
    try:
        data = json.loads(request.body)
        card_number = _normalize_card_number(data.get('card_number') or '')
        if not card_number:
            return JsonResponse({'success': False, 'message': 'Card number required'})

        card = _find_employee_card(card_number)
        if not card:
            return JsonResponse({'success': False, 'message': f'Card not found: {card_number}'})

        employee = card.employee
        if not employee.is_active or employee.is_deleted:
            return JsonResponse({'success': False, 'message': 'Employee is inactive'})

        bal = EmployeeBalance.objects.filter(employee_id=employee.id).first()
        balance = float(bal.advance_balance) if bal else 0.0
        credit_limit = float((bal.credit_limit - bal.credit_used) if bal else 0)
        dept = employee.department.department_name if employee.department_id else '—'

        return JsonResponse({
            'success': True,
            'employee_name': employee.full_name,
            'department': dept,
            'balance': balance,
            'credit_limit': credit_limit,
            'card_id': card.id,
            'employee_id': employee.id,
            'card_number': card.card_number,
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'})
    except Exception as exc:
        logger.exception('Card scan failed')
        return JsonResponse({'success': False, 'message': str(exc)})


@login_required
@require_POST
def api_checkout(request):
    try:
        data = json.loads(request.body)
        items = data.get('items') or {}
        card_id = data.get('card_id')
        employee_id = data.get('employee_id')
        is_guest = str(card_id).upper() == 'GUEST' or str(employee_id).upper() == 'GUEST'

        if not is_guest and (not card_id or not employee_id):
            return JsonResponse({'success': False, 'message': 'Scan employee card or enable guest mode'})

        result = process_checkout(
            items_raw=items,
            card_id=card_id,
            employee_id=employee_id,
            user_id=request.user.pk,
            is_guest=is_guest,
        )
        return JsonResponse(result)
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'})
    except Exception as exc:
        logger.exception('Checkout failed')
        return JsonResponse({'success': False, 'message': f'Checkout failed: {exc}'})


@login_required
@require_POST
def api_voice_order(request):
    """One turn of the Bangla voice ordering assistant (Claude)."""
    try:
        data = json.loads(request.body)
        history = data.get('messages') or []
        if not isinstance(history, list):
            return JsonResponse({'success': False, 'message': 'Invalid conversation'})
        # Keep the transcript bounded so a long session can't balloon the prompt.
        history = history[-20:]
        customer_name = data.get('customer_name') or None
        result = run_voice_turn(history=history, customer_name=customer_name)
        return JsonResponse(result)
    except VoiceAgentError as exc:
        return JsonResponse({'success': False, 'message': str(exc)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'})
    except Exception as exc:
        logger.exception('Voice order failed')
        return JsonResponse({'success': False, 'message': 'Voice assistant failed'})


@login_required
@require_GET
def api_voice_provider(request):
    """Report which LLM integration is currently active (for the modal header)."""
    from core.api_registry import get_active_llm
    labels = {
        'anthropic': 'Claude', 'gemini': 'Gemini', 'local': 'Local LLM',
        'openai': 'OpenAI', 'none': 'নিষ্ক্রিয়',
    }
    cfg = get_active_llm()
    active = cfg.is_configured
    return JsonResponse({
        'active': active,
        'provider': cfg.provider if active else 'none',
        'label': labels.get(cfg.provider, cfg.provider) if active else 'নিষ্ক্রিয়',
        'model': cfg.api_model if active else '',
    })


def _tts_chunks(text, limit=180):
    """Split text into <=limit-char pieces on spaces (Google TTS caps length)."""
    words = text.split()
    chunks, cur = [], ''
    for w in words:
        if len(cur) + len(w) + 1 > limit and cur:
            chunks.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        chunks.append(cur)
    return chunks[:6]  # cap total work per reply


@login_required
@require_GET
def api_tts(request):
    """Bangla text-to-speech proxy — returns MP3 audio (no OS voice needed).

    Uses Google Translate's public TTS endpoint (Bengali). The browser plays
    the audio, so speech works even when Windows has no Bangla voice installed.
    """
    text = (request.GET.get('text') or '').strip()
    if not text:
        return HttpResponse(status=400)
    text = text[:600]

    audio = bytearray()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'https://translate.google.com/',
    }
    try:
        for chunk in _tts_chunks(text):
            r = requests.get(
                'https://translate.google.com/translate_tts',
                params={'ie': 'UTF-8', 'q': chunk, 'tl': 'bn', 'client': 'tw-ob'},
                headers=headers, timeout=20,
            )
            if r.status_code != 200 or 'audio' not in r.headers.get('Content-Type', ''):
                logger.warning('TTS upstream %s for chunk', r.status_code)
                return HttpResponse(status=502)
            audio.extend(r.content)
    except requests.RequestException:
        logger.exception('TTS proxy failed')
        return HttpResponse(status=502)

    resp = HttpResponse(bytes(audio), content_type='audio/mpeg')
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp
