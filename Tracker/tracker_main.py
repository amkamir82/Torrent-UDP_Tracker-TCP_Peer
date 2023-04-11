import tracker


def handle_commands():
    while True:
        command = input("Enter command\n")
        if command == "help":
            print("run one of commands below")
            print("tracker <IP> <Port>")
        elif command.startswith("tracker"):
            splitted_command = command.split()
            ip, port = splitted_command[1], splitted_command[2]
            tracker.run_tracker(ip, port)
        elif command.startswith("request logs"):
            tracker.read_file(tracker.REQUEST_LOGS)
        elif command.startswith("file_logs -all"):
            tracker.read_file(tracker.FILE_LOGS)
        elif command.startswith("file_logs"):
            file_name = command.split()[1]
            tracker.read_file(file_name)
        else:
            print("invalid command")


if __name__ == "__main__":
    print("Tracker program started")
    print("run one of commands below:")
    print("help")
    print("tracker <IP> <Port>")
    handle_commands()
