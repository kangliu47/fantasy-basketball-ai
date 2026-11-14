"""Closed agent request schemas; analytics remain in application/domain code."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fantasy_ai.application.season.agent_models import ContextRef, Scenario

Code = Annotated[str, Field(min_length=1, max_length=20)]
PlayerID = Annotated[str, Field(min_length=1, max_length=150)]
Signature = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class ClosedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScenarioRequest(ClosedRequest):
    basis: Literal["recent", "projection"] = "recent"
    days: Literal[7, 15, 30] = 7
    strategy: Literal["balanced", "chase", "protect"] = "balanced"
    focus_categories: tuple[Code, ...] = Field(default=(), max_length=50)

    @model_validator(mode="after")
    def unique_focus(self) -> "ScenarioRequest":
        if len(set(self.focus_categories)) != len(self.focus_categories):
            raise ValueError("Choose each category at most once.")
        return self

    def domain(self) -> Scenario:
        return Scenario(self.basis, self.days, self.strategy, self.focus_categories)


class ContextRequest(ClosedRequest):
    league_id: int = Field(gt=0, strict=True)
    season: int = Field(ge=2018, le=9999, strict=True)
    team_id: PlayerID
    signature: Signature

    def domain(self) -> ContextRef:
        return ContextRef(self.league_id, self.season, self.team_id, self.signature)


class OutlookRequest(ClosedRequest):
    league_id: int | None = Field(default=None, gt=0, strict=True)
    season: int | None = Field(default=None, ge=2018, le=9999, strict=True)
    scenario: ScenarioRequest = Field(default_factory=ScenarioRequest)


class RankRequest(ClosedRequest):
    context: ContextRequest
    scenario: ScenarioRequest
    ranking: Literal["overall_fit", "category"] = "overall_fit"
    category_code: Code | None = None
    population: Literal["both", "available", "roster"] = "both"
    query: str | None = Field(default=None, min_length=1, max_length=150)
    positions: tuple[Code, ...] = Field(default=(), max_length=20)
    exclude_status_codes: tuple[Code, ...] = Field(default=(), max_length=20)
    include_unranked: bool = Field(default=False, strict=True)
    limit: int = Field(default=10, ge=1, le=25, strict=True)
    cursor: str | None = Field(default=None, min_length=1, max_length=2048)

    @model_validator(mode="after")
    def category_mode(self) -> "RankRequest":
        if (self.ranking == "category") != (self.category_code is not None):
            raise ValueError("Supply a category code only in category mode.")
        return self
