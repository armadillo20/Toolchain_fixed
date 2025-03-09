from program_compiler_and_deployer import *
from interactive_data_insertion_manager import *
from account_balance_manager import *


if __name__ == "__main__":
    # Path where anchor programs are placed
    programs_path = "anchor_programs"
    allowed_choices = ["1", "2", "3" "0"]

    # Interactive menu
    choice = None
    while choice != "0":
        # Print options
        print("What you wanna do?")
        print(f"1. Compile new program(s) (Place .rs files in {programs_path} folder)")
        print("2. Run program (Only anchorpy initialized programs)")
        print("3. Check account balance")
        print("0. Exit")

        # Manage choice
        choice = input()
        if choice == "1":
            file_names, programs = read_rs_files(programs_path)
            compile_programs(file_names, programs)
        elif choice == "2":
            choose_program_to_run()
        elif choice == "3":
            choose_wallet()
        elif choice == "0":
            print("Exiting...")
        elif choice not in allowed_choices:
            print("Please insert a valid choice.")
