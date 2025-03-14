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


import os
import json
import re
import toml
from solana_module.utils import solana_base_path


anchor_base_path = f"{solana_base_path}/anchor_module"

def find_initialized_programs():
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

def find_program_instructions(program_name):
    idl_file_path = f'{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/target/idl/{program_name}.json'
    idl = load_idl(idl_file_path)

    instructions = []
    # Extract instructions
    for instruction in idl['instructions']:
        instructions.append(instruction['name'])
    return instructions, idl

def load_idl(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def find_required_accounts(instruction, idl):
    # Find the instruction in the IDL
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract required accounts, excluding the systemProgram
    required_accounts = [camel_to_snake(account['name']) for account in instruction_dict['accounts'] if account['name'] != 'systemProgram']

    return required_accounts

def camel_to_snake(camel_str):
    # Use regex to add a _ before uppercase letters, excluded the first letter
    snake_str = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', camel_str)
    # Converto to lower case the whole string, leaving only the first letter as it is
    return snake_str[0] + snake_str[1:].lower()

def fetch_cluster(program_name):
    file_path = f"{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/Anchor.toml"
    config = toml.load(file_path)
    cluster = config['provider']['cluster']
    if cluster == "Localnet" or cluster == "Devnet" or cluster == "Mainnet":
        return cluster
    else:
        raise Exception("Cluster not found or not equal to the available choices")

def find_signer_accounts(instruction, idl):
    # Find the instruction in the IDL
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract signer accounts
    required_signer_accounts = [account['name'] for account in instruction_dict['accounts'] if account['isSigner']]

    return required_signer_accounts

def find_args(instruction, idl):
    # Find instruction
    instruction_dict = next(instr for instr in idl['instructions'] if instr['name'] == instruction)

    # Extract args
    required_args = [{'name': camel_to_snake(arg['name']), 'type': arg['type']} for arg in instruction_dict['args']]

    return required_args