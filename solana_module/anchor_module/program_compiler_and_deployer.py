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


import toml
import re
import subprocess
import os
import platform
from solana_module.solana_utils import solana_base_path
from solana_module.anchor_module.anchor_utils import anchor_base_path


# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

def compile_programs():
    program_id = None
    programs_path = f"{anchor_base_path}/anchor_programs" # Path where anchor programs are placed

    operating_system = platform.system()

    # Read programs
    file_names, programs = _read_rs_files(programs_path)

    # For each program
    for file_name,program in zip(file_names,programs):
        print(f"Compiling program: {file_name}")
        file_name_without_extension = file_name.removesuffix(".rs") # Get filename without .rs extension

        # Compiling phase
        done = _compile_program(file_name_without_extension, operating_system, program) # Compile program
        if not done:
            return

        # Deploying phase
        allowed_choice = ['y', 'n', 'Y', 'N']
        choice = None
        while choice not in allowed_choice:
            print("Deploy compiled program? (y/n):")
            choice = input()
            if choice == "y" or choice == "Y":
                program_id = _deploy_program(file_name_without_extension, operating_system)
            elif choice == "n" or choice == "N":
                return
            else:
                print('Please insert a valid choice.')

        # Anchorpy initialization phase
        if program_id: # If deploy succeed, initialize anchorpy
            _initialize_anchorpy(file_name_without_extension, program_id, operating_system)




# ====================================================
# PRIVATE FUNCTIONS
# ====================================================


# ====================================================
# Compiling phase functions
# ====================================================

def _read_rs_files(programs_path):
    # Check if the folder exists
    if not os.path.isdir(programs_path):
        print(f"The path '{programs_path}' does not exist.")
    else:
        # Get all .rs in the programs path
        file_names = [f for f in os.listdir(programs_path) if f.endswith(".rs")]

        # Read content of each file and store it in anchor_programs list
        anchor_programs = []
        for file_name in file_names:
            full_path = os.path.join(programs_path, file_name)
            with open(full_path, "r", encoding="utf-8") as f:
                anchor_programs.append(f.read())

        return file_names, anchor_programs

def _compile_program(program_name, operating_system, program):
    # Initialization phase
    done = _perform_anchor_initialization(program_name, operating_system)
    if not done:
        return False

    # Build phase
    done = _perform_anchor_build(program_name, program, operating_system)
    if not done:
        return False

    return True

def _perform_anchor_initialization(program_name, operating_system):
    # Define Anchor initialization commands to be executed
    initialization_commands = [
        f"mkdir -p {anchor_base_path}/.anchor_files/{program_name}", # Create folder for new program
        f"cd {anchor_base_path}/.anchor_files/{program_name}",  # Change directory to new folder
        "anchor init anchor_environment",  # Initialize anchor environment
    ]

    # Merge commands with '&&' to execute them on the same shell
    initialization_concatenated_command = " && ".join(initialization_commands)

    # Run Anchor initialization
    return _run_anchor_initialization_commands(operating_system, initialization_concatenated_command)

def _perform_anchor_build(program_name, program, operating_system):
    # Define Anchor build commands to be executed
    build_commands = [
        f"cd {anchor_base_path}/.anchor_files/{program_name}/anchor_environment",  # Change directory to new anchor environment
        "anchor build"  # Build program
    ]

    # Merge commands with '&&' to execute them on the same shell
    build_concatenated_command = " && ".join(build_commands)

    # Run Anchor build
    return _run_anchor_build_commands(program_name, program, operating_system, build_concatenated_command)

def _run_anchor_initialization_commands(operating_system, initialization_concatenated_command):
    # Initialize Anchor project
    print("Initializing Anchor project...")
    result = _run_command(operating_system, initialization_concatenated_command)

    # Error checks
    if result is None:
        print("Unsupported operating system.")
        return False
    # If there are error while initializing Anchor project, print them
    elif result.stderr:
        print(result.stderr)

    return True # Sometimes stderr is just a warning, so we return true anyway

def _run_anchor_build_commands(program_name, program, operating_system, build_concatenated_command):
    print("Building Anchor program, this may take a while... Please be patient.")
    _write_program_in_lib_rs(program_name, program)
    result = _run_command(operating_system, build_concatenated_command)
    if result is None:
        print("Unsupported operating system.")
        return False
    elif result.stderr:
        # try by imposing cargo version 3
        _impose_cargo_lock_version(program_name)
        result = _run_command(operating_system, build_concatenated_command)
        if result.stderr:
            print(result.stderr)

    return True # Sometimes stderr is just a warning, so we return true anyway

def _write_program_in_lib_rs(program_name, program):
    program = _update_program_id(program_name, program)
    lib_rs_path = f"{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/programs/anchor_environment/src/lib.rs"
    with open(lib_rs_path, 'w') as file:
        file.write(program)

def _update_program_id(program_name, program):
    file_path = f"{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/programs/anchor_environment/src/lib.rs"

    # Read program id generated by Anchor
    with open(file_path, 'r') as file:
        content = file.read()
        match = re.search(r'declare_id!\s*\(\s*"([^"]+)"\s*\)\s*;', content)
        if match:
            new_program_id = match.group(1)
        else:
            raise ValueError("Program ID not found in file")

    # Substitute program id in the file
    program = re.sub(r'declare_id!\s*\(\s*"([^"]+)"\s*\)\s*;', f'declare_id!("{new_program_id}");', program)
    return program

def _impose_cargo_lock_version(program_name):
    file_path = f"{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/Cargo.lock"
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            # Substitute each value of version with 3
            line = re.sub(r'^version = \d+', 'version = 3', line)
            file.write(line)



# ====================================================
# Deploying phase functions
# ====================================================

def _deploy_program(program_name, operating_system):
    file_path = f"{solana_base_path}/solana_wallets/my_wallet.json"
    print("Place your wallet in the solana_wallets folder and rename it to my_wallet.json. Press enter when done.")
    input()
    # Check if wallet exists
    if not os.path.exists(file_path):
        print(f"File my_wallet.json not found")
        return

    # Manage cluster choice
    allowed_choices = ["1", "2", "3"]
    choice = None
    cluster = None

    while choice not in allowed_choices:
        print("Where do you want to deploy program?")
        print("1. Localnet")
        print("2. Devnet")
        print("3. Mainnet")
        choice = input()
        if choice == "1":
            cluster = "Localnet"
        elif choice == "2":
            cluster = "Devnet"
        elif choice == "3":
            cluster = "Mainnet"
        else:
            print("Please insert a valid choice.")

    # Modify generated file to set chosen cluster
    _modify_cluster_wallet(program_name, cluster)

    # Define deploy commands to be executed
    deploy_commands = [
        f"cd {anchor_base_path}/.anchor_files/{program_name}/anchor_environment/",  # Change directory to environment folder
        "anchor deploy",  # Deploy program
    ]

    # Merge commands with '&&' to execute them on the same shell
    deploy_concatenated_command = " && ".join(deploy_commands)

    # Run Anchor deploy
    program_id = _run_deploying_commands(operating_system, deploy_concatenated_command)

    return program_id

def _modify_cluster_wallet(program_name, cluster):
    file_path = f"{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/Anchor.toml"
    config = toml.load(file_path)

    # Edit values
    config['provider']['cluster'] = cluster
    config['provider']['wallet'] = "../../../../solana_wallets/my_wallet.json"

    # Save modifications
    with open(file_path, 'w') as file:
        toml.dump(config, file)

def _run_deploying_commands(operating_system, deploy_concatenated_command):
    print("Deploying program...")
    result = _run_command(operating_system, deploy_concatenated_command)
    if result is None:
        print("Unsupported operating system.")
        return None
    elif result.stderr:
        print(result.stderr)
        return None
    else:
        program_id, signature = _get_deploy_details(result.stdout)
        print("Deploy success")
        print(f"Program ID: {program_id}")
        print(f"Signature: {signature}")
        return program_id

def _get_deploy_details(output):
    # RegEx to find Program ID and signature
    program_id_pattern = r"Program Id: (\S+)"
    signature_pattern = r"Signature: (\S+)"

    # Find Program ID
    program_id_match = re.search(program_id_pattern, output)
    program_id = program_id_match.group(1) if program_id_match else None

    # Find Signature
    signature_match = re.search(signature_pattern, output)
    signature = signature_match.group(1) if signature_match else None

    return program_id, signature



# ====================================================
# Anchorpy initialization phase functions
# ====================================================

def _initialize_anchorpy(program_name, program_id, operating_system):
    idl_path = f"{anchor_base_path}/.anchor_files/{program_name}/anchor_environment/target/idl/{program_name}.json"
    output_directory = f"{anchor_base_path}/.anchor_files/{program_name}/anchorpy_files/"
    anchorpy_initialization_command = f"anchorpy client-gen {idl_path} {output_directory} --program-id {program_id}"

    _run_initializing_anchorpy_commands(operating_system, anchorpy_initialization_command)

def _run_initializing_anchorpy_commands(operating_system, anchorpy_initialization_command):
    print("Initializing anchorpy...")
    result = _run_command(operating_system, anchorpy_initialization_command)
    if result is None:
        print("Unsupported operating system.")
    elif result.stderr:
        print(result.stderr)
    else:
        print("Anchorpy initialized successfully")



# ====================================================
# Utils functions
# ====================================================

def _run_command(operating_system, command):
    if operating_system == "Windows":
        result = subprocess.run(["wsl", command], capture_output=True, text=True) # On Windows, use WSL to execute commands in a Linux shell
    elif platform.system() == "Darwin" or platform.system() == "Linux":
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    else:
        result = None

    return result