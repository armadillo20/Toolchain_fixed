import asyncio
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from anchorpy import Provider, Wallet
from smart_contracts.bet.instructions import win


async def main():
    # Genera le chiavi per i partecipanti e gli account
    participant1 = Keypair()
    participant2 = Keypair()
    oracle = Keypair()
    winner = participant1  # Esempio: participant1 è il vincitore
    wallet = Wallet(oracle)
    bet_info_seeds = [bytes(participant1.pubkey()), bytes(participant2.pubkey())]

    # Calcola il BetInfo PDA
    program_id = Pubkey.from_string("56k9cTd2cv1X7RzMG3rzK1V8s8xzXDtHTsPKFQyoiQAt")
    bet_info, _ = Pubkey.find_program_address(bet_info_seeds, program_id)

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

    # Configura il provider
    provider = Provider.local()

    # Configura il client per connetterti alla Devnet
    rpc_url = "https://api.devnet.solana.com"
    connection = AsyncClient(rpc_url)
    provider = Provider(connection, wallet)

    # Firma e invia la transazione
    wallet.sign_transaction(tx)
    await provider.send(tx)


if __name__ == "__main__":
    asyncio.run(main())

