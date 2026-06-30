import io
import tempfile
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .docx_importer import convert_docx_to_article_content
from .docx_importer import _read_zip_member_bytes, _save_docx_image
from .models import Article


def make_docx_fixture():
    document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>导入标题</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>这是摘要文字。</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:rPr><w:b/></w:rPr><w:t>加粗文字</w:t></w:r>
      <w:r><w:t> 和普通文字</w:t></w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:drawing>
          <wp:inline>
            <a:graphic>
              <a:graphicData>
                <a:blip r:embed="rId5"/>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>
  </w:body>
</w:document>'''
    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId5"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    Target="media/image1.png"/>
</Relationships>'''
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as docx:
        docx.writestr('[Content_Types].xml', '')
        docx.writestr('word/document.xml', document_xml)
        docx.writestr('word/_rels/document.xml.rels', rels_xml)
        docx.writestr('word/media/image1.png', b'fake image bytes')
    buffer.seek(0)
    return buffer.getvalue()


class DocxImportTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)

    def test_docx_import_preserves_text_format_and_images(self):
        uploaded = SimpleUploadedFile(
            'weekly.docx',
            make_docx_fixture(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )

        result = convert_docx_to_article_content(uploaded)

        self.assertEqual(result.title, '导入标题')
        self.assertEqual(result.summary, '这是摘要文字。')
        self.assertIn('<h1>导入标题</h1>', result.html)
        self.assertIn('<strong>加粗文字</strong>', result.html)
        self.assertIn('<img src="/media/news/docx/', result.html)
        self.assertTrue(result.cover_image_path.startswith('news/docx/'))

    def test_article_detail_api_returns_full_body_format(self):
        article = Article.objects.create(
            section=Article.SECTION_NEWS,
            title='详情测试',
            summary='外部摘要',
            body='<div class="docx-article"><p>内部完整正文</p></div>',
            body_format=Article.BODY_FORMAT_HTML,
            published_at=timezone.now(),
            is_published=True,
        )

        response = self.client.get(reverse('article-detail', args=(article.slug,)))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['summary'], '外部摘要')
        self.assertEqual(payload['bodyFormat'], 'html')
        self.assertIn('内部完整正文', payload['body'])

    def test_docx_import_reads_embedded_image_even_when_crc_is_bad(self):
        class CorruptedDocx:
            def read(self, member):
                raise zipfile.BadZipFile(f"Bad CRC-32 for file {member!r}")

            def open(self, member):
                return TolerantMember()

        class TolerantMember:
            def __enter__(self):
                self._expected_crc = 123
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            def read(self):
                if self._expected_crc is not None:
                    raise zipfile.BadZipFile('CRC still checked')
                return b'image bytes'

        image_bytes = _read_zip_member_bytes(CorruptedDocx(), 'word/media/image1.png')

        self.assertEqual(image_bytes, b'image bytes')

    def test_docx_import_saves_embedded_image_even_when_crc_is_bad(self):
        class CorruptedDocx:
            def read(self, member):
                raise zipfile.BadZipFile(f"Bad CRC-32 for file {member!r}")

            def open(self, member):
                return TolerantMember()

        class TolerantMember:
            def __enter__(self):
                self._expected_crc = 123
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            def read(self):
                if self._expected_crc is not None:
                    raise zipfile.BadZipFile('CRC still checked')
                return b'image bytes'

        image_path, image_url = _save_docx_image(CorruptedDocx(), 'word/media/image1.png', {})

        self.assertTrue(image_path.startswith('news/docx/'))
        self.assertTrue(image_url.startswith('/media/news/docx/'))


class ArticleSearchTests(TestCase):
    def setUp(self):
        Article.objects.create(
            section=Article.SECTION_NEWS,
            title='魔女周刊发布',
            summary='普通摘要',
            body='普通正文',
            is_published=True,
            published_at=timezone.datetime(2026, 6, 30, 10, 0, tzinfo=timezone.get_current_timezone()),
        )
        Article.objects.create(
            section=Article.SECTION_TRIVIA,
            title='圈内观察',
            summary='普通摘要',
            body='这里写着隐藏关键词',
            is_published=True,
            published_at=timezone.datetime(2026, 6, 30, 9, 0, tzinfo=timezone.get_current_timezone()),
        )
        Article.objects.create(
            section=Article.SECTION_OFFICIAL_WORKS,
            title='官方作品索引',
            summary='公开素材',
            body='普通正文',
            is_published=True,
            published_at=timezone.datetime(2026, 6, 30, 8, 0, tzinfo=timezone.get_current_timezone()),
        )
        Article.objects.create(
            section=Article.SECTION_NEWS,
            title='隐藏关键词未发布',
            summary='不应出现',
            body='隐藏关键词',
            is_published=False,
        )

    def result_titles(self, response):
        self.assertEqual(response.status_code, 200)
        return [item['title'] for item in response.json()['results']]

    def test_simple_search_matches_title_only_across_all_sections(self):
        response = self.client.get(reverse('article-list'), {'q': '官方', 'mode': 'simple', 'section': 'news'})

        self.assertEqual(self.result_titles(response), ['官方作品索引'])

    def test_simple_search_does_not_match_body(self):
        response = self.client.get(reverse('article-list'), {'q': '隐藏关键词', 'mode': 'simple'})

        self.assertEqual(self.result_titles(response), [])

    def test_advanced_search_matches_full_text_across_all_sections(self):
        response = self.client.get(reverse('article-list'), {'q': '隐藏关键词', 'mode': 'advanced', 'section': 'news'})

        self.assertEqual(self.result_titles(response), ['圈内观察'])
