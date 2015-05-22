# -*- coding: utf-8 -*-

"""Configuration layout for default base config"""

#TODO: write tooltips and descriptions
#TODO: use apis config related classes

def make_config(config):
    # Check if gettext is installed
    # _ = lambda x: x

    config.addConfigSection("download",
                            _("Download"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("max_downloads", "int"                            , _("Max parallel downloads")                 , 5     ),
                                ("max_speed"    , "int"                            , _("Max download speed in KB/s")             , -1    ),
                                ("limit_speed"  , "bool"                           , _("Limit download speed")                   , False ),
                                ("chunks"       , "int"                            , _("Max connections for one download")       , -1    ),
                                ("skip_existing", "bool"                           , _("Skip already existing files")            , False ),
                                ("interface"    , "str"                            , _("Download interface to bind (ip or Name)"), ""    ),
                                ("jsengine"     , "auto;common;pyv8;node;rhino;jsc", _("JS Engine")                              , "auto"),
                                ("ipv6"         , "bool"                           , _("Allow IPv6")                             , True  ),
                            ])

    config.addConfigSection("downloadTime",
                            _("Download Time"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("start", "time", _("Start"), "0:00"),
                                ("end"  , "time", _("End")  , "0:00"),
                            ])

    config.addConfigSection("general",
                            _("General"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("language"          , "en;de;fr;it;es;nl;sv;ru;pl;cs;sr;pt_BR", _("Language")                      , "en"       ),
                                ("download_folder"   , "folder"                                , _("Download Folder")               , "Downloads"),
                                ("folder_per_package", "bool"                                  , _("Create folder for each package"), True       ),
                                ("min_free_space"    , "int"                                   , _("Min Free Space in MB")          , 512        ),
                                ("renice"            , "int"                                   , _("CPU Priority")                  , 0          ),
                                ("debug_mode"        , "bool"                                  , _("Debug Mode")                    , False      ),
                            ])

    config.addConfigSection("log",
                            _("Log"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("log_size"     , "int"   , _("Size in KB")     , 100   ),
                                ("log_folder"   , "folder", _("Folder")         , "Logs"),
                                ("file_log"     , "bool"  , _("File Log")       , True  ),
                                ("log_count"    , "int"   , _("Count")          , 5     ),
                                ("log_rotate"   , "bool"  , _("Log Rotate")     , True  ),
                                ("color_console", "bool"  , _("Colored console"), True  ),
                            ])

    config.addConfigSection("permission",
                            _("Permissions"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("group"       , "str" , _("Groupname")                         , "users"),
                                ("change_dl"   , "bool", _("Change Group and User of Downloads"), False  ),
                                ("change_file" , "bool", _("Change file mode of downloads")     , False  ),
                                ("user"        , "str" , _("Username")                          , "user" ),
                                ("file"        , "str" , _("Filemode for Downloads")            , "0644" ),
                                ("change_group", "bool", _("Change group of running process")   , False  ),
                                ("folder"      , "str" , _("Folder Permission mode")            , "0755" ),
                                ("change_user" , "bool", _("Change user of running process")    , False  ),
                            ])

    config.addConfigSection("proxy",
                            _("Proxy"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("activated", "bool"              , _("Activated") , False      ),
                                ("type"     , "http;socks4;socks5", _("Protocol")  , "http"     ),
                                ("ip"       , "ip"                , _("IP address"), "localhost"),
                                ("port"     , "int"               , _("Port")      , 7070       ),
                                ("username" , "str"               , _("Username")  , ""         ),
                                ("password" , "password"          , _("Password")  , ""         ),
                            ])

    config.addConfigSection("reconnect",
                            _("Reconnect"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("activated", "bool", _("Activated"), False           ),
                                ("method"   , "str" , _("Method")   , "./reconnect.sh"),
                                ("start"    , "time", _("Start")    , "0:00"          ),
                                ("end"      , "time", _("End")      , "0:00"          ),
                            ])

    config.addConfigSection("ssl",
                            _("SSL"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("activated", "bool", _("Activated")      , False    ),
                                ("cert"     , "file", _("SSL Certificate"), "ssl.crt"),
                                ("key"      , "file", _("SSL Key")        , "ssl.key"),
                            ])

    config.addConfigSection("webui",
                            _("Web User Interface"),
                            _("Description"),
                            _("Long description"),
                            [
                                ("server"     , "auto;threaded;fastcgi;lightweight", _("Server")                , "threaded"),
                                ("ip"         , "ip"                               , _("IP address")            , "0.0.0.0" ),
                                ("port"       , "int"                              , _("Port")                  , 8001      ),
                                ("ssl"        , "bool"                             , _("Use HTTPS")             , False     ),
                                ("theme"      , "default;dark;flat;next"           , _("Theme")                 , "next"    ),
                                ("prefix"     , "str"                              , _("Path Prefix")           , ""        ),
                                ("nolocalauth", "bool"                             , _("No login on LAN access"), True      ),
                            ])
