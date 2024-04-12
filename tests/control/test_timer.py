from datetime import datetime, timedelta

from freezegun import freeze_time
from energy_box_control.control.timer import Timer


def test_initial_run(mocker):
    timer = Timer(timedelta(minutes=1))

    mock = mocker.Mock()
    _ = timer.run(mock)

    mock.assert_called_once()


def test_timing(mocker):
    timer = Timer(timedelta(minutes=1))
    initial_datetime = datetime(year=1, month=7, day=12, hour=15, minute=6, second=3)

    with freeze_time(initial_datetime) as frozen_datetime:
        mock = mocker.Mock()
        timer = timer.run(mock)
        mock.assert_called_once()

        timer = timer.run(mock)
        mock.assert_called_once()

        frozen_datetime.tick(timedelta(seconds=30))

        timer = timer.run(mock)
        mock.assert_called_once()

        frozen_datetime.tick(timedelta(seconds=30))

        timer = timer.run(mock)
        assert mock.call_count == 2

        frozen_datetime.tick(timedelta(minutes=1))

        timer = timer.run(mock)
        assert mock.call_count == 3
