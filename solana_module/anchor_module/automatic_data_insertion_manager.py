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
from solana_module.anchor_module.anchor_utils import anchor_base_path, find_initialized_programs, find_program_instructions, find_required_accounts


def run_execution_trace():
    print(f"Place execution trace in the in the execution_traces folder of the Anchor module")
    print("Insert name of the execution trace file")
    file_name = input()
    csv_file = _read_csv(f"{anchor_base_path}/execution_traces/{file_name}")
    if csv_file is None:
        print("Execution trace not found")
        return

    initialized_programs = find_initialized_programs()
    for execution_trace in csv_file:
        # Get execution trace ID
        trace_id = execution_trace[0]

        # Manage program
        program = execution_trace[1]
        if program not in initialized_programs:
            print(f"Program {program} not initialized yet (execution trace {trace_id}).")
            return

        # Manage instruction
        instructions, idl = find_program_instructions(program)
        instruction = execution_trace[2]
        if instruction not in instructions:
            print(f"Instruction {instruction} not found for the program {program} (execution trace {trace_id}).")

        # Manage accounts
        final_accounts = dict()
        signer_accounts_keypairs = dict()
        required_accounts = find_required_accounts(instruction, idl)
        i = 3
        for account in required_accounts:
            final_accounts[account] = Pubkey.from_string(execution_trace[i])
            i += 1



def _read_csv(file_path):
    if os.path.exists(file_path):
        with open(file_path, mode='r') as file:
            csv_file = csv.reader(file)
            return csv_file
    else:
        return None

def _write_csv():
    cartella = f'{anchor_base_path}/execution_traces_results'
    file_csv = os.path.join(cartella, 'file_results.csv')

    # Crea la cartella se non esiste
    os.makedirs(cartella, exist_ok=True)  # 'exist_ok=True' evita errori se la cartella esiste già

    # Scrivi il file CSV nella cartella
    with open(file_csv, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['Alice', 30, 'Roma'])