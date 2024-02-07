from typing import Tuple

State = Tuple[()]
Sensors = Tuple[()]
Controls = Tuple[()]


def control(state: State, sensors: Sensors) -> Tuple[(State, Controls)]:
    return ((), ())


if __name__ == "__main__":
    print("hello world")
