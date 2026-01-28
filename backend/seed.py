"""
테스트 데이터 시드 스크립트.
Usage: cd backend && python seed.py
"""

from datetime import datetime, timedelta

from passlib.context import CryptContext

from database import SessionLocal
from models import (
    CaseStatus,
    Checklist,
    Comment,
    CSCase,
    License,
    LicenseMemo,
    Notification,
    NotificationType,
    Priority,
    Product,
    ProductMemo,
    User,
    UserRole,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    db = SessionLocal()
    try:
        # 기존 데이터가 있으면 스킵
        if db.query(User).first():
            print("데이터가 이미 존재합니다. 시드를 건너뜁니다.")
            return

        # ---------- Users ----------
        users = [
            User(
                name="관리자",
                email="admin@company.com",
                password_hash=pwd_context.hash("admin1234"),
                role=UserRole.ADMIN,
            ),
            User(
                name="홍길동",
                email="hong@company.com",
                password_hash=pwd_context.hash("password1234"),
                role=UserRole.CS,
            ),
            User(
                name="김철수",
                email="kim@company.com",
                password_hash=pwd_context.hash("password1234"),
                role=UserRole.CS,
            ),
            User(
                name="이영희",
                email="lee@company.com",
                password_hash=pwd_context.hash("password1234"),
                role=UserRole.ENGINEER,
            ),
        ]
        db.add_all(users)
        db.flush()

        # ---------- Products ----------
        products = [
            Product(
                name="ChatGPT",
                description="AI 대화 서비스",
                created_by=users[0].id,
            ),
            Product(
                name="DALL-E",
                description="AI 이미지 생성 서비스",
                created_by=users[0].id,
            ),
            Product(
                name="API Platform",
                description="개발자용 API 플랫폼",
                created_by=users[0].id,
            ),
        ]
        db.add_all(products)
        db.flush()

        # ---------- Licenses ----------
        licenses = [
            License(
                product_id=products[0].id,
                name="Free",
                description="무료 플랜",
            ),
            License(
                product_id=products[0].id,
                name="Plus",
                description="월 $20 구독 플랜",
            ),
            License(
                product_id=products[0].id,
                name="Pro",
                description="월 $200 프로 플랜",
            ),
            License(
                product_id=products[1].id,
                name="Basic",
                description="기본 이미지 생성",
            ),
            License(
                product_id=products[1].id,
                name="Premium",
                description="고급 이미지 생성 + API",
            ),
            License(
                product_id=products[2].id,
                name="Developer",
                description="개발자 API 키",
            ),
            License(
                product_id=products[2].id,
                name="Enterprise",
                description="기업용 API",
            ),
        ]
        db.add_all(licenses)
        db.flush()

        # ---------- Product Memos ----------
        product_memos = [
            ProductMemo(
                product_id=products[0].id,
                author_id=users[1].id,
                content="ChatGPT 관련 문의 시 플랜별 기능 차이 안내 필수",
            ),
            ProductMemo(
                product_id=products[1].id,
                author_id=users[2].id,
                content="DALL-E 이미지 저작권 관련 문의가 잦음. 이용약관 참고",
            ),
        ]
        db.add_all(product_memos)
        db.flush()

        # ---------- License Memos ----------
        license_memos = [
            LicenseMemo(
                license_id=licenses[2].id,
                author_id=users[1].id,
                content="Pro 플랜 기업 고객은 SLA가 다름. 별도 확인 필요",
            ),
            LicenseMemo(
                license_id=licenses[1].id,
                author_id=users[2].id,
                content="Plus 결제 이슈 발생 시 결제 시스템 팀 연동 필요",
            ),
        ]
        db.add_all(license_memos)
        db.flush()

        # ---------- CS Cases ----------
        now = datetime.utcnow()
        cases = [
            CSCase(
                title="ChatGPT Pro 결제 후 기능 미노출",
                content="Pro 플랜 결제 완료했으나 고급 기능이 표시되지 않습니다.",
                product_id=products[0].id,
                license_id=licenses[2].id,
                requester="고객A",
                assignee_id=users[1].id,
                status=CaseStatus.IN_PROGRESS,
                priority=Priority.HIGH,
                tags=["결제", "기능오류"],
            ),
            CSCase(
                title="ChatGPT Plus 구독 해지 요청",
                content="Plus 구독을 해지하고 싶습니다. 절차를 알려주세요.",
                product_id=products[0].id,
                license_id=licenses[1].id,
                requester="고객B",
                assignee_id=users[2].id,
                status=CaseStatus.OPEN,
                priority=Priority.MEDIUM,
                tags=["구독", "해지"],
            ),
            CSCase(
                title="DALL-E 이미지 생성 오류",
                content="이미지 생성 요청 시 계속 타임아웃이 발생합니다.",
                product_id=products[1].id,
                license_id=licenses[3].id,
                requester="고객C",
                assignee_id=users[1].id,
                status=CaseStatus.OPEN,
                priority=Priority.HIGH,
                tags=["오류", "타임아웃"],
            ),
            CSCase(
                title="API 키 발급 문의",
                content="Enterprise API 키 발급 절차가 어떻게 되나요?",
                product_id=products[2].id,
                license_id=licenses[6].id,
                requester="고객D",
                assignee_id=users[3].id,
                status=CaseStatus.DONE,
                priority=Priority.LOW,
                tags=["API", "발급"],
                completed_at=now - timedelta(days=1),
            ),
            CSCase(
                title="ChatGPT Free 사용량 제한 문의",
                content="무료 플랜의 일일 사용량 제한이 얼마인지 알고 싶습니다.",
                product_id=products[0].id,
                license_id=licenses[0].id,
                requester="고객E",
                assignee_id=users[2].id,
                status=CaseStatus.DONE,
                priority=Priority.LOW,
                tags=["사용량", "제한"],
                completed_at=now - timedelta(days=3),
            ),
        ]
        db.add_all(cases)
        db.flush()

        # ---------- Comments ----------
        comments = [
            Comment(
                case_id=cases[0].id,
                author_id=users[1].id,
                content="라이선스 상태 확인 중입니다.",
                is_internal=True,
            ),
            Comment(
                case_id=cases[0].id,
                author_id=users[1].id,
                content="확인 후 안내드리겠습니다. 잠시만 기다려 주세요.",
                is_internal=False,
            ),
            Comment(
                case_id=cases[1].id,
                author_id=users[2].id,
                content="해지 절차 안내 메일 발송 예정",
                is_internal=True,
            ),
        ]
        db.add_all(comments)
        db.flush()

        # ---------- Checklists ----------
        checklists = [
            Checklist(
                case_id=cases[0].id,
                content="라이선스 상태 확인",
                is_done=True,
            ),
            Checklist(
                case_id=cases[0].id,
                content="고객 회신",
                is_done=False,
            ),
            Checklist(
                case_id=cases[0].id,
                content="결제 시스템 확인",
                is_done=False,
            ),
            Checklist(
                case_id=cases[1].id,
                content="해지 절차 안내",
                is_done=False,
            ),
        ]
        db.add_all(checklists)
        db.flush()

        # ---------- Notifications ----------
        notifications = [
            Notification(
                user_id=users[1].id,
                case_id=cases[0].id,
                message="ChatGPT Pro 결제 문의 1건이 배정되었습니다.",
                type=NotificationType.ASSIGNEE,
                is_read=True,
            ),
            Notification(
                user_id=users[2].id,
                case_id=cases[1].id,
                message="ChatGPT Plus 해지 요청 1건이 배정되었습니다.",
                type=NotificationType.ASSIGNEE,
                is_read=False,
            ),
            Notification(
                user_id=users[1].id,
                case_id=cases[2].id,
                message="DALL-E 이미지 오류 문의가 3시간째 미처리입니다.",
                type=NotificationType.REMINDER,
                is_read=False,
            ),
        ]
        db.add_all(notifications)

        db.commit()
        print("시드 데이터 삽입 완료!")
        print(f"  Users: {len(users)}")
        print(f"  Products: {len(products)}")
        print(f"  Licenses: {len(licenses)}")
        print(f"  Product Memos: {len(product_memos)}")
        print(f"  License Memos: {len(license_memos)}")
        print(f"  CS Cases: {len(cases)}")
        print(f"  Comments: {len(comments)}")
        print(f"  Checklists: {len(checklists)}")
        print(f"  Notifications: {len(notifications)}")

    except Exception as e:
        db.rollback()
        print(f"시드 실패: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
