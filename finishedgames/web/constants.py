
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

FORM_ACTION_DELETE = "DELETE"
