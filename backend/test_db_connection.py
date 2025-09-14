#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

try:
    from app.database import engine
    from sqlalchemy import text
    
    print("Testing database connection...")
    
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print("Database connection test: SUCCESS")
        print("Result:", result.scalar())
        
except Exception as e:
    print(f"Database connection test: FAILED")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()