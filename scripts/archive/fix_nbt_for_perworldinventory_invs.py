#!/usr/bin/env python
"""
This is a horrible disgusting one-off script.

PerWorldInventories, not having updated since 1.15, does not handle the 1.20.x -> 1.21.x update converting NBT tags to Component tags.

This means a ton of items break, especially ender chests and shulker boxes.

This script attempts to do a super hacky fix so players A) don't crash when opening inventories and B) tries to restore parts of ender chests/shulkers
"""
import nbtlib
import json
import tempfile
import gzip
import io
import base64
import pprint

from pathlib import Path
from typing import Dict, List


# file = "creative_creative.working_shulker.json"
file = "creative_creative.json.bak"


def convert_nbt_file_to_b64_str(nbt_file: nbtlib.File, use_gzip=False) -> str:
    out_bytes_io = io.BytesIO()
    nbt_file.write(out_bytes_io, "big")
    out_bytes_io.seek(0)

    if use_gzip:
        # out_bytes_io = gzip.GzipFile(fileobj=out_bytes_io, mode="rw")
        out_bytes = gzip.compress(out_bytes_io.read())
    else:
        out_bytes = out_bytes_io.read()

    pprint.pprint(out_bytes)

    fixed_b64 = base64.b64encode(out_bytes).decode("ascii")
    print(fixed_b64)

    return fixed_b64


def load_nbt_b64_str(b64_str: str) -> nbtlib.File:
    nbt_metadata_binary = base64.decodebytes(b64_str.encode("ascii"))

    print(nbt_metadata_binary)
    print(len(nbt_metadata_binary) * 8)

    bytes_io = io.BytesIO(nbt_metadata_binary)
    print(bytes_io)

    magic_number = bytes_io.read(2)
    bytes_io.seek(0)

    print(magic_number)
    if magic_number == b"\x1f\x8b":
        bytes_io = gzip.GzipFile(fileobj=bytes_io)

    nbt_file = nbtlib.File.from_fileobj(bytes_io, "big")

    return nbt_file


def load_item_frame_b64_metadata_and_add_id(b64_str: str) -> str:
    nbt_file = load_nbt_b64_str(b64_str)

    entity_tag = nbt_file["EntityTag"].unpack(json=True)
    nbt_file["EntityTag"] = nbtlib.parse_nbt(
        json.dumps({**entity_tag, "id": "item_frame"})
    )

    return convert_nbt_file_to_b64_str(nbt_file)


def return_updated_player_skull_texture_b64_value(skull_owner_property_b64_str) -> str:
    skull_owner_property_dict = json.loads(
        base64.b64decode(skull_owner_property_b64_str).decode("utf8")
    )
    texture_url = skull_owner_property_dict["textures"]["SKIN"]["url"]

    new_skull_owner_property_dict = {"textures": {"SKIN": {"url": texture_url}}}

    return base64.b64encode(
        json.dumps(new_skull_owner_property_dict).encode("utf8")
    ).decode("utf8")


def fix_player_skull_item_object(obj: Dict) -> None:
    if "meta" not in obj:
        return

    pprint.pprint(obj)
    try:
        owner_name = obj["item"]["meta"]["skull-owner"]["name"]
    except:
        try:
            owner_name = json.loads(obj["item"]["meta"]["display-name"])["text"]
        except:
            owner_name = "UNKNOWN"

    new_display_name_obj = {
        "text": "",
        "extra": [
            {
                "text": owner_name,
                "obfuscated": False,
                "italic": False,
                "underlined": False,
                "strikethrough": False,
                "color": "blue",
                "bold": False,
            }
        ],
    }

    skull_owner_property_b64_str = obj["item"]["meta"]["skull-owner"]["properties"][0][
        "value"
    ]
    skull_owner_properties = [
        {
            "name": "textures",
            "value": return_updated_player_skull_texture_b64_value(
                skull_owner_property_b64_str
            ),
        }
    ]
    pprint.pprint(skull_owner_properties)

    obj["item"]["meta"]["display-name"] = json.dumps(new_display_name_obj)
    obj["item"]["meta"]["skull-owner"]["name"] = "HeadDatabase"
    obj["item"]["meta"]["skull-owner"]["properties"] = skull_owner_properties


def fix_shulker_box_player_skull_nbt(obj: nbtlib.Compound) -> None:
    pprint.pprint({"msg": "fix_shulker_box_player_skull_nbt()", "data": obj})
    try:
        texture_str = obj["tag"]["SkullOwner"]["Properties"]["textures"][0]["Value"]
        updated_texture_b64_str = return_updated_player_skull_texture_b64_value(
            texture_str
        )
    except:
        updated_texture_b64_str = ""

    count = obj["Count"]
    slot = obj["Slot"]
    block_id = obj["id"]
    try:
        owner_uuid = obj["tag"]["SkullOwner"]["Id"]
    except:
        owner_uuid = obj["tag"]["SkullOwner"]["Name"]

    try:
        skull_name = json.loads(obj["tag"]["display"]["Name"])["text"]
    except:
        try:
            skull_name = obj["tag"]["SkullOwner"]["Name"]
        except:
            skull_name = "UNKNOWN"
    pprint.pprint(f"Using skull owner: '{skull_name}'")

    return nbtlib.Compound(
        {
            "slot": nbtlib.Int(slot),
            "item": nbtlib.Compound(
                {
                    "components": nbtlib.Compound(
                        {
                            "minecraft:custom_name": nbtlib.String(
                                json.dumps(
                                    {
                                        "extra": [
                                            {
                                                "bold": False,
                                                "color": "blue",
                                                "italic": False,
                                                "obfuscated": False,
                                                "strikethrough": False,
                                                "text": skull_name,
                                                "underlined": False,
                                            }
                                        ],
                                        "text": "",
                                    }
                                )
                            ),
                            "minecraft:profile": nbtlib.Compound(
                                {
                                    "id": owner_uuid,
                                    "name": nbtlib.String("Remi_Scarlet"),
                                    "properties": nbtlib.List[nbtlib.Compound](
                                        [
                                            {
                                                "name": nbtlib.String("textures"),
                                                "value": nbtlib.String(
                                                    updated_texture_b64_str
                                                ),
                                            }
                                        ]
                                    ),
                                }
                            ),
                        }
                    ),
                    "count": nbtlib.Int(count),
                    "id": nbtlib.String(block_id),
                }
            ),
        }
    )


def fix_shulker_box_written_book_nbt(obj: nbtlib.Compound):
    pprint.pprint({"msg": "fix_shulker_box_written_book_nbt()", "data": obj})

    count = obj["Count"]
    slot = obj["Slot"]
    block_id = obj["id"]

    author = obj.get("tag", {}).get("author", "")
    title = obj.get("tag", {}).get("title", "")

    pages = []
    for page in obj.get("tag", {}).get("pages", []):
        pages.append({"raw": page})

    return nbtlib.Compound(
        {
            "slot": nbtlib.Int(slot),
            "item": nbtlib.Compound(
                {
                    "components": nbtlib.Compound(
                        {
                            "minecraft:written_book_content": nbtlib.Compound(
                                {
                                    "author": nbtlib.String(author),
                                    "pages": nbtlib.List[nbtlib.Compound](pages),
                                    "title": nbtlib.Compound(
                                        {"raw": nbtlib.String(title)}
                                    ),
                                }
                            )
                        }
                    ),
                    "count": nbtlib.Int(count),
                    "id": nbtlib.String(block_id),
                }
            ),
        }
    )


def fix_shulker_box_metaless_item_nbt(obj: nbtlib.Compound):
    count = obj["Count"]
    slot = obj["Slot"]
    block_id = obj["id"]

    return nbtlib.Compound(
        {
            "slot": nbtlib.Int(slot),
            "item": nbtlib.Compound(
                {
                    "count": nbtlib.Int(count),
                    "id": nbtlib.String(block_id),
                }
            ),
        }
    )


def fix_shulker_box_metadata_nbt(b64_str: str) -> bytes:
    nbt_file = load_nbt_b64_str(b64_str)
    pprint.pprint(nbt_file.keys())

    if "BlockEntityTag" not in nbt_file:
        # This is already in components format
        return b64_str

    shulker_items = nbt_file["BlockEntityTag"]["Items"]
    pprint.pprint(shulker_items.unpack(json=True))

    shulker_items_121 = []
    for item in shulker_items:
        # FIX PLAYER HEAD NBT FORMAT CHANGE
        if item["id"] == "minecraft:player_head":
            shulker_items_121.append(fix_shulker_box_player_skull_nbt(item))
        elif item["id"] == "minecraft:written_book":
            shulker_items_121.append(fix_shulker_box_written_book_nbt(item))
        else:
            # No tag, no nbt metadata, can append wholesale without modification
            try:
                shulker_items_121.append(fix_shulker_box_metaless_item_nbt(item))
            except:
                pass  # Failed to parse somehow - ignore

        pass

    print("!!!")
    nbt_file["block-entity-components"] = nbtlib.Compound(
        {"minecraft:container": nbtlib.List[nbtlib.Compound](shulker_items_121)}
    )
    del nbt_file["BlockEntityTag"]
    pprint.pprint(nbt_file)
    return convert_nbt_file_to_b64_str(nbt_file, use_gzip=True)


def fix_list_of_items(contents: List):
    for item in contents:
        item_data = item["item"]
        item_type = item_data["type"]
        meta = item_data.get("meta", {})

        # FIX BAD ITEM FRAME METADATA
        if item_type == "ITEM_FRAME":
            pprint.pprint(item_data)
            if meta:
                nbt_b64 = meta.get("internal", None)
                if nbt_b64 is None:
                    continue
                meta["internal"] = load_item_frame_b64_metadata_and_add_id(nbt_b64)

        # FIX PLAYER HEAD NBT FORMAT CHANGE
        elif item_type == "PLAYER_HEAD":
            fix_player_skull_item_object(item)

        elif "SHULKER_BOX" in item_type:  # Ie, YELLOW_SHULKER_BOX, RED_SHULKER_BOX, etc
            if meta:
                nbt_b64 = meta.get("internal", None)
                if nbt_b64 is None:
                    continue
                meta["internal"] = fix_shulker_box_metadata_nbt(nbt_b64)


def fix_file(file):
    with open(file, "r") as inv_f:
        inv_d = json.loads(inv_f.read())

        if "inventory" in inv_d:
            if "contents" in inv_d["inventory"]:
                fix_list_of_items(inv_d["inventory"]["contents"])

        if "ender-chest" in inv_d:
            fix_list_of_items(inv_d["ender-chest"])

        pprint.pprint(inv_d)
        # pprint.pprint(inv_d["inventory"]["contents"])

    with open(file, "w") as inv_f:
        inv_f.write(json.dumps(inv_d))


for p in Path("data/").iterdir():
    if p.is_file():
        continue
    # if "e18aa899-1c62-41ad-acc4-2ef50e46114a" not in p.name: # Koko
    #    continue
    # if "0093a48d-b26a-4e01-b090-f44ada97573e" not in p.name: # Purp
    #    continue
    # if "6a0bbafd -cb56-4075-ab5a-fd4ba4f7f8a7" not in p.name: # Mystia
    #    continue

    for file in p.iterdir():
        if "creative_" not in file.name:
            continue
        if file.suffix != ".json":
            continue
        print(file)
        fix_file(file)
