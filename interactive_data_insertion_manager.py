import json
import re
import os
import toml
import random
import string
import importlib
import importlib.util
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from anchorpy import Provider, Wallet
from function_caller import make_transaction


def choose_program_to_run():
    programs = find_initialized_programs()

    # Generate list of numbers corresponding to the number of found programs
    allowed_choices = list(map(str, range(1, len(programs) + 1)))
    choice = None

    # If initialized programs are found
    if programs:
        while choice not in allowed_choices:
                print("Which program do you want to run?")
                for idx, program in enumerate(programs, 1):
                    print(f"{idx}. {program}")
                choice = input()

        # Run chosen program
        choose_instruction_to_run(programs[int(choice) - 1])
    else:
        print("No program has been initialized yet.")
        return

def find_initialized_programs():
    path_to_explore = ".anchor_files"
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

def choose_instruction_to_run(program):
    # Get list of instructions from IDL file
    idl_file_path = f'.anchor_files/{program}/anchor_environment/target/idl/{program}.json'
    idl = load_idl(idl_file_path)
    instructions = find_program_functions(idl)

    # Generate list of numbers corresponding to the number of found instructions
    allowed_choices = list(map(str, range(1, len(instructions) + 1)))
    choice = None

    # If initialized instructions are found
    if instructions:
        while choice not in allowed_choices:
                print("Which instruction do you want to run?")
                for idx, instruction in enumerate(instructions, 1):
                    print(f"{idx}. {instruction}")
                choice = input()

        # Run chosen program
        prepare_instruction(instructions[int(choice) - 1], idl, program)
    else:
        print("No instructions found for this program")
        return

def load_idl(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def find_program_functions(idl):
    instructions_list = []
    # Extract instructions
    for instruction in idl['instructions']:
        instructions_list.append(instruction['name'])
    return instructions_list

def prepare_instruction(instruction, idl, program):
    client = manage_cluster(program)
    required_accounts, required_signer_accounts = find_required_accounts(instruction, idl)
    required_args = find_args(instruction, idl)
    accounts, signer_accounts_keypairs = manage_required_accounts(required_accounts, required_signer_accounts, program)
    args = manage_args(required_args)
    provider = prepare_provider(client)
    asyncio.run(make_transaction(program, instruction, accounts, signer_accounts_keypairs, args, client, provider))

def manage_cluster(program):
    cluster = fetch_cluster(program)
    print(f"This program is deployed on {cluster}")
    client = manage_cluster_setting(cluster)
    return client

def fetch_cluster(program):
    file_path = f"./.anchor_files/{program}/anchor_environment/Anchor.toml"
    config = toml.load(file_path)
    cluster = config['provider']['cluster']
    if cluster == "Localnet" or cluster == "Devnet" or cluster == "Mainnet":
        return cluster
    else:
        raise Exception("Cluster not found or not equal to the available choices")

def manage_cluster_setting(cluster):
    # Set client basing on the cluster
    rpc_url = None
    if cluster == "Localnet":
        rpc_url = "http://localhost:8899"
    elif cluster == "Devnet":
        rpc_url = "https://api.devnet.solana.com"
    elif cluster == "Mainnet":
        rpc_url = "https://api.mainnet-beta.solana.com"

    client = AsyncClient(rpc_url)
    return client

def find_required_accounts(instruction, idl):
    # Find the instruction in the IDL
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract required accounts, exluding the systemProgram
    required_accounts = [camel_to_snake(account['name']) for account in instruction_dict['accounts'] if account['name'] != 'systemProgram']

    # Extract signer accounts
    required_signer_accounts = [account['name'] for account in instruction_dict['accounts'] if account['isSigner']]

    return required_accounts, required_signer_accounts

def camel_to_snake(camel_str):
    # Use regex to add a _ before uppercase letters, excluded the first letter
    snake_str = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', camel_str)
    # Converto to lower case the whole string, leaving only the first letter as it is
    return snake_str[0] + snake_str[1:].lower()

def find_args(instruction, idl):
    # Find instruction
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract args
    required_args = [{'name': camel_to_snake(arg['name']), 'type': arg['type']} for arg in instruction_dict['args']]

    return required_args

def manage_required_accounts(required_accounts, required_signer_accounts, program):
    pda_accounts = []
    final_accounts = dict()
    signer_accounts_keypairs = dict()

    print("Required accounts to be inserted:")
    for account in required_accounts:
        print(f"- {account}")

    # Manage annotation of PDA accounts
    print("Please choose:")
    choice = None
    while not choice == '1':
        print("1. Continue")
        print("2. Some of these account is a PDA")
        choice = input()
        if choice == "2":
            required_accounts, pda_accounts = annotate_pda_account(required_accounts, pda_accounts)

    # Setup normal accounts
    for required_account in required_accounts:
        print(f"Place {required_account} wallet in the solana_wallets folder and rename it to {required_account}_wallet.json")
        print("Press enter when done")
        input()

        # Add the public key extracted from the wallet in the final_account dict
        keypair = load_keypair_from_file(f"./solana_wallets/{required_account}_wallet.json")
        final_accounts[required_account] = keypair.pubkey()

        # If it is a signer account, save its keypair into signer_accounts_keypairs
        if required_account in required_signer_accounts:
            signer_accounts_keypairs[required_account] = keypair
        print(f"{required_account} account added.")

    # Manage PDA accounts
    if pda_accounts:
        print("Let's continue with PDA accounts")
        for pda_account in pda_accounts:
            print(f"Now working with {pda_account} PDA account")
            final_accounts[pda_account] = manage_pda_account_creation(final_accounts, program)
            print(f"{pda_account} PDA account added.")

    return final_accounts, signer_accounts_keypairs

def annotate_pda_account(required_accounts, pda_accounts):
    allowed_choices = list(map(str, range(1, len(required_accounts) + 1)))
    choice = None

    while choice not in allowed_choices:
        print("Which of these account is a PDA?")
        for idx, account in enumerate(required_accounts, 1):
            print(f"{idx}. {account}")
        choice = input()

    pda_accounts.append(required_accounts[int(choice) - 1])
    required_accounts.pop(int(choice) - 1)
    print("PDA account added. We will work on it later.")

    return required_accounts, pda_accounts

def load_keypair_from_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        return Keypair.from_bytes(data)

def manage_pda_account_creation(final_accounts, program):
    # Dynamically import program id
    module_path = f"./.anchor_files/{program}/anchorpy_files/program_id.py"
    spec = importlib.util.spec_from_file_location("program_id", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    program_id = module.PROGRAM_ID

    pda_key = ''
    allowed_choices = ['1','2','3']
    choice = None

    while choice not in allowed_choices:
        print("How do you want to generate the PDA account?")
        print("1. Insert manually")
        print("2. Generate randomly")
        print("3. Generate using seeds")
        choice = input()
        if choice == "1":
            while len(pda_key) != 44:
                print("Insert PDA key. It must be 44 characters long.")
                pda_key = input()
        elif choice == "2":
            pda_key = ''.join(random.choices(string.ascii_letters + string.digits, k=44))
        elif choice == "3":
            pda_key, _ = manage_seed_choice(program_id, final_accounts)

    return pda_key

def manage_seed_choice(program_id, final_accounts):
    seeds = []
    allowed_choices = ['1','2','3']

    print("How many seeds do you want to use?")
    n_seeds = int(input())

    for i in range(n_seeds):
        # Reset choice for next seed insertions
        choice = None
        while choice not in allowed_choices:
            print(f"How do you want to insert the seed n. {i+1}?")
            print("1. Insert manually")
            print("2. Generate randomly")
            print("3. Generate using key from previously inserted account")
            choice = input()
            if choice == "1":
                while len(seeds[i]) != 44:
                    print("Insert seed. It must be 44 characters long.")
                    seeds[i] = input()
            elif choice == "2":
                seeds.append(''.join(random.choices(string.ascii_letters + string.digits, k=44)))
            elif choice == "3":
                if final_accounts.items():
                    seeds.append(bytes(manage_seed_generation_from_account(final_accounts)))
                else:
                    print("No account has been inserted yet.")
                    choice = None

    return Pubkey.find_program_address(seeds, program_id)

def manage_seed_generation_from_account(final_accounts):
    # Generate list of numbers corresponding to the number of found accounts
    allowed_choices = list(map(str, range(1, len(final_accounts.items()) + 1)))
    choice = None

    # If there are inserted accounts
    if final_accounts.items():
        while choice not in allowed_choices:
            print("Which account do you want to use for generating the key?")
            for idx, (name, pubkey) in enumerate(final_accounts.items(), 1):
                print(f"{idx}. {name}")
            choice = input()
        return list(final_accounts.values())[int(choice) - 1]

def manage_args(args):
    final_args = dict()

    for arg in args:
        print(f"Insert {arg['name']} value. ", end="", flush=True)

        # Arrays management
        if isinstance(arg['type'], dict) and 'array' in arg['type']:
            array_type = arg['type']['array'][0]
            array_length = arg['type']['array'][1]
            print(f"It is an array of {check_type(array_type)} type and length {array_length}. Please insert array values separated by spaces")
            array_values = input().split()

            # Check if array has correct length
            if len(array_values) != array_length:
                raise Exception(f"Error: Expected array of length {array_length}, but got {len(array_values)}")

            # Convert array elements basing on the type
            for i in range(len(array_values)):
                array_values[i] = check_type_and_convert(array_type, array_values[i])

            final_args[arg['name']] = array_values

        else:
            # Single value management
            print(f"It is a {check_type(arg['type'])}")
            text_input = input()
            final_args[arg['name']] = check_type_and_convert(arg['type'], text_input)

    return final_args

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
    if (type == "u8" or type == "u16" or type == "u32" or type == "u64" or type == "u128" or type == "u256"
            or type == "i8" or type == "i16" or type == "i32" or type == "i64" or type == "i128" or type == "i256"):
        return int(value)
    elif type == "bool":
        return bool(value)
    elif type == "f32" or type == "f64":
        return float(value)
    elif type == "string":
        return value
    else:
        return value

def prepare_provider(client):
    print("Place your wallet in the solana_wallets folder and rename it to my_wallet.json")
    print("Press enter when done")
    input()
    provider_account = load_keypair_from_file("./solana_wallets/my_wallet.json")
    provider_wallet = Wallet(provider_account)
    provider = Provider(client, provider_wallet)
    return provider