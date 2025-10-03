import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="skyboot_mail", 
        user="skyboot_user",
        password="skyboot_pass",
        port="5432"
    )
    cursor = conn.cursor()
    
    # mail_recipients 테이블 구조 확인
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'mail_recipients' 
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    print("mail_recipients table columns:")
    for col in columns:
        print(f"  {col[0]}: {col[1]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")