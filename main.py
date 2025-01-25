import asyncio
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from anchorpy import Provider, Wallet
from smart_contracts.bet.instructions import join, win
import json

def load_keypair_from_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        return Keypair.from_bytes(data)

async def get_recent_blockhash(user):
    # Usa il metodo corretto per ottenere l'ultimo blockhash
    resp = await user.get_latest_blockhash()
    return resp.value.blockhash

async def get_account_balance(user, pubkey):
    # Controlla il saldo dell'account
    resp = await user.get_balance(pubkey)
    return resp.value


async def check_all_accounts(user, accounts):
    for account in accounts:
        balance = await get_account_balance(user, account.pubkey())
        print(f"Account {account.pubkey()} balance: {balance} SOL")

async def join_function():
    # Prepara l'istruzione join
    join_ix = join(
        accounts={
            "oracle": oracle.pubkey(),
            "participant1": participant1.pubkey(),
            "participant2": participant2.pubkey(),
            "bet_info": bet_info,
        },
        args={
            "delay": 300,  # Esempio di delay
            "wager": 1  # Esempio di scommessa
        }
    )

    # Crea la transazione per join
    tx = Transaction().add(join_ix)

    # Prendi l'ultimo blockhash
    recent_blockhash = await get_recent_blockhash(client)
    tx.recent_blockhash = recent_blockhash

    # Sign transaction
    tx.sign(participant1, participant2)
    participant1_wallet.sign_transaction(tx)
    participant2_wallet.sign_transaction(tx)

    # Prepare provider and send transaction
    participant1_provider = Provider(client, participant1_wallet)
    await participant1_provider.send(tx)

async def win_function():
    winner = participant1  # Esempio: participant1 è il vincitore
    # Prepara l'istruzione win
    win_ix = win(
        accounts={
            "oracle": oracle.pubkey(),
            "winner": winner.pubkey(),
            "bet_info": bet_info,
            "participant1": participant1.pubkey(),
            "participant2": participant2.pubkey(),
        }
    )

    # Crea la transazione per win
    tx = Transaction().add(win_ix)

    # Prendi l'ultimo blockhash
    recent_blockhash = await get_recent_blockhash(client)
    tx.recent_blockhash = recent_blockhash

    oracle_provider = Provider(client, oracle_wallet)

    # Firma e invia la transazione per win
    oracle_wallet.sign_transaction(tx)
    await oracle_provider.send(tx)


if __name__ == "__main__":
    # Genera le chiavi per i partecipanti e gli account
    participant1 = load_keypair_from_file("/Users/Manuel/.config/solana/participant1_wallet.json")
    participant2 = load_keypair_from_file("/Users/Manuel/.config/solana/participant2_wallet.json")
    oracle = load_keypair_from_file("/Users/Manuel/.config/solana/wallet-keypair.json")

    # Calcola il BetInfo PDA
    bet_info_seeds = [bytes(participant1.pubkey()), bytes(participant2.pubkey())]
    program_id = Pubkey.from_string("56k9cTd2cv1X7RzMG3rzK1V8s8xzXDtHTsPKFQyoiQAt")
    bet_info, _ = Pubkey.find_program_address(bet_info_seeds, program_id)


    # Crea un client Solana
    rpc_url = "https://api.devnet.solana.com"
    client = AsyncClient(rpc_url)

    # Crea wallet
    participant1_wallet = Wallet(participant1)
    participant2_wallet = Wallet(participant2)
    oracle_wallet = Wallet(oracle)

    # Choose what to do
    choice = 1

    if choice == 1:
        asyncio.run(check_all_accounts(client, [participant1, participant2, oracle]))
    elif choice == 2:
        asyncio.run(join_function())
    elif choice == 3:
        asyncio.run(win_function())