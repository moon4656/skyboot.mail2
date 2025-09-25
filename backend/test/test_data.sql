-- 테스트 도메인 추가
INSERT INTO virtual_domains (name) VALUES ('test.com');

-- 테스트 사용자 추가
INSERT INTO virtual_users (domain_id, email, password) 
VALUES (
    (SELECT id FROM virtual_domains WHERE name = 'test.com'),
    'user@test.com',
    '{PLAIN}testpassword'
);

-- 테스트 별칭 추가
INSERT INTO virtual_aliases (domain_id, source, destination)
VALUES (
    (SELECT id FROM virtual_domains WHERE name = 'test.com'),
    'admin@test.com',
    'user@test.com'
);

-- 데이터 확인
SELECT * FROM virtual_domains;
SELECT * FROM virtual_users;
SELECT * FROM virtual_aliases;