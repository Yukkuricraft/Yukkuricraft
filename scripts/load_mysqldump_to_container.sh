TARGET_ENV=env1

# BigFour - All data before 2024/11/10
#SQLDUMP_PATH=scripts/archive/data/dump.bigfour.until-20241110.sql
#PRE_IMPORT_SQL_PATH=scripts/archive/delete_all_records_bigfour.sql

# All Other Tables - All data forever
SQLDUMP_PATH=scripts/archive/data/dump.allothertables.sql
PRE_IMPORT_SQL_PATH=scripts/archive/delete_all_records_allother.sql


# Big Four - All data AFTER 2024/11/10
# TODO: Need to write a preimport script that deletes any records created after 2024/11/10
#       Trying to import the AFTER as-is will likely cause PK conflicts from edits CO tracks
#       after 11/10 but before cutoff.
#SQLDUMP_PATH=scripts/archive/data/dump.bigfour.after-20241110.sql

docker exec \
    -i YC-${TARGET_ENV}-mysql \
    sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < $PRE_IMPORT_SQL_PATH

docker exec \
    -i YC-${TARGET_ENV}-mysql \
    sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < $SQLDUMP_PATH