import sys
from pathlib import Path
import importlib
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solana.transaction import Transaction

async def make_transaction(program, instruction, accounts, signer_account_keypairs, args, client, provider):
    # Get instruction from anchorpy
    function = import_function(program, instruction)
    ix = prepare_function(accounts, args, function)

    # If signature is required, sign transaction with signer_accounts
    keypairs = list(signer_account_keypairs.values())
    if keypairs:
        # Create transaction
        tx = Transaction().add(ix)

        # Get latest blockhash
        tx.recent_blockhash = await get_latest_blockhash(client)

        # If signature is required, sign transaction with signer_accounts
        keypairs = list(signer_account_keypairs.values())
        tx.sign(*keypairs)

        # Compute transaction size and fee
        await measure_transaction_size(tx)
        await compute_transaction_fee(client, tx)
    else:
        msg = MessageV0.try_compile(
            payer=provider.wallet.payer.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=await get_latest_blockhash(client)
        )

        tx = VersionedTransaction(msg, [provider.wallet.payer])

        # Compute versioned transaction size and fee
        await measure_versioned_transaction_size(tx)
        await compute_versioned_transaction_fee(client, tx)

    # Send transaction
    await provider.send(tx)
    print("Transaction sent")

def import_function(program_name: str, instruction_name: str):
    # Update absolute path in the root folder of the package
    program_root = Path(f".anchor_files/{program_name}").resolve()

    if not program_root.exists():
        raise FileNotFoundError(f"The folder {program_root} does not exist. Check program name")

    # Path to the instruction
    module_path = program_root / "anchorpy_files" / "instructions" / f"{instruction_name}.py"

    if not module_path.exists():
        raise FileNotFoundError(f"The file {module_path} does not exist. Verify instruction name.")

    # Add program root to sys.path to enable relative imports
    if str(program_root) not in sys.path:
        sys.path.append(str(program_root))

    # Complete name of the module to import
    module_name = f"anchorpy_files.instructions.{instruction_name}"

    # Dynamic import of the module
    module = importlib.import_module(module_name)

    # Verify that the function exists
    if not hasattr(module, instruction_name):
        raise AttributeError(f"The module {module_name} does not contain the function {instruction_name}.")

    return getattr(module, instruction_name)

def prepare_function(accounts, args, function):
    if accounts:
        if args:
            # Call instruction with given accounts and args
            ix = function(accounts=accounts, args=args)
        else:
            # Call instruction only with given accounts
            ix = function(accounts=accounts)
    else:
        if args:
            # Call instruction with given accounts and args
            ix = function(args=args)
        else:
            # Call instruction only with given accounts
            ix = function()

    return  ix

async def get_latest_blockhash(client):
    resp = await client.get_latest_blockhash()
    return resp.value.blockhash

async def measure_transaction_size(transaction):
    serialized_tx = transaction.serialize()
    size_in_bytes = len(serialized_tx)
    print(f"Transaction size: {size_in_bytes} bytes")
    return size_in_bytes

async def compute_transaction_fee(client, transaction):
    # Get message from transaction
    tx_message = transaction.compile_message()

    # Compute fee from message
    response = await client.get_fee_for_message(tx_message)
    if response.value:
        print(f"Transaction fee: {response.value} lamports")
        return response.value
    else:
        print("Failed to fetch fee information")
        return None

async def measure_versioned_transaction_size(transaction):
    # Manually serialize transaction
    serialized_tx = bytes(transaction)
    size_in_bytes = len(serialized_tx)
    print(f"Transaction size: {size_in_bytes} bytes")
    return size_in_bytes

async def compute_versioned_transaction_fee(client, transaction):
    # Ottenere il messaggio dalla VersionedTransaction
    tx_message = transaction.message

    # Calcolare la commissione dalla rete
    response = await client.get_fee_for_message(tx_message)
    if response.value:
        print(f"Transaction fee: {response.value} lamports")
        return response.value
    else:
        print("Failed to fetch fee information")
        return None