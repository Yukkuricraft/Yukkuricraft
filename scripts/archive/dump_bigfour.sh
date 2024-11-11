# Dumps the four largest tables in our DB by date.
# Was used when cutting over from YC1.0 -> YC2.0

# Remove `echo` before the line if you need to re-execute
# May need to tweak exact dump sql location

echo mysqldump -u root -p minecraft \
    --complete-insert \
    -t co_block \
    -t co_entity \
    -t co_container \
    -t co_item \
    -w "time <= UNIX_TIMESTAMP('2024-11-10')" \
    > scripts/archive/data/dump.bigfour.until-20241110.sql

echo mysqldump -u root -p minecraft \
    --complete-insert \
    -t co_block \
    -t co_entity \
    -t co_container \
    -t co_item \
    -w "time > UNIX_TIMESTAMP('2024-11-10')" \
    > scripts/archive/data/dump.bigfour.after-20241110.sql