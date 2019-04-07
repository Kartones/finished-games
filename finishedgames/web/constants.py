
SORT_BY_GAME_NAME = "game"
SORT_BY_GAME_NAME_DESC = "-game"
SORT_BY_PLATFORM = "platform"
SORT_BY_PLATFORM_DESC = "-platform"
SORT_BY_YEAR = "year"
SORT_BY_YEAR_DESC = "-year"

SORT_FIELDS_MAPPING = {
    SORT_BY_GAME_NAME: ["game__name"],
    SORT_BY_GAME_NAME_DESC: ["-game__name"],
    SORT_BY_PLATFORM: ["platform__shortname", "game__name"],
    SORT_BY_PLATFORM_DESC: ["-platform__shortname", "game__name"],
    SORT_BY_YEAR: ["year_finished", "game__name"],
    SORT_BY_YEAR_DESC: ["-year_finished", "game__name"],
}

FORM_METHOD_DELETE = "DELETE"
FORM_ACTION_REMOVE_WISHLIST = "rmwl_"
FORM_ACTION_WISHLIST = "wl_"
FORM_ACTION_PLAYING = "cp_"
FORM_ACTION_REMOVE_PLAYING = "rmcp_"
FORM_ACTION_FINISHED = "f_"
FORM_ACTION_REMOVE_FINISHED = "rmf_"

KEY_GAMES = "games"
KEY_GAMES_WISHLISTED = "wishlisted"
KEY_GAMES_CURRENTLY_PLAYING = "currently_playing"
KEY_GAMES_FINISHED = "finished"
KEY_GAMES_NO_LONGER_OWNED = "not_owned"

CHARACTER_FILTER_NON_ALPHANUMERIC = "-"
