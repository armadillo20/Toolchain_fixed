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


from solana_module.anchor_module.anchor_utils import find_initialized_programs, generate_pda


def choose_program_for_pda_generation():
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
            print("For which program you want to generate a PDA key?")
            for idx, program_name in enumerate(initialized_programs, 1):
                print(f"{idx}) {program_name}")
            print("0) Back to utilities")

            choice = input()
            if choice == '0':
                return
            elif choice in allowed_choices:
                # Manage choice
                chosen_program = initialized_programs[int(choice) - 1]
                pda = generate_pda(chosen_program, True)
                if pda is not None:
                    repeat = False
            else:
                print("Please choose a valid choice.")