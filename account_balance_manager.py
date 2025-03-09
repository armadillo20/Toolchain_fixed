import asyncio
from interactive_data_insertion_manager import load_keypair_from_file, manage_cluster_setting

def choose_wallet():
    print(f"Place wallet in the solana_wallets folder")
    print("What is the name of the wallet file?")
    file_name = input()
    try:
        keypair = load_keypair_from_file(f"./solana_wallets/{file_name}")
        client = manage_client_creation()
        asyncio.run(print_account_balance(client, keypair.pubkey()))
    except:
        raise Exception("Wallet not found")

def manage_client_creation():
    clusters = ["Localnet", "Devnet", "Mainnet"]
    allowed_choices = list(map(str, range(1, len(clusters) + 1)))
    choice = None

    while choice not in allowed_choices:
        print("In which network is the account?")
        for idx, cluster in enumerate(clusters, 1):
            print(f"{idx}. {cluster}")
        choice = input()

    client = manage_cluster_setting(clusters[int(choice) - 1])
    return client

async def print_account_balance(client, pubkey):
    resp = await client.get_balance(pubkey)
    print(f"Account {pubkey} balance: {resp.value} SOL")
    return resp.value
