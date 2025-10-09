# Mind@Work 2025 - Team Conscious

### **👥 Team Members**

| Name | GitHub Handle | Contribution |
| ----- | ----- | ----- |
| Patricija | @ | Usability Test, Feedback and Fixed Model |
| Isha | @ | Led Feature Engineering and Model Evaluation |
| Le| @ | Built and Optimized Streamlit Dashboard|
| Karin | @ | Explore EDA|
| Harish | @ | Built and Optimized Models and Dashboard |

---


## **📋 Table of Contents**  
1. [**🎯 Project Highlights**](#project-highlights)  
2. [**👩🏽‍💻 Setup & Execution**](#setup-execution)  
3. [**🏗️ Project Overview**](#project-overview)  
4. [**📊 Data Exploration**](#data-exploration)  
5. [**🧠 Model Development**](#model-development)  
6. [**🖼️ Impact Narrative**](#impact-narrative)  
7. [**🚀 Next Steps & Future Improvements**](#next-steps-future-improvements)  
8. [**📄 References & Additional Resources**](#references-additional-resources)  


---

<a id="project-highlights"></a>
## **🎯 Project Highlights**
* 
*
*
*

---

<a id="setup-execution"></a>  
## **👩🏽‍💻 Setup & Execution**
#### 1. Retrieve our Code by Cloning this Repository or Downloading the Notebooks

  > To Clone the Repo Run ``

#### 2. Download Datasets Through Kaggle
   
> Visit [Data Tab]

#### 3. Replace File Paths to Data
```
EDA = ‘<>’
Catboost model = ‘<>’
EAI = ‘<>’
 = ‘<>’

df_categorical = pd.read_excel(categorical_path)
df_functional = pd.read_csv(function_path')
df_quantitative = pd.read_excel(quantitative_path)
df_target = pd.read_excel(target_path)
```
#### 4. Press `Run All` to Run Notebook

#### 5. Retrieve Test Predictions 
> Results stored in `` and ``

---

<a id="project-overview"></a> 
## **🏗️ Project Overview**
The **Mind@Work**   

As **    

#### Objective of the Challenge  
Our project focused on predicting .  

#### Real-World Significance and Potential Impact  
.  



---

<a id="data-exploration"></a>  
## **📊 Data Exploration**
#### Datasets used
Data provided in Kaggle as mentioned in Setup
Data sets included 

#### Exploration and Preprocessing Approaches

First preprocessing step was to find and take care of all null values.





#### Challenges and Assumptions


---

<a id="model-development"></a> 
## **🧠 Model Development**

#### Randon Forest Model

We started with a RF model
Below is the setup for this model:

* Tailored model for both labels
* Performed GridSearch to find optimal LR parameters for each label
* 80/20 train/test split
* Using primarily F1-Score and accuracy evaluation metrics.
* 77-82% accuracy, 80-85% F1
  
#### Neural Network Model




---


## **📈 Results & Key Findings**

|                     |  |  |  |
|---------------------|--------------------------|----------------------|---------------------|
| RF |            |           |             |
|   Catboost  |                |               |              |


---

<a id="impact-narrative"></a>  
## **🖼️ Impact Narrative**

The top ten features of our RF Model for predicting Output 

| Top Feature                | Coefficient |
|----------------------------|-------------|
|         |    |




---

<a id="next-steps-future-improvements"></a>  
## **🚀 Next Steps & Future Improvements**

#### Limitations of Our Model
One key limitation of our   

#### Improvements with More Time and Resources
With additional time and resources, we would focus on:  
* 
*

#### Future Exploration 
In future projects, we would like to explore:  
* 
* 


---

<a id="references-additional-resources"></a>  
## **📄 References & Additional Resources**





## Instruction to open website: In terminal (with Mac)

source .venv/bin/activate
pip install -r requirements.txt
streamlit run About_Project.py

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

