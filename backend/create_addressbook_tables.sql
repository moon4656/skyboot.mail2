-- SkyBoot Mail SaaS - Addressbook 테이블 생성 스크립트
-- 다중 조직 지원 및 데이터 격리를 위한 addressbook 테이블들

-- 1. departments 테이블 생성
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES departments(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_org_department_name UNIQUE (org_id, name)
);

-- 2. groups 테이블 생성
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_org_group_name UNIQUE (org_id, name)
);

-- 3. contacts 테이블 생성
CREATE TABLE IF NOT EXISTS contacts (
    contact_uuid VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    company VARCHAR(200),
    title VARCHAR(100),
    department_id INTEGER REFERENCES departments(id),
    address TEXT,
    memo TEXT,
    favorite BOOLEAN DEFAULT FALSE,
    profile_image_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_org_contact_email UNIQUE (org_id, email)
);

-- 4. contact_groups 테이블 생성 (다대다 관계)
CREATE TABLE IF NOT EXISTS contact_groups (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
    contact_uuid VARCHAR(36) NOT NULL REFERENCES contacts(contact_uuid),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_org_contact_group UNIQUE (org_id, contact_uuid, group_id)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_departments_org_id ON departments(org_id);
CREATE INDEX IF NOT EXISTS idx_groups_org_id ON groups(org_id);
CREATE INDEX IF NOT EXISTS idx_contacts_org_id ON contacts(org_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contact_groups_org_id ON contact_groups(org_id);
CREATE INDEX IF NOT EXISTS idx_contact_groups_contact_uuid ON contact_groups(contact_uuid);
CREATE INDEX IF NOT EXISTS idx_contact_groups_group_id ON contact_groups(group_id);

-- 테이블 코멘트 추가
COMMENT ON TABLE departments IS '부서 정보 테이블 - 조직별 분리';
COMMENT ON TABLE groups IS '그룹 정보 테이블 - 조직별 분리';
COMMENT ON TABLE contacts IS '연락처 정보 테이블 - 조직별 분리';
COMMENT ON TABLE contact_groups IS '연락처-그룹 관계 테이블 - 조직별 분리';

-- 컬럼 코멘트 추가
COMMENT ON COLUMN departments.org_id IS '조직 ID';
COMMENT ON COLUMN departments.name IS '부서명';
COMMENT ON COLUMN departments.parent_id IS '상위 부서 ID';

COMMENT ON COLUMN groups.org_id IS '조직 ID';
COMMENT ON COLUMN groups.name IS '그룹명';
COMMENT ON COLUMN groups.description IS '그룹 설명';

COMMENT ON COLUMN contacts.contact_uuid IS '연락처 고유 ID';
COMMENT ON COLUMN contacts.org_id IS '조직 ID';
COMMENT ON COLUMN contacts.name IS '이름';
COMMENT ON COLUMN contacts.email IS '이메일 주소';
COMMENT ON COLUMN contacts.phone IS '전화번호';
COMMENT ON COLUMN contacts.mobile IS '휴대폰 번호';
COMMENT ON COLUMN contacts.company IS '회사명';
COMMENT ON COLUMN contacts.title IS '직책';
COMMENT ON COLUMN contacts.department_id IS '부서 ID';
COMMENT ON COLUMN contacts.address IS '주소';
COMMENT ON COLUMN contacts.memo IS '메모';
COMMENT ON COLUMN contacts.favorite IS '즐겨찾기 여부';
COMMENT ON COLUMN contacts.profile_image_url IS '프로필 이미지 URL';

COMMENT ON COLUMN contact_groups.org_id IS '조직 ID';
COMMENT ON COLUMN contact_groups.contact_uuid IS '연락처 UUID';
COMMENT ON COLUMN contact_groups.group_id IS '그룹 ID';

-- 완료 메시지
SELECT 'Addressbook 테이블들이 성공적으로 생성되었습니다.' AS result;