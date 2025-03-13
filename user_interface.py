from solana_module.solana_user_interface import request_balance_or_choose_language
# ADD HERE NEW MODULES REQUIRED IMPORTS (STARTING FROM THE PROJECT ROOT)


def choose_module(supported_modules):
    # Manage allowed choices
    allowed_choices = list(map(str, range(1, len(supported_modules) + 1))) + ['0']
    choice = None

    # Print available choices
    while choice not in allowed_choices:
        print("Choose a module:")
        for i, lang in enumerate(supported_modules, start=1):
            print(f"{i}) {lang}")
        print("0) Exit")

        choice = input()

        if choice == '1':
            request_balance_or_choose_language()
            choice = None # Reset choice
        # ADD HERE NEW MODULE CALLS (elif)
        elif choice == 0:
            print("Exiting...")
        else:
            print("Invalid choice. Please insert a valid choice.")


if __name__ == "__main__":
    # ADD HERE NEW SUPPORTED MODULES
    supported_modules = ['Solana']

    # Start toolchain
    choose_module(supported_modules)