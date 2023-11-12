
from django.urls import path, include
from rest_framework import permissions

from .views import *
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


router_book = DefaultRouter()
router_book.register(r'books', BookViewSet, basename='book')

router_author = DefaultRouter()
router_author.register(r'authors', BookViewSet, basename='author')

schema_view = get_schema_view(
   openapi.Info(
      title="User",
      default_version='v1',
      description="UserViewSet doc and api test with ui",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
)

urlpatterns = [
    path('api/book', include(router_book.urls)),
    path('api/author', include(router_author.urls)),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]