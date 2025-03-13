import asyncio
from solana_module.utils import load_keypair_from_file, create_client


# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

def request_balance():
    keypair = _choose_wallet()
    client = _manage_client_creation()
    asyncio.run(_print_account_balance(client, keypair.pubkey()))




# ====================================================
# PRIVATE FUNCTIONS
# ====================================================

def _choose_wallet():
    print(f"Place wallet in the solana_wallets folder")
    print("Insert name of the wallet file")
    file_name = input()
    try:
        return load_keypair_from_file(f"solana_module/solana_wallets/{file_name}")
    except:
        raise Exception("Wallet not found")

def _manage_client_creation():
    clusters = ["Localnet", "Devnet", "Mainnet"]
    allowed_choices = list(map(str, range(1, len(clusters) + 1)))
    choice = None

    while choice not in allowed_choices:
        print("For which network you want to check balance?")
        for idx, cluster in enumerate(clusters, 1):
            print(f"{idx}. {cluster}")
        choice = input()

    client = create_client(clusters[int(choice) - 1])
    return client

async def _print_account_balance(client, pubkey):
    try:
        resp = await client.get_balance(pubkey)
        print(f"Account {pubkey} balance: {resp.value} SOL")
        return resp.value
    except ConnectionError:
        print('Error: Could not get account balance')