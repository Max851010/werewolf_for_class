import socket
import sys
import select
import signal

def connect_to_server(host='localhost', port=9999):
    """ Create a socket connection to the server """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        client_socket.setblocking(0)  # Set the socket to non-blocking
        client_socket.sendall("connect")
        return client_socket
    except socket.error as e:
        print "Failed to connect to the server:", e
        sys.exit()

def listen(server_socket):
    """ Check for messages from the server """
    try:
        while True:
            ready_to_read, _, _ = select.select([server_socket], [], [], 0.5)
            if server_socket in ready_to_read:
                data = server_socket.recv(1024).decode()
                if not data:
                    print "Connection closed by the server."
                    return False
                else:
                    print data
            return True
    except Exception as e:
        print "Error receiving data:", e
        return False

def send(server_socket):
    """Send a message entered by the user."""
    try:
        ready_to_write, _, _ = select.select([sys.stdin], [], [], 0.1)
        if ready_to_write:
            msg = sys.stdin.readline().strip()  # Read a line from stdin without blocking the program
            if msg:
                server_socket.sendall(msg.encode())
                if msg.lower() == 'exit':
                    return False
        return True
    except Exception as e:
        print("Error sending data:", e)
        return False

def signal_handler(signal, frame, server_socket):
    """Handle SIGINT and SIGTERM to close the socket gracefully."""
    print("\nReceived termination signal, closing connection...")
    server_socket.sendall("CLOSE".encode())
    server_socket.close()
    sys.exit(0)

if __name__ == '__main__':
    server_socket = connect_to_server()
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, server_socket))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, server_socket))

    print "Connected to the server. Type 'exit' to quit."
    try:
        while True:
            # Use select to check for input readiness on both stdin and the socket
            if not listen(server_socket):  # Listen for incoming messages
                break
            if not send(server_socket):  # Check for user input and send messages
                break
    finally:
        server_socket.close()
        print "Disconnected from the server."

