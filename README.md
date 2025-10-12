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
6. [**🚀 Next Steps & Future Improvements**](#next-steps-future-improvements)  

---

<a id="project-highlights"></a>
## **🎯 Project Highlights**
* Predict mental health outcomes of employees using structured datasets.
* Built multiple models (Random Forest, CatBoost, Neural Network).
* Integrated Explainable AI (XAI) to show feature importance.
* Developed an interactive Streamlit dashboard for live predictions and insights.

---

<a id="setup-execution"></a>  
## **👩🏽‍💻 Setup & Execution**
#### 1. Retrieve our Code by Cloning this Repository or Downloading the Notebooks

  > To Clone the Repo Run ``

#### 2. Download Datasets Through Kaggle
   
> Visit [Data Tab]

#### 3. Create and activate a virtual environment (Mac)
* python3 -m venv .venv
* source .venv/bin/activate
* pip install -r requirements.txt
* streamlit run About_Project.py



<a id="project-overview"></a> 
## **🏗️ Project Overview**
Mind@Work predicts employee mental health outcomes by combining workplace, personal, and behavioral data.
It integrates data science, psychology, and explainable AI to identify the most influential factors on well-being.
Key Objectives:
- Predict likelihood of mental health issues.
- Identify actionable workplace factors.
- Build an interactive and explainable dashboard.

---

<a id="data-exploration"></a>  
## **📊 Data Exploration**
#### Datasets used
Kaggle mental health datasets including demographic, work condition, and satisfaction variables.
Data sets included 

#### Exploration and Preprocessing Approaches
Null handling
Categorical encoding
Feature scaling and correlation checks


<a id="model-development"></a> 
## **🧠 Model Development**

#### Random Forest (Baseline)
- Train/test split: 80/20
- Metrics: Accuracy, F1-score
- GridSearchCV for tuning
- Accuracy: ~0.80 | F1: ~0.83
- CatBoost (Final)
- Handles categorical data natively
- SHAP for explainability
- Accuracy: ~0.84 | F1: ~0.86



<a id="impact-narrative"></a>  
## **🖼️ Impact Narrative**

The top ten features of our RF Model for predicting Output 

| Top Feature                | Impact |
|----------------------------|-------------|
|       Weekly Hours  |  High  |
|       Number of virtual meeting  |  High  |
|       Age  |  High  |
|       Stress level  |  Low  |
|       Compant support for mental health  |  High  |
---

<a id="next-steps-future-improvements"></a>  
## **🚀 Next Steps & Future Improvements**

#### Limitations of Our Model
One key limitation of our synthetic dataset and short-time deployment

#### Improvements with More Time and Resources
With additional time and resources, we would focus on:  
* Website imporovement
* More data collection


---







