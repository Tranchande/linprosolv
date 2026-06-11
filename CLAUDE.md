# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Flask web app that solves Linear Programming (LP) problems and visualizes them.
The UI and all comments/output are in **Vietnamese** — keep new strings in Vietnamese
to stay consistent. All application code lives in the `linprosolv-project/` subdirectory.

## Commands

All commands run from `linprosolv-project/`:

```powershell
cd linprosolv-project
pip install flask plotly numpy matplotlib   # no requirements.txt exists; these are the imports
python app.py                               # serves on http://127.0.0.1:2026 (debug=True)
```

There is no test suite, linter, or build step. Verify changes by running the server
and exercising the solver through the web form at `/`.

## Architecture

Request flow: browser form → `POST /api/solve` → a solver module → JSON
(`{ status, z, solution, plot_html, raw_logs }`) → rendered back into the page.

- **`app.py`** — Flask entry point. Parses/validates the form (number of variables,
  constraints, objective coefficients `c{j}`, matrix `A{i}_{j}`, RHS `b{i}`, constraint
  types `<=`/`>=`/`=`, variable signs `không âm`/`không dương`/`tự do`). Inputs accept
  fractions like `1/2` (parsed via `fractions.Fraction`). It **redirects `sys.stdout` to
  a `StringIO`** so every `print(...)` inside the solvers is captured and returned as
  `raw_logs` — this is the primary mechanism for showing solution steps to the user. Do
  not remove the prints; they ARE the step-by-step output.
- **`solve_two_phase.py`** — `solve_two_phase(...)`: two-phase simplex using **Bland's
  rule** over a "dictionary" representation. All arithmetic uses `Fraction` for exact
  results (no rounding). Returns `path_vertices` (the sequence of visited vertices) used
  to draw the green path arrow on 2-variable plots.
- **`duality.py`** — `solve_duality(...)`: converts primal→dual (`convert_to_dual`), then
  solves the dual. **Important:** this file contains its own *duplicate* copies of
  `standardize_problem`, `build_initial_dictionary`, `print_dictionary`, `pivot`, and
  `simplex_bland` — it does NOT import them from `solve_two_phase.py`. A fix to the
  simplex logic in one file usually needs mirroring in the other.
- **`plot_graph.py`** — `plot_2d_lp(...)`: builds a Plotly figure (feasible region,
  constraint lines, optimum, path) and returns it as embeddable HTML. Only works for
  exactly 2 variables. `duality.py` has its own `plot_dual_lp`; for the duality method
  `app.py` uses the solver-supplied `plot_html`, otherwise it calls `plot_2d_lp`.
- **`templates/index.html`** — single-page UI. Tailwind (CDN), light/dark theme via CSS
  vars, dynamically generated input grid, and JS that submits `FormData` to `/api/solve`
  and renders `plot_html` + `raw_logs`.

## Conventions worth knowing

- Both solvers return a dict shaped like
  `{ 'status', 'z', 'solution', 'path_vertices', ('plot_html') }`. `solution` keys are
  `x1, x2, ...` (and duality also sets `y1, y2, ...`); values are formatted fraction
  strings. `app.py` filters keys by `x`/`y` prefix depending on the chosen method.
- Statuses are Vietnamese strings: `Tối ưu (Nghiệm duy nhất)`, `Tối ưu (Vô số nghiệm)`,
  `Vô nghiệm` (infeasible), `Không giới nội` (unbounded).
- `standardize_problem` renames variables to `x` when all are non-negative, otherwise `y`,
  and splits free variables into a difference of two non-negative vars — this var naming
  (`var_char`) is threaded through printing and plotting.
