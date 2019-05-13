from CertGenerator import *


thiscertpath = "certs/testcert.pem"
ca_keypath = "certs/testCAkey.pem"
ca_certpath ="certs/testCAcert.pem"

def createRootCA(cakeypath, cacertpath):
    
    # First Generate a key for our demo csa
    key = genKey(cakeypath)

    # Now generate a demo CSR for this cert, using the key as both the
    csr = genRootCA(key,cacertpath)

    print (csr)


def genRootedCert():

    ensureDirectoriesExist()
    #First generate a random key for our requester
    key = genKey("certs/testkey.pem")

    # Now generate a CSR
    csr = genCSR(key, organization="Testers inc")

    # Get it signed
    signed_cert = signCSR(csr, "certs/testcert.crt")

    print (signed_cert)




def testKeyGen(keypath):
    # Generate Key
    key_gen = genKey(keypath)

    # Test that key loaded from file is the same as genned key
    key_read = loadKey(keypath)


genRootedCert()