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