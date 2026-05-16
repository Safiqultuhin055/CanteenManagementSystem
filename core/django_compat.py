"""
Compatibility fixes for Django running on Python 3.14+.

Django 5.0.x BaseContext.__copy__ uses copy(super()) which breaks on Python 3.14
('super' object has no attribute 'dicts'). Patch to the correct copy semantics.
"""

from copy import copy as copy_copy


def patch_django_template_context_copy():
    try:
        from django.template import context as template_context
    except ImportError:
        return

    if getattr(template_context.BaseContext.__copy__, '_cms_patched', False):
        return

    def _basecontext_copy(self):
        duplicate = object.__new__(self.__class__)
        duplicate.__dict__ = copy_copy(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    _basecontext_copy._cms_patched = True
    template_context.BaseContext.__copy__ = _basecontext_copy


# Apply as early as possible when Django is importable.
patch_django_template_context_copy()
