# Witch Weekly Official Website

魔女周刊官方网站源码。这个项目是一套围绕《魔法少女的魔女审判》同好内容建设的中文资讯站，目标是把新闻、趣闻、考据、评论、官方作品资料和读者投稿放在一个清晰、可维护的发布系统里。

站点采用“周刊式编辑部”的表达方式：前台像一份轻量电子报，强调栏目、时间线、来源和摘要；后台则面向内容维护者，提供新闻管理、投稿审核、Markdown 导入、Word 导入、封面预览和发布流程。

## 项目特点

- 前后台分离的开发体验，但生产环境可由 Django 统一托管前端构建产物。
- Vue/Vite 前台提供首页、搜索页、栏目页、详情页和投稿反馈页。
- Django Admin 作为内容编辑后台，使用 django-simpleui 改善管理界面。
- 新闻条目支持标题、摘要、正文、封面图、来源、发布时间和发布状态。
- 正文支持纯文本、Markdown 和 HTML 三种格式。
- 后台可直接导入 Markdown 文件，也可导入 Word `.docx` 文件并提取正文图片。
- 投稿表单支持新闻线索、反馈建议、来源链接和图片附件。
- 投稿内容可在后台审核、润色、归档，并一键发布为新闻条目。
- 搜索页支持简单搜索和高级搜索，关键词会在结果中红色高亮。
- 新闻卡片整卡可点击，封面、标题、摘要和按钮区域都能进入详情页。
- 项目已添加 MIT License，适合继续二次开发、部署或学习参考。

## 技术栈

### 后端

- Python
- Django 6.0.6
- django-simpleui 2026.1.13
- SQLite 默认本地数据库
- Django Admin 内容管理
- Django FileField 媒体上传

### 前端

- Vue 3
- Vite 8
- 原生 CSS
- 多页面构建入口
- Fetch API 调用 Django JSON 接口

### 开发与发布

- `requirements.txt` 管理 Python 依赖。
- `frontend/package-lock.json` 锁定前端依赖。
- `frontend/dist/` 为构建产物，由 Django 读取并返回。
- `DJANGO_SECRET_KEY` 可通过环境变量配置。
- 默认 SQLite 适合本地开发；生产环境可按 Django 标准方式切换数据库。

## 目录结构

```text
accounts/
  admin.py                  账号后台注册
  models.py                 自定义用户模型
  migrations/               账号相关迁移

articles/
  admin.py                  新闻与投稿后台管理、Markdown/Word 导入
  docx_importer.py          Word 文档转站内正文内容
  models.py                 Article 与 Submission 数据模型
  urls.py                   API 路由
  views.py                  新闻列表、新闻详情、投稿接口
  templates/admin/          后台自定义导入页面
  migrations/               内容模型迁移

config/
  settings.py               Django 设置
  urls.py                   站点路由、前台页面路由、API 和 Admin
  views.py                  Vue 构建产物托管视图
  asgi.py / wsgi.py         部署入口

frontend/
  src/App.vue               前台主应用
  src/style.css             全站样式
  src/searchHighlight.js    搜索关键词高亮逻辑
  src/searchHighlight.test.mjs
                            搜索高亮轻量测试
  public/                   favicon 与图标资源
  index.html                首页入口
  search/index.html         搜索页入口
  news/index.html           新闻栏目入口
  trivia/index.html         趣闻轶事栏目入口
  official-works/index.html 官方作品栏目入口
  submit-feedback/index.html
                            投稿反馈页入口
  vite.config.js            Vite 多页面构建配置

manage.py
requirements.txt
LICENSE
README.md
```

## 功能说明

### 首页

首页用于展示全站最新内容。默认从后端新闻接口读取最新条目，按发布时间倒序排列。页面右侧保留编辑部说明，帮助访客理解站点的资料原则、评论口径和投稿方向。

如果后端接口暂时不可用，前端会展示占位内容，避免页面完全空白。这适合早期开发和前端样式调试。

### 新闻栏目

新闻栏目对应后端 `news` 分区，主要用于发布公开资讯、公告、资料来源和站内整理内容。栏目页按发布时间倒序展示新闻卡片。

每张卡片包含栏目、发布时间、标题、摘要、来源和封面图。卡片整体可点击，鼠标悬停时会高亮，表示它是可进入详情页的内容块。

### 趣闻轶事

趣闻轶事栏目对应后端 `trivia` 分区，适合整理热点讨论、考据片段、评论复盘和轻量话题内容。它与新闻栏目使用同一套 Article 数据模型，因此可以共用后台维护、搜索和详情页能力。

### 官方作品

官方作品栏目对应后端 `official_works` 分区，适合整理公开视觉、设定资料、PV 截帧、官方素材和相关说明。内容结构与新闻栏目一致，但栏目标签、路由和页面标题独立。

### 搜索页

搜索页通过 URL 参数读取查询内容：

```text
/search/?q=关键词&mode=simple
/search/?q=关键词&mode=advanced
```

简单搜索只匹配标题。高级搜索会匹配标题、摘要、正文和来源名称。搜索结果中的关键词会以红色高亮显示，帮助用户快速定位命中位置。

搜索高亮逻辑位于 `frontend/src/searchHighlight.js`，会先做 HTML 转义，再插入 `<mark class="search-hit">`，减少直接拼接 HTML 带来的风险。

### 详情页

详情页通过栏目路径和文章 slug 访问：

```text
/news/<slug>/
/trivia/<slug>/
/official-works/<slug>/
```

详情页会展示完整标题、摘要、封面、正文、来源和同栏目最新内容。正文格式由后台的 `body_format` 决定：

- `text`：按换行拆成段落。
- `markdown`：支持轻量标题、段落和图片语法。
- `html`：用于 Word 导入或后台手动维护的富文本 HTML。

### 投稿与反馈

投稿与反馈页面向读者和内容贡献者。表单字段包括：

- 提交类型：投稿或反馈建议。
- 目标页面：新闻、趣闻轶事、官方作品。
- 标题。
- 投稿人称呼。
- 联系方式。
- 摘要。
- 正文或反馈内容。
- 来源链接。
- 图片附件。

提交后内容会进入 `Submission` 模型，管理员可在后台审核、润色、归档或发布为正式新闻条目。

## 后台管理

Django Admin 是当前项目的主要内容生产入口。管理员可以访问：

```text
/admin/
```

后台包含两个核心模型：`Article` 和 `Submission`。

### Article 新闻条目

新闻条目字段包括：

- 所属页面：新闻、趣闻轶事、官方作品。
- 标题与 slug。
- 摘要。
- 正文格式。
- 正文内容。
- 封面图片。
- 来源名称与来源链接。
- 发布时间。
- 是否发布到前台。

后台列表支持按栏目、发布状态和发布时间筛选，也支持搜索标题、摘要、正文和来源名称。封面图会在后台列表和详情里显示预览。

### Markdown 导入

后台新闻列表页提供 Markdown 导入入口。导入时可以选择栏目、上传 `.md` 文件、上传关联图片、填写来源名称和来源链接。

导入逻辑会：

1. 从第一个一级标题提取新闻标题。
2. 从首个有效正文段落提取摘要。
3. 保存关联图片。
4. 将 Markdown 图片路径替换为站内 `/media/` 地址。
5. 创建 `body_format=markdown` 的新闻条目。

### Word 导入

后台也提供 Word `.docx` 导入入口。导入逻辑会读取文档结构，转换正文 HTML，并保存文档中的图片。适合把已有图文稿件快速转为站内新闻。

Word 导入创建的文章会使用 `body_format=html`，前台详情页会直接渲染转换后的 HTML。

### Submission 投稿审核

投稿内容进入后台后，管理员可以：

- 标记为润色中。
- 填写编辑后的标题、摘要和正文。
- 发布为新闻条目。
- 归档提交。
- 查看附件预览。

发布为新闻条目时，系统会把投稿目标栏目、标题、摘要、正文、附件、来源等内容转换成新的 Article，并把投稿状态标记为已发布。

## API 说明

### 新闻列表

```http
GET /api/news/
```

支持参数：

| 参数 | 说明 |
| --- | --- |
| `section` | 可选，筛选栏目：`news`、`trivia`、`official_works` |
| `limit` | 可选，返回数量，最大 50 |
| `q` | 可选，搜索关键词 |
| `mode` | 可选，`simple` 或 `advanced` |

返回示例：

```json
{
  "results": [
    {
      "id": 1,
      "section": "news",
      "sectionLabel": "新闻",
      "title": "示例新闻",
      "slug": "example-news",
      "summary": "新闻摘要",
      "bodyFormat": "markdown",
      "coverImage": "/media/news/covers/example.png",
      "sourceName": "魔女周刊编辑部",
      "sourceUrl": "",
      "publishedAt": "2026-06-30T09:30:00+08:00"
    }
  ]
}
```

### 新闻详情

```http
GET /api/news/<slug>/
```

详情接口会在列表字段基础上额外返回 `body`，用于详情页渲染完整正文。

### 投稿创建

```http
POST /api/submissions/
```

接口支持 JSON，也支持 `multipart/form-data`。当前前台使用 `FormData` 提交，以便上传附件。

常用字段：

| 字段 | 说明 |
| --- | --- |
| `kind` | `submission` 或 `feedback` |
| `targetSection` | `news`、`trivia`、`official_works` |
| `title` | 标题，必填 |
| `authorName` | 投稿人称呼 |
| `contact` | 联系方式 |
| `summary` | 摘要 |
| `body` | 正文或反馈内容，必填 |
| `sourceUrl` | 来源链接 |
| `attachment` | 图片附件 |

## 本地开发

### 环境准备

建议准备：

- Python 3.12 或更新版本。
- Node.js 20 或更新版本。
- npm。

克隆项目后，先安装后端依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

初始化数据库：

```powershell
python manage.py migrate
python manage.py createsuperuser
```

安装前端依赖并构建：

```powershell
cd frontend
npm install
npm run build
cd ..
```

启动 Django：

```powershell
python manage.py runserver 127.0.0.1:8000
```

打开：

```text
http://127.0.0.1:8000/
```

后台入口：

```text
http://127.0.0.1:8000/admin/
```

### 前端开发模式

如果只调试前端，可以进入 `frontend/` 使用 Vite：

```powershell
cd frontend
npm run dev
```

如果需要联调 Django API，请确认 Django 后端也在运行，并根据实际端口处理代理或请求路径。当前生产构建路径默认由 Django 托管。

## 常用命令

后端检查：

```powershell
.\.venv\Scripts\python.exe manage.py check
```

前端构建：

```powershell
cd frontend
npm run build
```

搜索高亮测试：

```powershell
cd frontend
npm run test:highlight
```

启动本地服务器：

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

## 配置说明

### SECRET_KEY

生产环境应设置 `DJANGO_SECRET_KEY`：

```powershell
$env:DJANGO_SECRET_KEY="your-production-secret"
```

如果未设置，项目会使用仅适合本地开发的默认值。

### DEBUG 与 ALLOWED_HOSTS

当前项目默认 `DEBUG=True`，适合本地开发。正式部署前应按 Django 部署规范关闭 DEBUG，并配置 `ALLOWED_HOSTS`。

### 静态文件与媒体文件

前端静态页面由 `frontend/dist/` 提供。媒体文件由 Django 的 `MEDIA_ROOT` 管理，默认路径为项目根目录下的 `media/`。

生产环境建议使用 Nginx、对象存储或其他静态资源服务来托管媒体文件和构建产物。

## 部署思路

一个简单部署流程如下：

1. 拉取源码。
2. 安装 Python 依赖。
3. 安装前端依赖。
4. 执行 `npm run build` 生成 `frontend/dist/`。
5. 设置 `DJANGO_SECRET_KEY` 等环境变量。
6. 执行数据库迁移。
7. 创建管理员账号。
8. 使用 WSGI/ASGI 服务运行 Django。
9. 配置反向代理、静态文件和媒体文件访问。

如果项目后续需要面向高流量环境，可以进一步拆分数据库、媒体存储、缓存和静态资源 CDN。

## 安全提示

- 不要在公开源码中写入生产密钥、Cookie、令牌、数据库密码或服务器地址。
- 投稿接口当前使用 `csrf_exempt` 以便前台表单提交，正式公开部署前建议结合登录、验证码、限流或 CSRF 策略重新评估。
- 后台账号应使用强密码，并限制管理入口访问范围。
- Word/Markdown 导入用于可信管理员后台，仍建议对上传内容来源保持审查。
- 生产部署前应关闭 `DEBUG`，配置 `ALLOWED_HOSTS`，并检查媒体文件访问权限。

## 测试

当前项目包含两类轻量验证：

- Django system check：检查配置、模型和项目结构。
- 搜索高亮测试：验证关键词高亮、HTML 转义和空关键词处理。

命令：

```powershell
.\.venv\Scripts\python.exe manage.py check
cd frontend
npm run test:highlight
npm run build
```

后续如果继续扩展项目，建议补充：

- Django API 单元测试。
- 投稿表单提交测试。
- Markdown/Word 导入回归测试。
- 前端组件测试。
- 端到端浏览器测试。

## 路线建议

这个仓库目前已经能支撑一个轻量内容站。后续可以考虑：

- 添加分页和栏目归档。
- 添加标签系统。
- 添加草稿预览。
- 改进 Markdown 渲染能力。
- 为投稿接口增加验证码和限流。
- 增加 RSS Feed。
- 增加站点地图 `sitemap.xml`。
- 将媒体文件迁移到对象存储。
- 添加自动化部署流程。

## 许可证

本项目基于 MIT License 开源。详见 [LICENSE](LICENSE)。
