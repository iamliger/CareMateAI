from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from .models import UserProfile


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if User.objects.filter(username=username).exists():
            messages.error(request, "이미 사용 중인 아이디입니다.")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "가입 완료! 로그인 해주세요.")
            return redirect("login")
    return render(request, "registration/signup.html")


def check_id(request):
    username = request.GET.get("username", None)
    return JsonResponse(
        {"is_taken": User.objects.filter(username__iexact=username).exists()}
    )


def custom_login(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user is not None:
            if user.is_active:
                login(request, user)
                # 세션 키 저장 (중복 로그인 방지용)
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.last_session_key = request.session.session_key
                profile.save()
                return redirect("/")
            else:
                messages.error(request, "차단된 계정입니다.")
        else:
            messages.error(request, "아이디 또는 비밀번호가 틀렸습니다.")
    return render(request, "registration/login.html")
