Before using Anchor module:
1. Do everything required by the README.md of the Solana module
2. Install anchor on your terminal. You can find a guide here: https://solana.com/it/docs/intro/installation. Do not install the last version of Anchor, version 0.29.0 MUST be installed.
3. Only if you are on Windows: install WSL

To use Anchor module:
Launch user_interface and reach Anchor section through the menus, then two possibilities are given:
- Compile and eventually deploy new anchor programs
  - Put your Anchor programs in .rs format inside the "anchor_programs" folder of the Anchor module
  - The tool will guide you to compile and eventually deploy each program inside the "anchor_programs" directory
- Run functions of a compiled and deployed Anchor program (must be compiled and deployed through the given toolchain)
  - The tool will guide you for inserting the required parameters, also letting you know the required types
  - It will launch the function with the given parameters, letting you know the transaction size and fees

Please note:
- Compiling may take a while, please be patient
- At the moment, if you make a wrong choice in the menu, you can't go back. Sorry, if that happens, restart the program and re-insert required data
- At the moment, the tool can only deal with classical parameter types (e.g. uint, int, float, string) and arrays. It can't deal with structs or other complex parameter types
- The tool has been tested only on bet and htlc smart contracts
