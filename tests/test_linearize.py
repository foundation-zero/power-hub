from dataclasses import dataclass

import pytest

from energy_box_control.linearize import linearize


@dataclass(eq=True, frozen=True)
class Item:
    deps: "tuple[Item, ...]"


def test_linearize_abcd():
    a = Item(())
    b = Item((a,))
    c = Item((a, b))
    d = Item((a, b, c))

    result = linearize([d, c, b, a], lambda item: item.deps, lambda x: [x])
    assert result == [a, b, c, d]


def test_circular():
    with pytest.raises(Exception, match="failed to linearize"):
        a = Item(())
        b = Item((a,))

        # using or (b,) to make the circular dependency
        linearize([a, b], lambda item: item.deps or (b,), lambda x: [x])
