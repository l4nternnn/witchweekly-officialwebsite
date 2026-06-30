import json

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Article, Submission


SECTION_ALIASES = {
    Article.SECTION_NEWS: Article.SECTION_NEWS,
    Article.SECTION_TRIVIA: Article.SECTION_TRIVIA,
    Article.SECTION_OFFICIAL_WORKS: Article.SECTION_OFFICIAL_WORKS,
    'official-works': Article.SECTION_OFFICIAL_WORKS,
    'officialWorks': Article.SECTION_OFFICIAL_WORKS,
}


def _article_payload(article, include_body=False):
    request = getattr(article, '_request', None)
    cover_url = ''
    if article.cover_image:
        cover_url = article.cover_image.url
        if request is not None:
            cover_url = request.build_absolute_uri(cover_url)

    payload = {
        'id': article.id,
        'section': article.section,
        'sectionLabel': article.get_section_display(),
        'title': article.title,
        'slug': article.slug,
        'summary': article.summary,
        'bodyFormat': article.body_format,
        'coverImage': cover_url,
        'sourceName': article.source_name,
        'sourceUrl': article.source_url,
        'publishedAt': article.published_at.isoformat(),
    }
    if include_body:
        payload['body'] = article.body
    return payload


def article_list(request):
    section = request.GET.get('section', '').strip()
    limit = request.GET.get('limit', '').strip()
    query = request.GET.get('q', '').strip()
    search_mode = request.GET.get('mode', 'simple').strip()
    queryset = Article.objects.filter(is_published=True).order_by('-published_at', '-created_at')

    if query:
        if search_mode == 'advanced':
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(body__icontains=query)
                | Q(source_name__icontains=query)
            )
        else:
            queryset = queryset.filter(title__icontains=query)
    elif section:
        normalized_section = SECTION_ALIASES.get(section)
        if normalized_section is None:
            return JsonResponse({'results': []})
        queryset = queryset.filter(section=normalized_section)

    if limit.isdigit():
        queryset = queryset[: max(1, min(int(limit), 50))]

    articles = list(queryset)
    for article in articles:
        article._request = request

    return JsonResponse({'results': [_article_payload(article) for article in articles]})


def article_detail(request, slug):
    try:
        article = Article.objects.get(slug=slug, is_published=True)
    except Article.DoesNotExist:
        return JsonResponse({'error': '新闻条目不存在。'}, status=404)

    article._request = request
    return JsonResponse(_article_payload(article, include_body=True))


@csrf_exempt
@require_POST
def submission_create(request):
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.POST
        files = request.FILES
    else:
        try:
            data = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': '请求内容不是有效 JSON。'}, status=400)
        files = {}

    kind = data.get('kind', Submission.KIND_SUBMISSION)
    target_section = data.get('targetSection', Article.SECTION_NEWS)
    title = data.get('title', '').strip()
    body = data.get('body', '').strip()

    if kind not in dict(Submission.KIND_CHOICES):
        return JsonResponse({'error': '提交类型无效。'}, status=400)
    if target_section not in dict(Article.SECTION_CHOICES):
        return JsonResponse({'error': '目标页面无效。'}, status=400)
    if not title or not body:
        return JsonResponse({'error': '标题和正文不能为空。'}, status=400)

    submission = Submission.objects.create(
        kind=kind,
        target_section=target_section,
        title=title,
        author_name=data.get('authorName', '').strip(),
        contact=data.get('contact', '').strip(),
        summary=data.get('summary', '').strip(),
        body=body,
        source_url=data.get('sourceUrl', '').strip(),
        attachment=files.get('attachment') if files else None,
    )

    return JsonResponse({
        'ok': True,
        'id': submission.id,
        'message': '已收到提交，管理员审核后会处理。',
    }, status=201)
