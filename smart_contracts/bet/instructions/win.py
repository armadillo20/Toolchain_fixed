from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class WinAccounts(typing.TypedDict):
    oracle: Pubkey
    winner: Pubkey
    bet_info: Pubkey
    participant1: Pubkey
    participant2: Pubkey


def win(
    accounts: WinAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["oracle"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["winner"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["bet_info"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["participant1"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["participant2"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'R"\x90h!\x17d\x04'
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
