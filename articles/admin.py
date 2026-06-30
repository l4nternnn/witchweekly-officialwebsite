import re
import zipfile
from pathlib import Path

from django import forms
from django.contrib import admin, messages
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils import timezone

from .docx_importer import convert_docx_to_article_content
from .models import Article, Submission


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return [single_file_clean(data, initial)] if data else []


class MarkdownImportForm(forms.Form):
    section = forms.ChoiceField(label='所属页面', choices=Article.SECTION_CHOICES)
    markdown_file = forms.FileField(
        label='Markdown 文件',
        help_text='上传 .md 文件。标题默认取第一个 # 一级标题，正文会保留 Markdown 格式。',
    )
    images = MultipleFileField(
        label='关联图片',
        required=False,
        widget=MultipleFileInput(attrs={'multiple': True}),
        help_text='可同时上传 Markdown 中引用的图片。文件名匹配时会自动替换为 /media/ 地址。',
    )
    source_name = forms.CharField(label='来源名称', required=False)
    source_url = forms.URLField(label='来源链接', required=False)
    is_published = forms.BooleanField(label='导入后立即发布到前台', required=False, initial=True)


class DocxImportForm(forms.Form):
    section = forms.ChoiceField(label='所属页面', choices=Article.SECTION_CHOICES)
    docx_file = forms.FileField(
        label='Word 文件',
        help_text='上传 .docx 文件。系统会转换为站内 HTML 正文，并保存文档中的图片。',
    )
    source_name = forms.CharField(label='来源名称', required=False)
    source_url = forms.URLField(label='来源链接', required=False)
    is_published = forms.BooleanField(label='导入后立即发布到前台', required=False, initial=True)


def _extract_markdown_title(markdown_text, fallback_name):
    for line in markdown_text.splitlines():
        match = re.match(r'^#\s+(.+)$', line.strip())
        if match:
            return match.group(1).strip()[:120]
    return Path(fallback_name).stem[:120] or 'Markdown 导入文章'


def _extract_markdown_summary(markdown_text):
    for line in markdown_text.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith('#') or cleaned.startswith('!['):
            continue
        cleaned = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', cleaned)
        cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
        cleaned = re.sub(r'[`*_>#-]+', '', cleaned).strip()
        if cleaned:
            return cleaned[:300]
    return 'Markdown 导入内容'


def _save_markdown_images(images):
    image_map = {}
    first_image_path = ''
    date_path = timezone.localtime().strftime('%Y/%m')

    for image in images:
        original_name = Path(image.name).name
        safe_name = slugify(Path(original_name).stem, allow_unicode=True) or 'image'
        extension = Path(original_name).suffix.lower()
        storage_path = f'news/markdown/{date_path}/{safe_name}{extension}'
        saved_path = default_storage.save(storage_path, image)
        image_map[original_name] = default_storage.url(saved_path)
        image_map[Path(original_name).name] = default_storage.url(saved_path)
        if not first_image_path:
            first_image_path = saved_path

    return image_map, first_image_path


def _rewrite_markdown_image_urls(markdown_text, image_map):
    def replace(match):
        alt_text = match.group(1)
        image_path = match.group(2).strip()
        matched_url = image_map.get(image_path) or image_map.get(Path(image_path).name)
        if not matched_url:
            return match.group(0)
        return f'![{alt_text}]({matched_url})'

    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace, markdown_text)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'published_at', 'is_published', 'cover_preview', 'updated_at')
    list_filter = ('section', 'is_published', 'published_at')
    search_fields = ('title', 'summary', 'body', 'source_name')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ('-published_at', '-created_at')
    list_editable = ('is_published',)
    readonly_fields = ('cover_preview', 'created_at', 'updated_at')
    change_list_template = 'admin/articles/article/change_list.html'
    fieldsets = (
        ('基础内容', {
            'fields': ('section', 'title', 'slug', 'summary', 'body_format', 'body'),
        }),
        ('封面与来源', {
            'fields': ('cover_image', 'cover_preview', 'source_name', 'source_url'),
        }),
        ('发布设置', {
            'fields': ('published_at', 'is_published'),
        }),
        ('系统信息', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-md/',
                self.admin_site.admin_view(self.import_markdown_view),
                name='articles_article_import_md',
            ),
            path(
                'import-docx/',
                self.admin_site.admin_view(self.import_docx_view),
                name='articles_article_import_docx',
            ),
        ]
        return custom_urls + urls

    def import_markdown_view(self, request):
        if request.method == 'POST':
            form = MarkdownImportForm(request.POST, request.FILES)
            if form.is_valid():
                markdown_file = form.cleaned_data['markdown_file']
                if not markdown_file.name.lower().endswith('.md'):
                    form.add_error('markdown_file', '请上传 .md 文件。')
                else:
                    markdown_text = markdown_file.read().decode('utf-8-sig', errors='replace')
                    image_map, first_image_path = _save_markdown_images(form.cleaned_data['images'])
                    body = _rewrite_markdown_image_urls(markdown_text, image_map)
                    article = Article.objects.create(
                        section=form.cleaned_data['section'],
                        title=_extract_markdown_title(markdown_text, markdown_file.name),
                        summary=_extract_markdown_summary(markdown_text),
                        body=body,
                        body_format=Article.BODY_FORMAT_MARKDOWN,
                        cover_image=first_image_path,
                        source_name=form.cleaned_data['source_name'],
                        source_url=form.cleaned_data['source_url'],
                        is_published=form.cleaned_data['is_published'],
                    )
                    messages.success(request, f'已导入 Markdown：{article.title}')
                    return redirect(reverse('admin:articles_article_change', args=(article.pk,)))
        else:
            form = MarkdownImportForm()

        return render(
            request,
            'admin/articles/article/import_md.html',
            {
                'form': form,
                'title': '导入 Markdown',
                'opts': self.model._meta,
            },
        )

    def import_docx_view(self, request):
        if request.method == 'POST':
            form = DocxImportForm(request.POST, request.FILES)
            if form.is_valid():
                docx_file = form.cleaned_data['docx_file']
                if not docx_file.name.lower().endswith('.docx'):
                    form.add_error('docx_file', '请上传 .docx 文件。')
                else:
                    try:
                        converted = convert_docx_to_article_content(docx_file)
                    except (KeyError, zipfile.BadZipFile):
                        form.add_error('docx_file', '这个 Word 文件结构损坏，无法读取正文。请重新保存为 .docx 后再导入。')
                    else:
                        article = Article.objects.create(
                            section=form.cleaned_data['section'],
                            title=converted.title,
                            summary=converted.summary,
                            body=converted.html,
                            body_format=Article.BODY_FORMAT_HTML,
                            cover_image=converted.cover_image_path,
                            source_name=form.cleaned_data['source_name'],
                            source_url=form.cleaned_data['source_url'],
                            is_published=form.cleaned_data['is_published'],
                        )
                        messages.success(request, f'已导入 Word：{article.title}')
                        return redirect(reverse('admin:articles_article_change', args=(article.pk,)))
        else:
            form = DocxImportForm()

        return render(
            request,
            'admin/articles/article/import_docx.html',
            {
                'form': form,
                'title': '导入 Word',
                'opts': self.model._meta,
            },
        )

    @admin.display(description='封面预览')
    def cover_preview(self, obj):
        if not obj.cover_image:
            return '未上传'
        return format_html(
            '<img src="{}" style="width: 120px; max-height: 80px; object-fit: cover;" />',
            obj.cover_image.url,
        )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'target_section', 'status', 'author_name', 'created_at', 'published_article')
    list_filter = ('kind', 'target_section', 'status', 'created_at')
    search_fields = ('title', 'author_name', 'contact', 'summary', 'body', 'editor_notes')
    readonly_fields = ('attachment_preview', 'published_article', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ('mark_reviewing', 'publish_as_article', 'archive_submissions')
    fieldsets = (
        ('提交内容', {
            'fields': (
                'kind',
                'target_section',
                'title',
                'author_name',
                'contact',
                'summary',
                'body',
                'source_url',
                'attachment',
                'attachment_preview',
            ),
        }),
        ('审核与润色', {
            'fields': ('status', 'editor_title', 'editor_summary', 'editor_body', 'editor_notes'),
        }),
        ('发布记录', {
            'fields': ('published_article', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(description='附件预览')
    def attachment_preview(self, obj):
        if not obj.attachment:
            return '未上传'
        return format_html(
            '<img src="{}" style="width: 120px; max-height: 80px; object-fit: cover;" />',
            obj.attachment.url,
        )

    @admin.action(description='标记为润色中')
    def mark_reviewing(self, request, queryset):
        queryset.update(status=Submission.STATUS_REVIEWING)

    @admin.action(description='发布为新闻条目')
    def publish_as_article(self, request, queryset):
        created = 0
        for submission in queryset:
            if submission.kind != Submission.KIND_SUBMISSION or submission.published_article_id:
                continue
            article = Article.objects.create(
                section=submission.target_section,
                title=submission.publish_title,
                summary=submission.publish_summary,
                body=submission.publish_body,
                cover_image=submission.attachment,
                source_name=submission.author_name or '读者投稿',
                source_url=submission.source_url,
                is_published=True,
            )
            submission.published_article = article
            submission.status = Submission.STATUS_PUBLISHED
            submission.save(update_fields=('published_article', 'status', 'updated_at'))
            created += 1
        self.message_user(request, f'已发布 {created} 条新闻。')

    @admin.action(description='归档所选提交')
    def archive_submissions(self, request, queryset):
        queryset.update(status=Submission.STATUS_ARCHIVED)
