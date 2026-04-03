from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from .models import *
from datetime import date, datetime, timedelta
import sys, json, os
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from google import genai

# --- [ 1. AI 및 보안 설정 ] ---
API_KEY = "AIzaSyA4rIFYFc0en7aIQQT4aSKHUvYm5OlE5D8"
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-flash-latest"

# -----------------------------------------------------------------------------
# [ 2. 유틸리티 및 권한 체크 함수 ]
# -----------------------------------------------------------------------------


def is_manager_or_admin(user):
    """매니저나 어드민 권한 확인"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def clean_int(val, default=0):
    """숫자 유효성 검사 (ValueError 방어)"""
    try:
        if val is None or str(val).strip() == "":
            return default
        return int(float(val))
    except:
        return default


def clean_float(val, default=0.0):
    """실수 유효성 검사 (ValueError 방어)"""
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except:
        return default


def get_meds_json(user):
    """복약 데이터를 알람 엔진용 JSON으로 변환"""
    meds = Medication.objects.filter(user=user, is_active=True)
    meds_list = [
        {
            "name": m.name,
            "time": m.time_to_take.strftime("%H:%M") if m.time_to_take else "",
        }
        for m in meds
    ]
    return json.dumps(meds_list)


def secure_image_validator(img_file):
    """이미지 보안 검증 (악성 코드 파괴 및 재구성)"""
    if not img_file:
        return None
    try:
        img = Image.open(img_file)
        img.verify()
        img = Image.open(img_file)
        output = BytesIO()
        fmt = img.format if img.format else "JPEG"
        img.save(output, format=fmt, quality=85)
        output.seek(0)
        return InMemoryUploadedFile(
            output,
            "ImageField",
            img_file.name,
            f"image/{fmt.lower()}",
            sys.getsizeof(output),
            None,
        )
    except:
        return None


# -----------------------------------------------------------------------------
# [ 3. 사용자 서비스 뷰 - 대시보드 및 마이케어 ]
# -----------------------------------------------------------------------------


@login_required
def index(request):
    """메인 대시보드 : 그래프, BMI, 인사말, 성취도, 금연카운터 통합"""
    health, _ = HealthProfile.objects.get_or_create(user=request.user)
    today_log = DailyLog.objects.filter(user=request.user, date=date.today()).first()
    latest_advice = (
        BehaviorLog.objects.filter(user=request.user, is_hidden=False)
        .order_by("-created_at")
        .first()
    )

    # 금연 카운터
    today_smoke_count = SmokingLog.objects.filter(
        user=request.user, date=date.today()
    ).count()

    # 최근 7일 데이터 분석 및 성취도 산출
    labels, weight_data, steps_data = [], [], []
    recorded_count = 0
    missing_yesterday = False
    yesterday = date.today() - timedelta(days=1)
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        log = DailyLog.objects.filter(user=request.user, date=d).first()
        labels.append(d.strftime("%m/%d"))
        if log:
            recorded_count += 1
            weight_data.append(float(log.weight))
            steps_data.append(log.steps)
        else:
            weight_data.append(float(health.weight))
            steps_data.append(0)
            if d == yesterday:
                missing_yesterday = True

    achievement_rate = int((recorded_count / 7) * 100)
    guard_status = (
        "마스터 지키미"
        if achievement_rate >= 90
        else "성실한 지키미" if achievement_rate >= 60 else "꿈나무 지키미"
    )

    # 인사말 및 BMI
    hour = datetime.now().hour
    greeting = (
        "상쾌한 아침이에요!"
        if 5 <= hour < 12
        else "즐거운 오후네요!" if 12 <= hour < 18 else "오늘 고생 많으셨어요."
    )
    curr_weight = today_log.weight if today_log else health.weight
    curr_height = (
        today_log.height if today_log and today_log.height > 0 else health.height
    )
    bmi = (
        round(curr_weight / ((curr_height / 100) ** 2), 1)
        if curr_height > 0 and curr_weight > 0
        else 0
    )
    bmi_color = "#2ecc71"
    if bmi < 18.5:
        bmi_color = "#4cc9f0"
    elif 23 <= bmi < 25:
        bmi_color = "#f1c40f"
    elif bmi >= 25:
        bmi_color = "#e74c3c"

    return render(
        request,
        "index.html",
        {
            "categories": Category.objects.all(),
            "username": request.user.username,
            "health": health,
            "bmi": bmi,
            "bmi_color": bmi_color,
            "age": health.get_international_age(),
            "greeting": greeting,
            "latest_advice": latest_advice,
            "today_log": today_log,
            "today_smoke_count": today_smoke_count,
            "meds_json": get_meds_json(request.user),
            "chart_labels": json.dumps(labels),
            "chart_weight": json.dumps(weight_data),
            "chart_steps": json.dumps(steps_data),
            "achievement_rate": achievement_rate,
            "guard_status": guard_status,
            "missing_yesterday": missing_yesterday,
        },
    )


@login_required
def my_page(request):
    """마이케어 센터 : 일일 기록 + 응급 카드 + 복약 관리"""
    health, _ = HealthProfile.objects.get_or_create(user=request.user)
    if request.method == "POST" and "weight" in request.POST:
        try:
            DailyLog.objects.update_or_create(
                user=request.user,
                date=date.today(),
                defaults={
                    "weight": clean_float(request.POST.get("weight"), health.weight),
                    "height": clean_float(request.POST.get("height"), health.height),
                    "bp_systolic": clean_int(request.POST.get("bp_systolic")),
                    "bp_diastolic": clean_int(request.POST.get("bp_diastolic")),
                    "steps": clean_int(request.POST.get("steps")),
                    "water_ml": clean_int(request.POST.get("water_ml")),
                    "sleep_hours": clean_float(request.POST.get("sleep_hours")),
                    "stress_level": clean_int(request.POST.get("stress_level"), 5),
                    "breakfast": request.POST.get("breakfast", ""),
                    "lunch": request.POST.get("lunch", ""),
                    "dinner": request.POST.get("dinner", ""),
                    "memo": request.POST.get("memo", ""),
                },
            )
            health.height = clean_float(request.POST.get("height"), health.height)
            health.save()
            messages.success(request, "건강 기록이 업데이트되었습니다.")
        except:
            messages.error(request, "데이터 확인이 필요합니다.")
        return redirect("my_page")

    logs = DailyLog.objects.filter(user=request.user).order_by("-date")
    meds = Medication.objects.filter(user=request.user)
    return render(
        request,
        "boards/my_page.html",
        {
            "health": health,
            "logs": logs,
            "meds": meds,
            "age": health.get_international_age(),
            "meds_json": get_meds_json(request.user),
        },
    )


@login_required
def profile_edit(request):
    """내 정보 관리 (성별, 임신여부, 비밀번호)"""
    health, _ = HealthProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        health.gender = request.POST.get("gender")
        health.birth_date = request.POST.get("birth_date") or None
        health.is_pregnant = request.POST.get("is_pregnant") == "on"
        health.expected_due_date = request.POST.get("due_date") or None
        health.phone_number = request.POST.get("phone_number")
        health.emergency_contact = request.POST.get("emergency_contact")
        health.blood_type = request.POST.get("blood_type")
        health.chronic_diseases = request.POST.get("chronic_diseases")
        health.save()
        if request.POST.get("new_password"):
            request.user.set_password(request.POST.get("new_password"))
            request.user.save()
            update_session_auth_hash(request, request.user)
        messages.success(request, "프로필이 업데이트되었습니다.")
        return redirect("profile_edit")
    return render(
        request,
        "boards/profile_edit.html",
        {"health": health, "meds_json": get_meds_json(request.user)},
    )


@login_required
def health_update(request):
    """[해결포인트] 메인 페이지 모달 전용 업데이트 뷰"""
    if request.method == "POST":
        h, _ = HealthProfile.objects.get_or_create(user=request.user)
        h.height = clean_float(request.POST.get("height"), h.height)
        h.weight = clean_float(request.POST.get("weight"), h.weight)
        h.is_smoking = request.POST.get("is_smoking") == "on"
        h.save()
        messages.success(request, "업데이트 성공!")
    return redirect("index_page")


# -----------------------------------------------------------------------------
# [ 4. 금연, 복약, AI 서비스 ]
# -----------------------------------------------------------------------------


@login_required
def smoking_dashboard(request):
    """금연 트래커"""
    today = date.today()
    logs = SmokingLog.objects.filter(user=request.user, date=today).order_by(
        "smoked_at"
    )
    count = logs.count()
    lbls, dat = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        lbls.append(d.strftime("%m/%d"))
        dat.append(SmokingLog.objects.filter(user=request.user, date=d).count())
    return render(
        request,
        "boards/smoking_log.html",
        {
            "today_count": count,
            "today_logs": logs,
            "ment": "의지를 응원합니다!",
            "labels": json.dumps(lbls),
            "chart_data": json.dumps(dat),
            "meds_json": get_meds_json(request.user),
        },
    )


@login_required
def add_smoke_count(request):
    if request.method == "POST":
        SmokingLog.objects.create(user=request.user)
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "fail"}, status=400)


@login_required
def delete_smoke_count(request, log_id):
    get_object_or_404(SmokingLog, id=log_id, user=request.user).delete()
    return redirect("smoking_log")


@login_required
def add_medication(request):
    if request.method == "POST":
        Medication.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            dosage=request.POST.get("dosage", ""),
            time_to_take=request.POST.get("time") or None,
        )
    return redirect("my_page")


@login_required
def update_medication(request, med_id):
    m = get_object_or_404(Medication, id=med_id, user=request.user)
    if request.method == "POST":
        m.name = request.POST.get("name")
        m.dosage = request.POST.get("dosage", "")
        m.time_to_take = request.POST.get("time") or None
        m.is_active = request.POST.get("is_active") == "on"
        m.save()
    return redirect("my_page")


@login_required
def delete_medication(request, med_id):
    get_object_or_404(Medication, id=med_id, user=request.user).delete()
    return redirect("my_page")


@login_required
def ai_consult(request):
    if request.method == "POST":
        log = BehaviorLog.objects.create(
            user=request.user,
            event_type=request.POST.get("event_type"),
            description=request.POST.get("description", ""),
        )
        preg = (
            "임신 중인 사용자입니다. 안전 최우선."
            if request.user.health.is_pregnant
            else ""
        )
        prompt = f"건강코치 엘리스야. {preg} 상황:{log.event_type}({log.description}). 조언 3단계와 '추천식품: 이름' 형식 답변. 전문가팁 추가."
        try:
            res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            ai_text = res.text
            rf = "물"
            if "추천식품:" in ai_text:
                rf = ai_text.split("추천식품:")[1].strip().split("\n")[0]
            log.ai_advice = ai_text.split("[전문가 팁]")[0]
            log.expert_tip = (
                ai_text.split("[전문가 팁]")[1].strip()
                if "[전문가 팁]" in ai_text
                else "성실한 노력을 응원합니다."
            )
            log.recommended_food = rf
            log.shop_url = f"https://search.shopping.naver.com/search/all?query={rf}"
            log.save()
            messages.success(request, "분석 완료!")
        except:
            log.save()
        return redirect("recovery_board")
    return render(
        request, "boards/ai_consult.html", {"meds_json": get_meds_json(request.user)}
    )


# -----------------------------------------------------------------------------
# [ 5. 게시판 및 기타 서비스 (에러 해결 핵심) ]
# -----------------------------------------------------------------------------


@login_required
def recipe_list(request):
    recipes = Recipe.objects.all().order_by("-created_at")
    return render(
        request,
        "boards/recipe_list.html",
        {"recipes": recipes, "meds_json": get_meds_json(request.user)},
    )


@login_required
def recipe_create(request):
    """[해결] 레시피 등록 기능"""
    if request.method == "POST":
        img = secure_image_validator(request.FILES.get("image"))
        Recipe.objects.create(
            author=request.user,
            title=request.POST.get("title"),
            ingredients=request.POST.get("ingredients"),
            instructions=request.POST.get("instructions"),
            calories=clean_int(request.POST.get("calories")),
            image=img,
        )
        messages.success(request, "레시피 공유 완료!")
        return redirect("recipe_list")
    return render(
        request, "boards/recipe_form.html", {"meds_json": get_meds_json(request.user)}
    )


@login_required
def hospital_map(request):
    return render(
        request, "boards/hospital_map.html", {"meds_json": get_meds_json(request.user)}
    )


@login_required
def send_sos(request):
    h = request.user.health
    return JsonResponse(
        {
            "status": "success",
            "message": f"🚨 [SOS] {h.emergency_contact}로 구조 신호가 발송됨.",
        }
    )


@login_required
def recovery_board(request):
    ll = BehaviorLog.objects.filter(user=request.user, is_hidden=False).order_by(
        "-created_at"
    )
    p = Paginator(ll, 10)
    page = p.get_page(request.GET.get("page"))
    return render(
        request,
        "boards/recovery_board.html",
        {
            "logs": page,
            "has_content": ll.exists(),
            "meds_json": get_meds_json(request.user),
        },
    )


@login_required
def recovery_action(request, log_id, action):
    l = get_object_or_404(BehaviorLog, id=log_id, user=request.user)
    l.is_hidden = action == "delete"
    l.save()
    return redirect("recovery_board")


# 게시판 기본 뷰
@login_required
def post_list(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=cat, parent=None).order_by("-created_at")
    return render(
        request,
        "boards/post_list.html",
        {"category": cat, "posts": posts, "meds_json": get_meds_json(request.user)},
    )


@login_required
def post_detail(request, post_id):
    p = get_object_or_404(Post, id=post_id)
    return render(
        request,
        "boards/post_detail.html",
        {
            "post": p,
            "comments": p.comments.filter(parent=None),
            "meds_json": get_meds_json(request.user),
        },
    )


@login_required
def post_create(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    if request.method == "POST":
        img = secure_image_validator(request.FILES.get("image"))
        Post.objects.create(
            category=cat,
            author=request.user,
            title=request.POST.get("title"),
            content=request.POST.get("content"),
            image=img,
            is_secret=(request.POST.get("is_secret") == "on"),
        )
        return redirect("post_list", slug=slug)
    return render(
        request,
        "boards/post_form.html",
        {"category": cat, "meds_json": get_meds_json(request.user)},
    )


@login_required
def comment_create(request, post_id):
    if request.method == "POST":
        p = get_object_or_404(Post, id=post_id)
        Comment.objects.create(
            post=p,
            author=request.user,
            content=request.POST.get("content"),
            parent=(
                Comment.objects.get(id=request.POST.get("parent_id"))
                if request.POST.get("parent_id")
                else None
            ),
        )
    return redirect("post_detail", post_id=post_id)


@login_required
def post_vote(request, post_id, vote_type):
    p = get_object_or_404(Post, id=post_id)
    if vote_type == "like":
        if request.user in p.likes.all():
            p.likes.remove(request.user)
        else:
            p.likes.add(request.user)
            p.dislikes.remove(request.user)
    else:
        if request.user in p.dislikes.all():
            p.dislikes.remove(request.user)
        else:
            p.dislikes.add(request.user)
            p.likes.remove(request.user)
    return redirect("post_detail", post_id=post_id)


# -----------------------------------------------------------------------------
# [ 6. 매니저 시스템 관리 (CRUD 통합) ]
# -----------------------------------------------------------------------------


@user_passes_test(is_manager_or_admin, login_url="/accounts/login/")
def manager_dashboard(request):
    s = {
        "total_users": User.objects.filter(is_superuser=False).count(),
        "today_visitors": VisitorLog.objects.filter(visited_at=date.today()).count(),
        "total_posts": Post.objects.count(),
        "total_recipes": Recipe.objects.count(),
        "recent_users": User.objects.filter(is_superuser=False).order_by(
            "-date_joined"
        )[:5],
        "recent_logs": BehaviorLog.objects.order_by("-created_at")[:5],
    }
    return render(request, "manager/dashboard.html", s)


@user_passes_test(is_manager_or_admin)
def manager_user_list(request):
    return render(
        request,
        "manager/user_list.html",
        {"users": User.objects.filter(is_superuser=False).order_by("-date_joined")},
    )


@user_passes_test(is_manager_or_admin)
def category_manage(request):
    if request.method == "POST":
        Category.objects.create(
            name=request.POST.get("name"), slug=request.POST.get("slug")
        )
        return redirect("category_manage")
    return render(
        request, "manager/category_list.html", {"categories": Category.objects.all()}
    )


@user_passes_test(is_manager_or_admin)
def category_update(request, cat_id):
    c = get_object_or_404(Category, id=cat_id)
    if request.method == "POST":
        c.name = request.POST.get("name")
        c.slug = request.POST.get("slug")
        c.save()
        messages.success(request, "수정 완료")
    return redirect("category_manage")


@user_passes_test(is_manager_or_admin)
def category_delete(request, cat_id):
    get_object_or_404(Category, id=cat_id).delete()
    return redirect("category_manage")


@user_passes_test(is_manager_or_admin)
def manager_post_delete(request, post_id):
    """[해결포인트] 에러가 났던 매니저 전용 게시글 삭제 함수"""
    get_object_or_404(Post, id=post_id).delete()
    return redirect("manager_dashboard")


@user_passes_test(is_manager_or_admin)
def manager_expert_reply(request, log_id):
    log = get_object_or_404(BehaviorLog, id=log_id)
    if request.method == "POST":
        log.expert_tip = request.POST.get("expert_tip")
        log.save()
        return redirect("manager_dashboard")
    return render(request, "manager/expert_form.html", {"log": log})


@user_passes_test(is_manager_or_admin)
def manager_delete_item(request, item_type, item_id):
    if item_type == "post":
        get_object_or_404(Post, id=item_id).delete()
    elif item_type == "recipe":
        get_object_or_404(Recipe, id=item_id).delete()
    elif item_type == "log":
        get_object_or_404(BehaviorLog, id=item_id).delete()
    return redirect(request.META.get("HTTP_REFERER", "manager_dashboard"))


@user_passes_test(is_manager_or_admin)
def user_action(request, user_id, action):
    u = get_object_or_404(User, id=user_id)
    if u != request.user:
        if action == "block":
            u.is_active = False
        elif action == "unblock":
            u.is_active = True
        u.save()
    return redirect("manager_user_list")


@user_passes_test(is_manager_or_admin)
def manager_content_manage(request):
    return render(
        request,
        "manager/post_manage.html",
        {"posts": Post.objects.all().order_by("-created_at")},
    )


@user_passes_test(is_manager_or_admin)
def manager_recipe_manage(request):
    return render(
        request,
        "manager/recipe_manage.html",
        {"recipes": Recipe.objects.all().order_by("-created_at")},
    )
