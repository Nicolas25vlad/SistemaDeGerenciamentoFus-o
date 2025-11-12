# fusion_server.py
import asyncio
import websockets
import json
import time
from datetime import datetime
import os

class FusionServer:
    def __init__(self):
        self.connected_clients = set()
        self.reactor_data = {}
        self.turbine_data = {}
        self.json_file_path = "fusion_data.json"
        
        # Inicializa arquivo JSON
        self.initialize_json_file()
    
    def initialize_json_file(self):
        """Inicializa o arquivo JSON com estrutura vazia"""
        initial_data = {
            "timestamp": datetime.now().isoformat(),
            "reactor": {},
            "turbine": {},
            "status": "aguardando_dados"
        }
        with open(self.json_file_path, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    async def update_json_file(self):
        """Atualiza o arquivo JSON com os dados mais recentes"""
        current_data = {
            "timestamp": datetime.now().isoformat(),
            "reactor": self.reactor_data.copy(),
            "turbine": self.turbine_data.copy(),
            "status": "ativo" if self.reactor_data or self.turbine_data else "aguardando_dados"
        }
        
        # Remove timestamps internos para evitar duplicação
        if "timestamp" in current_data["reactor"]:
            del current_data["reactor"]["timestamp"]
        if "timestamp" in current_data["turbine"]:
            del current_data["turbine"]["timestamp"]
        
        try:
            with open(self.json_file_path, 'w') as f:
                json.dump(current_data, f, indent=2)
            print(f"📄 JSON atualizado: {len(self.reactor_data)} dados reator, {len(self.turbine_data)} dados turbina")
        except Exception as e:
            print(f"❌ Erro ao atualizar JSON: {e}")
    
    async def handle_client(self, websocket):
        """Manipula conexões de clientes ComputerCraft"""
        client_ip = websocket.remote_address[0]
        print(f"🎮 Cliente CC conectado: {client_ip}")
        self.connected_clients.add(websocket)
        
        try:
            # Envia confirmação de conexão
            await websocket.send(json.dumps({
                "tipo": "conexao",
                "mensagem": "Servidor Fusion conectado",
                "timestamp": time.time()
            }))
            
            # Processa mensagens do cliente
            async for message in websocket:
                await self.process_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Cliente desconectado: {client_ip}")
        finally:
            self.connected_clients.remove(websocket)
    
    async def process_message(self, websocket, message):
        """Processa mensagens recebidas do CC"""
        try:
            data = json.loads(message)
            message_type = data.get("tipo")
            
            if message_type == "dados_reator":
                # Armazena dados do reator
                self.reactor_data = data.get("dados", {})
                self.reactor_data["timestamp"] = datetime.now().isoformat()
                
                print(f"📊 Dados do reator recebidos: {len(self.reactor_data)} campos")
                
                # Atualiza JSON
                await self.update_json_file()
                
                # Confirma recebimento
                await websocket.send(json.dumps({
                    "tipo": "confirmacao",
                    "status": "dados_reator_recebidos",
                    "timestamp": time.time()
                }))
                
            elif message_type == "dados_turbina":
                # Armazena dados da turbina
                self.turbine_data = data.get("dados", {})
                self.turbine_data["timestamp"] = datetime.now().isoformat()
                
                print(f"📈 Dados da turbina recebidos: {len(self.turbine_data)} campos")
                
                # Atualiza JSON
                await self.update_json_file()
                
                # Confirma recebimento
                await websocket.send(json.dumps({
                    "tipo": "confirmacao", 
                    "status": "dados_turbina_recebidos",
                    "timestamp": time.time()
                }))
                
            elif message_type == "solicitar_dados_brutos":
                # Envia dados brutos para o cliente
                dados_brutos = {
                    "reator": self.reactor_data,
                    "turbina": self.turbine_data,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps({
                    "tipo": "dados_brutos",
                    "dados": dados_brutos,
                    "timestamp": time.time()
                }))
                
            elif message_type == "ping":
                # Responde ping
                await websocket.send(json.dumps({
                    "tipo": "pong",
                    "timestamp": data.get("timestamp")
                }))
                
        except json.JSONDecodeError:
            print(f"📨 Mensagem não-JSON recebida: {message}")
            await websocket.send(json.dumps({
                "tipo": "erro",
                "mensagem": "Formato JSON inválido"
            }))
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")

async def main():
    server = FusionServer()
    
    print("🚀 SERVIDOR FUSION INICIADO")
    print("📡 Aguardando conexões WebSocket na porta 8765")
    print("💾 Dados brutos salvos em: fusion_data.json")
    print("💡 ComputerCraft deve conectar como cliente")
    print("-" * 50)
    
    # Inicia o servidor WebSocket
    async with websockets.serve(server.handle_client, "0.0.0.0", 8765):
        print("✅ Servidor WebSocket rodando!")
        await asyncio.Future()  # Executa indefinidamente

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro no servidor: {e}")