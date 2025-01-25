from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class TimeoutAccounts(typing.TypedDict):
    participant1: Pubkey
    participant2: Pubkey
    bet_info: Pubkey


def timeout(
    accounts: TimeoutAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["participant1"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["participant2"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["bet_info"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\t6.\xa9\x9c\xbdP\xf7"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
