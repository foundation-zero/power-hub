from datetime import datetime, timedelta
import os
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import matplotlib.dates as mdates
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import fluxy as fl
from typing import Any


def plot_hourly_avg(data: pd.DataFrame, ylabel: str):
    hourly = data.set_index(data.index.hour)  # type: ignore
    hourly = hourly.stack().to_frame(name=ylabel).reset_index(names=["hour", "group"])  # type: ignore

    fig, ax = plt.subplots(dpi=300)
    ax = sns.lineplot(
        data=hourly,
        x="hour",
        y=ylabel,
        hue="group",
        palette="Paired",
        dashes=False,
        linewidth=2.0,
        ax=ax,
    )
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.title(f"Hourly averages from {data.index[0].date()} to {data.index[-1].date()}")  # type: ignore


def plot_daily_bars(data: pd.DataFrame, ylabel: str):

    daily = data.resample("h").mean().resample("d").sum()
    daily.index = daily.index.date  # type: ignore
    ax = daily.plot(kind="bar")
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.gcf().autofmt_xdate()
    plt.title("Daily totals")


async def submit_query(fl, token: str) -> pd.DataFrame:
    async with InfluxDBClientAsync(
        "https://influxdb.prod.power-hub.foundationzero.org",
        token,
        "power_hub",
        timeout=30000,
    ) as client:

        return await client.query_api().query_data_frame(fl.to_flux())


async def get_data(
    sensors_to_query: list[Any],
    query_range: tuple[datetime, datetime],
    resolution: timedelta,
    windowoperation: fl.WindowOperation,
    token: str,
) -> pd.DataFrame:

    query = fl.pipe(
        fl.from_bucket("power_hub"),
        fl.range(*query_range),
        fl.filter(fl.any(fl.conform, sensors_to_query)),
        fl.aggregate_window(resolution, windowoperation, False),
        fl.keep(["_time", "_value", "_field"]),
        fl.pivot(["_time"], ["_field"], "_value"),
    )

    df = await submit_query(query, token)

    return (
        df.drop(columns=["result", "table"]).set_index("_time", drop=True).sort_index()
    )


kwh_meters_rename_dict = {
    **{
        f"electrical_e{group}_voltage_L1": f"electrical_e{group}_voltage_L1"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_current_L1": f"electrical_e{group}_voltage_L2"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_power_L1": f"electrical_e{group}_voltage_L3"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_voltage_L2": f"electrical_e{group}_current_L1"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_current_L2": f"electrical_e{group}_current_L2"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_power_L2": f"electrical_e{group}_current_L3"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_voltage_L3": f"electrical_e{group}_power_L1"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_current_L3": f"electrical_e{group}_power_L2"
        for group in range(1, 9)
    },
    **{
        f"electrical_e{group}_power_L3": f"electrical_e{group}_power_L3"
        for group in range(1, 9)
    },
    **{
        f"electrical_thermo_cabinet_voltage_L1": f"electrical_thermo_cabinet_voltage_L1"
    },
    **{
        f"electrical_thermo_cabinet_current_L1": f"electrical_thermo_cabinet_voltage_L2"
    },
    **{f"electrical_thermo_cabinet_power_L1": f"electrical_thermo_cabinet_voltage_L3"},
    **{
        f"electrical_thermo_cabinet_voltage_L2": f"electrical_thermo_cabinet_current_L1"
    },
    **{
        f"electrical_thermo_cabinet_current_L2": f"electrical_thermo_cabinet_current_L2"
    },
    **{f"electrical_thermo_cabinet_power_L2": f"electrical_thermo_cabinet_current_L3"},
    **{f"electrical_thermo_cabinet_voltage_L3": f"electrical_thermo_cabinet_power_L1"},
    **{f"electrical_thermo_cabinet_current_L3": f"electrical_thermo_cabinet_power_L2"},
    **{f"electrical_thermo_cabinet_power_L3": f"electrical_thermo_cabinet_power_L3"},
}

from itertools import product

grid_power = [f"electrical_vebus_e{phase}_input_power" for phase in range(1, 4)]
AC_power = [f"electrical_vebus_e{phase}_output_power" for phase in range(1, 4)]
compound_variables = [
    f"electrical_e{container}_{var}_{phase}"
    for container, var, phase in product(
        range(1, 9), ["voltage", "current", "power"], ["L1", "L2", "L3"]
    )
]
hub_variables = [
    f"electrical_thermo_cabinet_{var}_{phase}"
    for var, phase in product(["voltage", "current", "power"], ["L1", "L2", "L3"])
]

electric_variables = [
    "electrical_pv_power",
    *grid_power,
    *AC_power,
    *compound_variables,
    *hub_variables,
    "electrical_battery_system_soc",
]

electrical_groups = {
    "pv_power": ["electrical_pv_power"],
    "grid_power": [
        "electrical_vebus_e1_input_power",
        "electrical_vebus_e2_input_power",
        "electrical_vebus_e3_input_power",
    ],
    "AC_power": [
        "electrical_vebus_e1_output_power",
        "electrical_vebus_e2_output_power",
        "electrical_vebus_e3_output_power",
    ],
}

electrical_consumption_groups = {
    "office": [
        "electrical_e1_power_L1",
        "electrical_e1_power_L2",
        "electrical_e1_power_L3",
    ],
    "workshop": [
        "electrical_e2_power_L1",
        "electrical_e2_power_L2",
        "electrical_e2_power_L3",
    ],
    "simulator": [
        "electrical_e3_power_L1",
        "electrical_e3_power_L2",
        "electrical_e3_power_L3",
    ],
    "kitchen_sanitary_1": [
        "electrical_e4_power_L1",
        "electrical_e4_power_L2",
        "electrical_e4_power_L3",
    ],
    "kitchen_sanitary_2": [
        "electrical_e5_power_L1",
        "electrical_e5_power_L2",
        "electrical_e5_power_L3",
    ],
    "supply_box": [
        "electrical_e6_power_L1",
        "electrical_e6_power_L2",
        "electrical_e6_power_L3",
    ],
    "center_1": [
        "electrical_e7_power_L1",
        "electrical_e7_power_L2",
        "electrical_e7_power_L3",
    ],
    "center_2": [
        "electrical_e8_power_L1",
        "electrical_e8_power_L2",
        "electrical_e8_power_L3",
    ],
    "power_hub": [
        "electrical_thermo_cabinet_power_L1",
        "electrical_thermo_cabinet_power_L2",
        "electrical_thermo_cabinet_power_L3",
    ],
}

functional_consumption_groups = {
    "office": "office",
    "workshop": "workshop",
    "simulator": "simulator",
    "kitchen_sanitary_1": "sanitary",
    "kitchen_sanitary_2": "catering",
    "center_1": "catering",
    "center_2": "events",
}

electrical_groups_dict_inv = {
    i: k for k in electrical_groups for i in electrical_groups[k]
}

electrical_consumption_groups_dict_inv = {
    i: k
    for k in electrical_consumption_groups
    for i in electrical_consumption_groups[k]
}
