import typing
from anchorpy.error import ProgramError


class InvalidParticipant(ProgramError):
    def __init__(self) -> None:
        super().__init__(6000, "Invalid participant")

    code = 6000
    name = "InvalidParticipant"
    msg = "Invalid participant"


class InvalidOracle(ProgramError):
    def __init__(self) -> None:
        super().__init__(6001, "Invalid oracle")

    code = 6001
    name = "InvalidOracle"
    msg = "Invalid oracle"


class DeadlineNotReached(ProgramError):
    def __init__(self) -> None:
        super().__init__(6002, "The deadline was not reached yet")

    code = 6002
    name = "DeadlineNotReached"
    msg = "The deadline was not reached yet"


class DeadlineReached(ProgramError):
    def __init__(self) -> None:
        super().__init__(6003, "The deadline was reached")

    code = 6003
    name = "DeadlineReached"
    msg = "The deadline was reached"


class WinnerWasChosen(ProgramError):
    def __init__(self) -> None:
        super().__init__(6004, "The winner was already chosen")

    code = 6004
    name = "WinnerWasChosen"
    msg = "The winner was already chosen"


class AllParticipantsHaveDeposited(ProgramError):
    def __init__(self) -> None:
        super().__init__(6005, "All participants have deposited")

    code = 6005
    name = "AllParticipantsHaveDeposited"
    msg = "All participants have deposited"


class ParticipantsHaveNotDeposited(ProgramError):
    def __init__(self) -> None:
        super().__init__(6006, "Not all participants have deposited")

    code = 6006
    name = "ParticipantsHaveNotDeposited"
    msg = "Not all participants have deposited"


CustomError = typing.Union[
    InvalidParticipant,
    InvalidOracle,
    DeadlineNotReached,
    DeadlineReached,
    WinnerWasChosen,
    AllParticipantsHaveDeposited,
    ParticipantsHaveNotDeposited,
]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    6000: InvalidParticipant(),
    6001: InvalidOracle(),
    6002: DeadlineNotReached(),
    6003: DeadlineReached(),
    6004: WinnerWasChosen(),
    6005: AllParticipantsHaveDeposited(),
    6006: ParticipantsHaveNotDeposited(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
