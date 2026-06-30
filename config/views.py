from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.views.static import serve


def _disable_cache(response):
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def vue_index(request, page=None, **kwargs):
    page_dir = {
        'news-detail': 'news',
        'trivia-detail': 'trivia',
        'official-works-detail': 'official-works',
    }.get(page, page or '')
    index_file = settings.BASE_DIR / 'frontend' / 'dist' / page_dir / 'index.html'
    if not index_file.exists():
        return HttpResponse('Vue frontend has not been built yet.', status=503)
    return _disable_cache(FileResponse(index_file.open('rb'), content_type='text/html'))


def vue_asset(request, path):
    response = serve(request, path, document_root=settings.BASE_DIR / 'frontend' / 'dist' / 'assets')
    return _disable_cache(response)
