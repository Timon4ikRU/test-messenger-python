import socket
import threading
import json
import os
from datetime import datetime

class MessengerServer:
    def __init__(self, host='26.4.28.38', port=4899):  # ← ПОРТ 4899
        self.host = host
        self.port = port
        self.clients = []
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
    
    def handle_client(self, client_socket, address):
        print(f'Новое подключение: {address}')
        
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                    
                data = json.loads(message)
                
                if data['type'] == 'message':
                    message_data = {
                        'username': data['username'],
                        'message': data['message'],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.messages.append(message_data)
                    self.save_messages()
                    
                    # Рассылаем всем клиентам
                    for client in self.clients:
                        try:
                            client.send(json.dumps(message_data).encode('utf-8'))
                        except:
                            self.clients.remove(client)
                
                elif data['type'] == 'get_history':
                    client_socket.send(json.dumps(self.messages).encode('utf-8'))
                    
            except:
                break
        
        self.clients.remove(client_socket)
        client_socket.close()
        print(f'Отключение: {address}')
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f'Сервер запущен на {self.host}:{self.port}')
        
        while True:
            client_socket, address = server.accept()
            self.clients.append(client_socket)
            thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
            thread.start()

if __name__ == "__main__":
    server = MessengerServer()
    server.start()
