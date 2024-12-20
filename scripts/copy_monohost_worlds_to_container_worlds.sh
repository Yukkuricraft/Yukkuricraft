#!/usr/bin/env bash

ENV_NAME="env1"

MONOYC_BASE="/home/minecraft/YC/YukkuriCraft"

CONTAINER_YC_BASE="/var/lib/yukkuricraft/env/$ENV_NAME/minecraft"

# SURVIVAL_WORLDGROUP="yukkuricraft"
# mkdir -p "$CONTAINER_YC_BASE/$SURVIVAL_WORLDGROUP"

# Creative
CREATIVE_WORLDGROUP="yukkuricraft"
mkdir -p "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP"
rsync -arP "$MONOYC_BASE/CreativeFlat" "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/Statues" "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/buildingContest" "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/Dungeons" "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/SummerHeight" "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/NyadminFlats" "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP/worlds/"

chown -R yukkuricraft:yukkuricraft "$CONTAINER_YC_BASE/$CREATIVE_WORLDGROUP/worlds/"

# Old Gensokyo
OLDGENSOKYO_WORLDGROUP="yukkuricraft"
mkdir -p "$CONTAINER_YC_BASE/$OLDGENSOKYO_WORLDGROUP"
rsync -arP "$MONOYC_BASE/Gensokyo" "$CONTAINER_YC_BASE/$OLDGENSOKYO_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/NewHaku" "$CONTAINER_YC_BASE/$OLDGENSOKYO_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/Heaven" "$CONTAINER_YC_BASE/$OLDGENSOKYO_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/Makai" "$CONTAINER_YC_BASE/$OLDGENSOKYO_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/Senkai" "$CONTAINER_YC_BASE/$OLDGENSOKYO_WORLDGROUP/worlds/"

chown -R yukkuricraft:yukkuricraft "$CONTAINER_YC_BASE/$OLDGENSOKYO_WORLDGROUP/worlds/"

# Neo Gensokyo
NEOGENSOKYO_WORLDGROUP="yukkuricraft"
mkdir -p "$CONTAINER_YC_BASE/$NEOGENSOKYO_WORLDGROUP"
rsync -arP "$MONOYC_BASE/NeoGensokyo" "$CONTAINER_YC_BASE/$NEOGENSOKYO_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/Genso35" "$CONTAINER_YC_BASE/$NEOGENSOKYO_WORLDGROUP/worlds/"

chown -R yukkuricraft:yukkuricraft "$CONTAINER_YC_BASE/$NEOGENSOKYO_WORLDGROUP/worlds/"

# Minigames and Events
MINIGAMES_AND_EVENTS_WORLDGROUP="yukkuricraft"
mkdir -p "$CONTAINER_YC_BASE/$MINIGAMES_AND_EVENTS_WORLDGROUP"
rsync -arP "$MONOYC_BASE/PB_Gensokyo" "$CONTAINER_YC_BASE/$MINIGAMES_AND_EVENTS_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/EventWorld" "$CONTAINER_YC_BASE/$MINIGAMES_AND_EVENTS_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/halloween_2023" "$CONTAINER_YC_BASE/$MINIGAMES_AND_EVENTS_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/YukkuriKart" "$CONTAINER_YC_BASE/$MINIGAMES_AND_EVENTS_WORLDGROUP/worlds/"
rsync -arP "$MONOYC_BASE/Halloween2021" "$CONTAINER_YC_BASE/$MINIGAMES_AND_EVENTS_WORLDGROUP/worlds/"

chown -R yukkuricraft:yukkuricraft "$CONTAINER_YC_BASE/$MINIGAMES_AND_EVENTS_WORLDGROUP/worlds/"

# Retro Gensokyo Worlds
RETRO_SURVIVAL_WORLDS="yukkuricraft"
mkdir -p "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS"
rsync -arP "$MONOYC_BASE/Survival-12.29.13" "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS/worlds/"
rsync -arP "$MONOYC_BASE/NeoSurvival-7.24.2016" "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS/worlds/"
rsync -arP "$MONOYC_BASE/NovaSurvival-7.7.2019" "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS/worlds/"
# NOTE: RENAMING FOLDER NAMES
rsync -arP "$MONOYC_BASE/Survival4/" "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS/worlds/Survival4-11.24.2024"
rsync -arP "$MONOYC_BASE/Survival4_nether/" "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS/worlds/Survival4-11.24.2024_nether"
rsync -arP "$MONOYC_BASE/Survival4_the_end/" "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS/worlds/Survival4-11.24.2024_the_end"

chown -R yukkuricraft:yukkuricraft "$CONTAINER_YC_BASE/$RETRO_SURVIVAL_WORLDS/worlds/"


# Lobby
LOBBY_WORLDGROUP="yukkuricraft"
mkdir -p "$CONTAINER_YC_BASE/$LOBBY_WORLDGROUP"
# rsync -arP "$MONOYC_BASE/GapRealm" "$CONTAINER_YC_BASE/$LOBBY_WORLDGROUP/worlds/" # Disabled due to changes in dev server
rsync -arP "$MONOYC_BASE/BackDoorRealm" "$CONTAINER_YC_BASE/$LOBBY_WORLDGROUP/worlds/"
# rsync -arP "$MONOYC_BASE/Dreamworld" "$CONTAINER_YC_BASE/$LOBBY_WORLDGROUP/worlds/" # Disabled due to changes in dev server

chown -R yukkuricraft:yukkuricraft "$CONTAINER_YC_BASE/$LOBBY_WORLDGROUP/worlds/"