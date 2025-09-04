import socket
import json
import os
import threading
import time
from getpass import getpass

class MessengerClient:
    def __init__(self, server_ip='26.4.28.38', port=4899):
        self.server_ip = server_ip
        self.port = port
        self.username = None
        self.connected = False
        self.client_socket = None
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
    
    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(3)
            print(f"Подключаюсь к {self.server_ip}:{self.port}...")
            self.client_socket.connect((self.server_ip, self.port))
            print("Подключение установлено!")
            self.connected = True
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def keep_alive(self):
        while self.connected:
            try:
                time.sleep(2)
                if self.connected and self.client_socket:
                    self.client_socket.send(b'\x00')
            except:
                self.connected = False
                break
    
    def receive_data(self):
        """Прием всех данных от сервера"""
        while self.connected:
            try:
                if self.client_socket:
                    self.client_socket.settimeout(1)
                    data = self.client_socket.recv(16384).decode('utf-8')
                    
                    if data and data != '\x00':
                        # Пытаемся распарсить как JSON
                        try:
                            messages = json.loads(data)
                            
                            # Если это массив - значит история чата
                            if isinstance(messages, list):
                                print("\n" + "="*50)
                                print("НОВАЯ ИСТОРИЯ ЧАТА:")
                                print("="*50)
                                for msg in messages[-15:]:
                                    print(f"[{msg['timestamp']}] {msg['username']}: {msg['message']}")
                                print("="*50)
                                print("> ", end="", flush=True)
                            
                            # Если это объект - значит новое сообщение
                            elif isinstance(messages, dict) and messages.get('type') == 'message':
                                print(f"\n[{messages['timestamp']}] {messages['username']}: {messages['message']}")
                                print("> ", end="", flush=True)
                                
                        except json.JSONDecodeError:
                            continue
                            
            except:
                continue
    
    def send_json(self, data):
        try:
            if self.connected and self.client_socket:
                json_data = json.dumps(data)
                self.client_socket.send(json_data.encode('utf-8'))
                return True
        except:
            self.connected = False
        return False
    
    def start(self):
        while True:
            if self.connect_to_server():
                # Keep-alive поток
                keepalive_thread = threading.Thread(target=self.keep_alive)
                keepalive_thread.daemon = True
                keepalive_thread.start()
                
                # Поток для приема данных
                receive_thread = threading.Thread(target=self.receive_data)
                receive_thread.daemon = True
                receive_thread.start()
                
                print("Чат запущен! История загружается...")
                print("Пишите сообщения ('/exit' для выхода):")
                
                # Даем время получить историю
                time.sleep(1)
                
                while self.connected:
                    try:
                        message = input("> ")
                        
                        if message.lower() == '/exit':
                            break
                        
                        if message.strip():
                            self.send_json({
                                'type': 'message',
                                'username': self.username,
                                'message': message
                            })
                                
                    except KeyboardInterrupt:
                        break
                    except:
                        break
                
                self.connected = False
                if self.client_socket:
                    self.client_socket.close()
                
                if message.lower() == '/exit':
                    break
                    
                print("Переподключение через 2 секунды...")
                time.sleep(2)
            else:
                print("Повтор через 5 секунд...")
                time.sleep(5)

if __name__ == "__main__":
    client = MessengerClient()
    client.start()
