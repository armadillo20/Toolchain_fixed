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
from solana_module.solana_utils import create_client, choose_wallet
from solana_module.anchor_module.anchor_utils import find_initialized_programs, find_program_instructions, \
    find_required_accounts, find_signer_accounts, generate_pda, find_args, check_type, convert_type, \
    fetch_cluster
from solana_module.anchor_module.transaction_manager import manage_transaction


# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

def choose_program_to_run():
    # Fetch initialized programs
    initialized_programs = find_initialized_programs()
    if len(initialized_programs) == 0:
        print("No program has been initialized yet.")
        return

    # Generate list of numbers corresponding to the number of found programs
    allowed_choices = list(map(str, range(1, len(initialized_programs) + 1))) + ['0']
    repeat = True

    # Repeat is needed to manage the going back from the following menus
    while repeat:
        choice = None
        # Print available programs
        while choice not in allowed_choices:
            print("Which program do you want to run?")
            for idx, program_name in enumerate(initialized_programs, 1):
                print(f"{idx}) {program_name}")
            print("0) Back to mode selection")

            choice = input()
            if choice == '0':
                return
            elif choice in allowed_choices:
                # Manage choice
                chosen_program = initialized_programs[int(choice) - 1]
                instructions, idl = find_program_instructions(chosen_program)
                # If initialized instructions are found
                if instructions:
                    repeat = _choose_instruction_to_run(instructions, idl, chosen_program)
                else:
                    print("No instructions found for this program")
                    repeat = True
            else:
                print("Please choose a valid choice.")




# ====================================================
# PRIVATE FUNCTIONS
# ====================================================

# ====================================================
# Instruction selection
# ====================================================

def _choose_instruction_to_run(instructions, idl, program_name):
    # Generate list of numbers corresponding to the number of found instructions + the option to come back
    allowed_choices = list(map(str, range(1, len(instructions) + 1))) + ['0']
    choice = None
    repeat = True

    while repeat:
        while choice not in allowed_choices:
            print("Which instruction do you want to run?")
            for idx, instruction in enumerate(instructions, 1):
                print(f"{idx}) {instruction}")
            print("0) Back to program selection")
            choice = input()

            if choice == '0':
                return True
            elif choice in allowed_choices:
                # Run chosen program
                repeat = _setup_required_accounts(instructions[int(choice) - 1], idl, program_name)
            else:
                print("Please choose a valid choice")

    return False # Needed to come back to main menu after finishing

# ====================================================
# Accounts management
# ====================================================

def _setup_required_accounts(instruction, idl, program_name):
    required_accounts = find_required_accounts(instruction, idl)
    signer_accounts = find_signer_accounts(instruction, idl)
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
                keypair = choose_wallet()
                if keypair is not None:
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

    return False

# ====================================================
# Args management
# ====================================================

def _setup_args(instruction, idl, program_name, accounts, signer_account_keypairs):
    required_args = find_args(instruction, idl)
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
            if isinstance(arg['type'], dict) and 'array' in arg['type']:
                array_type = check_type(arg['type']['array'][0])
                if array_type is None:
                    print("Unsupported type for arg {arg['name']}")
                    return False
                array_length = arg['type']['array'][1]
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
        i -= 1

    return False

# ====================================================
# Provider management
# ====================================================

def _manage_provider(program_name, instruction, accounts, args, signer_account_keypairs):
    print("Now working with the transaction provider.")
    keypair = choose_wallet()
    if keypair is None:
        return True
    else:
        cluster = fetch_cluster(program_name)
        client = create_client(cluster)
        provider_wallet = Wallet(keypair)
        provider = Provider(client, provider_wallet)
        asyncio.run(manage_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider))