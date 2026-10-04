"""Create a self-signed HTTPS certificate for the gateway (certs/cert.pem + certs/key.pem).

Why: Chrome only gives a page GPS access over HTTPS. The phones load the app from
the laptop, so the laptop must speak HTTPS. Self-signed means each phone shows a
warning once ("Advanced -> Proceed"); fine for a demo, not for real deployment.

Run once from the project folder:  python gateway/make_cert.py
"""

import datetime
import ipaddress
import socket
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERTS = Path(__file__).resolve().parent.parent / "certs"
HOTSPOT_IP = "192.168.137.1"     # Windows Mobile Hotspot's default address for the laptop


def laptop_ips() -> set[str]:
    ips = {"127.0.0.1", HOTSPOT_IP}
    try:
        ips.update(info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    return ips


def main():
    CERTS.mkdir(exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Disaster Mesh Gateway")])
    ips = laptop_ips()
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName("localhost")] + [x509.IPAddress(ipaddress.ip_address(ip)) for ip in sorted(ips)]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    (CERTS / "key.pem").write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
    (CERTS / "cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print(f"Wrote {CERTS / 'cert.pem'} for: localhost, {', '.join(sorted(ips))}")


if __name__ == "__main__":
    main()
