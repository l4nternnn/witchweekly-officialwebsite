"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from .views import vue_asset, vue_index

urlpatterns = [
    path('api/', include('articles.urls')),
    path('', vue_index, name='vue-index'),
    path('search/', vue_index, {'page': 'search'}, name='vue-search'),
    path('news/', vue_index, {'page': 'news'}, name='vue-news'),
    path('news/<str:slug>/', vue_index, {'page': 'news-detail'}, name='vue-news-detail'),
    path('trivia/', vue_index, {'page': 'trivia'}, name='vue-trivia'),
    path('trivia/<str:slug>/', vue_index, {'page': 'trivia-detail'}, name='vue-trivia-detail'),
    path('official-works/', vue_index, {'page': 'official-works'}, name='vue-official-works'),
    path(
        'official-works/<str:slug>/',
        vue_index,
        {'page': 'official-works-detail'},
        name='vue-official-works-detail',
    ),
    path('submit-feedback/', vue_index, {'page': 'submit-feedback'}, name='vue-submit-feedback'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r'^assets/(?P<path>.*)$',
            vue_asset,
        ),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
