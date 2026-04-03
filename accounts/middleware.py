from django.contrib.sessions.models import Session
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages


class OneSessionPerUserMiddleware:
    """
    중복 로그인 방지 미들웨어:
    새로운 로그인이 발생하면 기존 로그인은 자동으로 로그아웃됩니다.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # 현재 접속한 세션 키
            current_session_key = request.session.session_key

            # 유저 모델에 저장된 최근 세션 키와 현재 세션 키가 다르면 로그아웃 시킴
            # (유저 모델에 session_key 저장 로직은 아래 API에서 구현)
            last_login_session_key = (
                request.user.profile.last_session_key
                if hasattr(request.user, "profile")
                else None
            )

            if last_login_session_key and last_login_session_key != current_session_key:
                # 다른 곳에서 로그인했으므로 현재 세션 종료
                logout(request)
                messages.error(
                    request,
                    "다른 기기에서 로그인이 감지되어 자동으로 로그아웃되었습니다.",
                )

        response = self.get_response(request)
        return response
