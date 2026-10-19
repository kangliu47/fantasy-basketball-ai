"""SciPy/HiGHS adapter; numerical details never enter the domain model."""

from time import monotonic

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp  # type: ignore[import-untyped]
from scipy.sparse import csc_matrix  # type: ignore[import-untyped]

from fantasy_ai.domain.draft.balanced_plan import LinearProblem, SolverAnswer


class ScipyRosterSolver:
    def solve(self, problem: LinearProblem, seconds: float) -> SolverAnswer:
        width = len(problem.columns) + 1
        rows, cols, values = [], [], []
        for r, row in enumerate(problem.rows):
            for c, value in row.items():
                if value:
                    rows.append(r)
                    cols.append(c)
                    values.append(value)
        matrix = csc_matrix((values, (rows, cols)), shape=(len(problem.rows), width))
        lower = np.zeros(width)
        upper = np.ones(width)
        lower[-1], upper[-1] = 1, problem.maximum_price
        objective = np.zeros(width)
        objective[-1] = -1
        started = monotonic()
        result = milp(
            objective,
            integrality=np.ones(width),
            bounds=Bounds(lower, upper),
            constraints=LinearConstraint(matrix, problem.lower, problem.upper),
            options={"time_limit": seconds, "mip_rel_gap": 0, "presolve": True},
        )
        return SolverAnswer(
            {0: "optimal", 1: "unproved", 2: "infeasible"}.get(result.status, "solver_error"),
            tuple(float(x) for x in result.x) if result.x is not None else None,
            round(monotonic() - started, 4),
            float(result.mip_gap) if getattr(result, "mip_gap", None) is not None else None,
        )
