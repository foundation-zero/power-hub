from energy_box_control.appliances.units import *

class Quantity:
    def __add__(self, other: Quantity | float | int) -> Quantity: ...
    __rmul__ = __add__
    __truediv__ = __add__
    __sub__ = __add__
    __radd__ = __add__
    __mul__ = __add__
    __gt__ = __add__
    __lt__ = __add__

    magnitude: float
    def to_base_units(self) -> Quantity: ...
