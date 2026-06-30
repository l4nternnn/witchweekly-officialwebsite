from django.urls import path

from .views import article_detail, article_list, submission_create


urlpatterns = [
    path('news/', article_list, name='article-list'),
    path('news/<str:slug>/', article_detail, name='article-detail'),
    path('submissions/', submission_create, name='submission-create'),
]
