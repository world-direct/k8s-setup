
import sys

if sys.version_info[0] >= 3:
    unicode = str

def generate_selfsigned_ca(clustername):
    """
    Generates a selfsiged ca certificate and it's private key
    Returns a tuple of two strings: crt, key
    """

    from datetime import datetime, timedelta
    import ipaddress

    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    
    # Generate key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    
    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, unicode(clustername))
    ])
 
    # path_len=1 means that this certificate can sign one level of sub-certs
    basic_contraints = x509.BasicConstraints(ca=True, path_length=1)
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=10*365))
        .add_extension(basic_contraints, False)
        .sign(key, hashes.SHA256(), default_backend())
    )

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)

    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return cert_pem, key_pem

