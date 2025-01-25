from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class JoinArgs(typing.TypedDict):
    delay: int
    wager: int


layout = borsh.CStruct("delay" / borsh.U64, "wager" / borsh.U64)


class JoinAccounts(typing.TypedDict):
    participant1: Pubkey
    participant2: Pubkey
    oracle: Pubkey
    bet_info: Pubkey


def join(
    args: JoinArgs,
    accounts: JoinAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["participant1"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["participant2"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["bet_info"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xce7\x02jq\xdc\x11\xa3"
    encoded_args = layout.build(
        {
            "delay": args["delay"],
            "wager": args["wager"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
