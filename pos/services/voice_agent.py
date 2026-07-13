"""Claude-powered Bangla voice ordering assistant for the POS.

The browser does speech-to-text (Web Speech API, bn-BD) and text-to-speech.
This module is the "brain": it takes the running conversation plus a live
snapshot of today's menu/stock and asks Claude to (a) reply to the customer in
friendly Bangla, (b) maintain the current order, and (c) decide when the order
is ready to auto-confirm.

No third-party SDK — we call the Anthropic Messages API over HTTPS with the
`requests` library that is already a project dependency.
"""
from __future__ import annotations

import json
import logging

import requests
from django.conf import settings

from core.business_date import get_business_date
from inventory.models import MenuItem
from pos.services.menu_stock import build_pos_menu_stock

logger = logging.getLogger(__name__)

_API_URL = 'https://api.anthropic.com/v1/messages'
_API_VERSION = '2023-06-01'
_TIMEOUT = 40
_MAX_TOKENS = 1024


class VoiceAgentError(Exception):
    pass


# ---------------------------------------------------------------------------
# Menu snapshot
# ---------------------------------------------------------------------------

def build_menu_snapshot(stock_date=None):
    """Compact, LLM-friendly list of orderable items with live stock."""
    stock_date = stock_date or get_business_date()
    menu_items = (
        MenuItem.objects.filter(is_active=True, is_available=True, is_deleted=False)
        .defer('image_data')
        .select_related('category')
        .order_by('category__category_name', 'item_name')
    )
    rows = build_pos_menu_stock(menu_items, stock_date)
    snapshot = []
    for row in rows:
        item = row.item
        if row.tracked:
            if row.expired:
                availability = 'expired'
            elif row.sold_out:
                availability = 'sold_out'
            else:
                availability = 'available'
            remaining = row.remaining
        else:
            availability = 'available'  # untracked = open item, always sellable
            remaining = None
        snapshot.append({
            'id': item.id,
            'name': item.item_name,
            'name_bn': item.item_name_bn or '',
            'category': item.category.category_name if item.category_id else '',
            'price': float(row.unit_price),
            'availability': availability,
            'remaining': remaining,
        })
    return snapshot


# ---------------------------------------------------------------------------
# Prompt + tool schema
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """তুমি "{canteen}"-এর একজন পেশাদার নারী বিক্রয় ও কাস্টমার কেয়ার সহকারী।
তুমি একজন অভিজ্ঞ ক্যান্টিন অ্যাটেন্ড্যান্টের মতো উষ্ণ, ভদ্র, আত্মবিশ্বাসী ও স্পষ্ট কণ্ঠে বাংলায় কথা বলো।
নিজের কোনো নাম বলবে না এবং সালাম/আসসালামু আলাইকুম বলবে না — সরাসরি ভদ্রভাবে সাহায্য করো।
গ্রাহককে "স্যার/আপা" সম্বোধন করে সম্মান দেখাও, স্বাভাবিক ও আন্তরিক থাকো — যন্ত্রের মতো নয়, একজন সহায়ক মানুষের মতো।

গ্রাহক: {customer}

আজকের মেনু ও স্টক (JSON):
{menu_json}

নিয়মাবলি:
1. প্রতিটি টার্নে অবশ্যই `submit_turn` টুল কল করবে — এর বাইরে কোনো টেক্সট লিখবে না।
2. গ্রাহকের কথা থেকে বুঝে নাও সে কী চায়। শুধু মেনুতে থাকা আইটেম অর্ডার করা যাবে; নাম বাংলা/ইংরেজি যেভাবেই বলুক মিলিয়ে নাও।
3. কোনো আইটেমের পরিমাণ (কয়টা) বলা না থাকলে আগে সেটাই বিনয়ের সাথে জিজ্ঞেস করো — যেমন "কয় কাপ কফি দেবো?" — তখন `needs_more_info` = true রাখো, `ready_to_confirm` = false।
4. পরিমাণ পাওয়ার পর ওই আইটেম যোগ করে পরের আইটেম জানতে চাও — যেমন "ঠিক আছে, আপনার পরের আইটেম বলুন।"
5. স্টক নিয়ম কড়াভাবে মানবে:
   - availability "sold_out" বা "expired" হলে ওই আইটেম দেওয়া যাবে না — দুঃখ প্রকাশ করে বিকল্প সাজেস্ট করো।
   - `remaining` সংখ্যার বেশি চাইলে যতটা আছে ততটাই অফার করো এবং জানাও।
6. `items` সবসময় বর্তমান পুরো অর্ডারের তালিকা — আগের আইটেমসহ (id ও quantity)। কিছু বাদ দিতে চাইলে তালিকা থেকে সরিয়ে দাও।
7. গ্রাহক "আর কিছু লাগবে না" জাতীয় কথা বললে সংক্ষেপে যোগফল বলো (আইটেম, পরিমাণ, মোট টাকা) এবং বলো "কনফার্ম করতে বলুন — অর্ডার কনফার্ম করো।"
8. গ্রাহক অর্ডার শেষ/কনফার্ম করতে চাইলে — এবং অন্তত একটি আইটেম থাকলে — `ready_to_confirm` = true দাও এবং সংক্ষেপে মোট টাকা বলে ধন্যবাদ জানাও। নিচের যেকোনো ধরনের কথা কনফার্ম হিসেবে ধরবে:
   - "অর্ডার কনফার্ম করো" / "কনফার্ম" / "কনফার্ম করো"
   - "অর্ডার শেষ করো" / "অর্ডার শেষ" / "শেষ করো"
   - "এবার বন্ধ করো" / "বন্ধ করো"
   - "আমার কাজ শেষ" / "হয়ে গেছে" / "ব্যাস"
   - "স্লিপ করো" / "স্লিপ দাও" / "রশিদ দাও" / "প্রিন্ট করো"
   - "হ্যাঁ" / "ঠিক আছে" / "দাও" (যখন যোগফল নিশ্চিত করার প্রশ্নের উত্তরে বলা হয়)
   কোনো আইটেম না থাকলে কনফার্ম করবে না — বিনয়ের সাথে আগে অর্ডার নিতে চাও।
9. উত্তর ছোট রাখো (এক-দুই বাক্য), কারণ এটি ভয়েসে পড়া হবে। টাকার অঙ্ক "টাকা" শব্দে বলো।
10. বিক্রয় ও কাস্টমার কেয়ার আচরণ (স্বাভাবিকভাবে, জোর করে নয়):
    - শুরুতে আন্তরিকভাবে স্বাগত জানাও।
    - কখনো কখনো ভদ্রভাবে একটি মানানসই আইটেম সাজেস্ট করো — যেমন চায়ের সাথে "সাথে একটা সিঙ্গারা দেবো কি?" — তবে একবারের বেশি চাপ দিও না, গ্রাহক না বললে সঙ্গে সঙ্গে সম্মান করো।
    - প্রতিটি আইটেমের জন্য সংক্ষিপ্ত ইতিবাচক স্বীকৃতি দাও — "জি, ঠিক আছে", "চমৎকার পছন্দ"।
    - শেষে আন্তরিকভাবে ধন্যবাদ দাও এবং টোকেনের জন্য অপেক্ষা করতে বলো।
    - সবসময় শান্ত, পেশাদার ও সহানুভূতিশীল থাকো।

উদাহরণ কথোপকথন:
গ্রাহক: "একটা কফি" → তুমি: "জি, কয় কাপ কফি দেবো?" (needs_more_info=true)
গ্রাহক: "দুইটা" → তুমি: "দুই কাপ কফি, ঠিক আছে। সাথে একটা বিস্কুট নেবেন কি?" (items: কফি x2)
গ্রাহক: "না, একটা চা দাও" → তুমি: "চমৎকার, একটা চা যোগ করলাম। আর কিছু লাগবে?" (items: কফি x2, চা x1)
গ্রাহক: "আর কিছু না, কনফার্ম অর্ডার" → তুমি: "আপনার মোট হলো ৬৫ টাকা। ধন্যবাদ, অর্ডার কনফার্ম হয়ে গেছে।" (ready_to_confirm=true)
"""

_TOOL = {
    'name': 'submit_turn',
    'description': 'Reply to the customer and report the current order state.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'reply_bn': {
                'type': 'string',
                'description': 'Short friendly reply to speak to the customer, in Bangla.',
            },
            'items': {
                'type': 'array',
                'description': 'The full current order. Empty until the customer names an item.',
                'items': {
                    'type': 'object',
                    'properties': {
                        'menu_item_id': {'type': 'integer'},
                        'quantity': {'type': 'integer', 'minimum': 1},
                    },
                    'required': ['menu_item_id', 'quantity'],
                },
            },
            'needs_more_info': {
                'type': 'boolean',
                'description': 'True when waiting on the customer (e.g. quantity or a choice).',
            },
            'ready_to_confirm': {
                'type': 'boolean',
                'description': 'True only when the customer has agreed to place the order.',
            },
        },
        'required': ['reply_bn', 'items', 'needs_more_info', 'ready_to_confirm'],
    },
}


# ---------------------------------------------------------------------------
# Claude call + validation
# ---------------------------------------------------------------------------

def run_voice_turn(*, history, customer_name=None, stock_date=None):
    """Run one assistant turn using whichever LLM integration is active.

    history: list of {'role': 'user'|'assistant', 'content': str}
    Returns a dict the view can hand straight back to the browser.
    """
    from core.api_registry import get_active_llm
    cfg = get_active_llm()
    if not cfg.is_configured:
        raise VoiceAgentError('Voice assistant not configured — add an active API key')

    stock_date = stock_date or get_business_date()
    menu = build_menu_snapshot(stock_date)
    menu_by_id = {row['id']: row for row in menu}

    system = _SYSTEM_TEMPLATE.format(
        canteen='MC-Canteen',
        customer=customer_name or 'গ্রাহক',
        menu_json=json.dumps(menu, ensure_ascii=False),
    )

    messages = [
        {'role': m['role'], 'content': m['content']}
        for m in history
        if m.get('role') in ('user', 'assistant') and (m.get('content') or '').strip()
    ]
    if not messages:
        raise VoiceAgentError('No conversation input')

    if cfg.provider == 'gemini':
        turn = _call_gemini(cfg, system, messages)
    elif cfg.provider == 'anthropic':
        turn = _call_anthropic(cfg, system, messages)
    else:
        raise VoiceAgentError(f'Unsupported voice provider: {cfg.provider}')

    return _finalize(turn, menu_by_id)


# ---- Anthropic (Claude) -----------------------------------------------------

def _call_anthropic(cfg, system, messages):
    model = cfg.api_model or 'claude-sonnet-5'
    payload = {
        'model': model,
        'max_tokens': _MAX_TOKENS,
        'system': system,
        'messages': messages,
        'tools': [_TOOL],
        'tool_choice': {'type': 'tool', 'name': 'submit_turn'},
    }
    headers = {
        'x-api-key': cfg.api_key,
        'anthropic-version': _API_VERSION,
        'content-type': 'application/json',
    }
    endpoint = cfg.base_url or _API_URL
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        logger.exception('Claude request failed')
        raise VoiceAgentError('Voice assistant unreachable') from exc
    if resp.status_code != 200:
        logger.error('Claude API %s: %s', resp.status_code, resp.text[:500])
        raise VoiceAgentError(f'Voice assistant error ({resp.status_code})')

    for block in resp.json().get('content', []):
        if block.get('type') == 'tool_use' and block.get('name') == 'submit_turn':
            return block.get('input') or {}
    raise VoiceAgentError('Voice assistant returned no order')


# ---- Google AI Studio (Gemini) ---------------------------------------------

_GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models'

# JSON response schema mirroring the Anthropic tool (OpenAPI subset for Gemini).
_GEMINI_SCHEMA = {
    'type': 'object',
    'properties': {
        'reply_bn': {'type': 'string'},
        'items': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'menu_item_id': {'type': 'integer'},
                    'quantity': {'type': 'integer'},
                },
                'required': ['menu_item_id', 'quantity'],
            },
        },
        'needs_more_info': {'type': 'boolean'},
        'ready_to_confirm': {'type': 'boolean'},
    },
    'required': ['reply_bn', 'items', 'needs_more_info', 'ready_to_confirm'],
}


def _call_gemini(cfg, system, messages):
    model = cfg.api_model or 'gemini-2.0-flash'
    contents = [
        {'role': 'model' if m['role'] == 'assistant' else 'user',
         'parts': [{'text': m['content']}]}
        for m in messages
    ]
    payload = {
        'systemInstruction': {'parts': [{'text': system}]},
        'contents': contents,
        'generationConfig': {
            'responseMimeType': 'application/json',
            'responseSchema': _GEMINI_SCHEMA,
            'maxOutputTokens': _MAX_TOKENS,
        },
    }
    base = cfg.base_url or _GEMINI_BASE
    endpoint = f'{base.rstrip("/")}/{model}:generateContent'
    headers = {'content-type': 'application/json', 'x-goog-api-key': cfg.api_key}
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        logger.exception('Gemini request failed')
        raise VoiceAgentError('Voice assistant unreachable') from exc
    if resp.status_code != 200:
        logger.error('Gemini API %s: %s', resp.status_code, resp.text[:500])
        raise VoiceAgentError(f'Voice assistant error ({resp.status_code})')

    data = resp.json()
    try:
        parts = data['candidates'][0]['content']['parts']
        text = ''.join(p.get('text', '') for p in parts)
        return json.loads(text)
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        logger.error('Gemini parse error: %s | %s', exc, str(data)[:400])
        raise VoiceAgentError('Voice assistant returned no order') from exc
    raise VoiceAgentError('Voice assistant returned no order')


def _finalize(turn, menu_by_id):
    """Validate Claude's items against live stock and compute totals."""
    reply = (turn.get('reply_bn') or '').strip()
    ready = bool(turn.get('ready_to_confirm'))
    needs_more = bool(turn.get('needs_more_info'))

    items = []
    issues = []
    subtotal = 0.0
    for raw in (turn.get('items') or []):
        try:
            mid = int(raw.get('menu_item_id'))
            qty = int(raw.get('quantity'))
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        row = menu_by_id.get(mid)
        if not row:
            continue
        capped = qty
        if row['availability'] != 'available':
            issues.append(f"{row['name']} এখন পাওয়া যাচ্ছে না")
            continue
        if row['remaining'] is not None and qty > row['remaining']:
            capped = row['remaining']
            issues.append(f"{row['name']} আছে মাত্র {row['remaining']}টি")
            if capped <= 0:
                continue
        line_total = round(row['price'] * capped, 2)
        subtotal += line_total
        items.append({
            'id': mid,
            'name': row['name'],
            'name_bn': row['name_bn'],
            'price': row['price'],
            'qty': capped,
            'line_total': line_total,
        })

    # If stock forced items away, it is not safe to auto-confirm this turn.
    if issues:
        ready = False

    return {
        'success': True,
        'reply': reply,
        'items': items,
        'subtotal': round(subtotal, 2),
        'qty_total': sum(i['qty'] for i in items),
        'needs_more_info': needs_more,
        'ready_to_confirm': ready and bool(items),
        'issues': issues,
    }
