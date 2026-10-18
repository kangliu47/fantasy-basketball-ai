"""Display aliases for source NBA team abbreviations; never identity matching."""

NBA_TEAMS = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GS": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NO": "New Orleans Pelicans",
    "NY": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHO": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SA": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards",
    "FA": "Free agent",
}
NBA_TEAMS.update(
    {
        "GSW": NBA_TEAMS["GS"],
        "NOP": NBA_TEAMS["NO"],
        "NYK": NBA_TEAMS["NY"],
        "PHX": NBA_TEAMS["PHO"],
        "SAS": NBA_TEAMS["SA"],
        "BRK": NBA_TEAMS["BKN"],
        "UTH": NBA_TEAMS["UTA"],
        "WSH": NBA_TEAMS["WAS"],
    }
)


def nba_team_name(code: str | None) -> str:
    return NBA_TEAMS.get(code.upper(), code) if code else "NBA team unknown"
