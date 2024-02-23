# pyright: reportInvalidTypeVarUse=false
# Disable single use of type vars, which is actually required to get the type checker to pass

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Self,
    Set,
    Tuple,
    TypeVar,
    TypeVarTuple,
    cast,
)

from energy_box_control.appliances import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)

# This file uses some fancy Self type hints to ensure the Appliance and ApplianceState are kept in sync
AnyAppliance = Appliance[Any, Any, Any]
SpecificAppliance = Appliance[ApplianceState, ApplianceControl, Port]
App = TypeVar("App", bound=AnyAppliance, covariant=True)
Prev = TypeVarTuple("Prev")
Net = TypeVar("Net", bound="Network[Any]")


class StateGetter[App: AnyAppliance]:
    def __init__[
        State: ApplianceState, Control: ApplianceControl, Port: Port
    ](self: "StateGetter[Appliance[State, Control, Port]]", _: App, state: State):
        self._state = state

    def get[
        State: ApplianceState, Control: ApplianceControl, Port: Port
    ](self: "StateGetter[Appliance[State, Control, Port]]") -> State:
        return cast(
            State, self._state
        )  # cast should be safe; State and App are bound together


class NetworkState(Generic[Net]):
    def __init__(
        self,
        appliance_state: dict[Appliance[Any, Any, Any], ApplianceState],
        connection_state: dict[
            Tuple[Appliance[Any, Any, Any], Port], ConnectionState
        ] = {},
    ):
        self._appliance_state = appliance_state
        self._connection_state = connection_state

    def appliance[App: AnyAppliance](self, appliance: App) -> StateGetter[App]:
        return StateGetter(appliance, self._appliance_state[appliance])

    def connection(self, appliance: AnyAppliance, port: Port) -> ConnectionState:
        return self._connection_state[(appliance, port)]


class NetworkStateBuilder(Generic[Net, *Prev]):
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def define_state[
        App: AnyAppliance
    ](self, app: App) -> "NetworkStateValueBuilder[Net, App, *Prev]":
        return NetworkStateValueBuilder(app, *self._prev)

    def build(self, connections: "NetworkConnections[Net]") -> NetworkState[Net]:
        state = dict(
            cast(
                Iterable[
                    tuple[
                        Appliance[ApplianceState, ApplianceControl, Port],
                        ApplianceState,
                    ]
                ],
                self._prev,
            )
        )

        missing_appliances = set(connections.execution_order()) - set(state.keys())
        if missing_appliances:
            raise Exception(f"missing states for {missing_appliances}")

        return NetworkState(state)


class NetworkStateValueBuilder(Generic[Net, App, *Prev]):
    def __init__(self, app: App, *prev: *Prev):
        self.app = app
        self.prev = prev

    def value[
        State: ApplianceState, Control: ApplianceControl, Port: Port
    ](
        self: "NetworkStateValueBuilder[Net, Appliance[State, Control, Port], *Prev]",
        state: State,
    ) -> NetworkStateBuilder[Net, *Prev, App, State]:
        return cast(
            NetworkStateBuilder[Net, *Prev, App, State],
            NetworkStateBuilder(*self.prev, (self.app, state)),
        )


FromPort = TypeVar("FromPort", bound=Port)
ToPort = TypeVar("ToPort", bound=Port)
From = TypeVar("From", bound=AnyAppliance, covariant=True)
To = TypeVar("To", bound=AnyAppliance, covariant=True)
ToControl = TypeVar("ToControl", bound=ApplianceControl)


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
        State: ApplianceState, ToPort: Port
    ](
        self: "PortToConnector[Net, From, FromPort, Appliance[State, ToControl, ToPort], ToControl, *Prev]",
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
        To: AnyAppliance, ToControl: ApplianceControl
    ](self, to: To) -> PortToConnector[Net, From, FromPort, To, ToControl, *Prev]:
        return PortToConnector(self._from_app, self._from_port, to, *self._prev)


class ApplianceConnector(Generic[Net, From, *Prev]):
    def __init__(self, from_app: From, *prev: *Prev):
        self.from_app = from_app
        self.prev = prev

    def at[
        State: ApplianceState, Control: ApplianceControl, Port: Port
    ](
        self: "ApplianceConnector[Net, Appliance[State, Control, Port], *Prev]",
        from_port: Port,
    ) -> PortFromConnector[Net, From, Port, *Prev]:
        return cast(
            PortFromConnector[Net, From, Port, *Prev],
            PortFromConnector(self.from_app, from_port, *self.prev),
        )


class NetworkConnector(Generic[Net, *Prev]):
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def connect[
        From: AnyAppliance
    ](self, from_app: From) -> ApplianceConnector[Net, From, *Prev]:
        return ApplianceConnector(from_app, *self._prev)

    def build(self) -> "NetworkConnections[Net]":
        connections = cast(
            list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]],
            list(self._prev),
        )
        return NetworkConnections[Net](connections)


class NetworkConnections[Net: "Network[Any]"]:
    def __init__(
        self, connections: list[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]]
    ):
        self._connections = connections

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

        ordered: list[AnyAppliance] = []
        found: Set[Connection[Net, AnyAppliance, Port, AnyAppliance, Port]] = set()
        while incoming_connections:
            newly_found: list[AnyAppliance] = []
            for appliance, connections in incoming_connections.items():
                if not (set(connections) - found):
                    found.update(outgoing_connections[appliance])
                    newly_found.append(appliance)

            if not newly_found:
                raise Exception(
                    "failed to sort connections for iteration, they mustn't be cyclical"
                )

            # can't remove inside iteration
            for item in newly_found:
                incoming_connections.pop(item)

            ordered.extend(newly_found)

        return ordered

    def port_mapping(
        self,
    ) -> dict[Tuple[SpecificAppliance, Port], Tuple[AnyAppliance, Port]]:
        return {
            (connection.from_app, connection.from_port): (
                connection.to_app,
                connection.to_port,
            )
            for connection in self._connections
        }


class ControlGetter[App: AnyAppliance]:
    def __init__[
        Control: ApplianceControl
    ](
        self: "ControlGetter[Appliance[ApplianceState, Control, Port]]",
        _: App,
        control: Control,
    ):
        self._control = control

    def get[
        Control: ApplianceControl
    ](self: "ControlGetter[Appliance[ApplianceState, Control, Port]]") -> Control:
        return cast(
            Control, self._control
        )  # cast should be safe; Control and App are bound together


class NetworkControl[Net: "Network[Any]"]:
    def __init__(self, controls: dict[AnyAppliance, ApplianceControl]):
        self._controls = controls

    def appliance[App: AnyAppliance](self, app: App) -> ControlGetter[App]:
        return ControlGetter(app, self._controls.get(app, ApplianceControl()))


class ControlBuilder[Net: "Network[Any]", *Prev]:
    def __init__(self: "ControlBuilder[Net, *Prev]", *prev: *Prev):
        self._prev = prev

    def control[
        App: AnyAppliance
    ](
        self: "ControlBuilder[Net, *Prev]", app: App
    ) -> "ControlApplianceBuilder[Net, App, *Prev]":
        return ControlApplianceBuilder(app, *self._prev)

    def build(self) -> NetworkControl[Net]:
        control = dict(
            cast(Iterable[tuple[AnyAppliance, ApplianceControl]], self._prev)
        )
        return NetworkControl(control)


class ControlApplianceBuilder[Net: "Network[Any]", App: AnyAppliance, *Prev]:
    def __init__[
        State: ApplianceState, Control: ApplianceControl, Port: Port
    ](
        self: "ControlApplianceBuilder[Net, Appliance[State, Control, Port], *Prev]",
        app: App,
        *prev: *Prev,
    ):
        self._prev = prev
        self._app = app

    def value[
        State: ApplianceState, Control: ApplianceControl, Port: Port
    ](
        self: "ControlApplianceBuilder[Net, Appliance[State, Control, Port], *Prev]",
        control: Control,
    ) -> ControlBuilder[Net, Tuple[App, Control], *Prev]:
        return cast(
            ControlBuilder[Net, Tuple[App, Control], *Prev],
            ControlBuilder((self._app, control), *self._prev),
        )


class Network[Sensors](ABC):
    def __init__(self):
        connections = self.connections()
        self._execution_order = connections.execution_order()
        self._port_mapping = connections.port_mapping()

    def connect[
        From: AnyAppliance
    ](self, from_app: From) -> ApplianceConnector[Self, From]:
        return ApplianceConnector(from_app)

    def simulate(
        self, state: NetworkState[Self], controls: NetworkControl[Self]
    ) -> NetworkState[Self]:
        port_inputs: dict[SpecificAppliance, dict[Port, ConnectionState]] = {}
        appliance_states: dict[SpecificAppliance, ApplianceState] = {}
        connection_states: dict[tuple[SpecificAppliance, Port], ConnectionState] = {}
        for appliance in self._execution_order:
            appliance_state = state.appliance(appliance).get()
            new_appliance_state, outputs = appliance.simulate(
                port_inputs.get(appliance, {}),
                appliance_state,
                controls.appliance(appliance).get(),
            )
            appliance_states[appliance] = new_appliance_state
            for port, connection_state in outputs.items():
                connection_states[(appliance, port)] = connection_state
                to = self._port_mapping.get((appliance, port), None)
                if to is not None:
                    to_app, to_port = to
                    to_mapping = port_inputs.get(to_app, {})
                    if to_port in to_mapping:
                        raise Exception(
                            f"{to_app} at port {to_port} already has an input"
                        )
                    to_mapping[to_port] = connection_state
                    port_inputs[to_app] = to_mapping
                    connection_states[(to_app, to_port)] = connection_state

        return NetworkState(appliance_states, connection_states)

    def define_state[
        App: AnyAppliance
    ](self, app: App) -> NetworkStateValueBuilder[Self, App]:
        return NetworkStateValueBuilder(app)

    def control[
        App: AnyAppliance
    ](self, app: App) -> ControlApplianceBuilder[Self, App]:
        return ControlApplianceBuilder(app)

    @abstractmethod
    def initial_state(self) -> NetworkState[Self]: ...

    @abstractmethod
    def connections(self) -> NetworkConnections[Self]: ...

    @abstractmethod
    def sensors(self, state: NetworkState[Self]) -> Sensors: ...
