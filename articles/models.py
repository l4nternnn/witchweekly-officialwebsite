from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Article(models.Model):
    SECTION_NEWS = 'news'
    SECTION_TRIVIA = 'trivia'
    SECTION_OFFICIAL_WORKS = 'official_works'
    BODY_FORMAT_TEXT = 'text'
    BODY_FORMAT_MARKDOWN = 'markdown'
    BODY_FORMAT_HTML = 'html'

    SECTION_CHOICES = (
        (SECTION_NEWS, '新闻'),
        (SECTION_TRIVIA, '趣闻轶事'),
        (SECTION_OFFICIAL_WORKS, '官方作品'),
    )
    BODY_FORMAT_CHOICES = (
        (BODY_FORMAT_TEXT, '纯文本'),
        (BODY_FORMAT_MARKDOWN, 'Markdown'),
        (BODY_FORMAT_HTML, 'HTML'),
    )

    section = models.CharField('所属页面', max_length=32, choices=SECTION_CHOICES, db_index=True)
    title = models.CharField('标题', max_length=120)
    slug = models.SlugField('链接标识', max_length=140, unique=True, blank=True)
    summary = models.TextField('摘要', max_length=300)
    body = models.TextField('正文', blank=True)
    body_format = models.CharField(
        '正文格式',
        max_length=20,
        choices=BODY_FORMAT_CHOICES,
        default=BODY_FORMAT_TEXT,
        help_text='列表页只显示摘要，详情页按此格式显示完整正文。',
    )
    cover_image = models.FileField(
        '封面图片',
        upload_to='news/covers/%Y/%m/',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'gif'])],
        help_text='支持 jpg、png、webp、gif。',
    )
    source_name = models.CharField('来源名称', max_length=80, blank=True)
    source_url = models.URLField('来源链接', blank=True)
    published_at = models.DateTimeField('发布时间', default=timezone.now, db_index=True)
    is_published = models.BooleanField('发布到前台', default=True, db_index=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '新闻条目'
        verbose_name_plural = '新闻条目'
        ordering = ('-published_at', '-created_at')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or 'article'
            slug = base_slug
            index = 2
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{index}'
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Submission(models.Model):
    KIND_SUBMISSION = 'submission'
    KIND_FEEDBACK = 'feedback'
    KIND_CHOICES = (
        (KIND_SUBMISSION, '投稿'),
        (KIND_FEEDBACK, '反馈建议'),
    )

    STATUS_PENDING = 'pending'
    STATUS_REVIEWING = 'reviewing'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = (
        (STATUS_PENDING, '待审核'),
        (STATUS_REVIEWING, '润色中'),
        (STATUS_PUBLISHED, '已发布'),
        (STATUS_ARCHIVED, '已归档'),
    )

    kind = models.CharField('类型', max_length=20, choices=KIND_CHOICES, default=KIND_SUBMISSION)
    target_section = models.CharField(
        '目标页面',
        max_length=32,
        choices=Article.SECTION_CHOICES,
        default=Article.SECTION_NEWS,
    )
    title = models.CharField('标题', max_length=120)
    author_name = models.CharField('投稿人称呼', max_length=80, blank=True)
    contact = models.CharField('联系方式', max_length=120, blank=True)
    summary = models.TextField('摘要/简述', max_length=300, blank=True)
    body = models.TextField('正文/反馈内容')
    source_url = models.URLField('来源链接', blank=True)
    attachment = models.FileField(
        '附件图片',
        upload_to='submissions/%Y/%m/',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'gif'])],
        help_text='支持 jpg、png、webp、gif。',
    )
    status = models.CharField('审核状态', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    editor_title = models.CharField('润色后标题', max_length=120, blank=True)
    editor_summary = models.TextField('润色后摘要', max_length=300, blank=True)
    editor_body = models.TextField('润色后正文', blank=True)
    editor_notes = models.TextField('管理员备注', blank=True)
    published_article = models.ForeignKey(
        Article,
        verbose_name='发布后的新闻条目',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='source_submissions',
    )
    created_at = models.DateTimeField('提交时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '投稿与反馈'
        verbose_name_plural = '投稿与反馈'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.get_kind_display()}：{self.title}'

    @property
    def publish_title(self):
        return self.editor_title or self.title

    @property
    def publish_summary(self):
        return self.editor_summary or self.summary or self.body[:120]

    @property
    def publish_body(self):
        return self.editor_body or self.body
