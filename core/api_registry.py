"""Resolve third-party API credentials at runtime.

Order of resolution for a provider:
  1. Active row in api_integrations (is_default first, newest next).
  2. Fallback to Django settings / .env (so existing config keeps working).

Cached briefly so hot paths don't hit the DB every call; the admin clears the
cache on save/delete.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

_CACHE_PREFIX = 'api_integration:v1:'
_CACHE_TTL = 300  # seconds

# provider -> (settings key for api_key, settings key for model, default model)
_SETTINGS_FALLBACK = {
    'anthropic': ('ANTHROPIC_API_KEY', 'ANTHROPIC_MODEL', 'claude-sonnet-5'),
    'openai': ('OPENAI_API_KEY', 'OPENAI_MODEL', ''),
    'gemini': ('GEMINI_API_KEY', 'GEMINI_MODEL', 'gemini-2.0-flash'),
}

# Chat/LLM providers usable by the voice assistant. The active one runs.
LLM_PROVIDERS = ('anthropic', 'gemini', 'local', 'openai')
_LLM_CACHE_KEY = f'{_CACHE_PREFIX}__active_llm__'


@dataclass
class ApiConfig:
    provider: str
    api_key: str
    api_model: str
    base_url: str
    extra: dict
    source: str  # 'db' | 'settings' | 'none'

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


def _cache_key(provider: str) -> str:
    return f'{_CACHE_PREFIX}{provider}'


def invalidate(provider: str | None = None) -> None:
    cache.delete(_LLM_CACHE_KEY)   # active-LLM choice may change on any edit
    if provider:
        cache.delete(_cache_key(provider))
    else:
        for p in _SETTINGS_FALLBACK:
            cache.delete(_cache_key(p))


def _row_to_cfg(row) -> ApiConfig:
    extra = {}
    if row.extra_config:
        try:
            extra = json.loads(row.extra_config)
        except (ValueError, TypeError):
            extra = {}
    return ApiConfig(
        provider=row.provider,
        api_key=(row.api_key or '').strip(),
        api_model=(row.api_model or '').strip(),
        base_url=(row.base_url or '').strip(),
        extra=extra,
        source='db',
    )


def get_active_llm_chain() -> list[ApiConfig]:
    """All active LLM integrations, best-first (is_default, then newest).

    The voice assistant tries them in order so a failing/expired provider
    (e.g. a dead local key) falls through to the next working one.

    Not cached: admin toggles must take effect immediately, and LocMemCache is
    per-process so a cross-process invalidate can't be relied on.
    """
    from core.models import ApiIntegration
    base = ApiIntegration.objects.filter(
        provider__in=LLM_PROVIDERS, is_deleted=False,
    )
    rows = list(
        base.filter(is_active=True)
        .exclude(api_key__isnull=True)
        .exclude(api_key='')
        .order_by('-is_default', '-updated_at', '-id')
    )
    if rows:
        return [_row_to_cfg(r) for r in rows]
    if base.exists():
        # Rows exist but none active → intentionally disabled (no .env fallback).
        return []
    # Empty table (fresh install) → allow .env fallback so nothing breaks.
    fb = _resolve_from_settings('anthropic')
    return [fb] if fb else []


def get_active_llm() -> ApiConfig:
    """The primary active LLM integration (first of the chain)."""
    chain = get_active_llm_chain()
    return chain[0] if chain else ApiConfig('none', '', '', '', {}, 'none')


def get_integration(provider: str) -> ApiConfig:
    """Return the active config for a provider (DB first, then settings)."""
    key = _cache_key(provider)
    cached = cache.get(key)
    if cached:
        return ApiConfig(**cached)

    config = _resolve_from_db(provider) or _resolve_from_settings(provider)
    if config is None:
        config = ApiConfig(provider, '', '', '', {}, 'none')

    cache.set(key, config.__dict__, _CACHE_TTL)
    return config


def _resolve_from_db(provider: str):
    # Imported lazily so this module is import-safe before Django apps load.
    from core.models import ApiIntegration
    row = (
        ApiIntegration.objects.filter(
            provider=provider, is_active=True, is_deleted=False,
        )
        .order_by('-is_default', '-updated_at', '-id')
        .first()
    )
    if not row or not (row.api_key or '').strip():
        return None

    extra = {}
    if row.extra_config:
        try:
            extra = json.loads(row.extra_config)
        except (ValueError, TypeError):
            extra = {}

    return ApiConfig(
        provider=provider,
        api_key=(row.api_key or '').strip(),
        api_model=(row.api_model or '').strip(),
        base_url=(row.base_url or '').strip(),
        extra=extra,
        source='db',
    )


def _resolve_from_settings(provider: str):
    spec = _SETTINGS_FALLBACK.get(provider)
    if not spec:
        return None
    key_name, model_name, default_model = spec
    api_key = getattr(settings, key_name, '') or ''
    if not api_key:
        return None
    return ApiConfig(
        provider=provider,
        api_key=api_key,
        api_model=getattr(settings, model_name, default_model) or default_model,
        base_url='',
        extra={},
        source='settings',
    )
