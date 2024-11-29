from http import HTTPStatus
import random
import requests
import json
import urllib
import uuid
from flask_sqlalchemy import SQLAlchemy
import redis

from flask import abort, Flask, make_response, render_template, Response, redirect, request, jsonify

app = Flask(__name__)

naver_client_id = '0RCfb0FK4ADDQNpLQfdz'
naver_client_secret = '7ibZ5Fy7MF'
naver_redirect_uri = 'http://mylb-1731078004.ap-northeast-2.elb.amazonaws.com/memo/auth'


# Redis 클라이언트 초기화
redis_client = redis.StrictRedis(
    host = '172.31.9.176', # Redis 서버 프라이빗 ip 주소
    port = 50121, # Redis 서버에서 사용할 포트 번호
    decode_responses = True
)

try:
    redis_client.ping()
    print("Redis 연결 성공")
except redis.ConnectionError:
    print("Redis 연결 실패")


@app.route('/')
def home():
    # HTTP 세션 쿠키를 통해 이전에 로그인 한 적이 있는지를 확인한다.
    # 이 부분이 동작하기 위해서는 OAuth 에서 access token 을 얻어낸 뒤
    # user profile REST api 를 통해 유저 정보를 얻어낸 뒤 'userId' 라는 cookie 를 지정해야 된다.
    # (참고: 아래 onOAuthAuthorizationCodeRedirected() 마지막 부분 response.set_cookie('userId', user_id) 참고)
    # userId = request.cookies.get('userId', default=None)
    user_id = request.cookies.get('userId', default=None)
    name = None

    ####################################################
    # TODO: 아래 부분을 채워 넣으시오.
    #       userId 로부터 DB 에서 사용자 이름을 얻어오는 코드를 여기에 작성해야 함

    if user_id:
        print(f"user_id: {user_id}")
        try:
            real_user_id = redis_client.get(f"session:{user_id}")
            print(f"real_user_id: {real_user_id}")
            if real_user_id:
                name = redis_client.get(real_user_id)
                print(f"name: {name}")
        except redis.RedisError as e:
            print(f"Redis 에러 발생: {e}")

    ####################################################


    # 이제 클라에게 전송해 줄 index.html 을 생성한다.
    # template 로부터 받아와서 name 변수 값만 교체해준다.
    return render_template('index.html', name=name)


# 로그인 버튼을 누른 경우 이 API 를 호출한다.
# 브라우저가 호출할 URL 을 index.html 에 하드코딩하지 않고,
# 아래처럼 서버가 주는 URL 로 redirect 하는 것으로 처리한다.
# 이는 CORS (Cross-origin Resource Sharing) 처리에 도움이 되기도 한다.
#
# 주의! 아래 API 는 잘 동작하기 때문에 손대지 말 것
@app.route('/login')
def onLogin():
    params={
            'response_type': 'code',
            'client_id': naver_client_id,
            'redirect_uri': naver_redirect_uri,
            'state': random.randint(0, 10000)
        }
    urlencoded = urllib.parse.urlencode(params)
    url = f'https://nid.naver.com/oauth2.0/authorize?{urlencoded}'
    return redirect(url)


# 아래는 Authorization code 가 발급된 뒤 Redirect URI 를 통해 호출된다.
@app.route('/auth')
def onOAuthAuthorizationCodeRedirected():
    random_key = str(uuid.uuid4())  # 랜덤 문자열 생성

    # TODO: 아래 1 ~ 4 를 채워 넣으시오.

    # 1. redirect uri 를 호출한 request 로부터 authorization code 와 state 정보를 얻어낸다.
    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state:
        abort(400, "Authorization code or state is missing")


    # 2. authorization code 로부터 access token 을 얻어내는 네이버 API 를 호출한다.
    token_url = "https://nid.naver.com/oauth2.0/token"
    token_params = {
        "grant_type": "authorization_code",
        "client_id": naver_client_id,
        "client_secret": naver_client_secret,
        "code": code,
        "state": state
    }

    token_response = requests.post(token_url, data=token_params)

    if token_response.status_code != 200:
        abort(400, "Failed to get access token")

    access_token = token_response.json().get('access_token')
    print(f"access_token: {access_token}")
    # 3. 얻어낸 access token 을 이용해서 프로필 정보를 반환하는 API 를 호출하고,
    #    유저의 고유 식별 번호를 얻어낸다.
    profile_url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}


    profile_response = requests.get(profile_url, headers=headers)
    if profile_response.status_code != 200:
        abort(400, "Failed to get user profile")

    profile_data = profile_response.json()
    
    # 사용자 정보를 Redis에 저장
    user_id = profile_data['response'].get('id')
    user_name = profile_data['response'].get('name')
    print(f"user_id: {user_id}")
    print(f"user_name: {user_name}")


    # 세션 ID와 사용자 이름을 Redis에 저장
    redis_client.set(f"session:{user_id}", user_id)
    redis_client.set(user_id, user_name)


    # 4. 얻어낸 user id 와 name 을 DB 에 저장한다.
    # user_id = None
    # user_name = None
    try:
        redis_client.set(f"session:{random_key}", user_id)
    except redis.RedisError as e:
        print(f"Redis 세션 저장 에러: {e}")
        abort(500, "Failed to create session")


    # 5. 첫 페이지로 redirect 하는데 로그인 쿠키를 설정하고 보내준다.
    #    user_id 쿠키는 "dkmoon" 처럼 정말 user id 를 바로 집어 넣는 것이 아니다.
    #    그렇게 바로 user id 를 보낼 경우 정보가 노출되기 때문이다.
    #    대신 user_id cookie map 을 두고, random string -> user_id 형태로 맵핑을 관리한다.
    #      예: user_id_map = {}
    #          key = random string 으로 얻어낸 a1f22bc347ba3 이런 문자열
    #          user_id_map[key] = real_user_id
    #          user_id = key

    try:
        redis_client.set(f"session:{random_key}", user_id)
    except redis.RedisError as e:
        print(f"Redis 세션 저장 에러: {e}")
        abort(500, "Failed to create session")
    
    response = redirect('/memo')
    response.set_cookie('userId', random_key, max_age=3600, httponly=True)
    return response


@app.route('/memo', methods=['GET'])
def get_memos():
    userId = request.cookies.get('userId', default=None)
    if not userId:
        return redirect('/')

    try:
        memos = redis_client.lrange(f"user:{userId}:memos", 0, -1)
        result = [json.loads(memo) for memo in memos]
        return {'memos': result}
    except redis.RedisError as e:
        print(f"Redis 에러 발생: {e}")
        return {"error": "메모 조회 중 문제가 발생했습니다."}, HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/memo', methods=['POST'])
def post_new_memo():
    userId = request.cookies.get('userId', default=None)
    if not userId:
        return redirect('/')

    if not request.is_json:
        abort(HTTPStatus.BAD_REQUEST)

    data = request.get_json()
    memo_content = data.get('text')
    if not memo_content:
        return {"error": "메모 내용이 비어있습니다."}, HTTPStatus.BAD_REQUEST

    try:
        memo_id = redis_client.incr(f"user:{userId}:memo_count")
        memo_data = json.dumps({'id': memo_id, 'text': memo_content})
        redis_client.rpush(f"user:{userId}:memos", memo_data)
        return jsonify({"message": "메모가 저장되었습니다.", "memo_id": memo_id}), HTTPStatus.CREATED
    except redis.RedisError as e:
        print(f"Redis 에러 발생: {e}")
        return {"error": "메모 저장 중 문제가 발생했습니다."}, HTTPStatus.INTERNAL_SERVER_ERROR


if __name__ == '__main__':
    app.run('0.0.0.0', port=10121, debug=True)
