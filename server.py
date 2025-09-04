import socket
import threading
import json
import os
import time
from datetime import datetime

class MessengerServer:
    def __init__(self, host='26.4.28.38', port=4899):
        self.host = host
        self.port = port
        self.clients = {}
        self.messages = []
        self.load_messages()
        
    def load_messages(self):
        if os.path.exists('data.json'):
            with open('data.json', 'r') as f:
                try:
                    self.messages = json.load(f)
                except:
                    self.messages = []
    
    def save_messages(self):
        with open('data.json', 'w') as f:
            json.dump(self.messages, f, indent=4)
    
    def send_history(self, client_socket):
        """Отправляем историю новому клиенту"""
        try:
            history_data = json.dumps(self.messages[-20:])  # Последние 20 сообщений
            client_socket.send(history_data.encode('utf-8'))
        except:
            pass
    
    def handle_client(self, client_socket, address):
        print(f'Новое подключение: {address}')
        self.clients[client_socket] = address
        
        # Сразу отправляем историю чата новому клиенту
        self.send_history(client_socket)
        
        while True:
            try:
                client_socket.settimeout(5.0)
                raw_data = client_socket.recv(1024)
                
                if not raw_data:
                    break
                
                try:
                    message = raw_data.decode('utf-8').strip()
                    
                    if message == '\x00' or message == '':
                        continue
                    
                    data = json.loads(message)
                    
                    if data['type'] == 'message':
                        message_data = {
                            'username': data['username'],
                            'message': data['message'],
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'type': 'message'
                        }
                        self.messages.append(message_data)
                        self.save_messages()
                        
                        # Рассылаем новое сообщение ВСЕМ клиентам
                        for client in list(self.clients.keys()):
                            try:
                                client.send(json.dumps(message_data).encode('utf-8'))
                            except:
                                if client in self.clients:
                                    del self.clients[client]
                                client.close()
                    
                    elif data['type'] == 'get_history':
                        self.send_history(client_socket)
                        
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                    
            except socket.timeout:
                continue
            except:
                break
        
        if client_socket in self.clients:
            del self.clients[client_socket]
        client_socket.close()
        print(f'Отключение: {address}')
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(10)
        print(f'Сервер запущен на {self.host}:{self.port}')
        
        while True:
            try:
                client_socket, address = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                thread.daemon = True
                thread.start()
            except:
                continue

if __name__ == "__main__":
    server = MessengerServer()
    server.start()
