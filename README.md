Mind@Work

## Instruction to open website: In terminal (with Mac)

source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

## Structure explaination
MIND_AT_WORK_WEBSITE/
│
├── .devcontainer/           # ignore - Development container configuration (VS Code, Docker)
├── .streamlit/              # ignore - Streamlit configuration files
├── .venv/                   # ignore - Python virtual environment (local dependencies)
│
├── data/mind@work/          # Raw and processed data files
│   ├── company_lists/       # Company-related datasets
│   └── mental heath dataset/ # Mental health datasets (note: folder name has typo)
│
├── models/catboost/         # Pre-trained CatBoost models and metadata. It runs by notebook
│   ├── feature_order.json   # Order of features using used by the model, should know, which conflict in Isha project
│   ├── model.cbm            # autotrain in notebook, ignore CatBoost model binary
│   ├── model.pkl            # autotrain in notebook, ignore Pickled model object
│   └── threshold.json       # Thresholds for predictions, should know
│
├── notebook/                # Jupyter notebooks for model training, Isha model
│   └── catboost_model.ipynb
│
├── src/                     # Source code for analysis and pipelines
│   ├── __pycache__/         # ignore - Compiled Python bytecode
│   ├── analysis.py          # Function call using in page "More Analysis" Data analysis scripts
│   ├── model_pipeline.py    # Function call using in page "Prediction" End-to-end ML pipeline (data → model → prediction)
│   └── __init__.py          # ignore Marks src as a Python package
│
├── .gitignore               # ignore - Git ignore rules
├── app.py                   # Most important - Main website entry point
├── README.md                # Project documentation (this file)
└── requirements.txt         # ignore - Python dependencies