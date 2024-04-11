from typing import Callable, Iterable, Set


def linearize[
    T, A
](
    items: Iterable[T],
    requires: Callable[[T], Iterable[A]],
    supplier: Callable[[T], Iterable[A]],
) -> list[T]:
    ordered: list[T] = []
    found: Set[A] = set()
    to_place = set(items)

    requirements = {item: set(requires(item)) for item in to_place}
    supplies = {item: set(supplier(item)) for item in to_place}

    while to_place:
        newly_found: list[T] = []

        for item in to_place:
            if not (requirements[item] - found):
                found.update(supplies[item])
                newly_found.append(item)

        if not newly_found:
            raise Exception("failed to linearize")

        for item in newly_found:
            to_place.remove(item)

        ordered.extend(newly_found)

    return ordered
