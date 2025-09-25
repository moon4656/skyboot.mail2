from app.database.base import get_db
from app.model.base_model import User
from app.model.mail_model import MailUser, MailFolder
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:password@localhost:5432/skyboot_mail')
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    users = db.query(User).all()
    mail_users = db.query(MailUser).all()
    folders = db.query(MailFolder).all()
    
    print(f'Users: {len(users)}')
    print(f'Mail Users: {len(mail_users)}')
    print(f'Folders: {len(folders)}')
    
    print('\n=== Users ===')
    for u in users:
        print(f'User ID: {u.id}, Email: {u.email}')
    
    print('\n=== Mail Users ===')
    for mu in mail_users:
        print(f'Mail User ID: {mu.id}, Email: {mu.email}, User ID: {mu.user_id}')
    
    print('\n=== Folders ===')
    for f in folders:
        print(f'Folder: {f.name} (user_id: {f.user_id}, type: {f.folder_type})')
        
finally:
    db.close()