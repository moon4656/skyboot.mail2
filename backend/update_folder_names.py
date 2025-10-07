#!/usr/bin/env python3
"""
메일 폴더명을 한국어에서 영어로 업데이트하는 스크립트

이 스크립트는 기존의 한국어 폴더명을 영어로 변경합니다:
- 받은편지함 → INBOX
- 보낸편지함 → SENT  
- 임시보관함 → DRAFT
- 휴지통 → TRASH
"""

import sys
import os
import argparse
from datetime import datetime
from typing import Dict, List

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.mail_model import MailFolder, FolderType
from sqlalchemy.orm import Session


class FolderNameUpdater:
    """폴더명 업데이트 클래스"""
    
    def __init__(self):
        """초기화"""
        self.folder_name_mapping = {
            "받은편지함": "INBOX",
            "보낸편지함": "SENT", 
            "임시보관함": "DRAFT",
            "휴지통": "TRASH"
        }
        
    def check_folder_names(self, db: Session) -> Dict[str, List[str]]:
        """
        현재 폴더명 상태를 확인합니다.
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            폴더명별 사용자 목록
        """
        print("📁 현재 폴더명 상태 확인 중...")
        
        folder_status = {}
        
        # 모든 시스템 폴더 조회
        system_folders = db.query(MailFolder).filter(
            MailFolder.is_system == True
        ).all()
        
        for folder in system_folders:
            folder_name = folder.name
            if folder_name not in folder_status:
                folder_status[folder_name] = []
            folder_status[folder_name].append(f"{folder.user_uuid} (조직: {folder.org_id})")
        
        return folder_status
    
    def update_folder_names(self, db: Session, dry_run: bool = True) -> Dict[str, int]:
        """
        폴더명을 업데이트합니다.
        
        Args:
            db: 데이터베이스 세션
            dry_run: True면 실제 업데이트하지 않고 시뮬레이션만 수행
            
        Returns:
            업데이트 통계
        """
        print(f"📝 폴더명 업데이트 {'시뮬레이션' if dry_run else '실행'} 중...")
        
        update_stats = {
            "total_updated": 0,
            "inbox_updated": 0,
            "sent_updated": 0,
            "draft_updated": 0,
            "trash_updated": 0
        }
        
        try:
            for korean_name, english_name in self.folder_name_mapping.items():
                # 한국어 이름을 가진 폴더들 조회
                folders_to_update = db.query(MailFolder).filter(
                    MailFolder.name == korean_name,
                    MailFolder.is_system == True
                ).all()
                
                print(f"\n📂 '{korean_name}' → '{english_name}' 업데이트:")
                print(f"   대상 폴더 수: {len(folders_to_update)}개")
                
                for folder in folders_to_update:
                    if not dry_run:
                        folder.name = english_name
                        folder.updated_at = datetime.utcnow()
                    
                    print(f"   ✓ 사용자: {folder.user_uuid}, 조직: {folder.org_id}")
                    
                    # 통계 업데이트
                    update_stats["total_updated"] += 1
                    if korean_name == "받은편지함":
                        update_stats["inbox_updated"] += 1
                    elif korean_name == "보낸편지함":
                        update_stats["sent_updated"] += 1
                    elif korean_name == "임시보관함":
                        update_stats["draft_updated"] += 1
                    elif korean_name == "휴지통":
                        update_stats["trash_updated"] += 1
            
            if not dry_run:
                db.commit()
                print("\n✅ 데이터베이스 변경사항이 커밋되었습니다.")
            else:
                print("\n🔍 시뮬레이션 완료 (실제 변경사항 없음)")
                
        except Exception as e:
            if not dry_run:
                db.rollback()
            print(f"\n❌ 폴더명 업데이트 중 오류 발생: {e}")
            raise
        
        return update_stats
    
    def verify_update(self, db: Session) -> bool:
        """
        업데이트 결과를 검증합니다.
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            검증 성공 여부
        """
        print("\n🔍 업데이트 결과 검증 중...")
        
        # 한국어 폴더명이 남아있는지 확인
        korean_folders = db.query(MailFolder).filter(
            MailFolder.name.in_(list(self.folder_name_mapping.keys())),
            MailFolder.is_system == True
        ).all()
        
        if korean_folders:
            print(f"❌ 아직 {len(korean_folders)}개의 한국어 폴더명이 남아있습니다:")
            for folder in korean_folders:
                print(f"   - {folder.name} (사용자: {folder.user_uuid})")
            return False
        
        # 영어 폴더명 개수 확인
        english_folders = db.query(MailFolder).filter(
            MailFolder.name.in_(list(self.folder_name_mapping.values())),
            MailFolder.is_system == True
        ).all()
        
        print(f"✅ 총 {len(english_folders)}개의 영어 폴더명이 확인되었습니다:")
        
        folder_counts = {}
        for folder in english_folders:
            if folder.name not in folder_counts:
                folder_counts[folder.name] = 0
            folder_counts[folder.name] += 1
        
        for name, count in folder_counts.items():
            print(f"   - {name}: {count}개")
        
        return True


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="메일 폴더명을 한국어에서 영어로 업데이트")
    parser.add_argument("--check", action="store_true", help="현재 폴더명 상태만 확인")
    parser.add_argument("--update", action="store_true", help="실제로 폴더명 업데이트 수행")
    parser.add_argument("--dry-run", action="store_true", help="업데이트 시뮬레이션만 수행")
    
    args = parser.parse_args()
    
    if not any([args.check, args.update, args.dry_run]):
        print("사용법: python update_folder_names.py [--check|--update|--dry-run]")
        print("  --check    : 현재 폴더명 상태 확인")
        print("  --dry-run  : 업데이트 시뮬레이션")
        print("  --update   : 실제 업데이트 수행")
        return
    
    print("📁 메일 폴더명 업데이트 도구")
    print("=" * 50)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    updater = FolderNameUpdater()
    
    try:
        # 데이터베이스 연결
        db = next(get_db())
        
        if args.check:
            # 현재 상태 확인
            folder_status = updater.check_folder_names(db)
            
            print("\n📊 현재 폴더명 상태:")
            for folder_name, users in folder_status.items():
                print(f"\n📂 '{folder_name}' 폴더:")
                print(f"   사용자 수: {len(users)}명")
                if len(users) <= 5:  # 5명 이하면 모두 표시
                    for user in users:
                        print(f"   - {user}")
                else:  # 5명 초과면 일부만 표시
                    for user in users[:3]:
                        print(f"   - {user}")
                    print(f"   ... 및 {len(users) - 3}명 더")
        
        elif args.dry_run:
            # 시뮬레이션 수행
            stats = updater.update_folder_names(db, dry_run=True)
            
            print(f"\n📊 업데이트 시뮬레이션 결과:")
            print(f"   총 업데이트 대상: {stats['total_updated']}개")
            print(f"   - INBOX: {stats['inbox_updated']}개")
            print(f"   - SENT: {stats['sent_updated']}개")
            print(f"   - DRAFT: {stats['draft_updated']}개")
            print(f"   - TRASH: {stats['trash_updated']}개")
            
        elif args.update:
            # 실제 업데이트 수행
            print("⚠️  실제 데이터베이스를 수정합니다!")
            confirm = input("계속하시겠습니까? (y/N): ")
            
            if confirm.lower() != 'y':
                print("❌ 업데이트가 취소되었습니다.")
                return
            
            stats = updater.update_folder_names(db, dry_run=False)
            
            print(f"\n📊 업데이트 완료:")
            print(f"   총 업데이트: {stats['total_updated']}개")
            print(f"   - INBOX: {stats['inbox_updated']}개")
            print(f"   - SENT: {stats['sent_updated']}개")
            print(f"   - DRAFT: {stats['draft_updated']}개")
            print(f"   - TRASH: {stats['trash_updated']}개")
            
            # 검증 수행
            if updater.verify_update(db):
                print("\n✅ 폴더명 업데이트가 성공적으로 완료되었습니다!")
                print("\n💡 권장사항:")
                print("   1. 서버를 재시작하세요")
                print("   2. 프론트엔드에서 INBOX 폴더가 정상적으로 표시되는지 확인하세요")
            else:
                print("\n❌ 업데이트 검증에 실패했습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()