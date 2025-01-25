import asyncio
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from anchorpy import Provider, Wallet
from smart_contracts.bet.instructions import win
import json

def load_keypair_from_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        return Keypair.from_bytes(data)

async def get_recent_blockhash(client):
    # Usa il metodo corretto per ottenere l'ultimo blockhash
    resp = await client.get_latest_blockhash()
    return resp.value.blockhash

async def get_account_balance(client, pubkey):
    # Controlla il saldo dell'account
    resp = await client.get_balance(pubkey)
    return resp.value


async def check_all_accounts(client, accounts):
    for account in accounts:
        balance = await get_account_balance(client, account.pubkey())
        print(f"Account {account.pubkey()} balance: {balance} SOL")

async def main():
    # Genera le chiavi per i partecipanti e gli account
    participant1 = Keypair()
    participant2 = Keypair()
    oracle = load_keypair_from_file("/Users/Manuel/.config/solana/id.json")

    winner = participant1  # Esempio: participant1 è il vincitore
    wallet = Wallet(oracle)
    bet_info_seeds = [bytes(participant1.pubkey()), bytes(participant2.pubkey())]

    # Calcola il BetInfo PDA
    program_id = Pubkey.from_string("56k9cTd2cv1X7RzMG3rzK1V8s8xzXDtHTsPKFQyoiQAt")
    bet_info, _ = Pubkey.find_program_address(bet_info_seeds, program_id)

    # Crea un client Solana
    rpc_url = "https://api.devnet.solana.com"
    client = AsyncClient(rpc_url)

    # Controlla il saldo di tutti gli account
    await check_all_accounts(client, [participant1, participant2, oracle])

    # Prepara l'istruzione win
    ix = win(
        accounts={
            "oracle": oracle.pubkey(),
            "winner": winner.pubkey(),
            "bet_info": bet_info,
            "participant1": participant1.pubkey(),
            "participant2": participant2.pubkey(),
        }
    )

    # Crea la transazione
    tx = Transaction().add(ix)

    # Prendi l'ultimo blockhash
    recent_blockhash = await get_recent_blockhash(client)
    tx.recent_blockhash = recent_blockhash

    provider = Provider(client, wallet)

    # Firma e invia la transazione
    wallet.sign_transaction(tx)
    await provider.send(tx)


if __name__ == "__main__":
    asyncio.run(main())