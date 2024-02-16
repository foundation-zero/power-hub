from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Callable,
    Generic,
    Iterable,
    Self,
    Tuple,
    TypeVar,
    TypeVarTuple,
    cast,
)
from energy_box_control.control import Control

from energy_box_control.simulation import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)

# This file uses some fancy Self type hints to ensure the Appliance and ApplianceState are kept in sync

App = TypeVar("App", bound=Appliance, covariant=True)
Prev = TypeVarTuple("Prev")
Net = TypeVar("Net", bound="Network")


class StateGetter[App: Appliance]:
    def __init__[
        State: ApplianceState, Port: Port
    ](self: "StateGetter[Appliance[State, Port]]", _: App, state: State):
        self._state = state

    def get[
        State: ApplianceState, Port: Port
    ](self: "StateGetter[Appliance[State, Port]]") -> State:
        return cast(
            State, self._state
        )  # cast should be safe; State and App are bound together


class NetworkState(Generic[Net]):
    def __init__(
        self,
        appliance_state: dict[Appliance, ApplianceState],
        connection_state: dict[Tuple[Appliance, Port], ConnectionState] = {},
    ):
        self._appliance_state = appliance_state
        self._connection_state = connection_state

    def appliance[T: Appliance](self, appliance: T) -> StateGetter[T]:
        return StateGetter(appliance, self._appliance_state[appliance])

    def connection(self, appliance: Appliance, port: Port) -> ConnectionState:
        return self._connection_state[(appliance, port)]


class NetworkStateBuilder(Generic[Net, *Prev]):
    def __init__(self, *prev: *Prev):
        self.prev = prev

    def define_state[
        App: Appliance
    ](self, app: App) -> "NetworkStateValueBuilder[Net, App, *Prev]":
        return NetworkStateValueBuilder(app, *self.prev)

    def build(self, connections: "NetworkConnections[Net]") -> NetworkState[Net]:
        state = dict(cast(Iterable[tuple[Appliance, ApplianceState]], self.prev))

        missing_appliances = set(connections.execution_order()) - set(state.keys())
        if missing_appliances:
            raise Exception(f"missing states for {missing_appliances}")

        return NetworkState(state)


class NetworkStateValueBuilder(Generic[Net, App, *Prev]):
    def __init__(self, app: App, *prev: *Prev):
        self.app = app
        self.prev = prev

    def value[
        State: ApplianceState, Port: Port
    ](
        self: "NetworkStateValueBuilder[Net, Appliance[State, Port], *Prev]",
        state: State,
    ) -> NetworkStateBuilder[Net, *Prev, App, State]:
        return cast(
            NetworkStateBuilder[Net, *Prev, App, State],
            NetworkStateBuilder(*self.prev, (self.app, state)),
        )


FromPort = TypeVar("FromPort", bound=Port)
ToPort = TypeVar("ToPort", bound=Port)
From = TypeVar("From", bound=Appliance, covariant=True)
To = TypeVar("To", bound=Appliance, covariant=True)


@dataclass(frozen=True, eq=True)
class Connection(Generic[Net, From, FromPort, To, ToPort]):
    from_app: From
    from_port: FromPort
    to_app: To
    to_port: ToPort


class PortToConnector(Generic[Net, From, FromPort, To, *Prev]):
    def __init__(self, from_app: From, from_port: FromPort, to_app: To, *prev: *Prev):
        self._from_app = from_app
        self._from_port = from_port
        self._to_app = to_app
        self._prev = prev

    def at[
        State: ApplianceState, ToPort: Port
    ](
        self: "PortToConnector[Net, From, FromPort, Appliance[State, ToPort], *Prev]",
        to_port: ToPort,
    ) -> "NetworkConnector[Net, *Prev, Connection[Net, From, FromPort, To, ToPort]]":
        return cast(
            "NetworkConnector[Net, *Prev, Connection[Net, From, FromPort, To, ToPort]]",
            NetworkConnector(
                *self._prev,
                Connection(self._from_app, self._from_port, self._to_app, to_port),
            ),
        )


class PortFromConnector(Generic[Net, From, FromPort, *Prev]):
    def __init__(self, from_app: From, from_port: FromPort, *prev: *Prev):
        self._from_app = from_app
        self._from_port = from_port
        self._prev = prev

    def to[
        To: Appliance
    ](self, to: To) -> PortToConnector[Net, From, FromPort, To, *Prev]:
        return PortToConnector(self._from_app, self._from_port, to, *self._prev)


class ApplianceConnector(Generic[Net, From, *Prev]):
    def __init__(self, from_app: From, *prev: *Prev):
        self.from_app = from_app
        self.prev = prev

    def at[
        State: ApplianceState, Port: Port
    ](
        self: "ApplianceConnector[Net, Appliance[State, Port], *Prev]", from_port: Port
    ) -> PortFromConnector[Net, From, Port, *Prev]:
        return cast(
            PortFromConnector[Net, From, Port, *Prev],
            PortFromConnector(self.from_app, from_port, *self.prev),
        )


class NetworkConnector(Generic[Net, *Prev]):
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def connect[
        From: Appliance
    ](self, from_app: From) -> ApplianceConnector[Net, From, *Prev]:
        return ApplianceConnector(from_app, *self._prev)

    def build(self) -> "NetworkConnections[Net]":
        return NetworkConnections(cast(list[Connection], list(self._prev)))


class NetworkConnections[Net: "Network"]:
    def __init__(
        self, connections: list[Connection[Net, Appliance, Port, Appliance, Port]]
    ):
        self._connections = connections

    def _connection_dict(
        self, key: Callable[[Connection], Appliance]
    ) -> dict[Appliance, list[Connection[Net, Appliance, Port, Appliance, Port]]]:
        connections: dict[
            Appliance, list[Connection[Net, Appliance, Port, Appliance, Port]]
        ] = {}
        for connection in self._connections:
            connections[connection.to_app] = []
            connections[connection.from_app] = []

        for connection in self._connections:
            connections[key(connection)].append(connection)

        return connections

    def execution_order(
        self,
    ) -> list[Appliance]:
        incoming_connections = self._connection_dict(
            lambda connection: connection.to_app
        )
        outgoing_connections = self._connection_dict(
            lambda connection: connection.from_app
        )

        ordered: list[Appliance] = []
        found = set()
        while incoming_connections:
            newly_found = []
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

    def port_mapping(self) -> dict[Tuple[Appliance, Port], Tuple[Appliance, Port]]:
        return {
            (connection.from_app, connection.from_port): (
                connection.to_app,
                connection.to_port,
            )
            for connection in self._connections
        }


class Network[Sensors]:
    def __init__(self):
        connections = self.connections()
        self._execution_order = connections.execution_order()
        self._port_mapping = connections.port_mapping()

    def connect[
        From: Appliance
    ](self, from_app: From) -> ApplianceConnector[Self, From]:
        return ApplianceConnector(from_app)

    def simulate(
        self, state: NetworkState[Self], controls: Control
    ) -> NetworkState[Self]:
        port_inputs: dict[Appliance, dict[Port, ConnectionState]] = {}
        appliance_states: dict[Appliance, ApplianceState] = {}
        connection_states: dict[tuple[Appliance, Port], ConnectionState] = {}
        for appliance in self._execution_order:
            appliance_state = state.appliance(appliance).get()
            new_appliance_state, outputs = appliance.simulate(
                port_inputs.get(appliance, {}), appliance_state, controls
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
        App: Appliance
    ](self, app: App) -> NetworkStateValueBuilder[Self, App]:
        return NetworkStateValueBuilder(app)

    @abstractmethod
    def initial_state(self) -> NetworkState[Self]: ...

    @abstractmethod
    def connections(self) -> NetworkConnections[Self]: ...

    @abstractmethod
    def sensors(self, state: NetworkState[Self]) -> Sensors: ...
