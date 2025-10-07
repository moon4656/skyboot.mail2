"""
기존 메일 사용자들의 누락된 기본 폴더 생성 스크립트

이 스크립트는 기존에 생성된 메일 사용자들에게 누락된 기본 폴더들을 생성합니다.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
import uuid

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import MailUser, MailFolder, FolderType
from sqlalchemy.orm import Session


class MailFolderFixer:
    """메일 폴더 수정 클래스"""
    
    def __init__(self):
        self.db = next(get_db())
    
    def create_default_folders_for_user(self, user_uuid: str, org_id: str) -> list:
        """
        사용자의 기본 메일 폴더들을 생성합니다.
        
        Args:
            user_uuid: 사용자 UUID
            org_id: 조직 ID
            
        Returns:
            생성된 폴더 목록
        """
        # 기본 폴더 정의
        default_folders = [
            {"name": "받은편지함", "folder_type": FolderType.INBOX, "is_system": True},
            {"name": "보낸편지함", "folder_type": FolderType.SENT, "is_system": True},
            {"name": "임시보관함", "folder_type": FolderType.DRAFT, "is_system": True},
            {"name": "휴지통", "folder_type": FolderType.TRASH, "is_system": True}
        ]
        
        created_folders = []
        
        for folder_info in default_folders:
            # 이미 존재하는 폴더인지 확인
            existing_folder = self.db.query(MailFolder).filter(
                MailFolder.user_uuid == user_uuid,
                MailFolder.org_id == org_id,
                MailFolder.folder_type == folder_info["folder_type"]
            ).first()
            
            if not existing_folder:
                folder = MailFolder(
                    folder_uuid=str(uuid.uuid4()),
                    user_uuid=user_uuid,
                    org_id=org_id,
                    name=folder_info["name"],
                    folder_type=folder_info["folder_type"],
                    is_system=folder_info["is_system"],
                    created_at=datetime.now(timezone.utc)
                )
                
                self.db.add(folder)
                created_folders.append(folder_info["name"])
        
        return created_folders
    
    def fix_all_mail_users(self):
        """모든 메일 사용자의 누락된 폴더를 수정합니다."""
        print("🔧 메일 사용자 폴더 수정 시작")
        print("=" * 60)
        
        try:
            # 모든 메일 사용자 조회
            mail_users = self.db.query(MailUser).filter(MailUser.is_active == True).all()
            
            if not mail_users:
                print("❌ 활성화된 메일 사용자가 없습니다.")
                return
            
            print(f"📊 총 {len(mail_users)}명의 메일 사용자 발견")
            
            total_fixed = 0
            total_created_folders = 0
            
            for mail_user in mail_users:
                print(f"\n👤 사용자 처리 중: {mail_user.email} (UUID: {mail_user.user_uuid})")
                
                # 기존 폴더 확인
                existing_folders = self.db.query(MailFolder).filter(
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.org_id == mail_user.org_id
                ).all()
                
                existing_types = [folder.folder_type for folder in existing_folders]
                print(f"   기존 폴더: {[folder_type.value for folder_type in existing_types]}")
                
                # 누락된 폴더 생성
                created_folders = self.create_default_folders_for_user(
                    mail_user.user_uuid, 
                    mail_user.org_id
                )
                
                if created_folders:
                    total_fixed += 1
                    total_created_folders += len(created_folders)
                    print(f"   ✅ 생성된 폴더: {created_folders}")
                else:
                    print(f"   ✓ 모든 기본 폴더가 이미 존재함")
            
            # 변경사항 커밋
            self.db.commit()
            
            print("\n" + "=" * 60)
            print("🎉 메일 폴더 수정 완료!")
            print(f"📊 수정된 사용자: {total_fixed}명")
            print(f"📁 생성된 폴더: {total_created_folders}개")
            
            if total_fixed > 0:
                print("\n💡 권장사항:")
                print("   - 서버를 재시작하여 변경사항을 적용하세요")
                print("   - 받은 메일함 API를 다시 테스트해보세요")
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.db.close()
    
    def check_user_folders(self, email: str = None):
        """특정 사용자의 폴더 상태를 확인합니다."""
        print("🔍 사용자 폴더 상태 확인")
        print("=" * 60)
        
        try:
            if email:
                mail_users = self.db.query(MailUser).filter(
                    MailUser.email == email,
                    MailUser.is_active == True
                ).all()
            else:
                mail_users = self.db.query(MailUser).filter(MailUser.is_active == True).all()
            
            if not mail_users:
                print(f"❌ 메일 사용자를 찾을 수 없습니다: {email}")
                return
            
            for mail_user in mail_users:
                print(f"\n👤 사용자: {mail_user.email}")
                print(f"   UUID: {mail_user.user_uuid}")
                print(f"   조직 ID: {mail_user.org_id}")
                
                # 폴더 조회
                folders = self.db.query(MailFolder).filter(
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.org_id == mail_user.org_id
                ).all()
                
                if folders:
                    print(f"   📁 폴더 목록:")
                    for folder in folders:
                        print(f"      - {folder.name} ({folder.folder_type.value}) [시스템: {folder.is_system}]")
                else:
                    print(f"   ❌ 폴더가 없습니다!")
                
                # 누락된 기본 폴더 확인
                required_types = [FolderType.INBOX, FolderType.SENT, FolderType.DRAFT, FolderType.TRASH]
                existing_types = [folder.folder_type for folder in folders]
                missing_types = [folder_type for folder_type in required_types if folder_type not in existing_types]
                
                if missing_types:
                    print(f"   ⚠️ 누락된 폴더: {[folder_type.value for folder_type in missing_types]}")
                else:
                    print(f"   ✅ 모든 기본 폴더 존재")
                    
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.db.close()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="메일 폴더 수정 도구")
    parser.add_argument("--check", "-c", help="특정 사용자의 폴더 상태 확인 (이메일 주소)")
    parser.add_argument("--check-all", action="store_true", help="모든 사용자의 폴더 상태 확인")
    parser.add_argument("--fix", action="store_true", help="누락된 폴더 자동 수정")
    
    args = parser.parse_args()
    
    fixer = MailFolderFixer()
    
    if args.check:
        fixer.check_user_folders(args.check)
    elif args.check_all:
        fixer.check_user_folders()
    elif args.fix:
        fixer.fix_all_mail_users()
    else:
        print("사용법:")
        print("  python fix_missing_mail_folders.py --check user@example.com  # 특정 사용자 확인")
        print("  python fix_missing_mail_folders.py --check-all              # 모든 사용자 확인")
        print("  python fix_missing_mail_folders.py --fix                    # 누락된 폴더 수정")


if __name__ == "__main__":
    main()