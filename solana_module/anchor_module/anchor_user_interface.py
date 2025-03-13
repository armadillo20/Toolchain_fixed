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


from solana_module.anchor_module.program_compiler_and_deployer import compile_programs
from solana_module.anchor_module.interactive_data_insertion_manager import run_program

def choose_action():
    allowed_choices = ["1", "2", "0"]
    choice = None

    # Interactive menu
    while choice != "0":
        # Print options
        print("What you wanna do?")
        print(f"1. Compile new program(s)")
        print("2. Run program (Only anchorpy initialized programs)")
        print("0. Back to Solana menu")

        # Manage choice
        choice = input()
        if choice == "1":
            compile_programs()
        elif choice == "2":
            run_program()
        elif choice == "0":
            print("Exiting...")
        elif choice not in allowed_choices:
            print("Please insert a valid choice.")