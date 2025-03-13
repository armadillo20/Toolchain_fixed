import json
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

solana_base_path = "solana_module"

def load_keypair_from_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        return Keypair.from_bytes(data)

def create_client(cluster):
    # Define rpc basing on the cluster
    rpc_url = None
    if cluster == "Localnet":
        rpc_url = "http://localhost:8899"
    elif cluster == "Devnet":
        rpc_url = "https://api.devnet.solana.com"
    elif cluster == "Mainnet":
        rpc_url = "https://api.mainnet-beta.solana.com"

    # Crete client
    client = AsyncClient(rpc_url)
    return client