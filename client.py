import socket
import json
import os
import threading
from getpass import getpass

class MessengerClient:
    def __init__(self, server_ip='26.4.28.38', port=4899):  # ← ПОРТ 4899
        self.server_ip = server_ip
        self.port = port
        self.username = None
        self.load_login()
        
    def load_login(self):
        if os.path.exists('login.json'):
            try:
                with open('login.json', 'r') as f:
                    login_data = json.load(f)
                    self.username = login_data.get('username')
                    print(f"Добро пожаловать, {self.username}!")
            except:
                self.register_user()
        else:
            self.register_user()
    
    def register_user(self):
        print("=== Регистрация ===")
        username = input("Придумайте логин: ")
        password = getpass("Придумайте пароль: ")
        
        login_data = {
            'username': username,
            'password': password
        }
        
        with open('login.json', 'w') as f:
            json.dump(login_data, f, indent=4)
        
        self.username = username
        print("Регистрация завершена!")
    
    def receive_messages(self, client_socket):
        while True:
            try:
                message = client_socket.recv(4096).decode('utf-8')
                if message:
                    data = json.loads(message)
                    print(f"\n[{data['timestamp']}] {data['username']}: {data['message']}")
                    print("> ", end="", flush=True)
            except:
                print("\nСоединение с сервером потеряно!")
                break
    
    def start(self):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(10)
            print(f"Подключаюсь к {self.server_ip}:{self.port}...")
            client.connect((self.server_ip, self.port))
            print("Подключение установлено!")
            
            # Запрос истории сообщений
            client.send(json.dumps({'type': 'get_history'}).encode('utf-8'))
            history = json.loads(client.recv(16384).decode('utf-8'))
            
            print("\n=== История чата ===")
            for msg in history[-20:]:  # Последние 20 сообщений
                print(f"[{msg['timestamp']}] {msg['username']}: {msg['message']}")
            print("====================\n")
            
            # Поток для приема сообщений
            receive_thread = threading.Thread(target=self.receive_messages, args=(client,))
            receive_thread.daemon = True
            receive_thread.start()
            
            print("Чат запущен! Пишите сообщения ('/exit' для выхода):")
            while True:
                try:
                    message = input("> ")
                    if message.lower() == '/exit':
                        break
                    
                    if message.strip():
                        client.send(json.dumps({
                            'type': 'message',
                            'username': self.username,
                            'message': message
                        }).encode('utf-8'))
                except KeyboardInterrupt:
                    print("\nВыход...")
                    break
            
            client.close()
            
        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу! Проверь:")
            print("1. Сервер запущен на 26.4.28.38:4899")
            print("2. Файрволл разрешает подключения")
            print("3. Radmin VPN работает (если используется)")
        except Exception as e:
            print(f"Ошибка подключения: {e}")

if __name__ == "__main__":
    client = MessengerClient()
    client.start()
