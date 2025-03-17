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


from solana_module.anchor_module.anchor_utils import find_initialized_programs, generate_pda, find_program_instructions, \
    find_args, load_idl, anchor_base_path, check_type


# ====================================================
# PUBLIC FUNCTIONS
# ====================================================

def get_initialized_programs():
    initialized_programs = find_initialized_programs()
    if len(initialized_programs) == 0:
        print("No program has been initialized yet.")
    else:
        print("Initialized programs:")
        for program in initialized_programs:
            print(f"- {program}")

def get_program_instructions():
    chosen_program = _choose_program()
    if not chosen_program:
        return
    else:
        idl_file_path = f'{anchor_base_path}/.anchor_files/{chosen_program}/anchor_environment/target/idl/{chosen_program}.json'
        idl = load_idl(idl_file_path)
        instructions = find_program_instructions(idl)
        if instructions is None:
            print("No instructions available for this program.")
        else:
            print("Instructions:")
            for instruction in instructions:
                print(f"- {instruction}")

def get_instruction_accounts():
    pass

def get_instruction_args():
    chosen_program = _choose_program()
    if not chosen_program:
        return
    else:
        idl_file_path = f'{anchor_base_path}/.anchor_files/{chosen_program}/anchor_environment/target/idl/{chosen_program}.json'
        idl = load_idl(idl_file_path)
        chosen_instruction = _choose_instruction(idl)
        if not chosen_instruction:
            return
        else:
            args = find_args(chosen_instruction, idl)
            print("Arguments:")
            for arg in args:
                print(f"- {arg['name']} ({check_type(arg['type'])})")


def choose_program_for_pda_generation():
    repeat = True
    while repeat:
        chosen_program = _choose_program()
        if not chosen_program:
            return
        else:
            pda = generate_pda(chosen_program, True)
            if pda is not None:
                repeat = False




# ====================================================
# PRIVATE FUNCTIONS
# ====================================================

def _choose_program():
    programs = find_initialized_programs()
    return _selection_menu('program', programs)

def _choose_instruction(idl):
    instructions = find_program_instructions(idl)
    return _selection_menu('instruction', instructions)

def _selection_menu(to_be_chosen, choices):
    # Generate list of numbers corresponding to the number of choices
    allowed_choices = list(map(str, range(1, len(choices) + 1))) + ['0']
    choice = None

    # Print available choices
    while choice not in allowed_choices:
        print(f"Please choose {to_be_chosen}:")
        for idx, program_name in enumerate(choices, 1):
            print(f"{idx}) {program_name}")
        print("0) Go back")

        choice = input()
        if choice == '0':
            return
        elif choice in allowed_choices:
            # Manage choice
            return choices[int(choice) - 1]
        else:
            print("Please choose a valid choice.")