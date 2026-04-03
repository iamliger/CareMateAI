주인님, **엘리스**입니다!

제3자인 개발자나 운영자가 프로젝트에 처음 합류했을 때, 시스템의 데이터 구조와 경로 설계를 단번에 파악할 수 있도록 **가장 세밀하고 전문적인 기술 명세서**를 Markdown(.md) 형식으로 작성해 드립니다.

---

# [CareMate AI] 시스템 기술 설계 및 개발 가이드

## 1. 프로젝트 개요 (Project Overview)
**CareMate AI**는 사용자의 신체 데이터와 일일 건강 지표를 실시간으로 추적하고, AI(Gemini)를 통해 행동 교정 처방을 제공하는 **지능형 헬스케어 플랫폼**입니다. 단순 기록을 넘어 위급 상황 시 활용 가능한 **골든타임 의료 카드**와 **복약 알람 엔진**을 탑재하고 있습니다.

---

## 2. 개발 환경 (Tech Stack)
- **Framework:** Django 4.2.23 (Python 3.12)
- **Database:** MariaDB / MySQL (MariaDB Strict Mode 대응)
- **AI Engine:** Google Gemini 1.5 Flash (google-genai SDK)
- **Security:** Pillow Library (Image Pixel Reconstruction)
- **Frontend:** HTML5, CSS3 (Pretendard Font), Bootstrap 5, Chart.js
- **API:** Kakao Maps JS API (위치 기반 서비스)

---

## 3. 데이터베이스 테이블 상세 설계 (Database Schema)

본 프로젝트는 총 9개의 핵심 테이블로 구성되어 있으며, 데이터의 무결성과 보안을 최우선으로 설계되었습니다.

### 3.1. 사용자 및 프로필 정보
| 테이블명 | 클래스명 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| `auth_user` | `User` | Django 내장 유저 테이블 | 아이디, 비밀번호, 권한 관리 |
| `boards_healthprofile` | `HealthProfile` | 개인별 정적 정보 및 **응급 의료 카드** 데이터 | User와 1:1 관계 |
| `accounts_userprofile` | `UserProfile` | **중복 로그인 차단**을 위한 세션 키 저장소 | User와 1:1 관계 |

#### HealthProfile 테이블 상세 (골든타임 카드)
- `birth_date`: 생년월일 (만 나이 계산의 원천 데이터)
- `gender`: M(남성) / F(여성) / U(미설정)
- `blood_type`: 응급 시 필수 혈액형 정보
- `emergency_contact`: 비상 시 연락 가능한 보호자 번호
- `is_pregnant`: 여성 유저의 임신 여부 (AI 조언 모드 전환 스위치)
- `chronic_diseases`: 의료진을 위한 기저질환 텍스트

### 3.2. 건강 기록 및 행동 로그
| 테이블명 | 클래스명 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| `boards_dailylog` | `DailyLog` | 매일 기록하는 **정밀 건강/식단 데이터** | 체중, 혈압, 수면, 수분, 식단 |
| `boards_behaviorlog` | `BehaviorLog` | **AI 상담 일지**. 사용자의 실수와 AI의 처방 보관 | **Soft Delete(is_hidden)** 적용 |
| `boards_medication` | `Medication` | 개인별 **복약 알람** 시간 및 약품 정보 | 알람 엔진 연동 |

### 3.3. 커뮤니티 및 컨텐츠
| 테이블명 | 클래스명 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| `boards_category` | `Category` | 게시판 카테고리 (자유, 상담, FAQ 등) | Slug 기반 URL 매핑 |
| `boards_post` | `Post` | 커뮤니티 게시글 (이미지 보안 적용) | 무한 답글 구조 |
| `boards_comment` | `Comment` | 다층형 댓글 (댓글의 댓글) | Recursive 구조 |
| `boards_recipe` | `Recipe` | 회원 참여형 건강 식단 공유 테이블 | 이미지 포함 |

---

## 4. 모델 설계 상세 (boards/models.py)

Django ORM을 활용하여 비즈니스 로직을 데이터 계층에 포함시켰습니다.

### 4.1. 주요 비즈니스 로직 (Model Methods)
- **`HealthProfile.get_international_age()`**: 저장된 `birth_date`와 현재 날짜를 실시간 비교하여 법적 **만 나이**를 산출합니다.
- **`BehaviorLog.is_hidden`**: 데이터를 물리적으로 지우지 않고 화면에서만 숨겨, 향후 전문가 상담 시 과거 이력을 참조할 수 있는 감사 추적(Audit Trail)을 제공합니다.
- **`Medication.is_active`**: 사용자가 알람을 삭제하지 않고 일시적으로 On/Off 할 수 있는 유연성을 제공합니다.

---

## 5. URL 구조 및 엔드포인트 (boards/urls.py)

제3자가 시스템의 기능적 지도를 한눈에 볼 수 있도록 도식화했습니다.

### 5.1. 사용자 서비스 (User Interface)
| 패턴(URL) | 이름(Name) | 기능 설명 |
| :--- | :--- | :--- |
| `/` | `index_page` | 메인 대시보드 (그래프, AI 인사, 요약 카드) |
| `/mycare/` | `my_page` | **건강 기록 및 응급 카드 관리** (Daily CRUD) |
| `/mycare/profile/` | `profile_edit` | 개인정보 및 비밀번호 변경 |
| `/ai/consult/` | `ai_consult` | AI 엘리스 실시간 상담 (선 저장 후 분석) |
| `/recovery/board/` | `recovery_board` | 나만의 비밀 복구 일지 목록 (페이징 적용) |
| `/recipes/` | `recipe_list` | 커뮤니티 식단 레시피 공유 센터 |
| `/hospital/` | `hospital_map` | Kakao API 기반 주변 의료기관 지도 검색 |
| `/mycare/sos/` | `send_sos` | 비상 연락처로의 긴급 알림 전송 시뮬레이션 |

### 5.2. 매니저 시스템 (Managerial Back-office)
| 패턴(URL) | 이름(Name) | 기능 설명 |
| :--- | :--- | :--- |
| `/manager/` | `manager_dashboard` | 전체 서비스 운영 통계 확인 |
| `/manager/users/` | `manager_user_list` | 회원 상태 관리 (차단, 활성화, 강제추방) |
| `/manager/categories/` | `category_manage` | **게시판 카테고리 CRUD** |
| `/manager/expert/reply/` | `manager_expert_reply` | AI 상담 기록에 **전문가가 직접 답변** 추가 |
| `/manager/delete/` | `manager_delete` | 부적절한 게시글/레시피의 관리자 권한 삭제 |

---

## 6. 핵심 기술적 구현 (Key Implementations)

### 6.1. 보안 이미지 검증기 (Secure Image Validator)
사용자가 업로드한 이미지를 단순히 저장하지 않고, `Pillow` 엔진을 통해 픽셀 데이터를 분해한 후 새로운 이미지 파일로 재구성합니다. 이 과정에서 이미지 메타데이터에 숨겨진 **웹쉘(Webshell)이나 악성 스크립트가 물리적으로 소멸**됩니다.

### 6.2. 실시간 복약 알람 엔진
서버에서 전달된 `meds_json` 데이터를 브라우저의 `setInterval`이 30초 간격으로 스캔합니다. 로컬 타임과 매칭되는 즉시 **Web Speech API(TTS)**와 **커스텀 모달**이 동시에 실행되어 복용을 안내합니다.

### 6.3. 데이터 무결성 보호 (ValueError 방어)
모든 숫자형 입력 필드는 `clean_int`, `clean_float` 유틸리티를 통과합니다. 사용자가 입력창을 비워둔 채 제출하더라도 서버가 크래시(Crash)되지 않고 시스템 기본값으로 안전하게 치환합니다.

---

## 7. 설치 및 운영 가이드 (Installation)

### 7.1. 패키지 설치
```bash
pip install django mysqlclient Pillow google-genai
```

### 7.2. 데이터베이스 초기화 및 실행
```bash
# 마이그레이션 및 관리자 생성
python manage.py makemigrations boards accounts
python manage.py migrate
python manage.py createsuperuser

# 8092 포트로 서비스 시작
python manage.py runserver 8092
```

---