import uuid
import json
from backend.config import STARTING_BALANCE
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec    
from cryptography.hazmat.primitives.asymmetric.utils import(
    encode_dss_signature, decode_dss_signature )
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class Wallet:
    def __init__(self, blockchain=None):
        self.address = str(uuid.uuid4())[:8]
        self.private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
        self.public_key = self.private_key.public_key()
        self.serializePublicKey()
        self.blockchain = blockchain

    @property
    def balance(self):

        return Wallet.calculateBalance(self.blockchain,self.address)

    def sign(self, data):

        return decode_dss_signature(self.private_key.sign(
                                    json.dumps(data).encode('utf-8'),
                                    ec.ECDSA(hashes.SHA256())
                                    ))

    def serializePublicKey(self):
         self.public_key = self.public_key.public_bytes(
                                     encoding= serialization.Encoding.PEM,
                                     format= serialization.PublicFormat.SubjectPublicKeyInfo
                                     ).decode('utf-8')
    @staticmethod
    def verify(public_key, data, signature):
        deserialized_public_key = serialization.load_pem_public_key(
            public_key.encode('utf-8'),
            default_backend()
        )
        (r, s) = signature
        try:
            deserialized_public_key.verify(encode_dss_signature(r, s),
                                           json.dumps(data).encode('utf-8'),
                                            ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False

    @staticmethod
    def calculateBalance(blockchain, address):
        balance = STARTING_BALANCE
        if not blockchain:
            return balance

        for block in blockchain.chain:
            for transaction in block.data:
                if transaction['input']['address'] == address:
                    balance = transaction['output'][address]
                elif address in transaction['output']:
                    balance += transaction['output'][address]

        return balance
    


def main():
    wallet = Wallet()
    print(f'wallet.__dict__: {wallet.__dict__}')

    data = {'dump' : 'girl'}
    signature = wallet.sign(data)
    print(f'signature: {signature}')

    should_be_valid = Wallet.verify(wallet.public_key, data, signature)
    print(f'sbv: {should_be_valid}')

    should_be_invalid = Wallet.verify(Wallet().public_key, data, signature)
    print(f'snbv: {should_be_invalid}')

if __name__ == "__main__":
    main()
