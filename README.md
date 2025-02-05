First:
- Install solana and anchor on your terminal. Here is the guide to install them: https://solana.com/it/docs/intro/installation . Do not install the last version of Anchor, version 0.29.0 MUST be installed.
- Install the tools required in the requirements.py file (Please let me know if someone is missing)
- Create at least one Solana wallet
- Airdrop the wallet (to pay transaction fees). You can do that at this link: https://faucet.solana.com


To execute the tool, launch main.py, then 3 possibilities are given:
1. Compile and eventually deploy new anchor programs
  - Put your Anchor programs in .rs format inside the "anchor_programs" folder in the main root of the tool.
  - Put your Solana wallet inside the "solana_wallets" folder in the main root
  - The tool will guide you to compile and eventually deploy each program inside che "anchor_programs" directory
2. Run functions of a compiled and deployed Anchor program (only through the given tool)
  - The tool will guide you for inserting the required parameters, also letting you know the required types
  - It will launch the function with the given parameters, letting you know the transaction size and fees
3. Check balance of a wallet
  - Put your wallet inside the "solana_wallets" folder.
  - The tool will ask you the name of the wallet for which you want to check the balance. Please insert full wallet filename (e.g. my_wallet.json)

Please note:
- Compiling may take a while, please be patient
- At the moment, if you make a wrong choice in the menu, you can't go back. Sorry, if that happens, restart the program and re-insert required data
- The tool still doesn't work with functions which do not require signers (e.g. timeout function of bet contract)
- At the moment, the tool can only deal with classical parameter types (e.g. uint, int, float, string) and arrays. It can't deal with structs or other complex parameter types
- The tool has been tested only on bet and htlc smart contracts
