# AMS App – Repository Analysis

## 1) What this application is (as implemented)
- Observed purpose: Desktop utility built with PySide6 that imports CSV data into a local DuckDB database, presents it in a paginated table, supports basic editing with undo/redo, re-formats date/time columns, exports CSV, and plots numeric series over time with filtering options.【F:main.py†L1-L64】【F:modules/core.py†L203-L439】【F:modules/plot_tool.py†L16-L368】
- User-visible workflows:
  - Select UI language on launch via dialog, defaulting to English if dismissed.【F:main.py†L11-L55】
  - Import CSV into a named DuckDB table with configurable delimiter, then browse via paginated table view and edit cells with undo/redo shortcuts.【F:modules/core.py†L214-L376】【F:modules/core.py†L94-L161】
  - Reformat first two columns into a formatted datetime string (dropping the original time column) and reload the table.【F:modules/core.py†L389-L407】【F:modules/core.py†L53-L70】
  - Export the current table to CSV through a file dialog.【F:modules/core.py†L318-L338】
  - Open plotting dialog to visualize selected numeric columns against detected datetime column, adjust time window, toggle toolbars, and apply spike removal or smoothing filters per series.【F:modules/core.py†L378-L386】【F:modules/plot_tool.py†L31-L368】
  - Adjust CSV delimiter through advanced settings dialog.【F:modules/core.py†L285-L292】【F:modules/core.py†L165-L199】
- Features present in code: language localization via JSON bundles, DuckDB-backed paging model, background worker threads with busy-state UI locking, Matplotlib plots with timeline sliders, filter toolbox (median spike removal, SMA/EMA smoothing), export packaging via PyInstaller build scripts, and localization consistency checker script.【F:modules/i18n.py†L5-L49】【F:modules/plot_tool.py†L239-L344】【F:build/build.py†L24-L123】【F:tools/test_locales.py†L1-L44】

## 2) Repository facts
- Primary language(s): Python (PySide6 GUI, data handling, build tooling).【cmd:ls】【F:main.py†L1-L64】【F:build/build.py†L1-L123】
- Frameworks / runtimes: PySide6 for GUI, DuckDB for storage, pandas for data handling, Matplotlib for plotting, PyInstaller for packaging.【F:modules/core.py†L2-L15】【F:modules/plot_tool.py†L8-L22】【F:build/build.spec†L33-L105】
- UI technology (if any): PySide6 widgets (QMainWindow, dialogs, table view, sliders, checkboxes) with Matplotlib QtAgg canvas for charts.【F:modules/core.py†L203-L376】【F:modules/plot_tool.py†L73-L185】
- Build system and tooling: PyInstaller spec and helper scripts (build.py, build.spec, PowerShell wrapper) that package the app with resources and localization files; optional cleaning and one-file mode support.【F:build/build.py†L24-L123】【F:build/build.spec†L11-L117】【F:build/build.ps1†L1-L1】
- Branch layout: Single visible branch `work`; no additional development branches shown.【cmd:git branch -a】
- Top-level directory structure: `main.py`, `modules/` (core, i18n, plotting), `locales/` (en, de, pl, jp JSON), `build/` (spec, scripts, hooks), `resources/` (icon), `tools/` (localization test).【cmd:ls】

## 3) Architecture overview
- Major subsystems/modules:
  - GUI entry and language selection (`main.py`).【F:main.py†L11-L64】
  - Core window, DuckDB manager, paging model, and dialogs (`modules/core.py`).【F:modules/core.py†L23-L439】
  - Plotting dialog with filtering (`modules/plot_tool.py`).【F:modules/plot_tool.py†L16-L368】
  - Localization loader (`modules/i18n.py`).【F:modules/i18n.py†L5-L49】
  - Packaging/build scripts (`build/`), localization validator (`tools/test_locales.py`).【F:build/build.py†L24-L123】【F:tools/test_locales.py†L1-L44】
- Project/solution layout: Flat Python application with modules folder for UI/business logic, locales folder for translations, resources for icons/plugins, build folder for PyInstaller configuration, and tools for auxiliary scripts.【cmd:ls】【F:build/build.spec†L44-L50】
- Key classes/services and responsibilities:
  - `Localization` handles loading translation JSON and key lookup; `get_localization` and `L` manage global active locale.【F:modules/i18n.py†L5-L49】
  - `DuckDBManager` wraps CSV import/export, pagination, and datetime reformat operations on DuckDB tables.【F:modules/core.py†L23-L70】
  - `WorkerThread` executes long-running jobs with progress/error signals for UI responsiveness.【F:modules/core.py†L75-L93】
  - `PagingTableModel` supplies paginated, editable data with undo/redo stacks for the table view.【F:modules/core.py†L97-L161】
  - `AdvancedSettingsDialog` collects delimiter preference.【F:modules/core.py†L165-L199】
  - `MainWindow` orchestrates UI controls, data import/export, pagination, plotting dialog, datetime reformat, busy state, and shortcut bindings.【F:modules/core.py†L203-L439】
  - `PlotDialog` loads full table, infers datetime/numeric columns, renders plots with sliders and filters, and updates charts interactively.【F:modules/plot_tool.py†L16-L368】
- Configuration system(s): Runtime configuration limited to chosen CSV delimiter and localization selection; translations loaded from `locales/*.json`; build configuration via PyInstaller spec and build.py constants (paths, metadata, version detection).【F:modules/core.py†L165-L199】【F:main.py†L46-L63】【F:build/build.py†L24-L53】【F:build/build.spec†L23-L105】
- Logging/diagnostics (if present): Minimal console prints for localization loading/missing keys and build script status messages; GUI uses QMessageBox for user-facing errors/warnings.【F:modules/i18n.py†L15-L33】【F:build/build.py†L55-L121】【F:modules/core.py†L296-L338】

## 4) Data handling and flow
- Input sources and formats: CSV files selected via file dialog; delimiter configurable; assumed header row; DuckDB `read_csv_auto` ingests into table.【F:modules/core.py†L296-L338】【F:modules/core.py†L27-L43】
- Internal data representations: DuckDB tables backed by a persistent connection; pandas DataFrames used for pagination, editing snapshots, datetime reformatting, and plotting subsets.【F:modules/core.py†L47-L161】【F:modules/core.py†L53-L70】【F:modules/plot_tool.py†L31-L70】
- Processing steps visible in code:
  - Import: create/replace table from CSV with optional error ignoring, signal progress.【F:modules/core.py†L27-L43】【F:modules/core.py†L296-L310】
  - Pagination: fetch limited rows per page; update page labels; allow edits and undo/redo via copied DataFrames.【F:modules/core.py†L97-L161】【F:modules/core.py†L348-L376】
  - Datetime reformat: strip prefixes, merge date/time columns, parse/format to `dd/mm/YYYY HH:MM:SS.sss`, drop time column, replace table.【F:modules/core.py†L53-L70】【F:modules/core.py†L389-L407】
  - Plotting: detect datetime column (coercion attempts), numeric series selection, apply windowed median and SMA/EMA filters, slice by time range from sliders, render Matplotlib lines.【F:modules/plot_tool.py†L31-L368】
- Output formats and exporters: CSV export of arbitrary SQL query (full table used) with delimiter and headers; plots rendered in Matplotlib canvas within dialog; build script packages binaries and zipped output directories.【F:modules/core.py†L318-L338】【F:modules/plot_tool.py†L170-L368】【F:build/build.py†L72-L121】

## 5) Visualization / UI (if applicable)
- UI structure and navigation: Main window with toolbar buttons (Import, Clear, Reformat DateTime, Plot, Advanced Settings, Export), table view, pager controls, status bar with progress and status text; modal dialogs for language selection, delimiter settings, plotting tool.【F:main.py†L11-L64】【F:modules/core.py†L214-L284】
- Plotting/visualization libraries: Matplotlib QtAgg backend embedded via FigureCanvas/NavigationToolbar; formatting uses `mdates` for axis ticks.【F:modules/plot_tool.py†L8-L22】【F:modules/plot_tool.py†L170-L368】
- Update and rendering flow: Plot dialog loads full dataset once, sets up time sliders and checkboxes, recalculates filtered DataFrame on slider or filter changes, clears axis and redraws lines, auto-formats x-axis, and suppresses legend visibility.【F:modules/plot_tool.py†L290-L368】

## 6) Extensibility patterns
- Plugin/module mechanisms (if any): No plugin architecture; modular separation via classes in `modules/` and reusable localization helper.【F:modules/i18n.py†L5-L49】【F:modules/core.py†L23-L439】
- How new functionality is typically added: Add UI controls to MainWindow, implement actions using DuckDBManager/pandas, or extend PlotDialog for new visual features; add locale keys to JSON files and validate with `tools/test_locales.py`.【F:modules/core.py†L214-L376】【F:modules/plot_tool.py†L16-L368】【F:tools/test_locales.py†L1-L44】
- Naming and structural conventions: Modules under `modules/` named by responsibility; localization keys use dot-delimited namespaces; build resources referenced via constants in build scripts and spec.【F:modules/i18n.py†L5-L49】【F:build/build.spec†L23-L50】

## 7) Build, run, and development workflow
- Build steps derived from repo: Execute `python build.py` (with optional `--clean`, `--onefile`) to run PyInstaller using build.spec, then copy dist output into timestamped folder and zip it.【F:build/build.py†L24-L123】
- Required tools and versions: Python 3.12 path hard-coded in build script/PowerShell wrapper; PyInstaller expected; dependencies include PySide6, DuckDB, pandas, Matplotlib (implied by imports and hiddenimports).【F:build/build.py†L24-L123】【F:build/build.spec†L33-L69】【F:build/build.ps1†L1-L1】
- Known limitations or TODOs visible in code or issues: No explicit TODOs; build scripts assume Windows-style Python path; plot dialog loads entire table into memory (could be large).【F:build/build.py†L24-L118】【F:modules/plot_tool.py†L31-L70】

## 8) Notable design decisions
- Patterns or architectural choices: Uses worker threads to keep UI responsive during long tasks (import/export/reformat) while disabling controls; paginated model with undo/redo snapshot stacks instead of live DB transactions; localization via global active instance accessed through helper L().【F:modules/core.py†L75-L161】【F:modules/core.py†L422-L432】【F:modules/i18n.py†L35-L49】
- Trade-offs visible from implementation: Plotting uses full-table load rather than streaming/paged approach; undo/redo copies whole DataFrame pages which may be memory-intensive; build configuration hardcodes paths, limiting portability without edits.【F:modules/plot_tool.py†L31-L70】【F:modules/core.py†L144-L161】【F:build/build.py†L24-L118】

## 9) Open questions / ambiguities
- Default branch upstream and intended release process beyond local `work` branch are unclear (only one branch visible locally).【cmd:git branch -a】
- Expected size/shape of CSV data (column semantics beyond datetime/numeric inference) is not documented in codebase.【F:modules/core.py†L27-L70】
- Whether localization JSON keys are fully synchronized across languages is unverified without running `tools/test_locales.py`.【F:tools/test_locales.py†L13-L44】
