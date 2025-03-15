from solana_module.solana_utils import choose_wallet

def get_public_key():
    keypair = choose_wallet()
    if keypair is None:
        return
    else:
        print(f"The public key is {keypair.pubkey()}")
        print(f"The private key is {keypair.secret()}")