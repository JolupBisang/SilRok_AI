fastapi_app/
│── app/                     # 메인 애플리케이션 디렉토리
│   │── api/                  # API 엔드포인트 라우터
│   │   │── v1/               # API 버전 관리 (v1, v2 등)
│   │   │   │── endpoints/    # 실제 API 엔드포인트 모음
│   │   │   │   │── users.py  # 사용자 관련 API 엔드포인트
│   │   │   │   │── items.py  # 기타 엔드포인트
│   │   │   │── __init__.py   # 패키지 초기화
│   │── core/                 # 설정 및 애플리케이션 초기화
│   │   │── config.py         # 환경 설정 (dotenv 활용)
│   │   │── security.py       # 보안 관련 설정 (JWT, OAuth)
│   │   │── database.py       # 데이터베이스 연결 설정
│   │── models/               # 데이터베이스 모델 (SQLAlchemy, Pydantic)
│   │   │── user.py           # 사용자 모델
│   │   │── item.py           # 아이템 모델
│   │── schemas/              # Pydantic 데이터 검증 스키마
│   │   │── user.py           # 사용자 요청 & 응답 스키마
│   │   │── item.py           # 아이템 요청 & 응답 스키마
│   │── services/             # 비즈니스 로직 (Service Layer)
│   │   │── user_service.py   # 사용자 관련 로직
│   │   │── item_service.py   # 아이템 관련 로직
│   │── repositories/         # 데이터 액세스 레이어 (Repository Pattern)
│   │   │── user_repo.py      # 사용자 데이터 접근 로직
│   │   │── item_repo.py      # 아이템 데이터 접근 로직
│   │── dependencies/         # 의존성 주입 (FastAPI Depends)
│   │   │── database.py       # DB 세션 의존성
│   │   │── auth.py           # 인증 관련 의존성
│   │── main.py               # FastAPI 앱 실행 파일
│
│── tests/                    # 테스트 코드 (pytest)
│   │── test_users.py         # 사용자 관련 테스트
│   │── test_items.py         # 아이템 관련 테스트
│
│── .env                      # 환경 변수 파일
│── requirements.txt          # Python 패키지 목록
│── Dockerfile                # 도커 컨테이너 설정
│── docker-compose.yml        # 도커 컴포즈 설정 (DB, Redis 등)
│── README.md                 # 프로젝트 설명 문서
