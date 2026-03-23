import socket
import ssl

def check_port(host, port):
    try:
        sock = socket.create_connection((host, port), timeout=2)
        print(f"[SUCCESS] Connection to {host}:{port} established.")
        sock.close()
    except Exception as e:
        print(f"[ERROR] Failed to connect to {host}:{port}: {e}")

def check_http_response(host, port, use_ssl=False):
    import urllib.request
    protocol = "https" if use_ssl else "http"
    url = f"{protocol}://{host}:{port}"
    
    context = ssl._create_unverified_context() if use_ssl else None
    
    try:
        print(f"Testing {url}...")
        response = urllib.request.urlopen(url, context=context, timeout=5)
        print(f"[SUCCESS] Received status code: {response.getcode()}")
    except Exception as e:
        print(f"[ERROR] Request to {url} failed: {e}")

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000
    check_port(host, port)
    check_http_response(host, port, use_ssl=True)
    check_http_response(host, port, use_ssl=False)
