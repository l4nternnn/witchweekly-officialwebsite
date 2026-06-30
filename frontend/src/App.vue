<script setup>
import { computed, onMounted, ref } from 'vue'
import { highlightMatches } from './searchHighlight.js'

const navItems = [
  { label: '新闻', href: '/news/', key: 'news', apiSection: 'news' },
  { label: '趣闻轶事', href: '/trivia/', key: 'trivia', apiSection: 'trivia' },
  { label: '官方作品', href: '/official-works/', key: 'officialWorks', apiSection: 'official_works' },
  { label: '投稿与反馈', href: '/submit-feedback/', key: 'submitFeedback' },
]

const contentNavItems = navItems.filter((item) => item.apiSection)

const pageMeta = {
  home: {
    eyebrow: 'Latest Posts',
    title: '最新资讯',
    subtitle: '按发布时间倒序汇总全站新闻条目。',
  },
  search: {
    eyebrow: 'Search',
    title: '搜索结果',
    subtitle: '全站范围内检索新闻条目。',
  },
  news: {
    eyebrow: 'News Desk',
    title: '新闻',
    subtitle: '按发布时间倒序整理公开资讯、公告和资料来源。',
  },
  trivia: {
    eyebrow: 'Trivia Notes',
    title: '趣闻轶事',
    subtitle: '按发布时间倒序整理热点、考据、评论和话题复盘。',
  },
  officialWorks: {
    eyebrow: 'Official Works',
    title: '官方作品',
    subtitle: '按发布时间倒序整理官方视觉、设定资料和公开素材。',
  },
  submitFeedback: {
    eyebrow: 'Submission & Feedback',
    title: '投稿与反馈',
    subtitle: '向编辑部提交新闻线索、稿件或反馈建议。',
  },
}

const fallbackArticles = [
  {
    id: 'fallback-news-1',
    section: 'news',
    sectionLabel: '新闻',
    title: '本周公开资料索引该怎么整理',
    summary: '以来源、日期、关键词和摘要建立可回看档案。',
    publishedAt: '2026-06-30T09:30:00+08:00',
    sourceName: '魔女周刊编辑部',
  },
  {
    id: 'fallback-trivia-1',
    section: 'trivia',
    sectionLabel: '趣闻轶事',
    title: '热点讨论需要一张冷静的资料卡',
    summary: '先复盘事实，再表达观点，减少误会在圈内扩散。',
    publishedAt: '2026-06-29T18:20:00+08:00',
    sourceName: '魔女周刊编辑部',
  },
  {
    id: 'fallback-official-1',
    section: 'official_works',
    sectionLabel: '官方作品',
    title: '官方视觉与设定资料该如何归档',
    summary: '整理公开图像、设定说明、PV 截帧与来源信息。',
    publishedAt: '2026-06-28T15:00:00+08:00',
    sourceName: '魔女周刊编辑部',
  },
]

const editorNotes = [
  ['资料原则', '不编造未确认情报，正式内容应保留来源、时间和上下文。'],
  ['编辑口径', '评论可以有立场，但需要先把事实和观点分开。'],
  ['投稿方向', '最新资讯、资料整理、官方作品都可以成为新闻条目。', '/submit-feedback/'],
]

const siteMissions = [
  { text: '追踪《魔法少女的魔女审判》系列最新资讯' },
  { text: '联系圈内各大企划，使创作信息互通' },
  { text: '对热点话题进行评论，增进圈内氛围' },
  { text: '整理官方作品，让公开内容被更清晰地看到' },
]

const footerLinks = [
  { label: '首页', href: '/' },
  ...navItems.map((item) => ({ label: item.label, href: item.href })),
]

const contactEmail = 'contact@example.com'
const sourceRepositoryUrl = 'https://github.com/l4nternnn/witchweekly-officialwebsite'

const normalizePath = (path) => path.replace(/\/+$/, '')
const currentPath = normalizePath(window.location.pathname)
const pathSegments = window.location.pathname.split('/').filter(Boolean)
const sectionPath = pathSegments[0] || ''
const detailSlug = pathSegments[1] || ''
const activePage = navItems.find((item) => normalizePath(item.href) === `/${sectionPath}`)
const isSearchPage = computed(() => sectionPath === 'search')
const currentMeta = computed(() => pageMeta[isSearchPage.value ? 'search' : activePage?.key || 'home'])
const isSubmitFeedbackPage = computed(() => activePage?.key === 'submitFeedback')
const isArticleDetailPage = computed(() => Boolean(activePage?.apiSection && detailSlug))
const articles = ref([])
const currentArticle = ref(null)
const isLoading = ref(true)
const loadError = ref('')
const submissionStatus = ref('')
const submissionError = ref('')
const submissionAttachment = ref(null)
const initialSearchParams = new URLSearchParams(window.location.search)
const searchQuery = ref(initialSearchParams.get('q') || '')
const searchMode = ref(initialSearchParams.get('mode') === 'advanced' ? 'advanced' : 'simple')
const submissionForm = ref({
  kind: 'submission',
  targetSection: 'news',
  title: '',
  authorName: '',
  contact: '',
  summary: '',
  body: '',
  sourceUrl: '',
})

const sortedByTime = (items) =>
  [...items].sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime())

const displayArticles = computed(() => {
  if (isSearchPage.value) {
    return sortedByTime(articles.value)
  }
  const source = articles.value.length ? articles.value : fallbackArticles
  const filtered = activePage?.apiSection
    ? source.filter((item) => item.section === activePage.apiSection)
    : source
  return sortedByTime(filtered)
})

const relatedArticles = computed(() =>
  sortedByTime(articles.value)
    .filter((article) => article.slug !== currentArticle.value?.slug)
    .slice(0, 4)
)

const sectionPathByKey = {
  news: '/news/',
  trivia: '/trivia/',
  official_works: '/official-works/',
}

const fetchArticles = async () => {
  if (isSubmitFeedbackPage.value) {
    isLoading.value = false
    return
  }

  if (isSearchPage.value) {
    if (!searchQuery.value.trim()) {
      isLoading.value = false
      return
    }

    const params = new URLSearchParams()
    params.set('q', searchQuery.value.trim())
    params.set('mode', searchMode.value)
    params.set('limit', '50')

    try {
      const response = await fetch(`/api/news/?${params.toString()}`, {
        headers: { Accept: 'application/json' },
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const payload = await response.json()
      articles.value = Array.isArray(payload.results) ? payload.results : []
    } catch (error) {
      loadError.value = '暂时无法读取搜索结果。'
    } finally {
      isLoading.value = false
    }
    return
  }

  if (isArticleDetailPage.value) {
    try {
      const [response, relatedResponse] = await Promise.all([
        fetch(`/api/news/${encodeURIComponent(detailSlug)}/`, {
          headers: { Accept: 'application/json' },
        }),
        fetch(`/api/news/?section=${encodeURIComponent(activePage.apiSection)}&limit=8`, {
          headers: { Accept: 'application/json' },
        }),
      ])
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      currentArticle.value = await response.json()
      if (relatedResponse.ok) {
        const relatedPayload = await relatedResponse.json()
        articles.value = Array.isArray(relatedPayload.results) ? relatedPayload.results : []
      }
    } catch (error) {
      loadError.value = '暂时无法读取这篇新闻。'
    } finally {
      isLoading.value = false
    }
    return
  }

  const params = new URLSearchParams()
  params.set('limit', activePage ? '30' : '2')
  if (activePage?.apiSection) {
    params.set('section', activePage.apiSection)
  }

  try {
    const response = await fetch(`/api/news/?${params.toString()}`, {
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const payload = await response.json()
    articles.value = Array.isArray(payload.results) ? payload.results : []
  } catch (error) {
    loadError.value = '暂时无法读取后台新闻，正在显示前端占位内容。'
  } finally {
    isLoading.value = false
  }
}

const formatDate = (value) =>
  new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))

const articleLink = (article) => {
  const sectionPath = sectionPathByKey[article.section] || '/news/'
  return article.slug ? `${sectionPath}${encodeURIComponent(article.slug)}/` : sectionPath
}

const highlightedText = (value) => (isSearchPage.value ? highlightMatches(value, searchQuery.value) : highlightMatches(value, ''))

const submitSearch = () => {
  const query = searchQuery.value.trim()
  if (!query) {
    return
  }
  const params = new URLSearchParams()
  params.set('q', query)
  params.set('mode', searchMode.value)
  window.location.href = `/search/?${params.toString()}`
}

const escapeHtml = (value) =>
  String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')

const renderMarkdownLite = (value) => {
  const lines = String(value || '').split(/\r?\n/)
  return lines
    .map((line) => {
      const image = line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/)
      if (image) {
        return `<figure><img src="${escapeHtml(image[2])}" alt="${escapeHtml(image[1])}"></figure>`
      }
      const heading = line.match(/^(#{1,3})\s+(.+)$/)
      if (heading) {
        const level = heading[1].length
        return `<h${level}>${escapeHtml(heading[2])}</h${level}>`
      }
      return line.trim() ? `<p>${escapeHtml(line)}</p>` : ''
    })
    .join('')
}

const articleBodyHtml = computed(() => {
  if (!currentArticle.value) {
    return ''
  }
  if (currentArticle.value.bodyFormat === 'html') {
    return currentArticle.value.body
  }
  if (currentArticle.value.bodyFormat === 'markdown') {
    return renderMarkdownLite(currentArticle.value.body)
  }
  return String(currentArticle.value.body || '')
    .split(/\r?\n/)
    .map((line) => (line.trim() ? `<p>${escapeHtml(line)}</p>` : ''))
    .join('')
})

const submitContribution = async () => {
  submissionStatus.value = ''
  submissionError.value = ''

  try {
    const formData = new FormData()
    Object.entries(submissionForm.value).forEach(([key, value]) => {
      formData.append(key, value)
    })
    if (submissionAttachment.value) {
      formData.append('attachment', submissionAttachment.value)
    }

    const response = await fetch('/api/submissions/', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
      body: formData,
    })
    const payload = await response.json()
    if (!response.ok) {
      throw new Error(payload.error || '提交失败，请稍后再试。')
    }
    submissionStatus.value = payload.message || '已收到提交。'
    submissionForm.value = {
      kind: 'submission',
      targetSection: 'news',
      title: '',
      authorName: '',
      contact: '',
      summary: '',
      body: '',
      sourceUrl: '',
    }
    submissionAttachment.value = null
  } catch (error) {
    submissionError.value = error.message || '提交失败，请稍后再试。'
  }
}

const updateAttachment = (event) => {
  submissionAttachment.value = event.target.files?.[0] || null
}

onMounted(fetchArticles)
</script>

<template>
  <main class="ww-site">
    <div class="top-strip">
      <span>魔女周刊 Witch Weekly</span>
      <span>中文 / 同人企划 / ACGN</span>
    </div>

    <header class="masthead">
      <a class="brand" href="/">
        <span class="brand-mark">W</span>
        <span>
          <strong>魔女周刊</strong>
          <small>Witch Weekly</small>
        </span>
      </a>

      <div class="masthead-note">
        <span>非官方资讯站</span>
        <strong>让资讯、评论与创作互相抵达</strong>
      </div>

      <form class="search-box" @submit.prevent="submitSearch">
        <span>Search</span>
        <div class="search-row">
          <select v-model="searchMode" aria-label="搜索模式">
            <option value="simple">简单</option>
            <option value="advanced">高级</option>
          </select>
          <input v-model="searchQuery" type="search" placeholder="输入关键词" />
          <button type="submit">搜索</button>
        </div>
      </form>
    </header>

    <nav class="nav-bar" aria-label="主导航">
      <a href="/" :aria-current="!activePage ? 'page' : undefined">首页</a>
      <a
        v-for="item in navItems"
        :key="item.key"
        :href="item.href"
        :aria-current="activePage?.key === item.key ? 'page' : undefined"
      >
        {{ item.label }}
      </a>
    </nav>

    <section class="ticker">
      <strong>Trending Now</strong>
      <span>所有页面均按发布时间倒序展示新闻条目，内容由后台统一维护。</span>
    </section>

    <section v-if="isSubmitFeedbackPage" class="submit-page">
      <div class="section-title">
        <p>{{ currentMeta.eyebrow }}</p>
        <h1>{{ currentMeta.title }}</h1>
      </div>

      <div class="submit-layout">
        <form class="submission-form" @submit.prevent="submitContribution">
          <label>
            <span>提交类型</span>
            <select v-model="submissionForm.kind">
              <option value="submission">投稿</option>
              <option value="feedback">反馈建议</option>
            </select>
          </label>

          <label>
            <span>目标页面</span>
            <select v-model="submissionForm.targetSection">
              <option value="news">新闻</option>
              <option value="trivia">趣闻轶事</option>
              <option value="official_works">官方作品</option>
            </select>
          </label>

          <label>
            <span>标题</span>
            <input v-model="submissionForm.title" type="text" required />
          </label>

          <label>
            <span>投稿人称呼</span>
            <input v-model="submissionForm.authorName" type="text" />
          </label>

          <label>
            <span>联系方式</span>
            <input v-model="submissionForm.contact" type="text" placeholder="邮箱、社交账号或其他联系方式" />
          </label>

          <label>
            <span>摘要</span>
            <textarea v-model="submissionForm.summary" rows="3" />
          </label>

          <label>
            <span>正文 / 反馈内容</span>
            <textarea v-model="submissionForm.body" rows="8" required />
          </label>

          <label>
            <span>来源链接</span>
            <input v-model="submissionForm.sourceUrl" type="url" placeholder="https://..." />
          </label>

          <label>
            <span>图片附件</span>
            <input type="file" accept=".jpg,.jpeg,.png,.webp,.gif" @change="updateAttachment" />
          </label>

          <button type="submit">提交给编辑部</button>
          <p v-if="submissionStatus" class="form-success">{{ submissionStatus }}</p>
          <p v-if="submissionError" class="form-error">{{ submissionError }}</p>
        </form>

        <aside class="feedback-panel">
          <h2>反馈建议</h2>
          <p>如果只是想反馈站点问题、提出选题建议或补充来源，也可以通过邮箱联系编辑部。</p>
          <a :href="`mailto:${contactEmail}`">{{ contactEmail }}</a>
          <p>邮箱暂为占位符，正式联系方式会在后续补充。</p>

          <h2>处理流程</h2>
          <ol>
            <li>读者提交稿件或反馈。</li>
            <li>管理员在后台审核、润色和补充来源。</li>
            <li>确认后发布为对应页面的新闻条目。</li>
          </ol>
        </aside>
      </div>
    </section>

    <section v-else-if="isArticleDetailPage" class="article-detail-page">
      <p v-if="loadError" class="status-text">{{ loadError }}</p>
      <p v-else-if="isLoading" class="status-text">正在读取完整正文...</p>

      <div v-else-if="currentArticle" class="article-detail-shell">
        <aside class="detail-side detail-nav-panel">
          <p>Sections</p>
          <h2>栏目导航</h2>
          <nav aria-label="详情页栏目导航">
            <a
              v-for="item in contentNavItems"
              :key="item.key"
              :href="item.href"
              :aria-current="currentArticle.section === item.apiSection ? 'page' : undefined"
            >
              {{ item.label }}
            </a>
          </nav>
          <a class="side-submit-link" href="/submit-feedback/">投稿与反馈</a>
        </aside>

        <article class="article-detail">
          <a class="back-link" :href="sectionPathByKey[currentArticle.section] || '/news/'">返回{{ currentArticle.sectionLabel }}</a>
          <div class="article-meta">
            <span>{{ currentArticle.sectionLabel }}</span>
            <time :datetime="currentArticle.publishedAt">{{ formatDate(currentArticle.publishedAt) }}</time>
          </div>
          <h1>{{ currentArticle.title }}</h1>
          <p class="detail-summary">{{ currentArticle.summary }}</p>
          <img
            v-if="currentArticle.coverImage"
            class="detail-cover"
            :src="currentArticle.coverImage"
            :alt="currentArticle.title"
          />
          <div class="detail-body" v-html="articleBodyHtml"></div>
        </article>

        <aside class="detail-side related-panel">
          <p>Related</p>
          <h2>同栏目最新</h2>
          <div class="detail-info">
            <span>{{ currentArticle.sectionLabel }}</span>
            <time :datetime="currentArticle.publishedAt">{{ formatDate(currentArticle.publishedAt) }}</time>
            <small v-if="currentArticle.sourceName">来源：{{ currentArticle.sourceName }}</small>
          </div>
          <div class="related-list">
            <a v-for="article in relatedArticles" :key="article.id" :href="articleLink(article)">
              <strong>{{ article.title }}</strong>
              <time :datetime="article.publishedAt">{{ formatDate(article.publishedAt) }}</time>
            </a>
            <span v-if="!relatedArticles.length">暂无其他新闻。</span>
          </div>
        </aside>
      </div>
    </section>

    <div v-else :class="activePage || isSearchPage ? 'page-layout' : 'home-layout'">
      <section class="news-board">
        <div class="section-title">
          <p>{{ currentMeta.eyebrow }}</p>
          <h1>{{ currentMeta.title }}</h1>
        </div>

        <p v-if="isSearchPage && searchQuery" class="search-summary">
          {{ searchMode === 'advanced' ? '高级搜索' : '简单搜索' }}：{{ searchQuery }}
        </p>
        <p v-else-if="isSearchPage" class="search-summary">请输入关键词开始搜索。</p>

        <p v-if="loadError" class="status-text">{{ loadError }}</p>
        <p v-else-if="isLoading" class="status-text">正在读取后台新闻...</p>

        <div class="article-list">
          <article v-for="article in displayArticles" :key="article.id">
            <a class="article-card" :href="articleLink(article)" :aria-label="`查看：${article.title}`">
              <img
                v-if="article.coverImage"
                class="article-cover"
                :src="article.coverImage"
                :alt="article.title"
              />
              <div class="article-main">
                <div class="article-meta">
                  <span>{{ article.sectionLabel }}</span>
                  <time :datetime="article.publishedAt">{{ formatDate(article.publishedAt) }}</time>
                </div>
                <h2 v-html="highlightedText(article.title)"></h2>
                <p v-html="highlightedText(article.summary)"></p>
                <div class="article-footer">
                  <small v-if="article.sourceName">来源：<span v-html="highlightedText(article.sourceName)"></span></small>
                </div>
              </div>
            </a>
          </article>
        </div>

        <p v-if="!displayArticles.length && !isLoading" class="empty-state">
          {{ isSearchPage ? '暂无搜索结果。' : '暂无新闻条目。' }}
        </p>
      </section>

      <aside v-if="!activePage && !isSearchPage" class="sidebar">
        <h2>编辑部说明</h2>
        <div v-for="note in editorNotes" :key="note[0]" class="note-card">
          <strong>{{ note[0] }}</strong>
          <p>{{ note[1] }}</p>
          <a v-if="note[2]" :href="note[2]">前往投稿与反馈</a>
        </div>
      </aside>
    </div>

    <template v-if="!activePage && !isSearchPage">
      <section class="mission-section">
        <div class="section-title">
          <p>Editorial Charter</p>
          <h1>我们要做的事</h1>
        </div>
        <ol>
          <li v-for="item in siteMissions" :key="item.text">
            <a v-if="item.href" :href="item.href">{{ item.text }}</a>
            <span v-else>{{ item.text }}</span>
          </li>
        </ol>
      </section>

      <section class="submit-band">
        <div>
          <p>Submission & Cooperation</p>
          <h2>投稿、联系与反馈入口预留</h2>
        </div>
        <a href="/submit-feedback/">前往投稿与反馈</a>
      </section>
    </template>

    <footer class="footer">
      <section class="footer-about">
        <strong>魔女周刊 Witch Weekly</strong>
        <p>
          面向《魔法少女的魔女审判》同好与 ACGN 兴趣用户的非官方中文资讯站，
          用周刊式编辑方法整理资讯、评论、趣闻与官方作品资料。
        </p>
      </section>

      <section>
        <h2>站点地图</h2>
        <nav class="footer-links" aria-label="页脚站点地图">
          <a v-for="link in footerLinks" :key="link.href" :href="link.href">{{ link.label }}</a>
        </nav>
      </section>

      <section>
        <h2>内容说明</h2>
        <p>新闻条目由后台统一维护，按发布时间倒序展示。</p>
        <p>资料整理以公开来源为准，评论内容会尽量区分事实与观点。</p>
      </section>

      <section>
        <h2>投稿联系</h2>
        <p>
          可通过
          <a href="/submit-feedback/">投稿与反馈</a>
          页面提交投稿、纠错、授权说明与联络反馈。
        </p>
        <a class="source-button" :href="sourceRepositoryUrl" target="_blank" rel="noreferrer">本站源码</a>
      </section>
    </footer>
  </main>
</template>
