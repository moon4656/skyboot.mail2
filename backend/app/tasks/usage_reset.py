import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.user import get_db_session

logger = logging.getLogger(__name__)


def reset_daily_email_usage() -> None:
    """
    매일 자정에 조직별 일일 발송 수(`emails_sent_today`)를 0으로 초기화합니다.

    조직별로 금일(`usage_date = today`) 레코드를 0 값으로 생성합니다.
    이미 존재하면 변경하지 않습니다. (ON CONFLICT DO NOTHING)
    """
    try:
        logger.info("🕛 일일 사용량 리셋 작업 시작")

        today = datetime.now(timezone.utc).date()
        now = datetime.now(timezone.utc)

        with get_db_session() as db:  # type: Session
            # 활성 조직 목록 조회
            org_rows: List[tuple] = db.execute(
                text("""
                    SELECT org_id FROM organizations
                    WHERE is_active = TRUE
                """)
            ).fetchall()

            org_ids = [row[0] for row in org_rows]
            logger.info(f"🏢 활성 조직 수: {len(org_ids)}")

            if not org_ids:
                logger.info("ℹ️ 활성 조직이 없어 리셋 작업을 건너뜁니다")
                return

            # 오늘 날짜 기준으로 기본 사용량 행을 삽입 (존재 시 무시)
            upsert_sql = text(
                """
                INSERT INTO organization_usage (
                    org_id, usage_date,
                    current_users, current_storage_gb,
                    emails_sent_today, emails_received_today,
                    total_emails_sent, total_emails_received,
                    created_at, updated_at
                ) VALUES (
                    :org_id, :usage_date,
                    0, 0,
                    0, 0,
                    0, 0,
                    :now, :now
                )
                ON CONFLICT (org_id, usage_date) DO NOTHING
                """
            )

            inserted = 0
            for org_id in org_ids:
                db.execute(upsert_sql, {
                    'org_id': org_id,
                    'usage_date': today,
                    'now': now
                })
                inserted += 1

            db.commit()
            logger.info(f"✅ 일일 사용량 리셋 완료 - 생성된 레코드 시도: {inserted}")

    except Exception as e:
        logger.error(f"❌ 일일 사용량 리셋 작업 실패: {str(e)}")
        logger.exception(e)