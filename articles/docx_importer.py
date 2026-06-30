import html
import posixpath
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from django.utils.text import slugify


NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
}


@dataclass
class DocxArticleContent:
    title: str
    summary: str
    html: str
    cover_image_path: str


def convert_docx_to_article_content(uploaded_file):
    uploaded_file.seek(0)
    with zipfile.ZipFile(uploaded_file) as docx:
        document = ElementTree.fromstring(docx.read('word/document.xml'))
        relationships = _read_relationships(docx)
        image_cache = {}
        fragments = []
        plain_blocks = []
        title = ''
        first_image_path = ''

        body = document.find('w:body', NS)
        if body is None:
            return DocxArticleContent(
                title=Path(uploaded_file.name).stem or 'Word 导入文章',
                summary='Word 导入内容',
                html='<div class="docx-article"></div>',
                cover_image_path='',
            )

        for child in body:
            tag = _local_name(child.tag)
            if tag == 'p':
                fragment, text, heading_level, image_path = _paragraph_to_html(docx, child, relationships, image_cache)
                if fragment:
                    fragments.append(fragment)
                if text:
                    plain_blocks.append(text)
                    if heading_level == 1 and not title:
                        title = text[:120]
                if image_path and not first_image_path:
                    first_image_path = image_path
            elif tag == 'tbl':
                fragment, text, image_path = _table_to_html(docx, child, relationships, image_cache)
                if fragment:
                    fragments.append(fragment)
                if text:
                    plain_blocks.append(text)
                if image_path and not first_image_path:
                    first_image_path = image_path

    fallback_title = Path(uploaded_file.name).stem or 'Word 导入文章'
    title = title or (plain_blocks[0][:120] if plain_blocks else fallback_title)
    summary = next((block for block in plain_blocks if block != title), '')
    summary = (summary or 'Word 导入内容')[:300]
    return DocxArticleContent(
        title=title,
        summary=summary,
        html=f'<div class="docx-article">{"".join(fragments)}</div>',
        cover_image_path=first_image_path,
    )


def _read_relationships(docx):
    try:
        root = ElementTree.fromstring(docx.read('word/_rels/document.xml.rels'))
    except KeyError:
        return {}

    relationships = {}
    for relationship in root.findall('rel:Relationship', NS):
        rel_id = relationship.attrib.get('Id')
        target = relationship.attrib.get('Target', '')
        if rel_id and target:
            relationships[rel_id] = posixpath.normpath(posixpath.join('word', target))
    return relationships


def _paragraph_to_html(docx, paragraph, relationships, image_cache):
    heading_level = _heading_level(paragraph)
    run_html = []
    plain_text = []
    first_image_path = ''

    for run in paragraph.findall('w:r', NS):
        fragment, text, image_path = _run_to_html(docx, run, relationships, image_cache)
        if fragment:
            run_html.append(fragment)
        if text:
            plain_text.append(text)
        if image_path and not first_image_path:
            first_image_path = image_path

    text = ''.join(plain_text).strip()
    content = ''.join(run_html).strip()
    if not content:
        return '', text, heading_level, first_image_path

    if heading_level:
        level = min(heading_level, 3)
        return f'<h{level}>{content}</h{level}>', text, heading_level, first_image_path

    if _is_list_item(paragraph):
        return f'<ul><li>{content}</li></ul>', text, heading_level, first_image_path

    return f'<p>{content}</p>', text, heading_level, first_image_path


def _table_to_html(docx, table, relationships, image_cache):
    rows = []
    texts = []
    first_image_path = ''
    for row in table.findall('w:tr', NS):
        cells = []
        for cell in row.findall('w:tc', NS):
            cell_fragments = []
            for paragraph in cell.findall('w:p', NS):
                fragment, text, _, image_path = _paragraph_to_html(docx, paragraph, relationships, image_cache)
                if fragment:
                    cell_fragments.append(fragment)
                if text:
                    texts.append(text)
                if image_path and not first_image_path:
                    first_image_path = image_path
            cells.append(f'<td>{"".join(cell_fragments)}</td>')
        if cells:
            rows.append(f'<tr>{"".join(cells)}</tr>')
    return f'<table>{"".join(rows)}</table>' if rows else '', ' '.join(texts).strip(), first_image_path


def _run_to_html(docx, run, relationships, image_cache):
    parts = []
    text_parts = []
    first_image_path = ''

    for node in run:
        name = _local_name(node.tag)
        if name == 't':
            text = node.text or ''
            parts.append(html.escape(text))
            text_parts.append(text)
        elif name == 'tab':
            parts.append('&#9;')
            text_parts.append('\t')
        elif name == 'br':
            parts.append('<br>')
            text_parts.append('\n')
        elif name == 'drawing':
            for blip in node.findall('.//a:blip', NS):
                rel_id = blip.attrib.get(f'{{{NS["r"]}}}embed')
                image_path, image_url = _save_docx_image(docx, relationships.get(rel_id), image_cache)
                if image_url:
                    parts.append(f'<figure><img src="{html.escape(image_url)}" alt=""></figure>')
                if image_path and not first_image_path:
                    first_image_path = image_path

    content = ''.join(parts)
    if content:
        content = _apply_run_format(run, content)
    return content, ''.join(text_parts), first_image_path


def _apply_run_format(run, content):
    props = run.find('w:rPr', NS)
    if props is None:
        return content

    if props.find('w:b', NS) is not None:
        content = f'<strong>{content}</strong>'
    if props.find('w:i', NS) is not None:
        content = f'<em>{content}</em>'
    if props.find('w:u', NS) is not None:
        content = f'<u>{content}</u>'

    color = props.find('w:color', NS)
    color_value = color.attrib.get(f'{{{NS["w"]}}}val') if color is not None else ''
    if color_value and color_value.lower() != 'auto':
        content = f'<span style="color: #{html.escape(color_value)}">{content}</span>'

    return content


def _save_docx_image(docx, image_member, image_cache):
    if not image_member:
        return '', ''
    if image_member in image_cache:
        return image_cache[image_member]
    image_bytes = _read_zip_member_bytes(docx, image_member)
    if not image_bytes:
        return '', ''

    original_name = Path(image_member).name
    safe_name = slugify(Path(original_name).stem, allow_unicode=True) or 'image'
    extension = Path(original_name).suffix.lower()
    date_path = timezone.localtime().strftime('%Y/%m')
    storage_path = f'news/docx/{date_path}/{safe_name}{extension}'
    saved_path = default_storage.save(storage_path, ContentFile(image_bytes))
    image_cache[image_member] = (saved_path, default_storage.url(saved_path))
    return image_cache[image_member]


def _read_zip_member_bytes(docx, member):
    try:
        return docx.read(member)
    except KeyError:
        return b''
    except zipfile.BadZipFile:
        try:
            with docx.open(member) as source:
                if hasattr(source, '_expected_crc'):
                    source._expected_crc = None
                return source.read()
        except (KeyError, RuntimeError, zipfile.BadZipFile, zlib.error):
            return b''


def _heading_level(paragraph):
    style = paragraph.find('w:pPr/w:pStyle', NS)
    style_value = style.attrib.get(f'{{{NS["w"]}}}val', '') if style is not None else ''
    if style_value.lower().startswith('heading'):
        return int(''.join(ch for ch in style_value if ch.isdigit()) or '1')
    if style_value in {'标题1', '標題1'}:
        return 1
    if style_value in {'标题2', '標題2'}:
        return 2
    return 0


def _is_list_item(paragraph):
    return paragraph.find('w:pPr/w:numPr', NS) is not None


def _local_name(tag):
    return tag.rsplit('}', 1)[-1]
