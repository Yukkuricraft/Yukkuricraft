#!/usr/bin/env bash

MONOYC_BASE=/home/minecraft/YC/YukkuriCraft

CONTAINER_YC_BASE=/var/lib/yukkuricraft/prod

# Survival
rsync -arP "$MONOYC_BASE/Survival4" "$CONTAINER_YC_BASE/survival/worlds/"
rsync -arP "$MONOYC_BASE/Survival4_nether" "$CONTAINER_YC_BASE/survival/worlds/"
rsync -arP "$MONOYC_BASE/Survival4_the_end" "$CONTAINER_YC_BASE/survival/worlds/"

# Creative
rsync -arP "$MONOYC_BASE/CreativeFlat" "$CONTAINER_YC_BASE/creative/worlds/"
rsync -arP "$MONOYC_BASE/Statues" "$CONTAINER_YC_BASE/creative/worlds/"
rsync -arP "$MONOYC_BASE/buildingContest" "$CONTAINER_YC_BASE/creative/worlds/"

# Old Gensokyo
rsync -arP "$MONOYC_BASE/Gensokyo" "$CONTAINER_YC_BASE/old-gensokyo/worlds/"
rsync -arP "$MONOYC_BASE/NewHaku" "$CONTAINER_YC_BASE/old-gensokyo/worlds/"
rsync -arP "$MONOYC_BASE/Heaven" "$CONTAINER_YC_BASE/old-gensokyo/worlds/"
rsync -arP "$MONOYC_BASE/Makai" "$CONTAINER_YC_BASE/old-gensokyo/worlds/"
rsync -arP "$MONOYC_BASE/Senkai" "$CONTAINER_YC_BASE/old-gensokyo/worlds/"

# Neo Gensokyo
rsync -arP "$MONOYC_BASE/NeoGensokyo" "$CONTAINER_YC_BASE/neo-gensokyo/worlds/"

# Minigames and Events
rsync -arP "$MONOYC_BASE/PB_Gensokyo" "$CONTAINER_YC_BASE/minigames-and-events/worlds/"

# Lobby
rsync -arP "$MONOYC_BASE/GapRealm" "$CONTAINER_YC_BASE/lobby/worlds/"
rsync -arP "$MONOYC_BASE/BackDoorRealm" "$CONTAINER_YC_BASE/lobby/worlds/"
