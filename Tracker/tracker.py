import copy
import asyncio
import time

from seeder import Seeder
import pickle
import threading

HOST = ""
PORT = None
BUFFER_SIZE = 1024

REQUEST_LOGS = "request_logs.txt"
FILE_LOGS = "file_logs.txt"

seeders = {}
file_stat = {}


async def log_message(file_name, message):
    async with asyncio.Lock():
        with open(file_name, "a") as file:
            file.write(f"{message}\n")
            file.close()


async def read_logs(file_name):
    async with asyncio.Lock():
        with open(file_name, "r") as file:
            lines = file.readlines()
            print("".join([item for item in lines]))
            file.close()


def remove_seeder(seeder):
    tmp_seeders = copy.deepcopy(seeders)
    for seeder_file in tmp_seeders:
        if seeder in seeders[seeder_file]:
            seeders[seeder_file].remove(seeder)


def check_seeders_heartbeat():
    while True:
        time.sleep(20)
        for seeder in Seeder.seeders:
            if not seeder.check_heartbeat():
                asyncio.run(log_message(REQUEST_LOGS, f"{seeder.ip}:{seeder.port} disconnected from tracker"))
                remove_seeder(seeder)
                Seeder.remove_seeder(seeder)


class TrackerUDPServer:
    async def handle_create_seeder(self, file_name, file_size, addr):
        seeder_ip, seeder_port = addr[0], addr[1]
        seeder = Seeder(seeder_ip, seeder_port, file_name)
        if file_name in seeders.keys():
            seeders[file_name].append(seeder)
        else:
            seeders[file_name] = [seeder]
            file_stat[file_name] = file_size
        self.transport.sendto(
            pickle.dumps(f"file {file_name} added to share"), addr)

    async def handle_get_seeders(self):
        result = []
        for seeder in seeders:
            result.append((seeder.ip, seeder.port))
        return result

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        loop = asyncio.get_event_loop()
        message = f"got message: \"{pickle.loads(data)}\" from {addr}"
        splitted_data = pickle.loads(data).split()

        if splitted_data[0] == "heartbeat":
            loop.create_task(log_message(REQUEST_LOGS, message))
            Seeder.update_heartbeat(str(addr[0]), str(addr[1]))

        elif splitted_data[0] == "share":
            loop.create_task(log_message(REQUEST_LOGS, message))
            loop.create_task(log_message(FILE_LOGS, f"{splitted_data[1]} shared from {addr}"))
            loop.create_task(log_message(splitted_data[1], f"shared from {addr}"))
            loop.create_task(
                self.handle_create_seeder(splitted_data[1], splitted_data[splitted_data.index("size") + 1], addr))

        elif splitted_data[0] == "get":
            peer_requested_file = splitted_data[1]
            loop.create_task(log_message(peer_requested_file, f"got from {addr}"))
            if peer_requested_file in seeders.keys():
                result = []
                for seeder in seeders[peer_requested_file]:
                    result.append((seeder.ip, seeder.port))
                message += f", the seeders that have this file are {result}"
                loop.create_task(log_message(REQUEST_LOGS, message))
                result.append(file_stat[peer_requested_file])
                self.transport.sendto(pickle.dumps(result), addr)
            else:
                message += ", wrong file"
                loop.create_task(log_message(REQUEST_LOGS, message))
                self.transport.sendto(pickle.dumps("wrong file"), addr)
        elif splitted_data[0] == "successful":
            loop.create_task(
                log_message(splitted_data[3], f"successfully downloaded from {splitted_data[5], splitted_data[6]}"))
            loop.create_task(log_message(REQUEST_LOGS, message))
        elif splitted_data[0] == "unsuccessful":
            loop.create_task(
                log_message(splitted_data[3], f"successfully downloaded from {splitted_data[5], splitted_data[6]}"))
            loop.create_task(log_message(REQUEST_LOGS, message))
        else:
            loop.create_task(log_message(REQUEST_LOGS, message))


async def run_server():
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: TrackerUDPServer(),
        local_addr=(HOST, PORT)
    )
    await log_message(REQUEST_LOGS, f"Listening on 127.0.0.1:{PORT}")
    threading.Thread(target=check_seeders_heartbeat).start()
    # print(f"Listening on 127.0.0.1:{PORT}")
    while True:
        await asyncio.sleep(3600)


def run_tracker(ip, port):
    global HOST, PORT
    HOST = str(ip)
    PORT = int(port)
    threading.Thread(target=asyncio.run, args=(run_server(),)).start()


def read_file(file_name):
    asyncio.run(read_logs(file_name))
