import asyncio
import socket
import pickle
import os
import copy
import random
import time
import threading

HOST, PORT = None, None
TRACKER_IP, TRACKER_PORT = None, None
FILE = None
FILE_DATA = None
LOG_FILE = "logs.txt"


async def log_message(message):
    async with asyncio.Lock():
        with open(f"{PORT}/{LOG_FILE}", "a") as file:
            file.write(f"{message}\n")
            file.close()


async def read_logs():
    async with asyncio.Lock():
        with open(f"{PORT}/{LOG_FILE}", "r") as file:
            lines = file.readlines()
            print("".join([item for item in lines]))
            file.close()


async def send_heartbeat():
    while True:
        time.sleep(5)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((HOST, PORT))
        message = f"heartbeat"
        udp_socket.sendto(pickle.dumps(message), (TRACKER_IP, TRACKER_PORT))
        udp_socket.close()
        await asyncio.get_event_loop().create_task(
            log_message(f"sent message: {message} to {TRACKER_IP}:{TRACKER_PORT}"))


async def handle_seeder_download_request(client):
    loop = asyncio.get_event_loop()
    res = pickle.loads(await loop.sock_recv(client, 1024))
    await loop.create_task(log_message(res))
    for chunk in FILE_DATA:
        await loop.sock_sendall(client, pickle.dumps([chunk]))
        await loop.create_task(log_message(f"sending chunk..."))
        time.sleep(0.1)
    time.sleep(1)
    await loop.sock_sendall(client, pickle.dumps("done"))

    # await loop.sock_sendall(client, pickle.dumps(FILE_DATA))
    chunk_size = 1024
    # chunks = [file_data[i:i + chunk_size] for i in range(0, len(file_data), chunk_size)]
    # chunks = copy.deepcopy(FILE_DATA)
    # for chunk in chunks:
    #     loop = asyncio.get_event_loop()
    #     await loop.sock_sendall(client, pickle.dumps(chunk))
    #     print(chunk)

    # print("done")


async def run_peer_as_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((HOST, PORT))
    tcp_socket.listen(5)
    tcp_socket.setblocking(False)
    loop = asyncio.get_event_loop()

    # async def accept_connections(s):
    #     while True:
    #         print("lsdfhsdlkfldhjf")
    #         l = asyncio.get_event_loop()
    #         client, addr = await l.sock_accept(s)
    #         print("===============")
    #         await loop.create_task(log_message(f"connected to client :{addr}"))
    #         loop.create_task(handle_seeder_download_request(client))
    #
    # loop.create_task(accept_connections(tcp_socket))
    while True:
        client, addr = await loop.sock_accept(tcp_socket)
        loop.create_task(handle_seeder_download_request(client))


def send_download_request(seeder, file_name):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((str(seeder[0]), int(seeder[1])))
    message = f"get file"
    tcp_socket.send(pickle.dumps(message))
    asyncio.run(log_message(f"sent message: {message} to {seeder[0]}:{seeder[1]}"))
    # tcp_socket.settimeout(10)
    try:
        file = open(f"{PORT}/{str(file_name)}", "wb")
        while True:
            res = tcp_socket.recv(4096)
            data = pickle.loads(res)
            # print(data)
            if data == "done":
                break
            file.writelines(data)
        tcp_socket.close()
        file.close()
        return True
    except Exception as e:
        tcp_socket.close()
        asyncio.run(log_message(e))
        return False


def send_is_download_successful_to_tracker(is_successful, file_name, seeder_ip, seeder_port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if is_successful:
        message = f"successful to get {file_name} from ({seeder_ip, seeder_port})"
    else:
        message = f"unsuccessful to get {file_name} from ({seeder_ip, seeder_port})"
    udp_socket.bind((HOST, PORT))
    udp_socket.sendto(pickle.dumps(message), (TRACKER_IP, TRACKER_PORT))
    udp_socket.close()
    asyncio.run(log_message(f"sent message: {message} to {TRACKER_IP}:{TRACKER_PORT}"))


def run_peer_as_client(file_name):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((HOST, PORT))
    message = f"get {file_name}"
    udp_socket.sendto(pickle.dumps(message), (TRACKER_IP, TRACKER_PORT))
    asyncio.run(log_message(f"sent message: {message} to {TRACKER_IP}:{TRACKER_PORT}"))

    udp_socket.settimeout(5)
    try:
        res, addr = udp_socket.recvfrom(1024)
        udp_socket.close()
        if pickle.loads(res) == "wrong file":
            asyncio.run(log_message(pickle.loads(res)))
            return False
        else:
            seeders = pickle.loads(res)
            file_size = seeders[-1]
            if len(seeders) == 0:
                asyncio.run(log_message(f"there is no seeder to upload file:{file_name}"))
                return False
            chose_seed = random.choice(seeders[:-1])
            asyncio.run(log_message(
                f"message from server: \"seeders: {seeders} have file: {file_name} with size: {file_size} and seeder: "
                f"{chose_seed} had chosen\""))
            try:
                is_successful = send_download_request(chose_seed, file_name)
                send_is_download_successful_to_tracker(is_successful, file_name, chose_seed[0], chose_seed[1])
                return is_successful
            except Exception as e:
                send_is_download_successful_to_tracker(False, file_name, chose_seed[0], chose_seed[1])
                asyncio.run(log_message(e))
                return False
    except Exception as e:
        udp_socket.close()
        asyncio.run(log_message(e))
        return False


def run_peer_as_seeder(file_name):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((HOST, PORT))
    fsize = os.stat(f"{PORT}/{str(file_name)}")
    message = f"share {file_name} with size {fsize.st_size.__str__()}"
    udp_socket.sendto(pickle.dumps(message), (TRACKER_IP, TRACKER_PORT))
    asyncio.run(log_message(f"sent message: {message} to {TRACKER_IP}:{TRACKER_PORT}"))

    udp_socket.settimeout(5)
    try:
        res, addr = udp_socket.recvfrom(1024)
        udp_socket.close()
        if pickle.loads(res).startswith(f"file {file_name} added to share"):
            asyncio.run(log_message(f"message from server: \"{pickle.loads(res)}\""))
            return True
    except Exception as e:
        udp_socket.close()
        asyncio.run(log_message(e))
    return False


def run_client(file_name, tracker_ip, tracker_port, peer_ip, peer_port):
    global TRACKER_IP, TRACKER_PORT, HOST, PORT, FILE, FILE_DATA
    TRACKER_IP, TRACKER_PORT = str(tracker_ip), int(tracker_port)
    HOST, PORT = str(peer_ip), int(peer_port)
    create_directory(PORT)
    is_successful = run_peer_as_client(file_name)
    if is_successful:
        FILE = open(f"{PORT}/{str(file_name)}", "rb")
        FILE_DATA = FILE.readlines()
        is_successful = run_peer_as_seeder(file_name)
        if is_successful:
            threading.Thread(target=asyncio.run, args=(run_peer_as_server(),)).start()
            threading.Thread(target=asyncio.run, args=(send_heartbeat(),)).start()


def run_seeder(file_name, tracker_ip, tracker_port, peer_ip, peer_port):
    global TRACKER_IP, TRACKER_PORT, HOST, PORT, FILE, FILE_DATA
    TRACKER_IP, TRACKER_PORT = str(tracker_ip), int(tracker_port)
    HOST, PORT = str(peer_ip), int(peer_port)
    create_directory(PORT)
    if not os.path.isfile(f"{PORT}/{str(file_name)}"):
        asyncio.run(log_message("file not exists in client"))
        return
    FILE = open(f"{PORT}/{str(file_name)}", "rb")
    FILE_DATA = []
    while True:
        read = FILE.read(1024)
        if not read:
            break
        FILE_DATA.append(read)

    is_successful = run_peer_as_seeder(f"{str(file_name)}")
    if is_successful:
        threading.Thread(target=asyncio.run, args=(run_peer_as_server(),)).start()
        threading.Thread(target=asyncio.run, args=(send_heartbeat(),)).start()
        # asyncio.run(send_heartbeat())


def create_directory(port):
    if not os.path.exists(f"{port}"):
        os.mkdir(f"{port}")


def read_file():
    asyncio.run(read_logs())
