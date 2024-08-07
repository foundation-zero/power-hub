#!/usr/bin/env python3
"""Create STL files with single parts from drawer_organizer.scad."""
from asyncio import TaskGroup, create_subprocess_exec, create_subprocess_shell
import asyncio
import itertools
from pathlib import Path
from re import sub
import shutil
import subprocess
import os
import json


def find_openscad():
    for path in [
        "openscad-nightly",
        "/Applications/OpenSCAD night.app/Contents/MacOS/OpenSCAD",
    ]:
        if shutil.which(path):
            return path


OUTPUT_TYPE = "stl"  # openscad also supports "amf", "3mf" and others

parts = [
    {"name": "absorption_chiller", "file": "svgs/absorption_chiller.svg", "scale": 11},
    {"name": "chiller", "file": "svgs/chiller.svg", "scale": 11},
    {
        "name": "cooling_demand",
        "file": "svgs/cooling_demand.svg",
        "scale": 11,
        "right_arrow": True,
    },
    {
        "name": "electrical_battery",
        "file": "svgs/electrical_battery.svg",
        "scale": 11,
        "left_arrow": True,
        "right_arrow": True,
    },
    {
        "name": "electrical_demand",
        "file": "svgs/electrical_demand.svg",
        "scale": 11,
        "right_arrow": True,
    },
    {"name": "heat_battery", "file": "svgs/heat_battery.svg", "scale": 11},
    {
        "name": "heat_pipes",
        "file": "svgs/heat_pipes.svg",
        "scale": 11,
        "right_arrow": True,
    },
    {"name": "pv", "file": "svgs/pv.svg", "scale": 9, "$fn": 200, "left_arrow": True},
    {
        "name": "sea_water",
        "file": "svgs/sea_water.svg",
        "scale": 11,
        "left_arrow": True,
    },
    {"name": "water_maker", "file": "svgs/water_maker.svg", "scale": 11},
    {
        "name": "water_tank",
        "file": "svgs/water_tank.svg",
        "scale": 11,
        "right_arrow": True,
    },
    {"name": "water_treatment", "file": "svgs/water_treatment.svg", "scale": 11},
]

variants = [
    {"render_front": True, "render_base": False},
    {"render_front": False, "render_base": True, "$fn": 300},
]

executable = find_openscad()

Path("./output/black").mkdir(parents=True, exist_ok=True)
Path("./output/white").mkdir(parents=True, exist_ok=True)


def color(variant_name):
    match variant_name:
        case "render_front":
            return "black"
        case "render_base":
            return "white"


async def generate(part, variant):
    variant_name = next(k for k, v in variant.items() if v)
    all_params = {**variant, **part}
    text_params = " ".join(f"{k}={v}" for k, v in all_params.items())
    repr_params = [f"{k}={json.dumps(v)}" for k, v in all_params.items()]

    filename = (
        f"output/{color(variant_name)}/{part["name"]}_{variant_name}.{OUTPUT_TYPE}"
    )
    cmd = [
        executable,
        "-o",
        filename,
        "-q",
        "--hardwarnings",
        *itertools.chain(*(("-D", p) for p in repr_params)),
        "model.scad",
    ]
    cmd_str = subprocess.list2cmdline(cmd)
    print(f"running '{cmd_str}'")
    # await create_subprocess_shell(cmd_str)
    subprocess.run(cmd, check=True)


async def generate_all():
    async with TaskGroup() as tg:
        for part in parts:
            for variant in variants:
                tg.create_task(generate(part, variant))


asyncio.run(generate_all())


# parts = {
#     # "connector_all": {},
#     "chiller.": {},
#     "connector_straight": {},
#     "connector_t": {},
#     "connector_t_round": {},
#     "connector_x": {},
#     "connector_x_round": {},
#     "connector_corner_edgy": {},
#     "connector_corner": {},
#     "connector_corner_round": {},
#     "divider": {"divider_length": divider_lengths},
#     "divider_lowered": {"divider_length": divider_lengths[2:]},
#     # can easily be created by mirroring in the slicer
#     # "divider_bend_right": {
#     #    "divider_length": divider_lengths,
#     #    "bend_distance": bend_distances},
#     "divider_bend_left": {
#         "divider_length": divider_lengths,
#         "bend_distance": bend_distances,
#     },
#     # "connector_border_all": {},
#     "connector_zero_border": {"border_overhang": border_overhangs},
#     "connector_straight_border": {"border_overhang": border_overhangs},
#     "connector_t_border": {"border_overhang": border_overhangs},
#     "connector_t_round_border": {"border_overhang": border_overhangs},
#     "connector_corner_edgy_border": {"border_overhang": border_overhangs},
#     "connector_corner_border": {"border_overhang": border_overhangs},
#     "connector_corner_round_border": {"border_overhang": border_overhangs},
#     "divider_border": {
#         "divider_length": divider_lengths,
#         "border_overhang": border_overhangs,
#     },
# }

# designs = [
#     {"height": 25},
#     {"height": 40},
#     {"height": 50},
#     {"height": 60},
# ]

# for design in designs:
#     design_name = " ".join(f"{k}={v}" for k, v in design.items())
#     dir_name = f"{OUTPUT_TYPE}/{design_name}"
#     os.makedirs(dir_name, exist_ok=True)
#     for part, params in parts.items():
#         variants = itertools.product(*params.values())
#         variants = [dict(zip(params.keys(), v)) for v in variants]
#         for variant in variants:
#             all_params = {"part": part, **design, **variant}
#             text_params = " ".join(f"{k}={v}" for k, v in all_params.items())
#             repr_params = [f"{k}={json.dumps(v)}" for k, v in all_params.items()]
#             filename = f"{dir_name}/{text_params[5:]}.{OUTPUT_TYPE}"
#             cmd = [
#                 EXECUTABLE,
#                 "-o",
#                 filename,
#                 "-q",
#                 "--hardwarnings",
#                 *itertools.chain(*(("-D", p) for p in repr_params)),
#                 "drawer_organizer.scad",
#             ]
#             print(f"running '{' '.join(cmd)}'")
#             subprocess.run(cmd, check=True)
