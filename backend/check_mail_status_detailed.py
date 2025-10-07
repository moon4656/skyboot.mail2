import psycopg2
import json
from datetime import datetime

def check_mail_status():
    """Check mail status in detail"""
    try:
        # Database connection
        conn = psycopg2.connect(
            host='localhost',
            database='skyboot_mail',
            user='postgres',
            password='1234'
        )
        cur = conn.cursor()

        print('Mail Status Analysis')
        print('=' * 50)

        # 1. Total mail count
        cur.execute('SELECT COUNT(*) FROM mails')
        total_mails = cur.fetchone()[0]
        print(f'Total mails: {total_mails}')

        # 2. user01 sent mails
        cur.execute("""
            SELECT COUNT(*) FROM mails m
            JOIN mail_users mu ON m.sender_uuid = mu.user_uuid
            WHERE mu.email = 'user01@example.com'
        """)
        user01_sent = cur.fetchone()[0]
        print(f'user01 sent mails: {user01_sent}')

        # 3. user01 received mails
        cur.execute("""
            SELECT COUNT(*) FROM mail_recipients mr
            WHERE mr.recipient_email = 'user01@example.com'
        """)
        user01_received = cur.fetchone()[0]
        print(f'user01 received mails: {user01_received}')

        # 4. user01 mail status in folders
        cur.execute("""
            SELECT 
                mif.folder_name,
                mif.is_read,
                COUNT(*) as count
            FROM mail_in_folder mif
            JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            WHERE mu.email = 'user01@example.com'
            GROUP BY mif.folder_name, mif.is_read
            ORDER BY mif.folder_name, mif.is_read
        """)
        folder_status = cur.fetchall()
        print(f'\nuser01 mail status by folder:')
        for folder, is_read, count in folder_status:
            read_status = 'read' if is_read else 'unread'
            print(f'  {folder}: {read_status} {count}')

        # 5. Recent mails
        cur.execute("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.created_at,
                mu.email as sender_email
            FROM mails m
            JOIN mail_users mu ON m.sender_uuid = mu.user_uuid
            WHERE m.created_at > NOW() - INTERVAL '10 minutes'
            ORDER BY m.created_at DESC
            LIMIT 5
        """)
        recent_mails = cur.fetchall()
        print(f'\nRecent mails (last 10 minutes):')
        for mail_uuid, subject, created_at, sender in recent_mails:
            print(f'  {mail_uuid}: {subject} (sender: {sender})')

        # 6. user01 unread mail details
        cur.execute("""
            SELECT 
                m.mail_uuid,
                m.subject,
                mif.is_read,
                mif.folder_name,
                m.created_at
            FROM mails m
            JOIN mail_recipients mr ON m.mail_uuid = mr.mail_uuid
            LEFT JOIN mail_in_folder mif ON m.mail_uuid = mif.mail_uuid
            LEFT JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            WHERE mr.recipient_email = 'user01@example.com'
            AND (mif.is_read = false OR mif.is_read IS NULL)
            ORDER BY m.created_at DESC
            LIMIT 10
        """)
        unread_details = cur.fetchall()
        print(f'\nuser01 unread mail details:')
        for mail_uuid, subject, is_read, folder_name, created_at in unread_details:
            print(f'  {mail_uuid}: {subject}')
            print(f'    read_status: {is_read}, folder: {folder_name}, created: {created_at}')

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Database query error: {e}")

if __name__ == "__main__":
    check_mail_status()