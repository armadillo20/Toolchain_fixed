import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey
from ..program_id import PROGRAM_ID


class BetInfoJSON(typing.TypedDict):
    oracle: str
    participant1: str
    participant2: str
    wager: int
    deadline: int


@dataclass
class BetInfo:
    discriminator: typing.ClassVar = b"\xf0\xbfk\x8f\xc7\xfa\xd5\xb4"
    layout: typing.ClassVar = borsh.CStruct(
        "oracle" / BorshPubkey,
        "participant1" / BorshPubkey,
        "participant2" / BorshPubkey,
        "wager" / borsh.U64,
        "deadline" / borsh.U64,
    )
    oracle: Pubkey
    participant1: Pubkey
    participant2: Pubkey
    wager: int
    deadline: int

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["BetInfo"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[Pubkey],
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["BetInfo"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["BetInfo"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "BetInfo":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = BetInfo.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            oracle=dec.oracle,
            participant1=dec.participant1,
            participant2=dec.participant2,
            wager=dec.wager,
            deadline=dec.deadline,
        )

    def to_json(self) -> BetInfoJSON:
        return {
            "oracle": str(self.oracle),
            "participant1": str(self.participant1),
            "participant2": str(self.participant2),
            "wager": self.wager,
            "deadline": self.deadline,
        }

    @classmethod
    def from_json(cls, obj: BetInfoJSON) -> "BetInfo":
        return cls(
            oracle=Pubkey.from_string(obj["oracle"]),
            participant1=Pubkey.from_string(obj["participant1"]),
            participant2=Pubkey.from_string(obj["participant2"]),
            wager=obj["wager"],
            deadline=obj["deadline"],
        )
