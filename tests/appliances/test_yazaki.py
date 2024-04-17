from datetime import datetime, timedelta
from pytest import approx
import pytest
from energy_box_control.appliances.base import ConnectionState, ProcessTime
from energy_box_control.appliances.source import Source
from energy_box_control.appliances.yazaki import (
    Yazaki,
    YazakiControl,
    YazakiPort,
    YazakiState,
)
from energy_box_control.networks import YazakiNetwork
import logging


def test_yazaki():
    network = YazakiNetwork(
        Source(1.2, 88), Source(2.55, 31), Source(0.77, 17.6), Yazaki(4184, 4184, 4184)
    )

    control = network.control(network.yazaki).value(YazakiControl(on=True)).build()

    state_1 = network.simulate(network.initial_state(), control)

    assert state_1.connection(network.yazaki, YazakiPort.HOT_OUT).temperature == approx(
        83, abs=1
    )
    assert state_1.connection(
        network.yazaki, YazakiPort.COOLING_OUT
    ).temperature == approx(35, abs=1)
    assert state_1.connection(
        network.yazaki, YazakiPort.CHILLED_OUT
    ).temperature == approx(12.5, abs=1)


def test_yazaki_outside_ref_values(caplog):
    yazaki = Yazaki(4184, 4184, 4184)
    initial_yazaki_state = YazakiState()
    yazaki_control = YazakiControl(on=True)
    hot_in = 15
    chilled_in = 0
    cooling_in = 0
    connections = {
        YazakiPort.HOT_IN: ConnectionState(1, hot_in),
        YazakiPort.CHILLED_IN: ConnectionState(1, chilled_in),
        YazakiPort.COOLING_IN: ConnectionState(1, cooling_in),
    }

    _, outputs = yazaki.simulate(
        connections,
        initial_yazaki_state,
        yazaki_control,
        ProcessTime(timedelta(seconds=1), 0, datetime.now()),
    )
    caplog.set_level(logging.WARNING)
    assert (
        f"Hot in temperature of {hot_in} outside of hot reference temperatures. All values are passed through without change"
        in caplog.text
    )
    assert outputs[YazakiPort.HOT_OUT].temperature == hot_in
    assert outputs[YazakiPort.CHILLED_OUT].temperature == chilled_in
    assert outputs[YazakiPort.COOLING_OUT].temperature == cooling_in
