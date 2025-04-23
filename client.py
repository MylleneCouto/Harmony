import grpc
import asyncio
from datetime import datetime
from colorama import init, Fore, Style
import harmony_pb2
import harmony_pb2_grpc

init(autoreset=True)

async def receive_messages(stub, channel, username):
    prompt = Fore.YELLOW + f"{username}@{channel}> " + Style.RESET_ALL
    request = harmony_pb2.ChannelRequest(channel=channel)
    async for message in stub.StreamMessages(request):
        if message.username == username:
            continue
        timestamp = datetime.now().strftime('%H:%M:%S')
        print()
        print(Fore.GREEN + f"[{timestamp}] {message.username}: {message.content}")
        print(prompt, end='', flush=True)

async def send_messages(stub, username, channel):
    loop = asyncio.get_event_loop()
    prompt = Fore.YELLOW + f"{username}@{channel}> " + Style.RESET_ALL
    while True:
        msg = await loop.run_in_executor(None, input, prompt)
        if msg.lower() == "/sair":
            print(Fore.CYAN + "Saindo...")
            break
        await stub.SendMessage(harmony_pb2.MessageRequest(
            username=username, channel=channel, content=msg
        ))

async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel_conn:
        stub = harmony_pb2_grpc.ChatServiceStub(channel_conn)
        loop = asyncio.get_running_loop()

        username = await loop.run_in_executor(None, input, Fore.YELLOW + "Seu nome: " + Style.RESET_ALL)
        channel = await loop.run_in_executor(None, input, Fore.YELLOW + "Canal (ex: geral): " + Style.RESET_ALL)

        await stub.JoinChannel(harmony_pb2.JoinRequest(username=username, channel=channel))
        print(Fore.CYAN + f"Entrou no canal #{channel}. Digite '/sair' para sair.\n")

        recv_task = asyncio.create_task(receive_messages(stub, channel, username))
        await send_messages(stub, username, channel)
        recv_task.cancel()

if __name__ == '__main__':
    asyncio.run(main())
