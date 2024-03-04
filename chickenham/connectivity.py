import socket

def connectivity_check(host="8.8.8.8", port=53, timeout=3, verbose=False):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    socket.setdefaulttimeout(timeout)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        return True
    except socket.error as ex:
        if verbose:
            print(ex)
        return False
    finally:
        s.close()
