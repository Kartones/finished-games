SORT_BY_GAME_NAME = "game"
SORT_BY_GAME_NAME_DESC = "-game"
SORT_BY_PLATFORM = "platform"
SORT_BY_PLATFORM_DESC = "-platform"
SORT_BY_YEAR = "year"
SORT_BY_YEAR_DESC = "-year"
SORT_BY_FINISHED = "finished"
SORT_BY_FINISHED_DESC = "-finished"
SORT_BY_ABANDONED = "abandoned"
SORT_BY_ABANDONED_DESC = "-abandoned"
SORT_BY_CURRENTLY_PLAYING = "playing"
SORT_BY_CURRENTLY_PLAYING_DESC = "-playing"
SORT_BY_NO_LONGER_OWNED = "notowned"
SORT_BY_NO_LONGER_OWNED_DESC = "-notowned"

SORT_FIELDS_MAPPING = {
    SORT_BY_GAME_NAME: ["game__name"],
    SORT_BY_GAME_NAME_DESC: ["-game__name"],
    SORT_BY_PLATFORM: ["platform__shortname", "game__name"],
    SORT_BY_PLATFORM_DESC: ["-platform__shortname", "game__name"],
    SORT_BY_YEAR: ["year_finished", "game__name"],
    SORT_BY_YEAR_DESC: ["-year_finished", "game__name"],
    SORT_BY_FINISHED: ["-year_finished", "game__name"],
    SORT_BY_FINISHED_DESC: ["year_finished", "game__name"],
    SORT_BY_ABANDONED: ["-abandoned", "game__name"],
    SORT_BY_ABANDONED_DESC: ["abandoned", "game__name"],
    SORT_BY_CURRENTLY_PLAYING: ["-currently_playing", "game__name"],
    SORT_BY_CURRENTLY_PLAYING_DESC: ["currently_playing", "game__name"],
    SORT_BY_NO_LONGER_OWNED: ["-no_longer_owned", "game__name"],
    SORT_BY_NO_LONGER_OWNED_DESC: ["no_longer_owned", "game__name"],
}

EXCLUDE_ABANDONED = "abandoned"

EXCLUDE_FIELDS_MAPPING = {EXCLUDE_ABANDONED: {"abandoned": True}}

# Used at actions template for the ids
FORM_METHOD_DELETE = "DELETE"
FORM_ACTION_WISHLIST = "wl_"
FORM_ACTION_REMOVE_WISHLIST = "rmwl_"
FORM_ACTION_PLAYING = "cp_"
FORM_ACTION_REMOVE_PLAYING = "rmcp_"
FORM_ACTION_FINISHED = "f_"
FORM_ACTION_REMOVE_FINISHED = "rmf_"
FORM_ACTION_NOT_OWNED = "no_"
FORM_ACTION_REMOVE_NOT_OWNED = "rmno_"
FORM_ACTION_ADD_TO_CATALOG = "c_"
FORM_ACTION_REMOVE_FROM_CATALOG = "rmc_"
FORM_ACTION_ABANDONED = "a_"
FORM_ACTION_REMOVE_ABANDONED = "ra_"

# Used at actions template to manage which buttons to show and hide (via javascript) upon clicking on a given one
ACTIONS_BUTTONS_MAPPING = {
    FORM_ACTION_WISHLIST: {"show": [FORM_ACTION_REMOVE_WISHLIST], "hide": []},
    FORM_ACTION_REMOVE_WISHLIST: {"show": [FORM_ACTION_WISHLIST], "hide": []},
    FORM_ACTION_PLAYING: {
        "show": [FORM_ACTION_REMOVE_PLAYING, FORM_ACTION_NOT_OWNED, FORM_ACTION_ABANDONED],
        "hide": [FORM_ACTION_REMOVE_NOT_OWNED, FORM_ACTION_REMOVE_ABANDONED],
    },
    FORM_ACTION_REMOVE_PLAYING: {"show": [FORM_ACTION_PLAYING], "hide": []},
    FORM_ACTION_FINISHED: {
        "show": [FORM_ACTION_REMOVE_FINISHED, FORM_ACTION_ABANDONED],
        "hide": [FORM_ACTION_REMOVE_ABANDONED],
    },
    FORM_ACTION_REMOVE_FINISHED: {"show": [FORM_ACTION_FINISHED], "hide": []},
    FORM_ACTION_NOT_OWNED: {
        "show": [FORM_ACTION_REMOVE_NOT_OWNED, FORM_ACTION_PLAYING, FORM_ACTION_ABANDONED],
        "hide": [FORM_ACTION_REMOVE_PLAYING, FORM_ACTION_REMOVE_ABANDONED],
    },
    FORM_ACTION_REMOVE_NOT_OWNED: {"show": [FORM_ACTION_NOT_OWNED], "hide": []},
    FORM_ACTION_ADD_TO_CATALOG: {
        "show": [
            FORM_ACTION_REMOVE_FROM_CATALOG,
            FORM_ACTION_PLAYING,
            FORM_ACTION_FINISHED,
            FORM_ACTION_NOT_OWNED,
            FORM_ACTION_ABANDONED,
        ],
        "hide": [FORM_ACTION_REMOVE_NOT_OWNED, FORM_ACTION_REMOVE_WISHLIST, FORM_ACTION_WISHLIST],
    },
    FORM_ACTION_REMOVE_FROM_CATALOG: {
        "show": [FORM_ACTION_ADD_TO_CATALOG, FORM_ACTION_WISHLIST],
        "hide": [
            FORM_ACTION_PLAYING,
            FORM_ACTION_REMOVE_PLAYING,
            FORM_ACTION_FINISHED,
            FORM_ACTION_REMOVE_FINISHED,
            FORM_ACTION_NOT_OWNED,
            FORM_ACTION_REMOVE_NOT_OWNED,
            FORM_ACTION_ABANDONED,
            FORM_ACTION_REMOVE_ABANDONED,
        ],
    },
    FORM_ACTION_ABANDONED: {
        "show": [FORM_ACTION_FINISHED, FORM_ACTION_PLAYING, FORM_ACTION_NOT_OWNED, FORM_ACTION_REMOVE_ABANDONED],
        "hide": [FORM_ACTION_REMOVE_FINISHED, FORM_ACTION_REMOVE_PLAYING, FORM_ACTION_REMOVE_NOT_OWNED],
    },
    FORM_ACTION_REMOVE_ABANDONED: {"show": [FORM_ACTION_ABANDONED], "hide": []},
}

KEY_GAMES = "games"
KEY_GAMES_WISHLISTED = "wishlisted"
KEY_GAMES_CURRENTLY_PLAYING = "currently_playing"
KEY_GAMES_FINISHED = "finished"
KEY_GAMES_ABANDONED = "abandoned"
KEY_GAMES_NO_LONGER_OWNED = "not_owned"

CHARACTER_FILTER_NON_ALPHANUMERIC = "-"
