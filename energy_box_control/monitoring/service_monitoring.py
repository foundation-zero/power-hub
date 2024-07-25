import asyncio
from dataclasses import dataclass
import schedule
import queue
from energy_box_control.config import CONFIG
from energy_box_control.monitoring.service_checks import service_checks
from energy_box_control.monitoring.monitoring import (
    Monitor,
    Notifier,
    PagerDutyNotificationChannel,
)


@dataclass
class HealthCheckResult:

    async def check(self, monitor: Monitor, notifier: Notifier) -> None:

        notifier.send_events(
            await monitor.run_url_health_checks(
                "Python cloud monitoring script",
            )
        )


async def run():
    notifier = Notifier([PagerDutyNotificationChannel(CONFIG.pagerduty_simulation_key)])
    monitor = Monitor(url_health_checks=service_checks)

    run_queue: queue.Queue[None] = queue.Queue()

    def _add_step_to_queue():
        run_queue.put(None)

    step = schedule.every(1).seconds.do(_add_step_to_queue)  # type: ignore
    result = HealthCheckResult()

    while True:
        schedule.run_pending()
        try:
            run_queue.get_nowait()
            await result.check(monitor, notifier)

        except queue.Empty:
            pass


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
