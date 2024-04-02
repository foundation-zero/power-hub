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
    TypeVar,
    TypeVarTuple,
    cast,
)
import uuid

from energy_box_control.appliances import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)

# This file uses some fancy Self type hints to ensure the Appliance and ApplianceState are kept in sync
AnyAppliance = Appliance[Any, Any, Any]
SpecificAppliance = Appliance[ApplianceState, ApplianceControl | None, Port]
GenericControl = ApplianceControl | None
App = TypeVar("App", bound=AnyAppliance, covariant=True)
Prev = TypeVarTuple("Prev")
Net = TypeVar("Net", bound="Network[Any]")


class StateGetter[App: AnyAppliance]:
    def __init__[
        State: ApplianceState, Control: GenericControl, Port: Port
    ](self: "StateGetter[Appliance[State, Control, Port]]", _: App, state: State):
        self._state = state

    def get[
        State: ApplianceState, Control: GenericControl, Port: Port
    ](self: "StateGetter[Appliance[State, Control, Port]]") -> State:
        return cast(
            State, self._state
        )  # cast should be safe; State and App are bound together


class NetworkState(Generic[Net]):
    def __init__(
        self,
        appliance_state: dict[Appliance[Any, Any, Any], ApplianceState],
        connection_state: dict[
            tuple[Appliance[Any, Any, Any], Port], ConnectionState
        ] = {},
    ):
        self._appliance_state = appliance_state
        self._connection_state = connection_state

    def get_appliances_states(self) -> dict[Appliance[Any, Any, Any], ApplianceState]:
        return self._appliance_state

    def get_connections_states(
        self,
    ) -> dict[tuple[Appliance[Any, Any, Any], Port], ConnectionState]:
        return self._connection_state

    def appliance[App: AnyAppliance](self, appliance: App) -> StateGetter[App]:
        return StateGetter(appliance, self._appliance_state[appliance])

    def connection(self, appliance: AnyAppliance, port: Port) -> ConnectionState:
        return self._connection_state[(appliance, port)]


class NetworkStateBuilder(Generic[Net, *Prev]):
    def __init__(self, network: Net, *prev: *Prev):
        self._network = network
        self._prev = prev

    def define_state[
        App: AnyAppliance
    ](self, app: App) -> "NetworkStateValueBuilder[Net, App, *Prev]":
        return NetworkStateValueBuilder(self._network, app, *self._prev)

    def build(self) -> NetworkState[Net]:
        state = dict(
            cast(
                Iterable[
                    tuple[
                        Appliance[ApplianceState, GenericControl, Port],
                        ApplianceState,
                    ]
                ],
                self._prev,
            )
        )

        missing_appliances = set(self._network.connections().execution_order()) - set(
            state.keys()
        )
        if missing_appliances:
            raise Exception(f"missing states for {missing_appliances}")

        return NetworkState(state, self._network.feedback().initial_states())


class NetworkStateValueBuilder(Generic[Net, App, *Prev]):
    def __init__(self, network: Net, app: App, *prev: *Prev):
        self._network = network
        self._app = app
        self._prev = prev

    def value[
        State: ApplianceState, Control: GenericControl, Port: Port
    ](
        self: "NetworkStateValueBuilder[Net, Appliance[State, Control, Port], *Prev]",
        state: State,
    ) -> NetworkStateBuilder[Net, *Prev, App, State]:
        return cast(
            NetworkStateBuilder[Net, *Prev, App, State],
            NetworkStateBuilder(self._network, *self._prev, (self._app, state)),
        )


FromPort = TypeVar("FromPort", bound=Port)
ToPort = TypeVar("ToPort", bound=Port)
From = TypeVar("From", bound=AnyAppliance, covariant=True)
To = TypeVar("To", bound=AnyAppliance, covariant=True)
ToControl = TypeVar("ToControl", bound=GenericControl)


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
        To: AnyAppliance, ToControl: GenericControl
    ](self, to: To) -> PortToConnector[Net, From, FromPort, To, ToControl, *Prev]:
        return PortToConnector(self._from_app, self._from_port, to, *self._prev)


class ApplianceConnector(Generic[Net, From, *Prev]):
    def __init__(self, from_app: From, *prev: *Prev):
        self._from_app = from_app
        self._prev = prev

    def at[
        State: ApplianceState, Control: GenericControl, Port: Port
    ](
        self: "ApplianceConnector[Net, Appliance[State, Control, Port], *Prev]",
        from_port: Port,
    ) -> PortFromConnector[Net, From, Port, *Prev]:
        return cast(
            PortFromConnector[Net, From, Port, *Prev],
            PortFromConnector(self._from_app, from_port, *self._prev),
        )


class NetworkConnector(Generic[Net, *Prev]):
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def connect[
        From: AnyAppliance
    ](self, from_app: From) -> ApplianceConnector[Net, From, *Prev]:
        return ApplianceConnector(from_app, *self._prev)

    def combine[
        *Others
    ](
        self, connector: "NetworkConnector[Net, *Others]"
    ) -> "NetworkConnector[Net, *Prev, *Others]":
        return NetworkConnector(*self._prev, *connector._prev)

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
    ) -> dict[tuple[SpecificAppliance, Port], tuple[AnyAppliance, Port]]:
        return {
            (connection.from_app, connection.from_port): (
                connection.to_app,
                connection.to_port,
            )
            for connection in self._connections
        }


class ControlGetter[App: AnyAppliance]:

    def __init__[
        Control: GenericControl
    ](
        self: "ControlGetter[Appliance[ApplianceState, Control, Port]]",
        _: App,
        control: Control,
    ):
        self._control = control

    def get[
        Control: GenericControl
    ](self: "ControlGetter[Appliance[ApplianceState, Control, Port]]") -> Control:
        return cast(
            Control, self._control
        )  # cast should be safe; Control and App are bound together


class NetworkControl[Net: "Network[Any]"]:

    def __init__(self, controls: dict[AnyAppliance, GenericControl]):
        self._controls = controls

    def appliance[App: AnyAppliance](self, app: App) -> ControlGetter[App]:
        return ControlGetter(app, self._controls.get(app, None))


class ControlBuilder[Net: "Network[Any]", *Prev]:
    def __init__(self, *prev: *Prev):
        self._prev = prev

    def control[
        App: AnyAppliance
    ](
        self: "ControlBuilder[Net, *Prev]", app: App
    ) -> "ControlApplianceBuilder[Net, App, *Prev]":
        return ControlApplianceBuilder(app, *self._prev)

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
        State: ApplianceState, Control: GenericControl, Port: Port
    ](
        self: "ControlApplianceBuilder[Net, Appliance[State, Control, Port], *Prev]",
        control: Control,
    ) -> ControlBuilder[Net, tuple[App, Control], *Prev]:
        return cast(
            ControlBuilder[Net, tuple[App, Control], *Prev],
            ControlBuilder((self._app, control), *self._prev),
        )


class InitialStateFeedback(Generic[Net, From, FromPort, To, ToPort, *Prev]):
    def __init__(
        self, connection: Connection[Net, From, FromPort, To, ToPort], *prev: *Prev
    ):
        self._connection = connection
        self._prev = prev

    def initial_state(
        self,
        state: ConnectionState,
    ) -> "NetworkFeedback[Net, *Prev, tuple[ConnectionState, Connection[Net, From, FromPort, To, ToPort]]]":
        return cast(
            NetworkFeedback[
                Net,
                *Prev,
                tuple[ConnectionState, Connection[Net, From, FromPort, To, ToPort]],
            ],
            NetworkFeedback(*self._prev, (state, self._connection)),
        )


class PortToFeedback(Generic[Net, From, FromPort, To, ToControl, *Prev]):
    def __init__(self, from_app: From, from_port: FromPort, to_app: To, *prev: *Prev):
        self._from_app = from_app
        self._from_port = from_port
        self._to_app = to_app
        self._prev = prev

    def at[
        State: ApplianceState, ToPort: Port
    ](
        self: "PortToFeedback[Net, From, FromPort, Appliance[State, ToControl, ToPort], ToControl, *Prev]",
        to_port: ToPort,
    ) -> "InitialStateFeedback[Net, From, FromPort, To, ToPort, *Prev]":
        to_app = cast(To, self._to_app)
        new_connection = Connection[Net, From, FromPort, To, ToPort](
            self._from_app, self._from_port, to_app, to_port
        )

        return InitialStateFeedback(
            new_connection,
            *self._prev,
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
        State: ApplianceState, Control: GenericControl, Port: Port
    ](
        self: "ApplianceFeedback[Net, Appliance[State, Control, Port], *Prev]",
        from_port: Port,
    ) -> PortFromFeedback[Net, From, Port, *Prev]:
        return cast(
            PortFromFeedback[Net, From, Port, *Prev],
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
            list[
                tuple[
                    ConnectionState,
                    Connection[Net, AnyAppliance, Port, AnyAppliance, Port],
                ]
            ],
            list(self._prev),
        )
        return NetworkFeedbacks[Net](connections)


class NetworkFeedbacks[Net: "Network[Any]"]:
    def __init__(
        self,
        feedbacks: list[
            tuple[
                ConnectionState, Connection[Net, AnyAppliance, Port, AnyAppliance, Port]
            ]
        ],
    ):
        self._feedbacks = feedbacks

    def initial_states(self) -> dict[tuple[AnyAppliance, Port], ConnectionState]:
        return {
            (connection.from_app, connection.from_port): state
            for state, connection in self._feedbacks
        }

    def enrich_execution_order(
        self, execution_order: list[SpecificAppliance]
    ) -> list[SpecificAppliance]:
        already_present = set(execution_order)
        additions = set(
            connection.to_app
            for _, connection in self._feedbacks
            if connection.to_app not in already_present
        )
        return [*additions, *execution_order]

    def port_mapping(
        self,
    ) -> dict[tuple[SpecificAppliance, Port], tuple[AnyAppliance, Port]]:
        connections = [connection for _, connection in self._feedbacks]
        return NetworkConnections(connections).port_mapping()


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
    ) -> dict[SpecificAppliance, dict[Port, ConnectionState]]:
        inputs: dict[SpecificAppliance, dict[Port, ConnectionState]] = {}
        for (from_app, from_port), (
            to_app,
            to_port,
        ) in self._feedback_port_mapping.items():
            input: dict[Port, ConnectionState] | None = inputs.get(to_app, None)
            if input is None:
                input = {}
                inputs[to_app] = input

            input[to_port] = state.connection(from_app, from_port)

        return inputs

    def find_appliance_name_by_id(self, id: uuid.UUID) -> str | None:
        for name, appliance in self.__dict__.items():
            if appliance.id == id:
                return name

    @staticmethod
    def check_temperatures(
        min_max_temperature: tuple[int, int],
        connection_state: ConnectionState,
        appliance_name: str | None,
        port: Port,
    ):
        (
            min_temperature,
            max_temperature,
        ) = min_max_temperature
        if not min_temperature < connection_state.temperature < max_temperature:
            raise Exception(
                f"{connection_state} is not within {min_temperature} and {max_temperature}, at appliance {appliance_name} and port {port.value}"
            )

    def simulate(
        self,
        state: NetworkState[Self],
        controls: NetworkControl[Self],
        min_max_temperature: tuple[int, int] | None = None,
    ) -> NetworkState[Self]:
        port_inputs: dict[SpecificAppliance, dict[Port, ConnectionState]] = (
            self._map_feedback(state)
        )
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
                if min_max_temperature is not None:
                    self.check_temperatures(
                        min_max_temperature,
                        connection_state,
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
                    to_mapping[to_port] = connection_state
                    port_inputs[to_app] = to_mapping
                    connection_states[(to_app, to_port)] = connection_state
        return NetworkState(appliance_states, connection_states)

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
    def sensors(self, state: NetworkState[Self]) -> Sensors: ...
