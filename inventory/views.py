from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from inventory.services.menu_image_cache import fetch_menu_item_image


@require_GET
def menu_item_image(request, pk):
    """Serve menu item photo from cache or SQL BLOB (browser cache + ETag)."""
    payload = fetch_menu_item_image(pk)
    if not payload:
        raise Http404('No image stored for this menu item')

    if request.META.get('HTTP_IF_NONE_MATCH') == payload.etag:
        response = HttpResponse(status=304)
        response['ETag'] = payload.etag
        response['Cache-Control'] = 'public, max-age=604800, immutable'
        return response

    response = HttpResponse(payload.data, content_type=payload.content_type)
    response['ETag'] = payload.etag
    response['Cache-Control'] = 'public, max-age=604800, immutable'
    return response
