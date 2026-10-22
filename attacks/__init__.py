"""Attack registry: one list of attacks shared by every watermarking method.

Each attack is a tuple (attack, params, fn), where fn(x) takes a mono float32 signal at
44.1 kHz and returns the attacked signal. Using this one list guarantees that every method
is tested with the same attacks and the same parameters.

    from attacks import all_attacks
    for attack, params, fn in all_attacks():
        y = fn(x)
"""

from __future__ import annotations

from attacks.compression import compression_attacks
from attacks.noise_filtering import noise_filtering_attacks
from attacks.time_dynamics import time_dynamics_attacks


def all_attacks(include_neural: bool = False) -> list[tuple[str, str, callable]]:
    """No-attack baseline + compression + time/dynamics + noise/filtering.

    include_neural: also add the EnCodec attack (needs `pip install encodec`).
    """
    return (
        [("none", "-", lambda x: x)]
        + compression_attacks(include_neural=include_neural)
        + time_dynamics_attacks()
        + noise_filtering_attacks()
    )
