import socket
import threading
import time

# === Configure this: (drone_ip is always 192.168.10.1 in AP mode)
# ('drone_ip', 'local_interface_ip', local_udp_port)
DRONES = [
    ('192.168.10.1', '192.168.10.3', 9000),  # USB Wi-Fi
    # ('192.168.10.1', '192.168.10.3', 9001),  # Internal Wi-Fi
]

# === Send command and wait for response
def tello_command(sock, drone_ip, cmd):
    try:
        sock.sendto(cmd.encode('utf-8'), (drone_ip, 8889))
        response, _ = sock.recvfrom(1024)
        return response.decode('utf-8')
    except socket.timeout:
        return "timeout"
    except Exception as e:
        return f"error: {e}"

# === Control one drone
def control_drone(drone_ip, local_ip, local_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((local_ip, local_port))
    sock.settimeout(5)

    print(f"[{local_ip}:{local_port}] → Sending 'command'")
    print("↪", tello_command(sock, drone_ip, 'command'))

    print(f"[{local_ip}:{local_port}] → Asking 'battery?'")
    print("↪", tello_command(sock, drone_ip, 'battery?'))

    sock.close()

# === Main multithreaded runner
def main():
    threads = []
    for drone_ip, local_ip, local_port in DRONES:
        t = threading.Thread(target=control_drone, args=(drone_ip, local_ip, local_port))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()