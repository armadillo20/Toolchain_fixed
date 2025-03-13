from solana_module.account_balance_manager import request_balance
from solana_module.anchor_module import anchor_user_interface
# ADD HERE NEW SOLANA LANGUAGES REQUIRED IMPORTS (STARTING FROM THE PROJECT ROOT)


def request_balance_or_choose_language():
    # Manage allowed choices
    allowed_choices = ['1', '2', '0']
    choice = None

    # Print available choices
    while choice not in allowed_choices:
        print("Please choose:")
        print("1) Choose language")
        print("2) Request balance")
        print("0) Back to module selection")

        choice = input()

        if choice == '1':
            _choose_language()
            choice = None
        elif choice == '2':
            request_balance()
            choice = None
        elif choice == '0':
            return
        else:
            print("Invalid choice. Please insert a valid choice.")

def _choose_language():
    # ADD HERE NEW SUPPORTED LANGUAGES
    supported_languages = ['Anchor']

    # Manage allowed choices
    allowed_choices = list(map(str, range(1, len(supported_languages) + 1))) + ['0']
    choice = None

    # Print available choices
    while choice not in allowed_choices:
        print("Please choose:")
        for i, lang in enumerate(supported_languages, start=1):
            print(f"{i}) {lang}")
        print("0) Go back")

        choice = input()

        if choice == '1':
            anchor_user_interface.choose_action()
            choice = None
        # ADD HERE NEW LANGUAGE CALLS
        elif choice == '0':
            return
        else:
            print("Invalid choice. Please insert a valid choice.")

