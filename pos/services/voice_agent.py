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
import re

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

_SYSTEM_TEMPLATE = """তুমি "{canteen}"-এর একজন দক্ষ, পেশাদার নারী বিক্রয় ও কাস্টমার কেয়ার সহকারী।
একজন অভিজ্ঞ ক্যান্টিন অ্যাটেন্ড্যান্টের মতো উষ্ণ, ভদ্র, আত্মবিশ্বাসী ও স্পষ্ট কণ্ঠে সবসময় শুদ্ধ বাংলায় কথা বলো — সাবলীল, স্বাভাবিক ও আন্তরিক, যন্ত্রের মতো নয়।
নিজের কোনো নাম বলবে না, সালাম/আসসালামু আলাইকুম বা কোনো ধর্মীয় সম্ভাষণ ব্যবহার করবে না — সরাসরি ভদ্রভাবে সাহায্য করো।
গ্রাহককে "স্যার/আপা" সম্বোধন করে সম্মান দেখাও। শান্ত, পেশাদার, সহানুভূতিশীল ও ধৈর্যশীল থাকো — কখনো তর্ক বা তাড়া দিও না।

গ্রাহক: {customer}

আজকের মেনু ও স্টক (JSON):
{menu_json}

── কার্যপ্রণালি ──
1. প্রতিটি টার্নে অবশ্যই `submit_turn` টুল কল করবে — এর বাইরে কোনো টেক্সট, ব্যাখ্যা বা markdown লিখবে না।
2. গ্রাহকের কথা বুঝে নাও সে কী চায়। শুধু আজকের মেনুতে থাকা আইটেমই অর্ডার করা যাবে; নাম বাংলা/ইংরেজি/মিশ্র যেভাবেই বলুক, বানানে ভুল থাকলেও নিকটতম আইটেমের সাথে মিলিয়ে নাও।
3. গ্রাহক যদি এক বাক্যে একাধিক আইটেম ও পরিমাণ একসাথে বলে (যেমন "দুইটা কফি আর একটা সমুচা"), সবগুলো একসাথে বুঝে `items`-এ যোগ করো — একটা একটা করে জিজ্ঞেস করে সময় নষ্ট করবে না।
4. পরিমাণ (কয়টা/কত কাপ) স্পষ্ট না থাকলে শুধু ওইটুকুই বিনয়ের সাথে জিজ্ঞেস করো — যেমন "জি, কয় কাপ কফি দেবো?" — তখন `needs_more_info` = true, `ready_to_confirm` = false। পরিমাণ পরিষ্কার থাকলে অযথা আবার জিজ্ঞেস করবে না।
5. পরিমাণ পাওয়ার পর সংক্ষেপে স্বীকার করে পরের আইটেম জানতে চাও — যেমন "জি, দুই কাপ কফি যোগ করলাম। আর কিছু লাগবে, স্যার?"
6. সংশোধন/বাতিল সঠিকভাবে সামলাও: গ্রাহক পরিমাণ বদলাতে বললে (যেমন "কফি তিনটা করো") ওই লাইনের quantity আপডেট করো; বাদ দিতে বললে ("চা বাদ দাও") তালিকা থেকে সরাও; "সব বাতিল করো" বললে `items` খালি করো।
7. স্টক নিয়ম কড়াভাবে মানবে:
   - availability "sold_out" বা "expired" হলে ওই আইটেম কোনোভাবেই দেওয়া যাবে না — বিনয়ের সাথে দুঃখ প্রকাশ করে একটি মানানসই বিকল্প সাজেস্ট করো।
   - `left` (remaining) সংখ্যার বেশি চাইলে যতটা আছে ততটাই অফার করো এবং সীমাটা জানাও।
   - দাম সবসময় মেনুর JSON থেকে নেবে; নিজে কোনো দাম বানাবে না।
8. `items` সবসময় বর্তমান পুরো অর্ডারের সম্পূর্ণ তালিকা — আগের সব আইটেমসহ (menu_item_id ও quantity)। আগের আইটেম ভুলে যাবে না, প্রতি টার্নে পুরো তালিকা ফেরত দেবে।
9. গ্রাহক "আর কিছু লাগবে না" জাতীয় কথা বললে সংক্ষেপে যোগফল বলো (কী কী, কয়টা, মোট কত টাকা) এবং কনফার্ম করতে অনুরোধ করো — "কনফার্ম করতে বললেই অর্ডার পাকা করে দিচ্ছি।" এই মুহূর্তে `ready_to_confirm` = false রাখো।
10. গ্রাহক অর্ডার শেষ/কনফার্ম করতে চাইলে — এবং অন্তত একটি আইটেম থাকলে — `ready_to_confirm` = true দাও, সংক্ষেপে মোট টাকা বলে আন্তরিকভাবে ধন্যবাদ দাও। নিচের যেকোনো ধরনের কথা কনফার্ম হিসেবে ধরবে:
    - "অর্ডার কনফার্ম করো" / "কনফার্ম" / "কনফার্ম করো"
    - "অর্ডার শেষ করো" / "অর্ডার শেষ" / "শেষ করো"
    - "এবার বন্ধ করো" / "বন্ধ করো"
    - "আমার কাজ শেষ" / "হয়ে গেছে" / "ব্যাস"
    - "স্লিপ করো" / "স্লিপ দাও" / "রশিদ দাও" / "প্রিন্ট করো"
    - "হ্যাঁ" / "ঠিক আছে" / "দাও" (যখন যোগফল নিশ্চিত করার প্রশ্নের উত্তরে বলা হয়)
    কোনো আইটেম না থাকলে কখনো কনফার্ম করবে না — বিনয়ের সাথে আগে অর্ডার নিতে চাও।
11. উত্তর ছোট ও পরিষ্কার রাখো (এক-দুই বাক্য), কারণ এটি ভয়েসে পড়ে শোনানো হবে। সংখ্যা ও টাকার অঙ্ক শব্দে বলো — যেমন "পঁয়ষট্টি টাকা", "দুই কাপ"; কোনো ইমোজি, প্রতীক বা তালিকা-চিহ্ন ব্যবহার করবে না।
12. বিক্রয় ও কাস্টমার কেয়ার আচরণ (স্বাভাবিকভাবে, জোর করে নয়):
    - প্রতিটি আইটেমের জন্য সংক্ষিপ্ত ইতিবাচক স্বীকৃতি দাও — "জি, ঠিক আছে", "চমৎকার পছন্দ"।
    - সুযোগ বুঝে ভদ্রভাবে একটি মানানসই আইটেম সাজেস্ট করো — যেমন চায়ের সাথে "সাথে একটা সিঙ্গারা নেবেন কি?" — তবে পুরো কথোপকথনে একবারই, গ্রাহক না বললে সঙ্গে সঙ্গে সম্মান করো, দ্বিতীয়বার চাপ দিও না।
    - গ্রাহক বিভ্রান্ত হলে বা কিছু বুঝতে না পারলে ধৈর্য ধরে সহজ ভাষায় আবার বলো।
    - শেষে আন্তরিকভাবে ধন্যবাদ দাও এবং টোকেন/স্লিপের জন্য একটু অপেক্ষা করতে অনুরোধ করো।

── উদাহরণ কথোপকথন ──
গ্রাহক: "একটা কফি" → তুমি: "জি স্যার, কয় কাপ কফি দেবো?" (needs_more_info=true, items খালি)
গ্রাহক: "দুইটা" → তুমি: "জি, দুই কাপ কফি যোগ করলাম। সাথে একটা বিস্কুট নেবেন কি?" (items: কফি x2)
গ্রাহক: "না, আর একটা চা দাও" → তুমি: "চমৎকার, একটা চা যোগ করলাম। আর কিছু লাগবে?" (items: কফি x2, চা x1)
গ্রাহক: "কফিটা একটা করে দাও" → তুমি: "জি, কফি এক কাপ করে দিলাম। আর কিছু?" (items: কফি x1, চা x1)
গ্রাহক: "আর কিছু না" → তুমি: "আপনার অর্ডার এক কাপ কফি ও এক কাপ চা, মোট চল্লিশ টাকা। কনফার্ম করতে বললেই পাকা করে দিচ্ছি।" (needs_more_info=false, ready_to_confirm=false)
গ্রাহক: "কনফার্ম" → তুমি: "ধন্যবাদ স্যার, আপনার অর্ডার কনফার্ম হলো — মোট চল্লিশ টাকা। একটু অপেক্ষা করুন।" (ready_to_confirm=true)
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
    from core.api_registry import get_active_llm_chain
    chain = get_active_llm_chain()
    if not chain:
        raise VoiceAgentError('Voice assistant not configured — add an active API key')

    stock_date = stock_date or get_business_date()
    menu = build_menu_snapshot(stock_date)
    menu_by_id = {row['id']: row for row in menu}

    # Slim menu for the prompt (fewer tokens → faster). Keep only what the model
    # needs to match items and respect stock; full data stays in menu_by_id.
    menu_slim = [
        {'id': r['id'], 'name': r['name'], 'bn': r['name_bn'],
         'price': r['price'], 'avail': r['availability'], 'left': r['remaining']}
        for r in menu
    ]

    system = _SYSTEM_TEMPLATE.format(
        canteen='MC-Canteen',
        customer=customer_name or 'গ্রাহক',
        menu_json=json.dumps(menu_slim, ensure_ascii=False),
    )

    messages = [
        {'role': m['role'], 'content': m['content']}
        for m in history
        if m.get('role') in ('user', 'assistant') and (m.get('content') or '').strip()
    ]
    if not messages:
        raise VoiceAgentError('No conversation input')
    # Only the last few turns matter for the current order → less to process.
    messages = messages[-10:]

    # Try each active provider best-first; fall through on failure (e.g. a dead
    # key) so a misconfigured provider doesn't take voice ordering down.
    dispatch = {
        'gemini': _call_gemini,
        'anthropic': _call_anthropic,
        'local': _call_local,
    }
    last_error = None
    for cfg in chain:
        fn = dispatch.get(cfg.provider)
        if not fn:
            continue
        try:
            turn = fn(cfg, system, messages)
            result = _finalize(turn, menu_by_id)
            _log_voice_request(
                provider=cfg.provider,
                customer_name=customer_name,
                user_text=_last_user_text(messages),
                result=result,
            )
            return result
        except VoiceAgentError as exc:
            last_error = exc
            logger.warning('Provider %s failed (%s); trying next', cfg.provider, exc)
            continue
    raise last_error or VoiceAgentError('No usable voice provider')


def _last_user_text(messages):
    """The customer's most recent utterance in this turn's window."""
    for m in reversed(messages):
        if m.get('role') == 'user':
            return (m.get('content') or '').strip()
    return ''


def _log_voice_request(*, provider, customer_name, user_text, result):
    """Persist one voice turn for demand analysis. Best-effort — a logging
    failure must never break voice ordering, so all errors are swallowed."""
    try:
        from pos.models import VoiceRequestLog, VoiceRequestItem
        items = result.get('items') or []
        log = VoiceRequestLog.objects.create(
            customer_name=(customer_name or '').strip()[:300] or None,
            user_text=user_text or None,
            reply_text=result.get('reply') or None,
            provider=provider,
            item_count=len(items),
            qty_total=result.get('qty_total') or 0,
            subtotal=result.get('subtotal') or 0,
            needs_more_info=bool(result.get('needs_more_info')),
            ready_to_confirm=bool(result.get('ready_to_confirm')),
            issues='; '.join(result.get('issues') or []) or None,
        )
        rows = [
            VoiceRequestItem(
                voice_request_log_id=log.id,
                menu_item_id=it.get('id'),
                item_name=(it.get('name') or '')[:300] or None,
                item_name_bn=(it.get('name_bn') or '')[:300] or None,
                quantity=it.get('qty') or 0,
                unit_price=it.get('price') or 0,
                line_total=it.get('line_total') or 0,
            )
            for it in items
        ]
        if rows:
            VoiceRequestItem.objects.bulk_create(rows)
    except Exception:
        logger.exception('Voice request logging failed')


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


# ---- Local / self-hosted LLM gateway ---------------------------------------
# Plain prompt->text API (no native tool calling): POST {base}/v1/chat with an
# X-API-KEY header and {project, model, prompt, stream}. We ask the model to
# emit a single JSON object and parse it out of the returned text.

_JSON_INSTRUCTION = (
    '\n\nএখন গ্রাহকের শেষ কথার উত্তর তৈরি করো। কেবল একটি বৈধ JSON object আউটপুট করবে — '
    'কোনো markdown, কোড-ফেন্স (```), বা অতিরিক্ত লেখা নয়। ঠিক এই স্কিমা: '
    '{"reply_bn": "বাংলা উত্তর", "items": [{"menu_item_id": 0, "quantity": 0}], '
    '"needs_more_info": false, "ready_to_confirm": false}'
)


def _build_text_prompt(system, messages):
    lines = [system, '', 'কথোপকথন এখন পর্যন্ত:']
    for m in messages:
        who = 'গ্রাহক' if m['role'] == 'user' else 'সহকারী'
        lines.append(f'{who}: {m["content"]}')
    lines.append(_JSON_INSTRUCTION)
    return '\n'.join(lines)


def _parse_json_turn(text):
    t = (text or '').strip()
    if t.startswith('```'):
        t = re.sub(r'^```[a-zA-Z]*\s*', '', t)
        t = re.sub(r'\s*```$', '', t).strip()
    try:
        return json.loads(t)
    except (ValueError, TypeError):
        pass
    i, j = t.find('{'), t.rfind('}')
    if 0 <= i < j:
        try:
            return json.loads(t[i:j + 1])
        except (ValueError, TypeError):
            pass
    logger.error('Local LLM parse fail: %s', t[:400])
    raise VoiceAgentError('Voice assistant returned no order')


def _call_local(cfg, system, messages):
    model = cfg.api_model or 'gpt-oss:120b-cloud'
    base = cfg.base_url or 'http://localhost:8009'
    endpoint = f'{base.rstrip("/")}/v1/chat'
    payload = {
        'model': model,
        'prompt': _build_text_prompt(system, messages),
        'stream': False,
    }
    # Some gateways require a project field; include it only when configured.
    project = (cfg.extra or {}).get('project')
    if project:
        payload['project'] = project
    try:
        resp = requests.post(
            endpoint, headers={'X-API-KEY': cfg.api_key},
            json=payload, timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception('Local LLM request failed')
        raise VoiceAgentError('Voice assistant unreachable') from exc
    if resp.status_code != 200:
        logger.error('Local LLM %s: %s', resp.status_code, resp.text[:400])
        raise VoiceAgentError(f'Voice assistant error ({resp.status_code})')

    try:
        text = resp.json().get('response') or ''
    except ValueError:
        text = resp.text
    return _parse_json_turn(text)


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
