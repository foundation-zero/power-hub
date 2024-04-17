from dataclasses import replace
from datetime import datetime, timedelta

from freezegun import freeze_time
from energy_box_control.control.timer import Timer
from energy_box_control.time import ProcessTime


def test_initial_run(mocker):
    timer = Timer(timedelta(minutes=1))

    mock = mocker.Mock()
    _ = timer.run(mock, ProcessTime(timedelta(seconds=1), 0, datetime.now()))

    mock.assert_called_once()


def test_timing(mocker):
    timer = Timer(timedelta(minutes=1))
    initial_datetime = datetime.now()

    time = ProcessTime(timedelta(seconds=1), 0, initial_datetime)

    mock = mocker.Mock()
    timer, _ = timer.run(mock, time)
    mock.assert_called_once()

    timer, _ = timer.run(mock, time)
    mock.assert_called_once()

    time = replace(time, step=30)

    timer, _ = timer.run(mock, time)
    mock.assert_called_once()

    time = replace(time, step=60)

    timer, _ = timer.run(mock, time)
    assert mock.call_count == 2

    time = replace(time, step=120)

    timer, _ = timer.run(mock, time)
    assert mock.call_count == 3
