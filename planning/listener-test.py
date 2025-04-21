import socket
import threading
import time

TELLO_IP = '192.168.10.1'
CMD_PORT = 8889
STATE_PORT = 8890
LOCAL_CMD_PORT = 9000  # Can be anything unused

# === Start telemetry listener on port 8890 ===
def listen_tello_state():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, 25, b'eth1')
    sock.bind(('0.0.0.0', STATE_PORT))
    sock.settimeout(10)
    print("📡 Listening for Tello state on UDP port 8890...")

    try:
        for _ in range(10):  # Read a few messages
            data, addr = sock.recvfrom(1024)
            print(f"[STATE] {data.decode().strip()}")
    except socket.timeout:
        print("⚠️ No telemetry received (timeout)")
    finally:
        sock.close()
        print("🛑 Closed state listener")

# === Send a single command and wait for response ===
def tello_command(cmd_sock, cmd):
    cmd_sock.sendto(cmd.encode('utf-8'), (TELLO_IP, CMD_PORT))
    try:
        resp, _ = cmd_sock.recvfrom(1024)
        return resp.decode('utf-8')
    except socket.timeout:
        return "timeout"

def main():

    # === Create command socket ===
    cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cmd_sock.settimeout(5)
    cmd_sock.connect((TELLO_IP, CMD_PORT))

    time.sleep(2)  # Give time for everything to stabilize

    # === Enter SDK mode ===
    print("→ Sending 'command'...")
    print("↪", tello_command(cmd_sock, 'command'))

    time.sleep(2)

    # Start telemetry listener in background
    listener = threading.Thread(target=listen_tello_state)
    listener.start()
    
    time.sleep(2)

    # === Ask for battery ===
    print("→ Sending 'battery?'...")
    print("↪", tello_command(cmd_sock, 'battery?'))

    cmd_sock.close()
    listener.join()
    print("✅ Done.")

if __name__ == "__main__":
    main()