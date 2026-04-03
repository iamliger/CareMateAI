import os
import time
import sys
from google import genai

# 주인님의 확인된 API 키
API_KEY = "AIzaSyA4rIFYFc0en7aIQQT4aSKHUvYm5OlE5D8"


def test_gemini_final():
    print("\n" + "🚀 " * 10)
    print("   엘리스 AI 최종 관문 테스트")
    print("🚀 " * 10)

    try:
        # 최신 SDK 클라이언트 생성
        client = genai.Client(api_key=API_KEY)

        # 주인님의 진단 리스트에서 100% 확인된 모델명들입니다.
        # 429 에러(할당량)를 피하기 위해 가장 가벼운 'lite'와 'latest' 위주로 구성했습니다.
        model_candidates = [
            "gemini-2.0-flash-lite",  # 1순위: 아까 429 확인됨 (존재 확인)
            "gemini-flash-latest",  # 2순위: 범용 최신
            "gemini-2.0-flash",  # 3순위: 표준 최신
            "gemini-pro-latest",  # 4순위: 성능 최신
        ]

        for model_name in model_candidates:
            print(f"\n📡 [{model_name}] 연결 시도 중...")

            # [중요] 구글 무료 티어의 1분당 할당량을 비우기 위해 강제 대기
            print("⏳ 할당량 초기화를 위해 15초간 대기합니다. 잠시만 기다려주세요...")
            for i in range(15, 0, -1):
                sys.stdout.write(f"\r남은 시간: {i}초 ")
                sys.stdout.flush()
                time.sleep(1)
            print("\n")

            try:
                # 실제 AI 호출
                response = client.models.generate_content(
                    model=model_name,
                    contents="안녕 엘리스! 드디어 연결된거니? 짧게 축하해줘.",
                )

                # 성공 시 출력
                print(f"✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨")
                print(f"✅ [대성공!] {model_name} 모델 응답 확인")
                print(f"💬 엘리스의 답변: {response.text}")
                print(f"✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨")
                print(
                    f"\n👉 주인님! 이제 이 '{model_name}' 이름을 서비스에 바로 적용하면 됩니다!"
                )
                return  # 성공했으므로 프로그램 종료

            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    print(
                        f"⚠️ 할당량 초과(429): 아직 구글 서버가 쉬고 싶어 하네요. 다음 후보로 갑니다."
                    )
                elif "503" in err_str:
                    print(f"❌ 서버 과부하(503): 구글 서버에 사용자가 너무 많습니다.")
                else:
                    print(f"❓ 기타 오류: {err_str}")
                continue

        print("\n❌ 모든 후보 모델이 할당량 초과나 오류로 실패했습니다.")
        print(
            "💡 마지막 팁: 5분 정도 커피 한 잔 마시고 다시 실행하면 100% 성공할 것입니다!"
        )

    except Exception as fatal:
        print(f"\n☢️ 시스템 오류: {str(fatal)}")


if __name__ == "__main__":
    test_gemini_final()
