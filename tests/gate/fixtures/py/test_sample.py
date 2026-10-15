"""Test di fixture: passa deliberatamente.

Serve a dimostrare che, con pytest presente, il gate ESEGUE davvero la
validazione (verde RUMOROSO con evidenza), invece del verde-MUTO del gate
originale che usciva 0 senza guardare nulla sui progetti non-Node.
"""


def test_addizione():
    assert 1 + 1 == 2
