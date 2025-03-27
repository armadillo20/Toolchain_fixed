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
    check_if_array
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
            print("Is this account a Wallet or a PDA?")
            print(f"1) Wallet")
            print(f"2) PDA")
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
            elif choice == '0':
                if i == 0:
                    return True
                else:
                    i -= 1  # Necessary to come back
            else:
                print(f"Please insert a valid choice.")

        repeat = _setup_args(instruction, idl, program_name, final_accounts, signer_accounts_keypairs)
        if i == 0:
            return True
        else:
            i -= 1

    return False

def _setup_args(instruction, idl, program_name, accounts, signer_account_keypairs):
    required_args = fetch_args(instruction, idl)
    repeat = _manage_args(required_args, program_name, instruction, accounts, signer_account_keypairs)
    if repeat:
        return True
    else:
        return False

def _manage_args(args, program_name, instruction, accounts, signer_account_keypairs):
    final_args = dict()
    repeat = True
    i = 0

    while repeat:
        while i < len(args):
            arg = args[i]
            print(f"Insert {arg['name']} value. ", end="", flush=True)

            # Arrays management
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
                    converted_value = convert_type(type, text_input)
                    if converted_value is not None:
                        final_args[arg['name']] = converted_value
                        i += 1
                    else:
                        print("Invalid input. Please try again.")
                        continue

        repeat = _manage_provider(program_name, instruction, accounts, final_args, signer_account_keypairs)
        if i == 0:
            if repeat:
                return True
            else:
                return False
        else:
            i -= 1

def _manage_provider(program_name, instruction, accounts, args, signer_account_keypairs):
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
        return asyncio.run(_manage_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider, is_deployed))

async def _manage_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider, is_deployed):
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