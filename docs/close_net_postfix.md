
## Rocky 8 에서 Postfix 오프라인 설치 방법

### 1. 온라인 환경에서 필요한 RPM 패키지 준비

1. Rocky 8과 동일한 버전(예: Rocky 8.6) 인터넷이 되는 서버를 준비합니다.
2. 다음 명령으로 Postfix와 의존성 패키지를 한꺼번에 다운로드합니다:

   ```bash
   dnf install --downloadonly --downloaddir=/tmp/postfix_rpms postfix
   ```

   * `--downloadonly`: 설치하지 않고 다운로드만 함
   * `--downloaddir`: 다운로드 저장 경로 지정

   이렇게 하면 `/tmp/postfix_rpms` 에 postfix와 필요한 의존성 `.rpm` 파일들이 모두 모입니다.

---

### 2. 폐쇄망 서버로 패키지 전달

* `/tmp/postfix_rpms` 디렉토리 전체를 고객 Rocky 8 서버로 복사합니다.
* (scp, USB, rsync 등 물리적 방법 활용)

---

### 3. 로컬에서 설치

고객 서버에서 다음을 실행:

```bash
cd /path/to/postfix_rpms
sudo dnf install *.rpm
```

---

### 4. 설치 확인

```bash
rpm -qa | grep postfix
systemctl enable --now postfix
systemctl status postfix
```

---

## 추가 팁

* **버전 매칭**: Rocky 8.4, 8.6, 8.10 등 minor 버전에 따라 패키지 차이가 있을 수 있으므로, 반드시 **같은 버전의 Rocky 8 온라인 리포지토리**에서 다운로드해야 합니다.
* **의존성 충돌 방지**: `dnf repoquery --requires postfix` 로 사전 확인 가능.
* **추가 도구**: 많은 서버에 반복 배포해야 한다면, ISO DVD 이미지에서 `BaseOS`와 `AppStream` repo를 마운트해서 **로컬 YUM repo**를 만드는 방식도 권장됩니다.

---

👉 혹시 고객사 서버에서 postfix만 딱 필요한 건가요, 아니면 **폐쇄망 환경에서 다른 패키지들도 계속 설치**해야 할 계획인가요?
그에 따라 제가 **1회성 오프라인 설치 방법**이랑 **영구 로컬 저장소 구축 방법** 중 어떤 걸 상세히 적어드릴지 달라집니다.
