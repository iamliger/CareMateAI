from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import user_passes_test


def superuser_only(view_func):
    return user_passes_test(lambda u: u.is_superuser, login_url="/")(view_func)


urlpatterns = [
    path("admin/", superuser_only(admin.site.urls)),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("boards.urls")),
]

# [중요] 미디어 파일 접근 허용
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
