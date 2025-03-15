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


import json
import os
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

solana_base_path = "solana_module"

def load_keypair_from_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            return Keypair.from_bytes(data)
    else:
        return None

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

def choose_wallet():
    print(f"Place wallet in the solana_wallets folder")
    print("Insert name of the wallet file")
    file_name = input()
    wallet = load_keypair_from_file(f"{solana_base_path}/solana_wallets/{file_name}")
    if wallet is None:
        print("Wallet not found")
        return None
    else:
        return wallet