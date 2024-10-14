#!/usr/bin/env python

"""
One-off script used to convert MagicalWarps warps to WarpSystem's SimpleWarps
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict
import datetime
import pprint
import json
import yaml  # type: ignore

yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)

##########
# CONFIG #
##########

SRC_DATA_PATH = "MagicalWarps/storage.json"
OUT_SIMPLEWARPS_PATH = "SimpleWarps.Test.yml"


@dataclass
class MagicalWarp:
    """
    A Warp from the MagicalWarps plugin

    TODO: Convert casing to match input exactly
    """

    allowedPermGroups: List[str]
    allowedUsers: List[str]
    displayName: Dict[str, str]
    groups: List[str]
    pitch: float
    world: str
    x: float
    y: float
    yaw: float
    z: float
    lore: Dict[str, str]


@dataclass
class WarpSystemLocation:
    """
    Location object used with the WarpSystem plugin
    """

    X: float
    Pitch: float
    Y: float
    Z: float
    World: str
    Yaw: float


@dataclass
class SimpleWarp:
    """
    A SimpleWarp from the WarpSystem plugin
    """

    LastChange: int
    Permission: str
    Name: str
    Location: WarpSystemLocation
    Created: int
    LastChanger: str

    @staticmethod
    def from_magical_warp(warp: MagicalWarp):
        now = 1726795383020  # datetime.utcNow()
        return SimpleWarp(
            LastChange=now,
            Permission="",
            Name=warp.displayName.get("text", "NAME_NOT_FOUND"),
            Location=WarpSystemLocation(
                X=warp.x,
                Y=warp.y,
                Z=warp.z,
                Yaw=warp.yaw,
                Pitch=warp.pitch,
                World=warp.world,
            ),
            Created=now,
            LastChanger="Remi_Scarlet",
        )


warps_src_data_path = Path(SRC_DATA_PATH)
out_simplewarps_path = Path(OUT_SIMPLEWARPS_PATH)

magical_warps: List[MagicalWarp] = []
simple_warps: List[SimpleWarp] = []

with open(warps_src_data_path, "r") as f:
    storage_dict = json.loads(f.read())
    warps_dict = storage_dict["warp"]

    for warp_name, warp_definition in warps_dict.items():
        if "displayName" not in warp_definition:
            warp_definition["displayName"] = {
                "text": warp_name,
            }
        if "lore" not in warp_definition:
            warp_definition["lore"] = {"text": ""}
        magical_warp = MagicalWarp(**warp_definition)
        magical_warps.append(magical_warp)

        simple_warp = SimpleWarp.from_magical_warp(magical_warp)
        simple_warps.append(simple_warp)

with open(out_simplewarps_path, "w") as f:
    out = yaml.safe_dump(
        {
            "Warps": [asdict(warp) for warp in simple_warps],
        },
        default_flow_style=False,
        sort_keys=False,
    ).encode("utf8")
    print(out)

    f.write(out.decode("utf8"))
