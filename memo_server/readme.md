## 실행 방법 

#### 메모장 초기 화면 접속
- http://mylb-1731078004.ap-northeast-2.elb.amazonaws.com/memo

## 코드 설명
1. 네이버 OAuth 로그인
- /login 에서 네이버 로그인 페이지로 리다이렉트합니다.
- /auth 에서 OAuth 인증 코드를 받아 처리하고, 사용자 정보를 Redis에 저장합니다.

2. 메모
- /memo GET 요청으로 사용자의 메모 목록을 조회합니다.
- /memo POST 요청으로 새 메모를 생성하고 저장합니다.

3. Redis
- 사용자 세션 및 메모 데이터를 Redis에 저장합니다.

## 배포된 실행 환경
- 메모 서버 public ip 주소: 54.180.24.52
- DB(redis)서버 private ip 주소: 172.31.9.176 
  메모서버에서 22번 포트를 통해 private ip로 접근
- 로드밸런서는 80번 포트에서 동작
- 대상 그룹은 8000번 포트 사용
- auth scaling을 통해 2개의 인스턴스 추가 생성