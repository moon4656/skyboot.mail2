import requests

# 토큰
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZmQ3NjI2Zi02YWUxLTQ4ZjAtYWMzZC1kMjlkMWRiMDg1MjQiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJ1c2VybmFtZSI6InRlc3R1c2VyIiwiaXNfYWRtaW4iOmZhbHNlLCJyb2xlIjoidXNlciIsIm9yZ19pZCI6ImRlZmF1bHQtb3JnLWlkIiwib3JnX25hbWUiOiJEZWZhdWx0IE9yZ2FuaXphdGlvbiIsIm9yZ19kb21haW4iOm51bGwsImV4cCI6MTc1ODg4NzYwOCwidHlwZSI6ImFjY2VzcyIsImp0aSI6IjU1ZjlhNTE4LTRlNmMtNGJiNC04NWI4LWVlMWM0ZjU4MjkwYiJ9.bceQ4xdND9JlwxSqpEQHrO3CIJumSMO1VkvRCWB2UvA"

headers = {"Authorization": f"Bearer {token}"}

# inbox 테스트
print("📧 inbox 테스트...")
response = requests.get("http://localhost:8000/api/v1/mail/inbox", headers=headers)
print(f"상태 코드: {response.status_code}")
print(f"응답: {response.text}")