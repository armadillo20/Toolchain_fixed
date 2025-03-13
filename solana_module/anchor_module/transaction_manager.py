import sys
from pathlib import Path
import importlib
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solana.transaction import Transaction
from solana_module.anchor_module.utils import anchor_base_path


# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

async def manage_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider):
    # Build transaction
    tx = await build_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider)
    print('Transaction built. Computing size and fees...')

    # Measure transaction size
    transaction_size = measure_transaction_size(tx)
    if transaction_size is None:
        print('Error while measuring transaction size.')
    else:
        print(f"Transaction size: {transaction_size} bytes")

    # Compute transaction fees
    transaction_fees = await measure_transaction_fees(client, tx)
    if transaction_fees is None:
        print('Error while computing transaction fees.')
    else:
        print(f"Transaction fee: {transaction_fees} lamports")

    allowed_choices = ['1','0']
    choice = None
    while choice not in allowed_choices:
        print('Choose an option.')
        print('1) Send transaction')
        print('0) Go back to Anchor menu')
        choice = input()
        if choice == '1':
            transaction = await send_transaction(provider, tx)
            print(f'Transaction sent. Hash: {transaction}')
        elif choice == '0':
            return
        else:
            print('Invalid option. Please choose a valid option.')

async def build_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider):
    # Get instruction from anchorpy
    function = _import_function(program_name, instruction)
    ix = _prepare_function(accounts, args, function)

    # If signature is required, sign transaction with signer_accounts
    keypairs = list(signer_account_keypairs.values())
    if keypairs:
        # Create transaction
        tx = Transaction().add(ix)

        # Get latest blockhash
        tx.recent_blockhash = await _get_latest_blockhash(client)

        # If signature is required, sign transaction with signer_accounts
        keypairs = list(signer_account_keypairs.values())
        tx.sign(*keypairs)
    else:
        msg = MessageV0.try_compile(
            payer=provider.wallet.payer.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=await _get_latest_blockhash(client)
        )

        tx = VersionedTransaction(msg, [provider.wallet.payer])

    return tx

def measure_transaction_size(tx):
    # Check transaction type
    if isinstance(tx, Transaction):
        # Compute transaction size
        serialized_tx = tx.serialize()
    elif isinstance(tx, VersionedTransaction):
        # Manually serialize transaction
        serialized_tx = bytes(tx)
    else:
        return None

    # Compute size
    size_in_bytes = len(serialized_tx)
    return size_in_bytes

async def measure_transaction_fees(client, tx):
    # Check transaction type
    if isinstance(tx, Transaction):
        tx_message = tx.compile_message()
    elif isinstance(tx, VersionedTransaction):
        tx_message = tx.message
    else:
        return None

    # Compute fee from message
    response = await client.get_fee_for_message(tx_message)
    if response.value:
        return response.value
    else:
        print("Failed to fetch fee information")
        return None

async def send_transaction(provider, tx):
    return await provider.send(tx)




# ====================================================
# PRIVATE FUNCTIONS
# ====================================================

def _import_function(program_name: str, instruction_name: str):
    # Update absolute path in the root folder of the package
    program_root = Path(f"{anchor_base_path}/.anchor_files/{program_name}").resolve()

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

def _prepare_function(accounts, args, function):
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

async def _get_latest_blockhash(client):
    resp = await client.get_latest_blockhash()
    return resp.value.blockhash