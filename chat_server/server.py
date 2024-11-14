import socket
import select
import json
import sys
import threading
import queue
from absl import app, flags

import message_pb2 as pb

FLAGS = flags.FLAGS
flags.DEFINE_integer(name='port', default=None, required=True, help='서버 port 번호')

class ChatServer:
    def __init__(self, port):
        # 서버 소켓 초기화
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', port))
        self.server_socket.listen(5)
        
        # 클라이언트와 방 관리
        self.sockets_list = [self.server_socket]
        self.clients = {}  # socket: nickname
        self.rooms = {}    # room_id: {title, members}
        
        # 동기화를 위한 락
        self.clients_lock = threading.Lock()
        self.rooms_lock = threading.Lock()
        
        # worker thread 관리
        self.message_queue = queue.Queue()
        self.workers = []
        self.num_workers = 2  # worker thread 수
        self.running = True

        # 추가된 부분: 각 클라이언트별 메시지 큐와 처리 중인 클라이언트를 추적하기 위한 집합
        self.message_queues = {}  # {client_socket: message_queue}
        self.processing_clients = set()  # 현재 처리 중인 클라이언트를 추적하는 집합

    def worker_thread(self):
        """메시지 큐에서 메시지를 처리하는 worker thread"""
        while self.running:
            try:
                # 큐에서 메시지 가져옴
                client_socket, message, format_type = self.message_queue.get(timeout=1)
                if client_socket is None:  # 종료 신호
                    break

                print(f"worker_thread에서 받은 message: {message}")
                
                # json 메시지 타입에 따른 처리
                if format_type == 'json':
                    message_type = message.get('type') # json 형식 메시지 처리. get()메소드의 경우 키 없을 때 None 반환(안전)
                    with self.clients_lock:  # 클라이언트 정보 접근시 락 사용
                        if message_type == 'CSName':
                            self.handle_name(client_socket, message)
                        elif message_type == 'CSRooms':
                            self.handle_rooms(client_socket, message)
                        elif message_type == 'CSCreateRoom':
                            self.handle_create_room(client_socket, message)
                        elif message_type == 'CSJoinRoom':
                            self.handle_join_room(client_socket, message)
                        elif message_type == 'CSLeaveRoom':
                            self.handle_leave_room(client_socket, message)
                        elif message_type == 'CSChat':
                            self.handle_chat(client_socket, message)
                        elif message_type == 'CSShutdown':
                            self.running = False
                            print("서버를 종료합니다.")
                            return

                # protobuf 메시지 타입에 따른 처리
                else:
                    # Protobuf Type 메시지 처리
                    try:
                        # Protobuf 메시지는 바이트 스트림으로 수신되므로 이를 역직렬화
                        if isinstance(message, bytes):  # 바이트인지 확인

                            # Protobuf 역직렬화 (Type 필드 먼저 확인)
                            message_type_int = pb.Type.FromString(message)  # Type 필드만 먼저 파싱
                            print(f"message_type_int.type: {message_type_int.type}")
                            message_type_name = pb.Type.MessageType.Name(message_type_int.type)
                            print(f"message_type_name: {message_type_name}")
                            # actual_message = pb.CSName.FromString(message)
                            # print(f"actual_message.name: {actual_message.name}")

                            with self.clients_lock: 
                                if message_type_name == 'CS_NAME':
                                    actual_message = pb.CSName.FromString(message)
                                    print(f"CS_NAME에서 actual_message.name: {actual_message.name}") 
                                    self.handle_name(client_socket, actual_message.name)
                                elif message_type_name == 'CS_ROOMS':
                                    self.handle_rooms(client_socket, {})
                                elif message_type_name == 'CS_CREATE_ROOM':
                                    actual_message = pb.CSCreateRoom.FromString(message)
                                    print(f"create room name : {actual_message.title}")
                                    #  self.handle_create_room(client_socket, {'title': create_message.title})
                                elif message_type_name == 'CS_JOIN_ROOM':
                                    actual_message = pb.CSJoinRoom.FromString(message)
                                    print(f"join roon number: {actual_message}")
                                    # self.handle_join_room(client_socket, {'roomId': join_message.roomId})
                                elif message_type_name == 'CS_LEAVE_ROOM':
                                    print("leave room")
                                    # self.handle_leave_room(client_socket, {})
                                elif message_type_name == 'CS_CHAT':
                                    actual_message = pb.CSChat.FromString(message)  
                                    print(f"chat message: {actual_message.text}")
                                    # self.handle_chat(client_socket, {'text': chat_message.text})
                                elif message_type_name == 'CS_SHUTDOWN':
                                    self.running = False
                                    print("서버를 종료합니다.")
                                    return
                    except Exception as e:
                        print(f"Protobuf parsing error: {e}")

                self.message_queue.task_done()
                
            except queue.Empty:
                continue
            except ConnectionRefusedError:
                print(f"disconnect_client")
            except Exception as e:
                print(f"Worker error: {e}")

    def start_workers(self):
        """Worker thread들을 시작"""
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self.worker_thread)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def stop_workers(self):
        """Worker thread들을 종료"""
        self.running = False
        for _ in self.workers:
            self.message_queue.put((None, None))
        for worker in self.workers:
            worker.join()

    def send_message(self, client_socket, message):
        """메시지를 클라이언트에게 전송"""
        try:
            message_bytes = json.dumps(message).encode()
            length = len(message_bytes)
            client_socket.sendall(length.to_bytes(2, byteorder='big') + message_bytes)
        except:
            self.disconnect_client(client_socket)



    def handle_name(self, client_socket, data):
        """대화명 설정 처리"""
        print("handle_name 함수 들어옴")
        print(f"data: {type(data)}")
        print(f"isinstance(data, str): {isinstance(data, str)}")

        # client_socket에 해당하는 Client 객체를 가져옴
        client = self.clients.get(client_socket)
        if not client:
            print(f"클라이언트를 찾을 수 없습니다: {client_socket}")
            return
        else:
            print(f"client 객체: {client}")


        # 클라이언트가 보낸 데이터에서 'name' 필드를 가져옴
        if isinstance(data, dict):  # JSON 처리
            name = data.get('name', '')
            print(f"handler 함수에서 name:: {name}")
        elif isinstance(data, str):  # Protobuf에서 이미 파싱된 문자열이 전달된 경우
            name = data
            print(f"handler 함수에서 name:: {name}")

        print(f"if not name: {not name}")            

        if not name:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '유효한 대화명을 입력해주세요.'
            })
            return
        else:
            print("유효한 대화명 맞음")

        # 다른 클라이언트가 이미 사용 중인 닉네임인지 확인
        if name in self.clients.values():
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': f'대화명 "{name}"은(는) 이미 사용 중입니다.'
            })
            return
        print("사용중인 닉네임도 아님")

        # 기존 이름 확인
        old_name = self.clients.get(client_socket)
        print(f"old_name: {old_name}")

         # old_name이 Client 객체인 경우, 아직 대화명이 설정되지 않은 것으로 간주
        if isinstance(old_name, Client):
            old_name = None  # 아직 대화명이 설정되지 않음

        # 새로운 대화명 설정 (기존 이름 덮어쓰기)
        self.clients[client_socket] = name  # 이제 Client 객체 대신 실제 대화명을 저장

        if old_name:
            # 기존 이름이 있으면 이름 변경 메시지 전송
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': f'대화명이 {old_name}에서 {name}으로 변경되었습니다.'
            })
        else:
            # 처음 이름을 설정하는 경우
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': f'대화명이 {name}으로 설정되었습니다.'
            })

    def handle_rooms(self, client_socket, data):
        room_list = [
            {
                'roomId': room_id,
                'title': room_info['title'],
                'members': room_info['members']
            }
            for room_id, room_info in self.rooms.items()
        ]
        response = {
            'type': 'SCRoomsResult',
            'rooms': room_list
        }
        self.send_message(client_socket, response)


    def handle_create_room(self, client_socket, data):
        nickname = self.clients.get(client_socket)
        if not nickname:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '대화명을 먼저 설정해주세요.'
            })
            return
            
        # 방 제목 확인
        title = data.get('title', '').strip()
        if not title:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '방 제목을 지정해야 합니다.'
            })
            return

        # 현재 사용자가 어떤 방에도 속해있지 않은지 확인
        is_in_room = False
        for room_info in self.rooms.values():
            if nickname in room_info['members']:
                is_in_room = True
                break

        if is_in_room:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '이미 방에 있어 새로운 방을 만들 수 없습니다.'
            })
            return

        # 새로운 방 생성 및 입장
        with self.rooms_lock:
            room_id = len(self.rooms) + 1
            self.rooms[room_id] = {
                'title': title,
                'members': [nickname]
            }
        
        self.send_message(client_socket, {
            'type': 'SCSystemMessage',
            'text': f'방 {title} 생성 완료! 방에 입장했습니다.'
        })
    

    def handle_join_room(self, client_socket, data):
        """클라이언트가 방에 입장할 때 처리"""
        nickname = self.clients.get(client_socket)
        if not nickname:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '대화명을 먼저 설정해주세요.'
            })
            return

        room_id = data.get('roomId')
        if not room_id:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '방 번호를 지정해주세요.'
            })
            return

        # 현재 다른 방에 있는지 확인
        for room_info in self.rooms.values():
            if nickname in room_info['members']:
                self.send_message(client_socket, {
                    'type': 'SCSystemMessage',
                    'text': '대화 방에 있을 때는 다른 방에 들어갈 수 없습니다.'
                })
                return

        # 방이 존재하는지 확인
        if room_id not in self.rooms:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '대화방이 존재하지 않습니다.'
            })
            return

        # 방에 입장
        with self.rooms_lock:
            if nickname not in self.rooms[room_id]['members']:
                self.rooms[room_id]['members'].append(nickname)

        # 락 해제 후 메시지 전송 작업 수행
        response = {
            'type': 'SCSystemMessage',
            'text': f'{self.rooms[room_id]["title"]} 방에 입장했습니다.'
        }
        self.send_message(client_socket, response)

        # 본인을 제외한 모든 멤버에게 입장 알림 메시지 전송
        for member_nickname in self.rooms[room_id]['members']:
            if member_nickname != nickname:
                member_socket = next((sock for sock, nick in self.clients.items() if nick == member_nickname), None)
                if member_socket:
                    try:
                        # 여기서 입장한 사용자의 닉네임인 `nickname`을 사용하여 메시지를 전송
                        self.send_message(member_socket, {
                            'type': 'SCSystemMessage',
                            'text': f'[시스템 메시지] [{nickname}] 님이 입장했습니다.'  # 중요한 부분: `nickname` 사용
                        })
                    except Exception as e:
                        print(f'{member_nickname}에게 메시지 전송 실패: {e}')


    def handle_leave_room(self, client_socket, data):
        """클라이언트가 방을 떠날 때 처리"""
        nickname = self.clients.get(client_socket)
        if not nickname:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '대화명을 먼저 설정해주세요.'
            })
            return

        # 현재 사용자가 속한 방을 찾아서 나가기 처리
        left_room = None
        room_id_to_delete = None  # 나중에 방 삭제를 위한 변수

        with self.rooms_lock:
            for room_id, room_info in self.rooms.items():
                if nickname in room_info['members']:
                    room_info['members'].remove(nickname)
                    left_room = room_info
                    room_id_to_delete = room_id  # 방이 비면 삭제할 방 ID 저장
                    
                    break  # 방을 찾았으므로 더 이상 반복할 필요 없음

        if left_room:
            # 퇴장하는 사용자에게 메시지 전송
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': f'{left_room["title"]} 대화 방에서 퇴장했습니다.'
            })

            # 다른 멤버들에게 퇴장 알림 메시지 전송
            response = {
                'type': 'SCSystemMessage',
                'text': f'[{nickname}] 님이 퇴장했습니다.'  # 중요한 부분: 실제로 나간 사람의 닉네임 사용
            }

            for member_nickname in left_room['members']:
                member_socket = next((sock for sock, nick in self.clients.items() if nick == member_nickname), None)
                if member_socket:
                    try:
                        # 여기서 퇴장한 사용자의 닉네임인 `nickname`을 사용하여 메시지를 전송
                        self.send_message(member_socket, response)
                    except Exception as e:
                        print(f'{member_nickname}에게 메시지 전송 실패: {e}')
            
            # 방이 비었으면 방 제거 (이미 위에서 삭제되었으므로 이 부분은 필요 없음)
            if not left_room['members']:
                with self.rooms_lock:
                    del self.rooms[room_id_to_delete]  # 빈 방 삭제
                
        else:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '현재 대화 방에 들어가 있지 않습니다.'
            })


    def handle_chat(self, client_socket, data):
        """채팅 메시지 처리"""
        text = data.get('text', '')
        nickname = self.clients.get(client_socket)
        
        if not nickname or not text:
            return

        # 사용자가 방에 속해 있는지 여부 추적하는 변수
        in_room = False

        with self.rooms_lock:
            for room_id, room_info in self.rooms.items():
                if nickname in room_info['members']:
                    in_room = True  # 사용자가 방에 있음
                    response = {
                        'type': 'SCChat',
                        'member': nickname,
                        'text': text
                    }
                    # 본인을 제외하고 같은 방의 다른 멤버들에게만 메시지 전송
                    for client in self.clients:
                        if self.clients[client] in room_info['members'] and self.clients[client] != nickname:
                            self.send_message(client, response)  # 즉시 클라이언트에게 메시지 전송
                    break
                    
        # 만약 사용자가 어떤 방에도 속해 있지 않다면 시스템 메시지 전송
        if not in_room:
            self.send_message(client_socket, {
                'type': 'SCSystemMessage',
                'text': '현재 대화방에 들어가 있지 않습니다.'
            })


    def start(self):
        """서버 시작"""
        print(f"서버가 포트 {FLAGS.port}에서 시작되었습니다...")
        self.start_workers()
        
        try:
            while self.running:
                try:
                    read_sockets, _, _ = select.select(self.sockets_list, [], [], 1)

                    for sock in read_sockets:
                        if sock == self.server_socket:
                            client_socket, addr = self.server_socket.accept()
                            client = Client(client_socket)
                            print(f"새로운 클라이언트 연결: {addr}")
                            self.sockets_list.append(client_socket)
                            self.clients[client_socket] = client  # 클라이언트 저장
                            continue

                        # 기존 클라이언트 처리
                        client = self.clients.get(sock)
                        if not client:
                            print(f"클라이언트를 찾을 수 없습니다: {sock}")
                            continue

                        print(f"client: {client}")

                        # 메시지 길이 읽기 (2바이트)
                        length_bytes = sock.recv(2)
                        if not length_bytes:
                            print("클라이언트 연결 끊김")
                            self.disconnect_client(sock)
                            continue

                        message_length = int.from_bytes(length_bytes, byteorder='big')
                        print(f"message_length: {message_length}")

                        # 전체 메시지를 받을 때까지 대기
                        data = sock.recv(message_length)
                        if not data:
                            print("메시지 수신 실패")
                            self.disconnect_client(sock)
                            continue

                        print(f"data: {data}")

                        # JSON 메시지 처리 시도
                        try:
                            message = json.loads(data.decode())
                            self.message_queue.put((sock, message, 'json'))
                            continue
                        except json.JSONDecodeError:
                            pass  # JSON이 아닌 경우 Protobuf 처리로 진행

                        # Protobuf 메시지 처리
                        # Protobuf 메시지도 큐에 넣음
                        self.message_queue.put((sock, data, 'protobuf'))
                        
                except Exception as e:
                    print(f"소켓 처리 오류: {e}")
                    continue

        finally:
            self.stop_workers()
            for sock in self.sockets_list:
                sock.close()

class Client:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.recv_buffer = b''  # 수신된 데이터를 저장할 버퍼
        self.condition = threading.Condition()  # Condition Variable

    def receive_data(self, num_bytes):
        """소켓에서 num_bytes 만큼 데이터를 읽어 recv_buffer에 추가"""
        data = self.sock.recv(num_bytes)
        if not data:
            return False  # 연결 끊어진 경우
        with self.condition:
            self.recv_buffer += data
            self.condition.notify_all()  # 데이터가 추가되었음을 알림
        return True

    def wait_for_data(self, expected_length):
        """원하는 길이 만큼 데이터가 수신될 때까지 대기"""
        with self.condition:
            while len(self.recv_buffer) < expected_length:
                if not self.condition.wait(timeout=5):  # 타임아웃 설정 (5초)
                    print(f"데이터 수신 타임아웃: {expected_length} 바이트 필요하지만 {len(self.recv_buffer)} 바이트만 수신됨")
                    return False
        return True
    


def main(argv):
    server = ChatServer(FLAGS.port)
    server.start()

if __name__ == "__main__":
    app.run(main)