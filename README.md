# CORDIS Explorer

A tool for Queensland Trade & Investment to search and explore EU-funded research organisations from the Horizon Europe program. Use it to find companies, universities, and research institutions that are active in specific fields — and identify potential partnership targets.

---

## What this tool does

CORDIS Explorer lets you search the full database of organisations that have received EU Horizon Europe research funding (2021–2027). You can filter by country, research area, organisation type, and more — then drill into any organisation to see exactly which projects they have worked on, who their research partners are, and how much EU funding they received.

### The five views

**Organisations**
A searchable, filterable table of every organisation in the dataset. Shows country, type, number of projects, and total EU funding received. Click any row to open the detail view for that organisation.

**Bar Chart**
A ranked chart of the top 25 organisations by project count or total funding. Useful for quickly identifying the most active players in a filtered research area. Click any bar to inspect that organisation.

**Map**
A world map showing where organisations are located, with dots sized by project count. Useful for spotting geographic clusters. Click any dot to inspect that organisation.

**Network**
A graph showing which organisations have worked together on the same projects. Organisations are connected by lines if they co-appear in a project. Thicker lines mean more shared projects.

**SQL Query**
A direct query interface for analysts who want to write their own searches. Results can be exported as a CSV.

### Inspecting an organisation

Clicking any organisation (in the table, chart, or map) opens a detail panel at the bottom of the page showing:

- Organisation name, country, total EU funding, and number of projects
- Address and website
- A full list of every Horizon Europe project they have participated in

Click any project in that list to see the project detail:

- Project title, budget, status, and timeframe
- Full project objective
- Every organisation that participated, with their individual funding amounts

Clicking any partner organisation in the project view navigates to that organisation's detail. Use **Back to org** to return, or **Clear** to close the panel entirely.

### Filters

All filters are in the left sidebar and apply across every tab.

| Filter | What it does |
|--------|-------------|
| Keyword search | Searches project objectives, keywords, and scientific vocabulary |
| Organisation type | Filter by private company, university, research institute, or public body |
| Country | Limit to specific countries (you can select multiple) |
| SME only | Show only small and medium enterprises |
| Project status | Filter by active, closed, or terminated projects |
| Framework programme | Filter by funding programme (e.g. HORIZON) |
| Policy priority tags | Filter by EU policy areas: AI, climate, biodiversity, clean air, digital agenda |
| Max results | Limit results to the top N organisations by project count (default 500) |

---

## Installation

Follow these steps exactly. This should take about 10–15 minutes on the first setup.

### Step 1 — Install Python

Python is the programming language this tool runs on. You only need to install it once.

1. Go to **https://www.python.org/downloads/**
2. Click the yellow **Download Python** button (the version number does not matter as long as it is 3.10 or higher)
3. Run the installer
4. **Important:** On the first screen of the installer, tick the box that says **"Add Python to PATH"** before clicking Install

To check Python installed correctly:
- On **Windows:** Press the Windows key, type `cmd`, and open **Command Prompt**. Type `python --version` and press Enter. You should see a version number.
- On **Mac:** Open **Terminal** (search for it in Spotlight). Type `python3 --version` and press Enter.

### Step 2 — Download this tool

1. Go to the folder where this tool is saved on your computer
2. If you received it as a ZIP file, right-click the ZIP and choose **Extract All**, then pick a location you will remember (e.g. your Desktop or Documents folder)

### Step 3 — Open a terminal in the tool's folder

**On Windows:**
1. Open the folder where the tool is saved (you should see files like `app.py`, `run.bat`, `requirements.txt`)
2. Click in the address bar at the top of the File Explorer window (it shows the folder path)
3. Type `cmd` and press Enter — a black Command Prompt window will open, already in the right folder

**On Mac:**
1. Open the folder in Finder
2. Right-click on the folder and choose **New Terminal at Folder** (if you do not see this option, go to System Settings > Privacy & Security > Extensions > Finder Extensions and enable Terminal)

### Step 4 — Install the required packages

In the terminal window you just opened, type the following and press Enter:

```
pip install -r requirements.txt
```

Wait for it to finish. You will see a lot of text scroll past — this is normal. It may take 2–5 minutes depending on your internet connection. You only need to do this once.

If you see an error saying `pip` is not recognised, try:
```
python -m pip install -r requirements.txt
```

### Step 5 — Download the CORDIS data

The tool needs the raw data files from the EU.

1. Go to: **https://cordis.europa.eu/data/cordis-HORIZONprojects-csv.zip**
2. This will download a ZIP file (approximately 100MB)
3. Extract the ZIP — you will get a folder containing several CSV files including `project.csv` and `organization.csv`
4. Keep note of where you saved this folder — you will need the path in the next step

### Step 6 — Run the tool

**On Windows:** Double-click `run.bat` in the tool folder. A terminal window will appear briefly, then your browser will open automatically.

**On Mac/Linux:** In your terminal, type:
```
./run.sh
```

If the browser does not open automatically, go to **http://localhost:8501** in any browser.

### Step 7 — Load the data

When the app opens:
1. In the left sidebar, you will see a **Path to CORDIS data folder** field
2. Paste the path to the folder containing the CSV files you downloaded in Step 5
3. Click **Load Data**

The app will take 10–30 seconds to load the data the first time. Once it says "Data loaded" in the sidebar, you are ready to use the tool.

---

## Each time you use the tool

You do not need to repeat the installation steps. Just:

1. Double-click `run.bat` (Windows) or run `./run.sh` (Mac)
2. The app opens in your browser at **http://localhost:8501**
3. The data path will be remembered from last time — click **Load Data** to load it

To close the tool, close the browser tab and then close the black terminal window that appeared when you launched it.

---

## Natural language queries (Claude Code users)

If you use Claude Code, this project includes a `/cordis` skill. Type `/cordis` and then describe what you want in plain English — Claude will write the SQL for you to paste into the SQL Query tab.

Examples:
- "Show me German biotech companies with active HORIZON projects"
- "Which Australian universities are coordinating climate projects?"
- "Top 10 SMEs by EC funding working on AI"

---

## Organisation type codes

| Code | Meaning |
|------|---------|
| PRC | Private for-profit company |
| HES | Higher education institution (university) |
| REC | Research organisation |
| PUB | Public body (government agency, etc.) |
| OTH | Other |

---

## Data source

CORDIS Horizon Europe dataset. Published by the Publications Office of the European Union, updated monthly. Covers all Horizon Europe projects from 2021 to 2027.
