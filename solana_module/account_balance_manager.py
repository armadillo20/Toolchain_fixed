# MIT License
#
# Copyright (c) 2025 Manuel Boi - Università degli Studi di Cagliari
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


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