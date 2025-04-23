import grpc
import asyncio
from collections import defaultdict
import harmony_pb2
import harmony_pb2_grpc

class ChatService(harmony_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.channels = defaultdict(list)
        self.lock = asyncio.Lock()

    async def JoinChannel(self, request, context):
        print(f"[Server] {request.username} entrou em #{request.channel}")
        return harmony_pb2.JoinResponse(message=f"Entrou em: #{request.channel}")

    async def SendMessage(self, request, context):
        print(f"[Server] Transmitindo messagem do {request.username} em #{request.channel}: '{request.content}'")
        async with self.lock:
            for queue in self.channels[request.channel]:
                await queue.put((request.username, request.content))
        return harmony_pb2.MessageAck(success=True)

    async def StreamMessages(self, request, context):
        peer = context.peer()
        queue = asyncio.Queue()
        async with self.lock:
            self.channels[request.channel].append(queue)
            print(f"[Server] {peer} entrou em #{request.channel}")
        try:
            while True:
                username, content = await queue.get()
                yield harmony_pb2.Message(username=username, content=content)
        except asyncio.CancelledError:
            pass
        finally:
            async with self.lock:
                self.channels[request.channel].remove(queue)
                print(f"[Server] {peer} saiu de #{request.channel}")

async def serve():
    server = grpc.aio.server()
    harmony_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    print("Server started on port 50051")
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
