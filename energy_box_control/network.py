# pyright: reportInvalidTypeVarUse=false
# Disable single use of type vars, which is actually required to get the type checker to pass

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Self,
    TypeVar,
    TypeVarTuple,
    cast,
    overload,
)
import uuid

from energy_box_control.appliances import (
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.appliances.base import (
    Appliance,
    has_appliance_state,
    port_for_appliance,
)
from energy_box_control.time import ProcessTime
from energy_box_control.linearize import linearize

# This file uses some fancy Self type hints to ensure the Appliance and ApplianceState are kept in sync
AnyAppliance = Appliance[Any, Any, Any, Any, Any]
SpecificAppliance = Appliance[
    ApplianceState | None, ApplianceControl | None, Port, Any, Any
]
GenericState = ApplianceState | None
GenericControl = ApplianceControl | None
App = TypeVar("App", bound=AnyAppliance, covariant=True)
Prev = TypeVarTuple("Prev")
Net = TypeVar("Net", bound="Network[Any]", covariant=True)
FromPort = TypeVar("FromPort", bound=Port)
ToPort = TypeVar("ToPort", bound=Port)
From = TypeVar("From", bound=AnyAppliance, covariant=True)
To = TypeVar("To", bound=AnyAppliance, covariant=True)
ToControl = TypeVar("ToControl", bound=GenericControl)


class StateGetter[App: AnyAppliance]:
    def __init__[
        State: GenericState, Control: GenericControl, TPort: Port
    ](
        self: "StateGetter[Appliance[State, Control, TPort, Any, Any]]",
        _: App,
        state: State,
    ):
        self._state = state

    def get[
        State: GenericState, Control: GenericControl, TPort: Port
    ](self: "StateGetter[Appliance[State, Control, TPort, Any, Any]]") -> State:
        return cast(
            State, self._state
        )  # cast should be safe; State and App are bound together


class NetworkState(Generic[Net]):
    def __init__(
        self,
        time: ProcessTime,
        appliance_state: dict[AnyAppliance, ApplianceState | None],
        signals: dict[tuple[AnyAppliance, Port], Any] = {},
    ):
        self._appliance_state = appliance_state
        self._signals = signals
        self._time = time

    def get_appliances_states(
        self,
    ) -> dict[AnyAppliance, ApplianceState | None]:
        return self._appliance_state

    def get_signal(
        self,
    ) -> dict[tuple[AnyAppliance, Port], Any]:
        return self._signals

    def appliance[App: AnyAppliance](self, appliance: App) -> StateGetter[App]:
        return StateGetter(appliance, self._appliance_state[appliance])

    def has_connection(self, appliance: AnyAppliance, port: Port) -> bool:
        return (appliance, port) in self._signals

    @overload
    def connection(self, appliance: AnyAppliance, port: Port) -> Any: ...

    @overload
    def connection[T](self, appliance: AnyAppliance, port: Port, default: T) -> T: ...

    def connection[
        T
    ](self, appliance: AnyAppliance, port: Port, default: T | None = None) -> Any | T:
        if default:
            return self._signals.get((appliance, port), default)

        return self._signals[(appliance, port)]

    @property
    def time(self) -> ProcessTime:
        return self._time


class NetworkStateConnectionBuilder(Generic[Net, App, ToPort, *Prev]):
    def __init__(self, network: Net, connection: tuple[App, ToPort], *prev: *Prev):
        self._network = network
        self._connection = connection
        self._prev = prev

    def value[
        T
    ](self, signal: T) -> "NetworkStateBuilder[Net, *Prev, tuple[App, ToPort, T]]":
        return NetworkStateBuilder(
            self._network, *self._prev, (*self._connection, signal)
        )


class NetworkStateBuilder(Generic[Net, *Prev]):
    def __init__(self, network: Net, *prev: *Prev):
        self._network = network
        self._prev = prev

    def define_state[
        App: AnyAppliance
    ](self, app: App) -> "NetworkStateValueBuilder[Net, App, *Prev]":
        return NetworkStateValueBuilder(self._network, app, *self._prev)

    def build(self, time: ProcessTime) -> NetworkState[Net]:
        state = list(
            cast(
                Iterable[
                    tuple[
                        SpecificAppliance,
                        ApplianceState,
                    ]
                    | tuple[SpecificAppliance, Port, Any]
                ],
                self._prev,
            )
        )
        order = self._network.connections().execution_order()

        without_states = {app: None for app in order if not has_appliance_state(app)}
        appliance_states: dict[SpecificAppliance, GenericState] = {
            **dict(entry for entry in state if len(entry) == 2),
            **without_states,
        }

        missing_appliances = set(order) - set(appliance_states.keys())
        if missing_appliances:
            raise Exception(
                f"missing states for {[self._network.find_appliance_name_by_id(missing.id) for missing in missing_appliances]}"
            )

        connections = [entry for entry in state if len(entry) == 3]
        feedbacks = dict(((app, port), state) for app, port, state in connections)
        missing_feedbacks = set(self._network.feedback().port_mapping().keys()) - set(
            feedbacks.keys()
        )
        if missing_feedbacks:
            raise Exception(f"missing feedback states for {missing_feedbacks}")

        return NetworkState[Net](time, appliance_states, feedbacks)


class NetworkStateValueBuilder(Generic[Net, App, *Prev]):
    def __init__(self, network: Net, app: App, *prev: *Prev):
        self._network = network
        self._app = app
        self._prev = prev

    def at[
        State: GenericState, Control: GenericControl, TPort: Port
    ](
        self: "NetworkStateValueBuilder[Net, Appliance[State, Control, TPort, Any, Any], *Prev]",
        port: TPort,
    ) -> NetworkStateConnectionBuilder[Net, App, TPort, *Prev]:
        return cast(
            NetworkStateConnectionBuilder[Net, App, TPort, *Prev],
            NetworkStateConnectionBuilder(
                self._network,
                (self._app, port),
                *self._prev,
            ),
        )

    def value[
        State: ApplianceState, Control: GenericControl, TPort: Port
    ](
        self: "NetworkStateValueBuilder[Net, Appliance[State, Control, TPort, Any, Any], *Prev]",
        state: State,
    ) -> NetworkStateBuilder[Net, *Prev, App, State]:
        return cast(
            NetworkStateBuilder[Net, *Prev, App, State],
            NetworkStateBuilder(self._network, *self._prev, (self._app, state)),
        )


@dataclass(frozen=True, eq=True)
class Connection(Generic[Net, From, FromPort, To, ToPort]):
    from_app: From
    from_port: FromPort
    to_app: To
    to_port: ToPort


class PortToConnector(Generic[Net, From, FromPort, To, ToControl, *Prev]):
    def __init__(self, from_app: From, from_port: FromPort, to_app: To, *prev: *Prev):
        self._from_app = from_app
        self._from_port = from_port
        self._to_app = to_app
        self._prev = prev

    def at[
        State: GenericState, ToPort: Port
    ](
        self: "PortToConnector[Net, From, FromPort, Appliance[State, ToControl, ToPort, Any, Any], ToControl, *Prev]",
        to_port: ToPort,
    ) -> "NetworkConnector[Net, *Prev, Connection[Net, From, FromPort, To, ToPort]]":
        new_connection = cast(
            Connection[Net, From, FromPort, To, ToPort],
            Connection(self._from_app, self._from_port, self._to_app, to_port),
        )
        return cast(
            "NetworkConnector[Net, *Prev, Connection[Net, From, FromPort, To, ToPort]]",
            NetworkConnector(
                *self._prev,
                new_connection,
            ),
        )


class PortFromConnector(Generic[Net, From, FromPort, *Prev]):
    def __init__(self, from_app: From, from_port: FromPort, *prev: *Prev):
        self._from_app = from_app
        self._from_port = from_port
        self._prev = prev

    def to[
        To: AnyAppliance, ToControl: GenericControl
    ](self, to: To) -> PortToConnector[Net, From, FromPort, To, ToControl, *Prev]:
        return PortToConnector(self._from_app, self._from_port, to, *self._prev)


class ApplianceConnector(Generic[Net, From, *Prev]):
    def __init__(self, from_app: From, *prev: *Prev):
        self._from_app = from_app
        self._prev = prev

    def at[
        State: GenericState, Control: GenericControl, TPort: Port
    ](
        self: "ApplianceConnector[Net, Appliance[State, Control, TPort, Any, Any], *Prev]",
        from_port: TPort,
    ) -> PortFromConnector[Net, From, TPort, *Prev]:
        return cast(
            PortFromConnector[Net, From, TPort, *Prev],
            PortFromConnector(self._from_app, from_port, *self._prev),
        )


class NetworkConnector(Generic[Net, *Prev]):
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def connect[
        From: AnyAppliance
    ](self, from_app: From) -> ApplianceConnector[Net, From, *Prev]:
        return ApplianceConnector(from_app, *self._prev)

    def unconnected[
        App: AnyAppliance
    ](self, app: App) -> "NetworkConnector[Net, *Prev, App]":
        return cast(
            "NetworkConnector[Net, *Prev, App]", NetworkConnector(*self._prev, app)
        )

    def combine[
        *Others
    ](
        self, connector: "NetworkConnector[Net, *Others]"
    ) -> "NetworkConnector[Net, *Prev, *Others]":
        return NetworkConnector(*self._prev, *connector._prev)

    def build(self) -> "NetworkConnections[Net]":
        items = cast(
            list[
                Connection[Net, AnyAppliance, Port, AnyAppliance, Port] | AnyAppliance
            ],
            list(self._prev),
        )
        connections = [item for item in items if isinstance(item, Connection)]
        unconnected_appliances = [item for item in items if isinstance(item, Appliance)]
        return NetworkConnections[Net](connections, unconnected_appliances)


class NetworkConnections[Net: "Network[Any]"]:
    def __init__(
        self,
        connections: list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]],
        unconnected: list[AnyAppliance] = [],
    ):
        self._connections = connections
        self._unconnected = unconnected

    def _connection_dict(
        self,
        key: Callable[
            [Connection[Net, AnyAppliance, Port, AnyAppliance, Port]], AnyAppliance
        ],
    ) -> dict[
        SpecificAppliance, list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]]
    ]:
        connections: dict[
            SpecificAppliance,
            list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]],
        ] = {}
        for connection in self._connections:
            connections[connection.to_app] = []
            connections[connection.from_app] = []

        for connection in self._connections:
            connections[key(connection)].append(connection)

        return connections

    def execution_order(
        self,
    ) -> list[SpecificAppliance]:
        incoming_connections = self._connection_dict(
            lambda connection: connection.to_app
        )
        outgoing_connections = self._connection_dict(
            lambda connection: connection.from_app
        )

        return self._unconnected + linearize(
            incoming_connections.keys(),
            lambda appliance: incoming_connections[appliance],
            lambda appliance: outgoing_connections[appliance],
        )

    def port_mapping(
        self,
    ) -> dict[tuple[SpecificAppliance, Port], tuple[AnyAppliance, Port]]:
        return {
            (connection.from_app, connection.from_port): (
                connection.to_app,
                connection.to_port,
            )
            for connection in self._connections
        }

    @property
    def connections(
        self,
    ) -> list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]]:
        return self._connections


class ControlGetter[App: AnyAppliance]:

    def __init__[
        State: GenericState, Control: GenericControl
    ](
        self: "ControlGetter[Appliance[State, Control, Port, Any, Any]]",
        _: App,
        control: Control,
    ):
        self._control = control

    def get[
        State: GenericState, Control: GenericControl
    ](self: "ControlGetter[Appliance[State, Control, Port, Any, Any]]") -> Control:
        return cast(
            Control, self._control
        )  # cast should be safe; Control and App are bound together


class NetworkControl[Net: "Network[Any]"]:

    def __init__(self, controls: dict[AnyAppliance, GenericControl]):
        self._controls = controls

    def appliance[App: AnyAppliance](self, app: App) -> ControlGetter[App]:
        return ControlGetter(app, self._controls.get(app, None))

    def name_to_control_values_mapping(self, network: Net) -> dict[str, GenericControl]:
        return {
            network.find_appliance_name_by_id(item.id): value
            for item, value in self._controls.items()
        }

    def __eq__(self, value: object) -> bool:
        if isinstance(value, NetworkControl):
            return self._controls == value._controls
        return False

    def replace_control(
        self, app: AnyAppliance, attr_to_replace: str, value: float | bool | int
    ) -> "NetworkControl[Net]":
        return NetworkControl({**self._controls, app: replace(self._controls[app], **{attr_to_replace: value})})  # type: ignore


class ControlBuilder[Net: "Network[Any]", *Prev]:
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def control[
        App: AnyAppliance
    ](
        self: "ControlBuilder[Net, *Prev]", app: App
    ) -> "ControlApplianceBuilder[Net, App, *Prev]":
        return ControlApplianceBuilder(app, *self._prev)

    def combine[
        *Others
    ](
        self, other: "ControlBuilder[Net, *Others]"
    ) -> "ControlBuilder[Net, *Prev, *Others]":
        return ControlBuilder(*self._prev, *other._prev)

    def build(self) -> NetworkControl[Net]:
        control = dict(cast(Iterable[tuple[AnyAppliance, GenericControl]], self._prev))
        return NetworkControl(control)


class ControlApplianceBuilder[Net: "Network[Any]", App: AnyAppliance, *Prev]:
    def __init__(
        self,
        app: App,
        *prev: *Prev,
    ):
        self._prev = prev
        self._app = app

    def value[
        State: GenericState, Control: GenericControl, TPort: Port
    ](
        self: "ControlApplianceBuilder[Net, Appliance[State, Control, TPort, Any, Any], *Prev]",
        control: Control,
    ) -> ControlBuilder[Net, tuple[App, Control], *Prev]:
        return cast(
            ControlBuilder[Net, tuple[App, Control], *Prev],
            ControlBuilder((self._app, control), *self._prev),
        )


class PortToFeedback(Generic[Net, From, FromPort, To, ToControl, *Prev]):
    def __init__(self, from_app: From, from_port: FromPort, to_app: To, *prev: *Prev):
        self._from_app = from_app
        self._from_port = from_port
        self._to_app = to_app
        self._prev = prev

    def at[
        State: GenericState, ToPort: Port
    ](
        self: "PortToFeedback[Net, From, FromPort, Appliance[State, ToControl, ToPort, Any, Any], ToControl, *Prev]",
        to_port: ToPort,
    ) -> "NetworkFeedback[Net, *Prev, Connection[Net, From, FromPort, To, ToPort]]":
        to_app = cast(To, self._to_app)
        new_connection = Connection[Net, From, FromPort, To, ToPort](
            self._from_app, self._from_port, to_app, to_port
        )

        return cast(
            NetworkFeedback[
                Net,
                *Prev,
                Connection[Net, From, FromPort, To, ToPort],
            ],
            NetworkFeedback(*self._prev, new_connection),
        )


class PortFromFeedback(Generic[Net, From, FromPort, *Prev]):
    def __init__(self, from_app: From, from_port: FromPort, *prev: *Prev):
        self._from_app = from_app
        self._from_port = from_port
        self._prev = prev

    def to[
        To: AnyAppliance, ToControl: GenericControl
    ](self, to: To) -> PortToFeedback[Net, From, FromPort, To, ToControl, *Prev]:
        return PortToFeedback(self._from_app, self._from_port, to, *self._prev)


class ApplianceFeedback(Generic[Net, From, *Prev]):
    def __init__(self, from_app: From, *prev: *Prev):
        self._from_app = from_app
        self._prev = prev

    def at[
        State: GenericState, Control: GenericControl, TPort: Port
    ](
        self: "ApplianceFeedback[Net, Appliance[State, Control, TPort, Any, Any], *Prev]",
        from_port: TPort,
    ) -> PortFromFeedback[Net, From, TPort, *Prev]:
        return cast(
            PortFromFeedback[Net, From, TPort, *Prev],
            PortFromFeedback(self._from_app, from_port, *self._prev),
        )


class NetworkFeedback(Generic[Net, *Prev]):
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def feedback[
        From: AnyAppliance
    ](self, from_app: From) -> ApplianceFeedback[Net, From, *Prev]:
        return ApplianceFeedback(from_app, *self._prev)

    def combine[
        *Others
    ](
        self, connector: "NetworkFeedback[Net, *Others]"
    ) -> "NetworkFeedback[Net, *Prev, *Others]":
        return NetworkFeedback(*self._prev, *connector._prev)

    def build(self) -> "NetworkFeedbacks[Net]":
        connections = cast(
            list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port],],
            list(self._prev),
        )
        return NetworkFeedbacks[Net](connections)


class NetworkFeedbacks[Net: "Network[Any]"]:
    def __init__(
        self,
        feedbacks: list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]],
    ):
        self._feedbacks = feedbacks

    def enrich_execution_order(
        self, execution_order: list[SpecificAppliance]
    ) -> list[SpecificAppliance]:
        already_present = set(execution_order)
        additions = set(
            connection.to_app
            for connection in self._feedbacks
            if connection.to_app not in already_present
        )
        return [*additions, *execution_order]

    def port_mapping(
        self,
    ) -> dict[tuple[SpecificAppliance, Port], tuple[AnyAppliance, Port]]:
        return NetworkConnections(self._feedbacks).port_mapping()

    @property
    def feedbacks(
        self,
    ) -> list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]]:
        return self._feedbacks


class EnummedDict[T: Enum]:
    def __init__(self, source: dict[T, Any], enum: type[T]) -> None:
        self._source = source
        self._enum = enum

    def __getitem__(self, key: T | str) -> Any:
        if key in self._source:
            return self._source[key]
        else:
            return self._source[self._enum(key)]  # type: ignore

    def __contains__(self, key: T | str) -> bool:
        return key in self._source or self._enum(key) in self._source


class Network[Sensors](ABC):
    def __init__(self):
        connections = self.connections()
        feedback = self.feedback()
        self._execution_order = feedback.enrich_execution_order(
            connections.execution_order()
        )
        self._port_mapping = connections.port_mapping()
        self._feedback_port_mapping: dict[
            tuple[SpecificAppliance, Port], tuple[AnyAppliance, Port]
        ] = feedback.port_mapping()

    def connect[
        From: AnyAppliance
    ](self, from_app: From) -> ApplianceConnector[Self, From]:
        return ApplianceConnector(from_app)

    def _map_feedback(
        self, state: NetworkState[Self]
    ) -> dict[SpecificAppliance, dict[Port, Any]]:
        inputs: dict[SpecificAppliance, dict[Port, Any]] = {}
        for (from_app, from_port), (
            to_app,
            to_port,
        ) in self._feedback_port_mapping.items():
            input: dict[Port, Any] | None = inputs.get(to_app, None)
            if input is None:
                input = {}
                inputs[to_app] = input

            input[to_port] = state.connection(from_app, from_port)

        return inputs

    def find_appliance_name_by_id(self, id: uuid.UUID) -> str:
        for name, appliance in self.__dict__.items():
            if appliance.id == id:
                return name
        raise ValueError(f"Name not found for appliance with id {id}")

    @staticmethod
    def check_temperatures(
        min_max_temperature: tuple[int, int],
        signal: ThermalState,
        appliance_name: str | None,
        port: Port,
    ):
        (
            min_temperature,
            max_temperature,
        ) = min_max_temperature
        if not min_temperature < signal.temperature < max_temperature:
            raise Exception(
                f"{signal} is not within {min_temperature} and {max_temperature}, at appliance {appliance_name} and port {port.value}"
            )

    def simulate(
        self,
        state: NetworkState[Self],
        controls: NetworkControl[Self],
        min_max_temperature: tuple[int, int] | None = None,
    ) -> NetworkState[Self]:
        port_inputs: dict[SpecificAppliance, dict[Port, Any]] = self._map_feedback(
            state
        )
        appliance_states: dict[SpecificAppliance, GenericState] = {}
        signals: dict[tuple[SpecificAppliance, Port], Any] = {}

        # copy feedback into connection states
        for appliance, mapping in port_inputs.items():
            for port, signal in mapping.items():
                signals[(appliance, port)] = signal

        for appliance in self._execution_order:
            appliance_state = state.appliance(appliance).get()
            port_class = port_for_appliance(appliance)
            new_appliance_state, outputs = appliance.simulate(
                EnummedDict(port_inputs.get(appliance, {}), port_class),
                appliance_state,
                controls.appliance(appliance).get(),
                state.time,
            )
            appliance_states[appliance] = new_appliance_state
            for port, signal in outputs.items():
                if not isinstance(port, port_class):
                    port = port_class(port)
                signals[(appliance, port)] = signal
                if min_max_temperature is not None and isinstance(signal, ThermalState):
                    self.check_temperatures(
                        min_max_temperature,
                        signal,
                        self.find_appliance_name_by_id(appliance.id),
                        port,
                    )
                to = self._port_mapping.get((appliance, port), None)
                if to is not None:
                    to_app, to_port = to
                    to_mapping = port_inputs.get(to_app, {})
                    if to_port in to_mapping:
                        raise Exception(
                            f"{to_app} at port {to_port} already has an input"
                        )
                    to_mapping[to_port] = signal
                    port_inputs[to_app] = to_mapping
                    signals[(to_app, to_port)] = signal

        return NetworkState(
            replace(state.time, step=state.time.step + 1),
            appliance_states,
            signals,
        )

    def define_state[
        App: AnyAppliance
    ](self, app: App) -> NetworkStateValueBuilder[Self, App]:
        return NetworkStateValueBuilder(self, app)

    def control[
        App: AnyAppliance
    ](self, app: App) -> ControlApplianceBuilder[Self, App]:
        return ControlApplianceBuilder(app)

    @abstractmethod
    def connections(self) -> NetworkConnections[Self]: ...

    def feedback(self) -> NetworkFeedbacks[Self]:
        return NetworkFeedbacks([])

    def define_feedback[
        App: AnyAppliance
    ](self, app: App) -> ApplianceFeedback[Self, App]:
        return ApplianceFeedback(app)

    @abstractmethod
    def sensors_from_state(self, state: NetworkState[Self]) -> Sensors: ...
