#!/bin/bash

echo "Backing up MySQL dump file using restic..."
command bash /restic.sh backup

# Otherwise each dump.sql will persist in the backups dir as long as the container lives
# thus for the Nth backup during a container's lifetime, we'll actually be backing up N dump.sql files as well.
echo "Clearing out backups dir..."
command bash rm -v $BACKUPDB_DUMP_TARGET/*