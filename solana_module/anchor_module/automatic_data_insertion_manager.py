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


import csv
import os
from solders.pubkey import Pubkey
from anchorpy import Wallet, Provider
from solana_module.anchor_module.transaction_manager import build_transaction, measure_transaction_size, \
    compute_transaction_fees, send_transaction
from solana_module.solana_utils import load_keypair_from_file, solana_base_path, create_client
from solana_module.anchor_module.anchor_utils import anchor_base_path, find_initialized_programs, \
    find_program_instructions, find_required_accounts, find_signer_accounts, find_args, check_type, convert_type


# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

async def run_execution_trace():
    # Fetch initialized programs
    initialized_programs = find_initialized_programs()
    if len(initialized_programs) == 0:
        print("No program has been initialized yet.")
        return

    results = []
    print(f"Place execution trace in the in the execution_traces folder of the Anchor module")
    print("Insert name of the execution trace file")
    file_name = input()
    csv_file = _read_csv(f"{anchor_base_path}/execution_traces/{file_name}")
    if csv_file is None:
        print("Execution trace not found")
        return

    # For each execution trace
    for index, row in enumerate(csv_file, start=1):
        print(f"Working on execution trace {index}...")
        # Separate values
        execution_trace = row[0].split(";")

        # Get execution trace ID
        trace_id = execution_trace[0]

        # Manage program
        program_name = execution_trace[1]
        if program_name not in initialized_programs:
            print(f"Program {program_name} not initialized yet (execution trace {trace_id}).")
            return

        # Manage instruction
        instructions, idl = find_program_instructions(program_name)
        instruction = execution_trace[2]
        if instruction not in instructions:
            print(f"Instruction {instruction} not found for the program {program_name} (execution trace {trace_id}).")

        # Manage accounts
        required_accounts = find_required_accounts(instruction, idl)
        signer_accounts = find_signer_accounts(instruction, idl)
        final_accounts = dict()
        signer_accounts_keypairs = dict()
        i = 3
        for account in required_accounts:
            # If it is a wallet
            if execution_trace[i].startswith("W:"):
                wallet_name = execution_trace[i].removeprefix('W:')
                file_path = f"{solana_base_path}/solana_wallets/{wallet_name}"
                keypair = load_keypair_from_file(file_path)
                if keypair is None:
                    print(f"Wallet for account {account} not found at path {file_path}.")
                    return
                if account in signer_accounts:
                    signer_accounts_keypairs[account] = keypair
                final_accounts[account] = keypair.pubkey()
            # If it is a PDA
            elif execution_trace[i].startswith("P:"):
                extracted_key = execution_trace[i].removeprefix('P:')
                pda_key = Pubkey.from_string(extracted_key)
                final_accounts[account] = pda_key
            else:
                print(f"Did not find 'W:' or 'P:' to indicate whether the cell contains a Wallet or a PDA.")
                return
            i += 1

        # Manage args
        required_args = find_args(instruction, idl)
        final_args = dict()
        for arg in required_args:
            type = check_type(arg["type"])
            if type is None:
                print(f"Unsupported type for arg {arg['name']}")
                return
            else:
                converted_value = convert_type(type, execution_trace[i])
                final_args[arg['name']] = converted_value
                i += 1

        # Manage provider
        provider_keypair_path = f"{solana_base_path}/solana_wallets/{execution_trace[i]}"
        keypair = load_keypair_from_file(provider_keypair_path)
        if keypair is None:
            print("Provider wallet not found.")
        i += 1
        cluster = execution_trace[i]
        client = create_client(cluster)
        provider_wallet = Wallet(keypair)
        provider = Provider(client, provider_wallet)

        # Manage transaction
        transaction = await build_transaction(program_name, instruction, final_accounts, final_args, signer_accounts_keypairs, client, provider)
        size = measure_transaction_size(transaction)
        fees = await compute_transaction_fees(client, transaction)
        transaction_hash = await send_transaction(provider, transaction)

        # CSV building
        csv_row = [trace_id, transaction_hash, size, fees]
        results.append(csv_row)

        print(f"Execution trace {index} results computed!")

    # CSV writing
    file_name_without_extension = file_name.removesuffix(".csv")
    file_path = _write_csv(file_name_without_extension, results)
    print(f"Results written successfully to {file_path}")





# ====================================================
# PRIVATE FUNCTIONS
# ====================================================

def _read_csv(file_path):
    if os.path.exists(file_path):
        with open(file_path, mode='r') as file:
            csv_file = csv.reader(file)
            return list(csv_file)
    else:
        return None

def _write_csv(file_name, results):
    folder = f'{anchor_base_path}/execution_traces_results/'
    csv_file = os.path.join(folder, f'{file_name}_results.csv')

    # Create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)

    # Write CSV file
    with open(csv_file, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        for row in results:
            csv_writer.writerow(row)
    return csv_file