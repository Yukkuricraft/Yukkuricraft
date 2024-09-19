#!/usr/bin/env bash

ENV_NAME="env2"

MONOYC_BASE="/home/minecraft/YC/YukkuriCraft"

CONTAINER_YC_BASE="/var/lib/yukkuricraft/env/$ENV_NAME/minecraft/yukkuricraft/configs/plugins"

declare -a PLUGIN_CONFIGS_TO_COPY=(
    "ArmorStandEditor"
    "BanManager"
    "ChatFeelings"
    "Chatty"
    "Chunky"
    "ChunkyBorder"
    "CoreProtect"
    "CraftBook"
    "CustomizablePlayerModels"
    "DiscordSRV"
    "dynmap"
    "Essentials"
    "FarmControl"
    "FeelingsRelay"
    "GriefDefender"
    "HeadDatabase"
    "HomeSweetHome"
    "InventoryRollbackPlus"
    "LibsDisguises"
    "LuckPerms"
    "LWC"
    "Multiverse-Core"
    "Multiverse-NetherPortals"
    "Multiverse-Portals"
    "OpenInv"
    "PlugMan"
    "ProtocolLib"
    "spark"
    "SuperVanish"
    "TabList"
    "UnifiedMetrics"
    "ViaBackwards"
    "ViaVersion"
    "Vivecraft-Spigot-Extensions"
    "VoxelSniper"
    "Vulcan"
    "WorldEdit"
)

mkdir -p "$CONTAINER_YC_BASE"
for i in "${PLUGIN_CONFIGS_TO_COPY[@]}"
do
   rsync -aP "$MONOYC_BASE/plugins/$i" "$CONTAINER_YC_BASE/"
   # or do whatever with individual element of the array
done