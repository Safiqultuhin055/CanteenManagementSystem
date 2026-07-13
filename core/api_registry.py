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
LLM_PROVIDERS = ('anthropic', 'gemini', 'openai')
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


def get_active_llm() -> ApiConfig:
    """Return the active chat/LLM integration — whichever provider is enabled.

    Picks the active, non-deleted row among LLM_PROVIDERS (is_default first,
    then most recently updated). Falls back to Anthropic settings/.env.
    """
    cached = cache.get(_LLM_CACHE_KEY)
    if cached:
        return ApiConfig(**cached)

    from core.models import ApiIntegration
    base = ApiIntegration.objects.filter(
        provider__in=LLM_PROVIDERS, is_deleted=False,
    )
    row = (
        base.filter(is_active=True)
        .exclude(api_key__isnull=True)
        .exclude(api_key='')
        .order_by('-is_default', '-updated_at', '-id')
        .first()
    )
    if row:
        extra = {}
        if row.extra_config:
            try:
                extra = json.loads(row.extra_config)
            except (ValueError, TypeError):
                extra = {}
        config = ApiConfig(
            provider=row.provider,
            api_key=(row.api_key or '').strip(),
            api_model=(row.api_model or '').strip(),
            base_url=(row.base_url or '').strip(),
            extra=extra,
            source='db',
        )
    elif base.exists():
        # Rows exist but none are active → intentionally disabled. Do NOT fall
        # back to .env, so toggling every row off truly turns the API off.
        config = ApiConfig('none', '', '', '', {}, 'none')
    else:
        # Empty table (fresh install) → allow .env fallback so nothing breaks.
        config = _resolve_from_settings('anthropic') or ApiConfig(
            'anthropic', '', '', '', {}, 'none')

    cache.set(_LLM_CACHE_KEY, config.__dict__, _CACHE_TTL)
    return config


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
