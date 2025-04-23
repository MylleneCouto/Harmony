import grpc
import asyncio
from datetime import datetime
from colorama import init, Fore, Style
import harmony_pb2
import harmony_pb2_grpc

init(autoreset=True)

async def receive_messages(stub, channel, username, exit_event):
    prompt = Fore.YELLOW + f"{username}@{channel}> " + Style.RESET_ALL
    request = harmony_pb2.ChannelRequest(channel=channel)
    async for message in stub.StreamMessages(request):
        if exit_event.is_set():
            break
        if message.username == username:
            continue
        timestamp = datetime.now().strftime('%H:%M:%S')
        print()
        print(Fore.GREEN + f"[{timestamp}] {message.username}: {message.content}")
        print(prompt, end='', flush=True)

async def send_messages(stub, username, channel, exit_event):
    loop = asyncio.get_event_loop()
    prompt = Fore.YELLOW + f"{username}@{channel}> " + Style.RESET_ALL
    while not exit_event.is_set():
        msg = await loop.run_in_executor(None, input, prompt)
        if msg.lower() == "/sair":
            exit_event.set()
            print(Fore.CYAN + "Saindo do canal...")
            break
        await stub.SendMessage(harmony_pb2.MessageRequest(
            username=username, channel=channel, content=msg
        ))

async def chat_loop(stub, username):
    loop = asyncio.get_event_loop()
    while True:
        channel = await loop.run_in_executor(None, input, Fore.YELLOW + "Canal (ex: geral, ou '/exit' para sair): " + Style.RESET_ALL)
        if channel.lower() == "/exit":
            print(Fore.CYAN + "Saindo do cliente...")
            break
        await stub.JoinChannel(harmony_pb2.JoinRequest(username=username, channel=channel))
        print(Fore.CYAN + f"Entrou no canal #{channel}. Digite '/sair' para voltar aos canais.\n")

        exit_event = asyncio.Event()
        recv_task = asyncio.create_task(receive_messages(stub, channel, username, exit_event))
        await send_messages(stub, username, channel, exit_event)
        recv_task.cancel()
        try:
            await recv_task
        except asyncio.CancelledError:
            pass
        print()

async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel_conn:
        stub = harmony_pb2_grpc.ChatServiceStub(channel_conn)
        loop = asyncio.get_running_loop()

        print(Fore.CYAN + "BEM-VINDO AO HARMONY")
        username = await loop.run_in_executor(None, input, Fore.YELLOW + "Seu nome: " + Style.RESET_ALL)
        await chat_loop(stub, username)

if __name__ == '__main__':
    asyncio.run(main())
