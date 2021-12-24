 Multi-Env Plugin Management Thoughts:
- Need to sync three types of info
    - Plugin jars
    - Config files (yaml)
    - Data (db/mysql)

- Strategy:
    - Copy on start (via flag)
    - Don't overwrite anything that already exists in dev plugin folder - ie files specific to dev take precedence
    - Files for dev all copied into env specific volumes/directories
    - Copying for DBs doesn't work as well though
        - Copying all coreprotect records is gonna be super slow. Blacklist certain tables?
        - If ignoring CO and prism tables, we reduce DB size down to <1gb

```
mysql> SELECT
    ->      table_schema as `Database`,
    ->      table_name AS `Table`,
    ->      round(((data_length + index_length) / 1024 / 1024), 2) `Size in MB`
    -> FROM information_schema.TABLES
    -> ORDER BY (data_length + index_length) DESC;
+--------------------+------------------------------------------------------+------------+
| Database           | Table                                                | Size in MB |
+--------------------+------------------------------------------------------+------------+
| minecraft          | co_block                                             |   94098.25 |
| minecraft          | co_entity                                            |   17344.00 |
| minecraft          | co_container                                         |    6659.48 |
| minecraft          | prism_dev_data_extra                                 |    6316.00 |
| minecraft          | prism_dev_data                                       |    5411.00 |
| minecraft          | co_item                                              |     336.50 |
| minecraft          | co_chat                                              |     142.25 |
| minecraft          | co_command                                           |     133.23 |
| minecraft          | co_sign                                              |      80.14 |
| minecraft          | lwc_history                                          |      73.16 |
| minecraft          | co_session                                           |      31.58 |
| minecraft          | bm_player_history                                    |      18.06 |
| minecraft          | lwc_protections                                      |      15.80 |
| minecraft          | co_skull                                             |       3.52 |
| minecraft          | prism_data                                           |       2.25 |
| mysql              | help_topic                                           |       1.59 |
| minecraft          | bm_players                                           |       0.55 |
| minecraft          | co_user                                              |       0.53 |
| minecraft          | co_username_log                                      |       0.50 |
| mysql              | proc                                                 |       0.29 |
| mysql              | help_keyword                                         |       0.20 |
| mysql              | innodb_index_stats                                   |       0.16 |
| minecraft          | bm_player_ban_records                                |       0.14 |
```

Plugin Info:
- Plugins can be categorized by the types of info present.
    - All plugins have jars
    - Most but not every plugin has configs
    - Few but not none of the plugins produce data in a db or disk
- "Plugin Version Control" consists of versioning metadata for each "type" of info
    - Plugins need versioning of file - inspect jar contents and extract plugin ver and append a checksum hash
    - Configs should be somewhat straightforward with diffs. Could we utilize a hacky automated submodule system here?
    - DB is hardest. Playing with replicas?

Management UI/UX:
- Do we want to build a UI for this or be done entirely via CLI?
    - CLI is error prone. Just from early stage thoughts though, complexity for this system may quicly grow beyond what's reasonable to handle manually
    - How much of a crutch would make targets and scripts be to automate the "heavy lifting"? But running all on a single host sounds dangerous
    - If automating, we likely need to rely on more cloud resources or I need to get more servers which partially increase developer friction anyway which is antithetical to our goals.
- One option would be to separate dev deployments into their own servers which allows us to keep YC hardware as the single prod host that contains source of truth for shit?
    - Deployment for dev environments would be automated and live on cloud resources at that point
