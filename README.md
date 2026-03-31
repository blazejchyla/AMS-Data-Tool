### AMS Data Tool v1.0.0
A high-performance desktop utility designed for SMC AMS sensor data visualization and format conversion. This tool streamlines the process of handling large CSV datasets using an embedded SQL engine.

---

🚀 **Key Features**
- **DuckDB Integration:** Utilizes a high-performance analytical database for near-instant loading and paging of massive CSV files without consuming excessive RAM.
- **CMTK Multi-File Conversion:** A dedicated "Dispatcher" mode to unify separate Pressure, Flow, and Temperature CSVs from CMTK systems into a single, standardized D055-compatible format.
- **Interactive Plotting:** Dynamic multi-axis visualization using Matplotlib, allowing for real-time toggling of data series (Pressure, Flow, Temp) and precise data inspection.
- **Automatic Data Formatting:** Automatically detects and reformats PLC-style timestamps (D# and TOD#) into standard human-readable formats for analysis.
- **Professional Installer:** Native Windows installation via Inno Setup, including desktop shortcuts and "Add/Remove Programs" integration.

🛠 **Technical Improvements**
- **Persistent AppData Storage:** The local database and exported files are now stored in %AppData%\SMC\AMSDataTool to avoid Windows "Access Denied" errors in protected directories.
- **Dual-Monitor Support:** Optimized UI logic to ensure the application always centers on the Primary Display regardless of launch mode.
- **Optimized Build Size:** Aggressive module exclusion in the build process, reducing the uncompressed footprint to ~225MB.

📦 **Installation**
- Download AMS_Data_Tool_Setup_v1.0.0.exe below.
- Run the installer (you may need to click "More Info" -> "Run Anyway" if prompted by Windows SmartScreen).
- Launch via the Desktop or Start Menu shortcut.

---

Publisher: Błażej Chyła
Support: [SMC Poland](https://www.smc.eu/pl-pl)
