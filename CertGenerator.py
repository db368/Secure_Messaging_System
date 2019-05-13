import cryptography
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import datetime


rootcapath = "certs/rootCAkey.pem"
rootcacert = "certs/rootCAcert.pem"

rootcakey = None
def ensureDirectoriesExist():
    """ Make sure we the correct directories for the root ca"""
    global rootcapath
    global rootcacert

    certdir = "certs"
    if not os.path.exists(certdir):
        os.mkdir(certdir)
    
    # Genertate our root CA key if it doesn't exist
    if not os.path.exists(rootcapath):
        key = genKey(rootcapath)
    else:
        key = loadKey(rootcapath)
    
    # Store this globally
    rootcakey = key

def genKey(path):
    """Generate a new key and store it to the specific path"""
    key = rsa.generate_private_key(public_exponent = 65537, key_size = 2048, backend = default_backend())
    with open(path, "wb") as f:
       f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(b"passphrase"),))

    return key

def genRootCA(key, cert_path, country = "US", state = "NewJersey", locality="Newark", organization ="NJIT", common_name="mysite.com" ):
    "Create a cert signing request, all it requires is a link to the key, and the path to the cert"
    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, locality),
        x509.NameAttribute(NameOID.LOCALITY_NAME, country),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Our certificate will be valid for the forseable future
        datetime.datetime.utcnow() + datetime.timedelta(days=9999)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
        # Sign our certificate with our private key
    ).sign(key, hashes.SHA256(), default_backend())

    #Print to file
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    return cert


def signCSR(csr, outpath, country = "US", state = "NewJersey", locality="Wayne", organization ="CAroot Authority", common_name="localhost"):
    """ Sign the given CSR using the root CA """
    
    global rootcakey
    
    # Get what we need from the CSR
    subject = csr.subject
    
    # Have our CA credentials here
    issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, locality),
        x509.NameAttribute(NameOID.LOCALITY_NAME, country),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
     
    # Create new certificate builder
    cert = x509.CertificateBuilder()

    # Enter issuer and subject name
    cert = cert.subject_name(subject)
    cert = cert.issuer_name(issuer)
    
    # Use CSR's Public key
    cert = cert.public_key(csr.public_key())

    # Generate a random serial number
    cert = cert.serial_number(x509.random_serial_number())
    
    # make this valid forever
    cert = cert.not_valid_before(datetime.datetime.utcnow())
    cert = cert.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=9999))
    cert = cert.add_extension(x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False)

    # Sign with CA key
    cert = cert.sign(rootcakey, hashes.SHA256(), default_backend())


    #Print to file
    with open(outpath, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    return cert

def genCSR(key, country = "US", state = "NewJersey", locality="Newark", organization ="NJIT", common_name="mysite.com" ):
    "Create a cert signing request, all it requires is a link to the key, and the path to the cert"
    
    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, locality),
        x509.NameAttribute(NameOID.LOCALITY_NAME, country),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # Generate CSR
    cert = x509.CertificateSigningRequestBuilder()
    cert = cert.subject_name(subject)
    cert = cert.add_extension(x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False)
    
    # Sign the cert with our private key
    cert = cert.sign(key, hashes.SHA256(), default_backend())   
    return cert

def loadKey(path):
    # Read the data from file
    s = ""
    with open(path) as f:
        s = f.read().encode('ascii')

    # deserialize file
    key = serialization.load_pem_private_key(s, backend=default_backend(), password=b"passphrase")
    
    return key

def signCert(key, cert, out_path):
    cert.sign(key, hashes.SHA256(), default_backend())
    # Write our certificate out to disk.
    with open(out_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
