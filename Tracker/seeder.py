import datetime


class Seeder:
    seeders = []

    def __init__(self, ip, port, file):
        self.ip = ip
        self.port = port
        self.file = file
        self.heartbeat = datetime.datetime.now()
        Seeder.seeders.append(self)

    def set_heartbeat(self):
        self.heartbeat = datetime.datetime.now()

    def check_heartbeat(self):
        time_diff = datetime.datetime.now() - self.heartbeat
        time_diff_seconds = int(time_diff.total_seconds())
        if time_diff_seconds <= 20:
            return True
        return False

    @staticmethod
    def update_heartbeat(ip, port):
        for seeder in Seeder.seeders:
            if seeder.port == int(port) and seeder.ip == str(ip):
                seeder.set_heartbeat()
    @staticmethod
    def remove_seeder(seeder):
        Seeder.seeders.remove(seeder)
        del seeder
