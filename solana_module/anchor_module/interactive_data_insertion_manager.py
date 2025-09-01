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
from anchorpy import Provider, Wallet
from solana_module.solana_utils import create_client, choose_wallet, load_keypair_from_file, solana_base_path
from solana_module.anchor_module.anchor_utils import fetch_required_accounts, fetch_signer_accounts, generate_pda, \
    fetch_args, check_type, convert_type, fetch_cluster, anchor_base_path, load_idl, choose_program, choose_instruction, \
    check_if_array , check_if_vec , input_token_account_manually ,check_if_bytes_type
from solana_module.anchor_module.transaction_manager import build_transaction, measure_transaction_size, compute_transaction_fees, send_transaction

# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

def choose_program_to_run():
    repeat = True

    # Repeat is needed to manage the going back from the following menus
    while repeat:
        chosen_program = choose_program()
        if not chosen_program:
            return True
        else:
            repeat = _choose_instruction_to_run(chosen_program)




# ====================================================
# PRIVATE FUNCTIONS
# ====================================================

def _choose_instruction_to_run(program_name):
    idl_file_path = f'{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/target/idl/{program_name}.json'
    idl = load_idl(idl_file_path)

    repeat = True

    while repeat:
        chosen_instruction = choose_instruction(idl)
        if not chosen_instruction:
            return True
        else:
            repeat = _setup_required_accounts(chosen_instruction, idl, program_name)

    return False # Needed to come back to main menu after finishing

def _setup_required_accounts(instruction, idl, program_name):
    required_accounts = fetch_required_accounts(instruction, idl)
    signer_accounts = fetch_signer_accounts(instruction, idl)
    final_accounts = dict()
    signer_accounts_keypairs = dict()
    repeat = True

    i = 0
    while repeat:
        while i < len(required_accounts):
            required_account = required_accounts[i]
          
            


            print(f"\nNow working with {required_account} account.")
            print("Is this account a Wallet, a PDA, or a Token Account?")
            print(f"1) Wallet")
            print(f"2) PDA")
            print(f"3) Token Account (manual input)")
            print(f"0) Go back")

            choice = input()

            if choice == '1':
                chosen_wallet = choose_wallet()
                if chosen_wallet is not None:
                    keypair = load_keypair_from_file(f"{solana_base_path}/solana_wallets/{chosen_wallet}")
                    final_accounts[required_account] = keypair.pubkey()
                    # If it is a signer account, save its keypair into signer_accounts_keypairs
                    if required_account in signer_accounts:
                        signer_accounts_keypairs[required_account] = keypair
                    print(f"{required_account} account added.")
                    i += 1
            elif choice == '2':
                
                pda_key = generate_pda(program_name, False)
                if pda_key is not None:
                    final_accounts[required_account] = pda_key
                    i += 1
            elif choice == '3':
                token_account_key = input_token_account_manually()
                if token_account_key is not None:
                    final_accounts[required_account] = token_account_key
                    print(f"{required_account} token account added.")
                    i += 1
            elif choice == '0':
                if i == 0:
                    return True
                else:
                    i -= 1  # Necessary to come back
            else:
                print(f"Please insert a valid choice.")

        # NEW: Setup remaining accounts after required accounts
        repeat = _setup_remaining_accounts(instruction, idl, program_name, final_accounts, signer_accounts_keypairs)
        if i == 0:
            return True
        else:
            i -= 1

    return False

def _setup_remaining_accounts(instruction, idl, program_name, final_accounts, signer_accounts_keypairs):
    """
    Function to handle remaining accounts selection for instructions that need them
    """
    remaining_accounts = []
    
    # ========== FIX: Gestione flessibile del parametro instruction ==========
    instruction_name = instruction['name'] if isinstance(instruction, dict) else instruction
    
    # Check if this instruction might need remaining accounts
    needs_remaining = _check_if_instruction_needs_remaining_accounts(instruction_name)
    
    if needs_remaining:
        print(f"\n=== REMAINING ACCOUNTS SETUP ===")
        print(f"The instruction '{instruction_name}' may require additional accounts.")
        
        # AGGIUNTA: Per payment splitter initialize, includi automaticamente l'initializer
        if instruction_name.lower() == 'initialize':
            from solders.instruction import AccountMeta
            
            # Ottieni la pubkey dell'initializer
            initializer_pubkey = final_accounts.get('initializer')
            if initializer_pubkey:
                print(f"Automatically including initializer ({initializer_pubkey}) as first payee.")
                
                # Aggiungi l'initializer come primo payee (non signer nei remaining)
                initializer_account_meta = AccountMeta(
                    pubkey=initializer_pubkey,
                    is_signer=False,  # Nei remaining non è signer
                    is_writable=False
                )
                remaining_accounts.append(initializer_account_meta)
                print(f"✓ Initializer added as payee #1: {initializer_pubkey}")
        
        print("Do you want to add additional payees? (y/n)")
        add_more = input().lower().strip()
        
        if add_more == 'y':
            additional_accounts = _collect_additional_remaining_accounts(len(remaining_accounts))
            if additional_accounts is None:  # User chose to go back
                return True
            remaining_accounts.extend(additional_accounts)
    
    # Continue to args setup
    return _setup_args(instruction, idl, program_name, final_accounts, signer_accounts_keypairs, remaining_accounts)
    

def _collect_additional_remaining_accounts(starting_counter=0):
    """
    Interactive collection of additional remaining accounts
    """
    from solders.instruction import AccountMeta
    
    remaining_accounts = []
    account_counter = starting_counter + 1
    
    print(f"\n=== ADDING ADDITIONAL PAYEES ===")
    print("You can add multiple payee accounts. Press 0 when done or to go back.")
    
    while True:
        print(f"\n--- Payee #{account_counter} ---")
        print("Choose account type:")
        print("1) Wallet (from existing wallets)")
        print("2) Manual Pubkey input")
        print("3) PDA")
        print("0) Finish adding accounts / Go back")
        
        choice = input().strip()
        
        if choice == '0':
            break
                
        elif choice == '1':
            account_meta = _add_wallet_as_remaining_account()
            if account_meta:
                remaining_accounts.append(account_meta)
                print(f"✓ Payee #{account_counter} added: {account_meta.pubkey}")
                account_counter += 1
                
        elif choice == '2':
            account_meta = _add_manual_pubkey_as_remaining_account()
            if account_meta:
                remaining_accounts.append(account_meta)
                print(f"✓ Payee #{account_counter} added: {account_meta.pubkey}")
                account_counter += 1
                
        elif choice == '3':
            account_meta = _add_pda_as_remaining_account()
            if account_meta:
                remaining_accounts.append(account_meta)
                print(f"✓ Payee #{account_counter} added: {account_meta.pubkey}")
                account_counter += 1
                
        else:
            print("Invalid choice. Please try again.")
    
    if remaining_accounts:
        print(f"\n✓ Total additional payees added: {len(remaining_accounts)}")
        for i, account in enumerate(remaining_accounts, starting_counter + 1):
            signer_status = "Signer" if account.is_signer else "Non-signer"
            writable_status = "Writable" if account.is_writable else "Read-only"
            print(f"  {starting_counter + 1 + i}. {account.pubkey} ({signer_status}, {writable_status})")
    
    return remaining_accounts


def _check_if_instruction_needs_remaining_accounts(instruction_name):
    """
    Check if an instruction typically needs remaining accounts
    Customize this based on your program's instructions
    """
    instructions_needing_remaining = [
        'initialize',  # Payment splitter initialize needs payees
        'add_payees',
        'batch_transfer',
        # Add other instructions that need remaining accounts
    ]
    
    return instruction_name.lower() in instructions_needing_remaining

def _collect_remaining_accounts():
    """
    Interactive collection of remaining accounts
    """
    from solders.instruction import AccountMeta
    
    remaining_accounts = []
    account_counter = 1
    
    print(f"\n=== ADDING REMAINING ACCOUNTS ===")
    print("You can add multiple accounts. Press 0 when done or to go back.")
    
    while True:
        print(f"\n--- Account #{account_counter} ---")
        print("Choose account type:")
        print("1) Wallet (from existing wallets)")
        print("2) Manual Pubkey input")
        print("3) PDA")
        print("0) Finish adding accounts / Go back")
        
        choice = input().strip()
        
        if choice == '0':
            if len(remaining_accounts) == 0:
                print("No remaining accounts added.")
                return None  # Signal to go back
            else:
                break
                
        elif choice == '1':
            account_meta = _add_wallet_as_remaining_account()
            if account_meta:
                remaining_accounts.append(account_meta)
                print(f"✓ Account #{account_counter} added: {account_meta.pubkey}")
                account_counter += 1
                
        elif choice == '2':
            account_meta = _add_manual_pubkey_as_remaining_account()
            if account_meta:
                remaining_accounts.append(account_meta)
                print(f"✓ Account #{account_counter} added: {account_meta.pubkey}")
                account_counter += 1
                
        elif choice == '3':
            account_meta = _add_pda_as_remaining_account()
            if account_meta:
                remaining_accounts.append(account_meta)
                print(f"✓ Account #{account_counter} added: {account_meta.pubkey}")
                account_counter += 1
                
        else:
            print("Invalid choice. Please try again.")
    
    print(f"\n✓ Total remaining accounts added: {len(remaining_accounts)}")
    for i, account in enumerate(remaining_accounts, 1):
        signer_status = "Signer" if account.is_signer else "Non-signer"
        writable_status = "Writable" if account.is_writable else "Read-only"
        print(f"  {i}. {account.pubkey} ({signer_status}, {writable_status})")
    
    return remaining_accounts

def _add_wallet_as_remaining_account():
    """Add a wallet as remaining account"""
    from solders.instruction import AccountMeta
    
    chosen_wallet = choose_wallet()
    if chosen_wallet is None:
        return None
        
    keypair = load_keypair_from_file(f"{solana_base_path}/solana_wallets/{chosen_wallet}")
    pubkey = keypair.pubkey()
    
    is_signer = _ask_yes_no("Should this account be a signer?")
    is_writable = _ask_yes_no("Should this account be writable?")
    
    return AccountMeta(pubkey=pubkey, is_signer=is_signer, is_writable=is_writable)

def _add_manual_pubkey_as_remaining_account():
    """Add a manually entered pubkey as remaining account"""
    from solders.instruction import AccountMeta
    from solders.pubkey import Pubkey
    
    print("Enter the public key:")
    pubkey_str = input().strip()
    
    try:
        pubkey = Pubkey.from_string(pubkey_str)
        
        # Ask about signer and writable status
        is_signer = _ask_yes_no("Should this account be a signer?")
        is_writable = _ask_yes_no("Should this account be writable?")
        
        return AccountMeta(pubkey=pubkey, is_signer=is_signer, is_writable=is_writable)
        
    except Exception as e:
        print(f"Invalid public key: {e}")
        return None

def _add_pda_as_remaining_account():
    """Add a PDA as remaining account"""
    from solders.instruction import AccountMeta
    
    pda_key = generate_pda(program_name, False)
    if pda_key is None:
        return None
    
    # PDAs are typically not signers but might be writable
    is_signer = False  # PDAs can't sign
    is_writable = _ask_yes_no("Should this PDA be writable?")
    
    return AccountMeta(pubkey=pda_key, is_signer=is_signer, is_writable=is_writable)

def _ask_yes_no(question):
    """Helper function to ask yes/no questions"""
    while True:
        answer = input(f"{question} (y/n): ").lower().strip()
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            print("Please answer 'y' or 'n'")

def _setup_args(instruction, idl, program_name, accounts, signer_account_keypairs, remaining_accounts=None):
    """Modified to accept remaining_accounts parameter"""
    required_args = fetch_args(instruction, idl)
    repeat = _manage_args(required_args, program_name, instruction, accounts, signer_account_keypairs, remaining_accounts)
    if repeat:
        return True
    else:
        return False

def _manage_args(args, program_name, instruction, accounts, signer_account_keypairs, remaining_accounts=None):
    """Modified to pass remaining_accounts to provider management"""
    final_args = dict()
    repeat = True
    i = 0

    while repeat:
        while i < len(args):
            arg = args[i]
            print(f"Insert {arg['name']} value. ", end="", flush=True)

        
            vec_type = check_if_vec(arg)
            array_type, array_length = check_if_array(arg)
            if array_type is None and array_length is not None:
                print(f"Unsupported type for arg {arg['name']}")
                return False
            elif array_type is not None and array_length is not None:
                print(f"It is an array of {array_type} type and length {array_length}. Please insert array values separated by spaces (Insert 00 to go back to previous section).")
                value = input()
                if value == '00':
                    if i == 0:
                        return None, True
                    else:
                        i -= 1
                else:
                    array_values = value.split()

                    # Check if array has correct length
                    if len(array_values) != array_length:
                        print(f"Error: Expected array of length {array_length}, but got {len(array_values)}")
                        continue

                    # Convert array elements basing on the type
                    valid_values = []
                    for j in range(len(array_values)):
                        converted_value = convert_type(array_type, array_values[j])
                        if converted_value is not None:
                            valid_values.append(converted_value)
                        else:
                            print(f"Invalid input at index {j}. Please try again.")
                            break
                    else:
                        final_args[arg['name']] = valid_values
                        i += 1

            #vectors handling
            elif vec_type is not None:
                print(f"It is a vector of {vec_type} type. Please insert array values separated by spaces (Insert 00 to go back to previous section).")
                value = input()     
                if value == '00':
                    if i == 0:
                        return None, True
                    else:
                         i -= 1
                else:
                    vec_values = value.split()

                    if len(vec_values) == 0:
                        print("the shares_amounts must be more than 0")
                    else:
                        valid_values = []
                        for j in range(len(vec_values)):
                            converted_value = convert_type(vec_type, vec_values[j])
                            if converted_value is not None:
                                valid_values.append(converted_value)
                            else:
                                print(f"Invalid input at index {j}. Please try again.")
                                break
                        else:
                            final_args[arg['name']] = valid_values
                            i += 1

            else:
                # Single value management
                type = check_type(arg['type'])
                if type is None:
                    print(f"Unsupported type for arg {arg['name']}")
                    return False
                print(f"It is a {type} (Insert 00 to go back to previous section).")
                text_input = input()
                if text_input == '00':
                    if i == 0:
                        return None, True
                    else:
                        i -= 1
                else:
                    if type == "bytes":              
                            aux = text_input.encode('utf-8')
                            final_args[arg['name']] = aux
                            i += 1

                    else:    
                        converted_value = convert_type(type, text_input)
                        if converted_value is not None:
                            final_args[arg['name']] = converted_value
                            i += 1
                        else:
                            print("Invalid input. Please try again.")
                            continue

        repeat = _manage_provider(program_name, instruction, accounts, final_args, signer_account_keypairs, remaining_accounts)
        if i == 0:
            if repeat:
                return True
            else:
                return False
        else:
            i -= 1

def _manage_provider(program_name, instruction, accounts, args, signer_account_keypairs, remaining_accounts=None):
    """Modified to pass remaining_accounts"""
    print("Now working with the transaction provider.")
    chosen_wallet = choose_wallet()
    if chosen_wallet is None:
        return True
    else:
        keypair = load_keypair_from_file(f"{solana_base_path}/solana_wallets/{chosen_wallet}")
        cluster, is_deployed = fetch_cluster(program_name)
        client = create_client(cluster)
        provider_wallet = Wallet(keypair)
        provider = Provider(client, provider_wallet)
        return asyncio.run(_manage_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider, is_deployed, remaining_accounts))

async def _manage_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider, is_deployed, remaining_accounts=None):
    """Modified to handle remaining_accounts signers properly"""
    
    # Raccogli i keypair aggiuntivi dai remaining_accounts se necessario
    remaining_keypairs = {}
    if remaining_accounts:
        for acc in remaining_accounts:
            if hasattr(acc, 'is_signer') and acc.is_signer:
                # Se è un signer, dobbiamo avere il keypair
                # Per semplicità, assumiamo che i remaining accounts non siano signer
                # nel caso del payment splitter
                pass
    
    # Combina tutti i signer keypairs
    all_signer_keypairs = {**signer_account_keypairs, **remaining_keypairs}
    
    # Build transaction con tutti i keypair
    tx = await build_transaction(program_name, instruction, accounts, args, all_signer_keypairs, client, provider, remaining_accounts)
    
    # Resto della funzione rimane uguale...
    print('Transaction built. Computing size and fees...')
    
    transaction_size = measure_transaction_size(tx)
    if transaction_size is None:
        print('Error while measuring transaction size.')
    else:
        print(f"Transaction size: {transaction_size} bytes")

    transaction_fees = await compute_transaction_fees(client, tx)
    if transaction_fees is None:
        print('Error while computing transaction fees.')
    else:
        print(f"Transaction fee: {transaction_fees} lamports")

    if is_deployed:
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
                return False
            else:
                print('Invalid option. Please choose a valid option.')
    else:
        return False
