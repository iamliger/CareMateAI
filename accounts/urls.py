from django.urls import path
from . import views

urlpatterns = [
    # 기본 /accounts/login/ 주소를 우리가 만든 custom_login으로 연결
    path("login/", views.custom_login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("check-id/", views.check_id, name="check_id"),
]
