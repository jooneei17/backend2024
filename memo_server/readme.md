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

