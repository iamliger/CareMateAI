from django.urls import path
from . import views

urlpatterns = [
    # 1. 사용자 서비스
    path("", views.index, name="index_page"),
    path("health/update/", views.health_update, name="health_update"),
    path("mycare/", views.my_page, name="my_page"),
    path("mycare/profile/", views.profile_edit, name="profile_edit"),
    path("mycare/sos/", views.send_sos, name="send_sos"),
    # 2. 금연 트래커
    path("smoking/", views.smoking_dashboard, name="smoking_log"),
    path("smoking/add/", views.add_smoke_count, name="add_smoke"),
    path("smoking/delete/<int:log_id>/", views.delete_smoke_count, name="delete_smoke"),
    # 3. 복약 관리 CRUD
    path("mycare/medication/add/", views.add_medication, name="add_medication"),
    path(
        "mycare/medication/update/<int:med_id>/",
        views.update_medication,
        name="update_medication",
    ),
    path(
        "mycare/medication/delete/<int:med_id>/",
        views.delete_medication,
        name="delete_medication",
    ),
    # 4. AI 및 기타 서비스
    path("ai/consult/", views.ai_consult, name="ai_consult"),
    path("recovery/board/", views.recovery_board, name="recovery_board"),
    path(
        "recovery/action/<int:log_id>/<str:action>/",
        views.recovery_action,
        name="recovery_action",
    ),
    path("hospital/", views.hospital_map, name="hospital_map"),
    path("recipes/", views.recipe_list, name="recipe_list"),
    path("recipes/create/", views.recipe_create, name="recipe_create"),
    # 5. 게시판 기능
    path("board/<slug:slug>/", views.post_list, name="post_list"),
    path("post/<int:post_id>/", views.post_detail, name="post_detail"),
    path("board/<slug:slug>/write/", views.post_create, name="post_create"),
    path("post/<int:post_id>/comment/", views.comment_create, name="comment_create"),
    path("post/<int:post_id>/vote/<str:vote_type>/", views.post_vote, name="post_vote"),
    # 6. 매니저 시스템
    path("manager/", views.manager_dashboard, name="manager_dashboard"),
    path("manager/users/", views.manager_user_list, name="manager_user_list"),
    path("manager/categories/", views.category_manage, name="category_manage"),
    path(
        "manager/category/update/<int:cat_id>/",
        views.category_update,
        name="category_update",
    ),
    path(
        "manager/category/delete/<int:cat_id>/",
        views.category_delete,
        name="category_delete",
    ),
    path(
        "manager/expert/reply/<int:log_id>/",
        views.manager_expert_reply,
        name="manager_expert_reply",
    ),
    path(
        "manager/delete/<str:item_type>/<int:item_id>/",
        views.manager_delete_item,
        name="manager_delete",
    ),
    path(
        "manager/post/delete/<int:post_id>/",
        views.manager_post_delete,
        name="manager_post_delete",
    ),
]
