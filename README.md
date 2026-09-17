# Smart Civic Complaint & Issue Management System
### Enterprise Municipal Operations & Citizen Portal with Machine Learning and MongoDB

A production-grade, full-stack municipal operations platform built with **FastAPI**, **MongoDB**, scikit-learn **Multi-Model Ensemble Machine Learning** (91.7% accuracy), and modern frontend technologies (**Tailwind CSS**, **Leaflet.js**, **Chart.js**).

---

## 💻 How to Run in Visual Studio Code (VS Code)

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Click **File -> Open Folder...** (or press `Ctrl+K, Ctrl+O`).
3. Select the project directory:
   ```
   C:\Users\baluv\.gemini\antigravity\scratch\smart_civic_portal
   ```
   *(Or from terminal: `code C:\Users\baluv\.gemini\antigravity\scratch\smart_civic_portal`)*

### Step 2: Ensure Prerequisites are Running
1. **Python 3.10+** (Python 3.14 recommended).
2. **MongoDB**:
   - Ensure MongoDB is running locally on port `27017` (`mongodb://localhost:27017`).
   - If running as a Windows Service, MongoDB starts automatically.
   - To verify in VS Code Terminal:
     ```powershell
     mongod --version
     ```

### Step 3: Install Dependencies
Open the VS Code Integrated Terminal (`Ctrl+\`` or **Terminal -> New Terminal**) and run:
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application
You have two easy ways to run the project in VS Code:

#### Method A: 1-Click VS Code Run & Debug (Recommended)
1. Press `Ctrl+Shift+D` to open the **Run & Debug** side panel.
2. Select **"Run Smart Civic Portal (Web Server)"** from the dropdown at the top.
3. Press **F5** (or click the green Play icon).
4. VS Code starts the FastAPI server with auto-reload.

#### Method B: Integrated Terminal Command
In the VS Code terminal, simply run:
```powershell
python run.py
```

### Step 5: Access the Application
Open your browser and navigate to:
- 🌐 **Web Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 📑 **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 👥 Demo Logins & Role-Based Access Control (RBAC)

The portal comes with pre-configured accounts:

| Persona | Email | Password | Permissions & Views |
|---|---|---|---|
| **Citizen (Public)** | `citizen@example.com` | `citizen123` | Submit complaints, view *only* their own complaints, track approval status. |
| **Municipal Official / Admin** | `admin@citygov.gov` | `admin123` | Unrestricted operations Kanban, Approve/Reject tickets, dispatch, retrain ML models. |

---

## 🧠 Machine Learning Engine

- **Finalized Winner**: **Soft Voting Multi-Model Ensemble** (`LinearSVC` + `LogisticRegression` + `ComplementNB` with Word + Sub-word Character N-Grams).
- **Test Accuracy**: **91.7%** (91.4% 5-fold cross-validation, 91.5% weighted F1-score).
- **1.5 GB+ Streaming Trainer**:
  ```powershell
  python scripts/train_large_dataset.py
  ```
  Streams massive datasets in constant memory (<180 MB RAM) using stateless HashingVectorizer and incremental mini-batch SGD.

---

## 🧪 Running Automated Tests in VS Code

You can run the full 23-test suite in VS Code:

- **Via Terminal**:
  ```powershell
  python -m pytest tests/ -v
  ```
- **Via VS Code Testing Panel**:
  1. Click the **Testing (Beaker)** icon on the left sidebar.
  2. Click **Run All Tests**.
- **Via Pre-Configured Debugger**:
  Select **"Run All Pytest Tests"** in Run & Debug (`Ctrl+Shift+D`) and press `F5`.

---

## 📁 Project Structure

```
smart_civic_portal/
├── .vscode/                     # Pre-configured VS Code debug & testing profiles
│   ├── launch.json              # 1-click F5 launch configurations
│   ├── settings.json            # Pytest test explorer settings
│   └── tasks.json               # Terminal build tasks
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI server entry point
│   │   ├── database.py          # MongoDB client connection
│   │   ├── models.py            # MongoDB complaint document factory
│   │   ├── schemas.py           # Pydantic v2 schemas
│   │   ├── ml_trainer.py        # Ensemble, LinearSVC, Logistic, NB trainers
│   │   ├── ai_service.py        # Live inference & NLP pipeline
│   │   ├── prioritization.py    # Multi-factor mathematical scoring
│   │   └── routes/              # Modular API routers (complaints, auth, analytics)
│   ├── data/                    # Balanced training datasets (NYC 311)
│   └── models/                  # Serialized ML model artifacts (.joblib)
├── frontend/                    # Single-Page Application (HTML5, Tailwind, Leaflet)
├── scripts/                     # Out-of-core 1.5GB streaming dataset trainer
├── tests/                       # 23 automated integration & unit tests
├── requirements.txt             # Python dependencies
└── run.py                       # Single-command application launcher
```
