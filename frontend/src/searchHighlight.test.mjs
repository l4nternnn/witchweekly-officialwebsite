import assert from 'node:assert/strict'

import { highlightMatches } from './searchHighlight.js'

assert.equal(
  highlightMatches('魔女周刊新闻', '新闻'),
  '魔女周刊<mark class="search-hit">新闻</mark>',
)

assert.equal(
  highlightMatches('<新闻> & 趣闻', '新闻 趣闻'),
  '&lt;<mark class="search-hit">新闻</mark>&gt; &amp; <mark class="search-hit">趣闻</mark>',
)

assert.equal(
  highlightMatches('没有关键词时只做转义 <ok>', ''),
  '没有关键词时只做转义 &lt;ok&gt;',
)
