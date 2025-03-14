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
import re
import os
import toml
import random
import string
import importlib
import importlib.util
import asyncio

from based58 import b58encode
from solders.pubkey import Pubkey
from anchorpy import Provider, Wallet
from solana_module.utils import create_client
from solana_module.anchor_module.utils import anchor_base_path
from solana_module.utils import load_keypair_from_file, solana_base_path
from solana_module.anchor_module.transaction_manager import manage_transaction


# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

def run_program():
    # Fetch initialized programs
    program_names = _find_initialized_programs()
    if len(program_names) == 0:
        print("No program has been initialized yet.")
        return

    _choose_program_to_run(program_names)




# ====================================================
# PRIVATE FUNCTIONS
# ====================================================


# ====================================================
# Program selection
# ====================================================

def _find_initialized_programs():
    path_to_explore = f"{anchor_base_path}/.anchor_files"
    programs_with_anchorpy_files = []

    # Check if the base directory exists before proceeding
    if not os.path.exists(path_to_explore):
        return programs_with_anchorpy_files

    # Iterate program folders
    for program in os.listdir(path_to_explore):
        program_path = os.path.join(path_to_explore, program)

        # Check if anchorpy_files folder is present
        if os.path.isdir(program_path):
            anchorpy_path = os.path.join(program_path, 'anchorpy_files')
            if os.path.isdir(anchorpy_path):
                programs_with_anchorpy_files.append(program)

    return programs_with_anchorpy_files

def _choose_program_to_run(program_names):
    # Generate list of numbers corresponding to the number of found programs
    allowed_choices = list(map(str, range(1, len(program_names) + 1))) + ['0']
    repeat = True

    # Repeat is needed to manage the going back from the following menus
    while repeat:
        choice = None
        # Print available programs
        while choice not in allowed_choices:
            print("Which program do you want to run?")
            for idx, program_name in enumerate(program_names, 1):
                print(f"{idx}) {program_name}")
            print("0) Back to Anchor menu")

            choice = input()
            if choice == '0':
                return

        # Manage choice
        chosen_program = program_names[int(choice) - 1]
        instructions, idl = _find_program_instructions(chosen_program)
        # If initialized instructions are found
        if instructions:
            repeat = _choose_instruction_to_run(instructions, idl, chosen_program)
        else:
            print("No instructions found for this program")
            repeat = True



# ====================================================
# Instruction selection
# ====================================================

def _find_program_instructions(program_name):
    idl_file_path = f'{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/target/idl/{program_name}.json'
    idl = _load_idl(idl_file_path)

    instructions = []
    # Extract instructions
    for instruction in idl['instructions']:
        instructions.append(instruction['name'])
    return instructions, idl

def _load_idl(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

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
        else:
            # Run chosen program
            repeat = _preselect_pda_accounts(program_name, instructions[int(choice) - 1], idl)
            choice = None

    return False # Needed to come back to main menu after finishing



# ====================================================
# Accounts management
# ====================================================

def _preselect_pda_accounts(program_name, instruction, idl):
    repeat = True
    # Find cluster and print to let the user know
    cluster = _fetch_cluster(program_name)
    print(f"This program is deployed on {cluster}")

    # Fetch required accounts
    required_accounts = _find_required_accounts(instruction, idl)
    pda_accounts = []

    # Manage pda account pre-selection
    while repeat:
        # Print required accounts
        print("Required accounts to be inserted:")
        for account in required_accounts:
            print(f"- {account}")
        print('Press enter to continue...')
        input()

        # Manage annotation of PDA accounts
        allowed_choices = ['1', '2', '0']
        choice = None
        while choice not in allowed_choices:
            print("Please choose:")
            print("1) Continue")
            print("2) Some of these account is a PDA")
            print("0) Back to instruction selection")
            choice = input()
            if choice == '1':
                repeat = _setup_required_accounts(required_accounts, instruction, idl, pda_accounts, program_name, cluster)
            elif choice == "2":
                required_accounts, pda_accounts = _annotate_pda_account(required_accounts, pda_accounts)
                repeat = True
            elif choice == "0":
                return True # Needed to reload previous menu

    return False # needed to come back to main menu when finished

def _fetch_cluster(program_name):
    file_path = f"{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/Anchor.toml"
    config = toml.load(file_path)
    cluster = config['provider']['cluster']
    if cluster == "Localnet" or cluster == "Devnet" or cluster == "Mainnet":
        return cluster
    else:
        raise Exception("Cluster not found or not equal to the available choices")

def _find_required_accounts(instruction, idl):
    # Find the instruction in the IDL
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract required accounts, excluding the systemProgram
    required_accounts = [_camel_to_snake(account['name']) for account in instruction_dict['accounts'] if account['name'] != 'systemProgram']

    return required_accounts

def _camel_to_snake(camel_str):
    # Use regex to add a _ before uppercase letters, excluded the first letter
    snake_str = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', camel_str)
    # Converto to lower case the whole string, leaving only the first letter as it is
    return snake_str[0] + snake_str[1:].lower()

def _annotate_pda_account(required_accounts, pda_accounts):
    allowed_choices = list(map(str, range(1, len(required_accounts) + 1)))
    choice = None

    while choice not in allowed_choices:
        print("Which of these account is a PDA?")
        for idx, account in enumerate(required_accounts, 1):
            print(f"{idx}) {account}")
        print("0) Go back")
        choice = input()
        if choice == "0":
            return required_accounts, pda_accounts # Needed to come back

    pda_accounts.append(required_accounts[int(choice) - 1])
    required_accounts.pop(int(choice) - 1)
    print("PDA account added. We will work on it later.")

    return required_accounts, pda_accounts

def _setup_required_accounts(required_accounts, instruction, idl, pda_accounts, program_name, cluster):
    final_accounts = dict()
    signer_accounts_keypairs = dict()
    repeat = True

    # Setup classical accounts
    i = 0
    while repeat:
        while i < len(required_accounts):
            required_account = required_accounts[i]
            print(f"Place {required_account} wallet in the solana_wallets folder and rename it to {required_account}_wallet.json")
            print("1) Done")
            print("0) Go back")
            choice = input()
            if choice == '1':
                # Add the public key extracted from the wallet in the final_account dict
                keypair = load_keypair_from_file(f"{solana_base_path}/solana_wallets/{required_account}_wallet.json")
                if keypair is None:
                    print("Wallet not found.")
                    continue
                final_accounts[required_account] = keypair.pubkey()

                # If it is a signer account, save its keypair into signer_accounts_keypairs
                signer_accounts = _find_signer_accounts(instruction, idl)
                if required_account in signer_accounts:
                    signer_accounts_keypairs[required_account] = keypair
                print(f"{required_account} account added.")
                i += 1
            elif choice == '0':
                if i == 0:
                    return True # Needed to come back to previous menu
                else:
                    i -= 1
            else:
                print('Please choose a valid choice.')

        repeat = _setup_pda_accounts(pda_accounts, final_accounts, program_name, instruction, idl, cluster, final_accounts, signer_accounts_keypairs)
        if i != 0:
            i -= 1 # Necessary to come back
        else:
            return True

    return False

def _find_signer_accounts(instruction, idl):
    # Find the instruction in the IDL
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract signer accounts
    required_signer_accounts = [account['name'] for account in instruction_dict['accounts'] if account['isSigner']]

    return required_signer_accounts

def _setup_pda_accounts(pda_accounts, final_accounts, program_name, instruction, idl, cluster, accounts, signer_accounts_keypairs):
    repeat = True

    while repeat:
        if pda_accounts:
            print("\nLet's continue with PDA accounts")
            i = 0
            while i < len(pda_accounts):
                pda_account = pda_accounts[i]
                pda_key, repeat = _manage_pda_account_creation(final_accounts, program_name, pda_account)
                if repeat:
                    if i == 0:
                        return True
                    else:
                        i -= 1
                else:
                    final_accounts[pda_account] = pda_key
                    print(f"{pda_account} PDA account added.")
                    i += 1

        repeat = _setup_args(instruction, idl, cluster, program_name, accounts, signer_accounts_keypairs)

    return False

def _manage_pda_account_creation(final_accounts, program, pda_account):
    # Dynamically import program id
    module_path = f"{anchor_base_path}/.anchor_files/{program}/anchorpy_files/program_id.py"
    spec = importlib.util.spec_from_file_location("program_id", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    program_id = module.PROGRAM_ID

    pda_key = ''
    allowed_choices = ['1','2','3','0']

    repeat = True
    while repeat:
        choice = None
        print(f"Working with {pda_account} PDA account")
        while choice not in allowed_choices:
            print("How do you want to generate the PDA account?")
            print("1) Insert manually")
            print("2) Generate randomly")
            print("3) Generate using seeds")
            print("0) Go back")
            choice = input()
            if choice == "1":
                while len(pda_key) != 44:
                    print("Insert PDA key. It must be 44 characters long. (Insert 0 to go back)")
                    pda_key = input()
                    if pda_key == '0':
                        choice = None
                        break
                    else:
                        pda_key = Pubkey.from_string(pda_key)
            elif choice == "2":
                random_bytes = os.urandom(32)
                base58_str = b58encode(random_bytes).decode("utf-8")
                pda_key = Pubkey.from_string(base58_str)
                print(f'Extracted pda is: {pda_key}')
                repeat = False
            elif choice == "3":
                pda_key, repeat = _choose_number_of_seed(final_accounts, program_id)
            elif choice == "0":
                return None, True

    return pda_key, False

def _choose_number_of_seed(final_accounts, program_id):
    pda_key = None
    repeat = True

    while repeat:
        print("How many seeds do you want to use? (Insert 0 to go back)")
        n_seeds = int(input())
        if n_seeds == 0:
            return None, True
        pda_key, repeat = _manage_seed_insertion(n_seeds, final_accounts, program_id)

    return pda_key, False

def _manage_seed_insertion(n_seeds, final_accounts, program_id):
    allowed_choices = ['1','2','3','0']
    seeds = [None] * n_seeds

    i = 0
    while i < n_seeds:
        # Reset choice for next seed insertions
        choice = None
        while choice not in allowed_choices:
            print(f"How do you want to insert the seed n. {i+1}?")
            print("1) Insert manually")
            print("2) Generate randomly")
            print("3) Generate using key from previously inserted account")
            print("0) Go back")
            choice = input()
            if choice == "1":
                seed = ''
                while len(seed) != 32:
                    print("Insert seed. It must be 32 characters long. (Insert 0 to go back)")
                    seed = input()
                    if seed == '0':
                        choice = None
                        break
                seeds[i] = bytes(seed, 'utf-8')
                i += 1
            elif choice == "2":
                seed = os.urandom(32)
                print(f'Extracted seed (hex): {seed.hex()}')
                seeds[i] = seed
                i += 1
            elif choice == "3":
                if final_accounts.items():
                    seed, repeat = _manage_seed_generation_from_account(final_accounts)
                    if not repeat:
                        seeds[i] = bytes(seed)
                        i += 1
                else:
                    print("No account has been inserted yet.")
                    choice = None
            elif choice == "0":
                if i == 0:
                    return None, True
                else:
                    i -= 1

    return Pubkey.find_program_address(seeds, program_id)[0], False

def _manage_seed_generation_from_account(final_accounts):
    # Generate list of numbers corresponding to the number of found accounts
    allowed_choices = list(map(str, range(1, len(final_accounts.items()) + 1))) + ['0']
    choice = None

    # If there are inserted accounts
    if final_accounts.items():
        while choice not in allowed_choices:
            print("Which account do you want to use for generating the key?")
            for idx, (name, pubkey) in enumerate(final_accounts.items(), 1):
                print(f"{idx}) {name}")
            print("0) Go back")
            choice = input()
            if choice == "0":
                return None, True
        return list(final_accounts.values())[int(choice) - 1], False



# ====================================================
# Args management
# ====================================================

def _setup_args(instruction, idl, cluster, program_name, accounts, signer_account_keypairs):
    required_args = find_args(instruction, idl)
    repeat = manage_args(required_args, cluster, program_name, instruction, accounts, signer_account_keypairs)
    if repeat:
        return True
    else:
        return False

def find_args(instruction, idl):
    # Find instruction
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract args
    required_args = [{'name': _camel_to_snake(arg['name']), 'type': arg['type']} for arg in instruction_dict['args']]

    return required_args

def manage_args(args, cluster, program_name, instruction, accounts, signer_account_keypairs):
    final_args = dict()
    repeat = True
    i = 0

    while repeat:
        while i < len(args):
            arg = args[i]
            print(f"Insert {arg['name']} value. ", end="", flush=True)

            # Arrays management
            if isinstance(arg['type'], dict) and 'array' in arg['type']:
                array_type = arg['type']['array'][0]
                array_length = arg['type']['array'][1]
                print(f"It is an array of {check_type(array_type)} type and length {array_length}. Please insert array values separated by spaces (Insert 00 to go back to previous section).")
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
                        converted_value = check_type_and_convert(array_type, array_values[j])
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
                print(f"It is a {check_type(arg['type'])} (Insert 00 to go back to previous section).")
                text_input = input()
                if text_input == '00':
                    if i == 0:
                        return None, True
                    else:
                        i -= 1
                else:
                    converted_value = check_type_and_convert(arg['type'], text_input)
                    if converted_value is not None:
                        final_args[arg['name']] = converted_value
                        i += 1
                    else:
                        print("Invalid input. Please try again.")
                        continue

        repeat = manage_provider(cluster, program_name, instruction, accounts, final_args, signer_account_keypairs)
        i -= 1

    return False

def check_type(type):
    if (type == "u8" or type == "u16" or type == "u32" or type == "u64" or type == "u128" or type == "u256"
            or type == "i8" or type == "i16" or type == "i32" or type == "i64" or type == "i128" or type == "i256"):
        return "integer"
    elif type == "bool":
        return "boolean"
    elif type == "f32" or type == "f64":
        return "floating point number"
    elif type == "string":
        return "string"
    else:
        return ""

def check_type_and_convert(type, value):
    try:
        if (type == "u8" or type == "u16" or type == "u32" or type == "u64" or type == "u128" or type == "u256" or type == "i8" or type == "i16" or type == "i32" or type == "i64" or type == "i128" or type == "i256"):
            return int(value)
        elif type == "bool":
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        elif type == "f32" or type == "f64":
            return float(value)
        elif type == "string":
            return value
        else:
            raise ValueError("Unsupported type")
    except ValueError as e:
        return None



# ====================================================
# Provider management
# ====================================================

def manage_provider(cluster, program_name, instruction, accounts, args, signer_account_keypairs):
    keypair = _get_client_wallet()
    if keypair is None:
        return True

    client = create_client(cluster)
    provider_wallet = Wallet(keypair)
    provider = Provider(client, provider_wallet)
    asyncio.run(manage_transaction(program_name, instruction, accounts, args, signer_account_keypairs, client, provider))

def _get_client_wallet():
    allowed_choices = ['1', '0']
    choice = None

    while choice not in allowed_choices:
        print("Place your wallet in the solana_wallets folder and rename it to my_wallet.json")
        print("1) Done")
        print("0) Go back")
        choice = input()
        if choice == '1':
            keypair = load_keypair_from_file(f"{solana_base_path}/solana_wallets/my_wallet.json")
            if keypair is None:
                print("Wallet not found.")
                choice = None
            else:
                return keypair
        elif choice == '0':
            return None
        else:
            print("Please choose a valid choice")