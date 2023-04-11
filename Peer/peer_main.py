import peer


def handle_commands():
    while True:
        command = input("Enter command\n")
        if command == "help":
            print("Peer program started")
            print("run one of commands below:")
            print("get <file name> <tracker IP> <tracker Port> <peer IP> <peer Port>")
            print("share <file name> <tracker IP> <tracker Port> <peer IP> <peer Port>")
        elif command.startswith("get"):
            splitted_command = command.split()
            file = splitted_command[1]
            tracker_ip, tracker_port = splitted_command[2], splitted_command[3]
            peer_ip, peer_port = splitted_command[4], splitted_command[5]
            peer.run_client(file, tracker_ip, tracker_port, peer_ip, peer_port)
        elif command.startswith("share"):
            splitted_command = command.split()
            file = splitted_command[1]
            tracker_ip, tracker_port = splitted_command[2], splitted_command[3]
            peer_ip, peer_port = splitted_command[4], splitted_command[5]
            peer.run_seeder(file, tracker_ip, tracker_port, peer_ip, peer_port)
        elif command.startswith("request logs"):
            peer.read_file()
        else:
            print("invalid command")


if __name__ == "__main__":
    print("Peer program started")
    print("run one of commands below:")
    print("help")
    print("get <file name> <tracker IP> <tracker Port> <peer IP> <peer Port>")
    print("share <file name> <tracker IP> <tracker Port> <peer IP> <peer Port>")
    handle_commands()
