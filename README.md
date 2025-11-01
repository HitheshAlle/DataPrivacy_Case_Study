# BCSE318L Case Study: Anonymization and Tokenization of Hospital Data

## 1. Project Overview

This project serves as a practical case study for the BCSE318L Data Privacy course. It demonstrates the application of fundamental privacy-preserving techniques to a synthetic hospital dataset. The primary goal is to transform a raw dataset containing Personally Identifiable Information (PII) into a de-identified version suitable for research sharing, while analyzing the inherent trade-off between data privacy and utility.

The case study includes:
- A synthetic dataset generator.
- Python scripts implementing k-anonymity, l-diversity, and tokenization.
- An experimental plan to measure privacy risk and data utility.
- A comprehensive report detailing the methodology, results, and discussion.
- Presentation slides summarizing the key findings.

## 2. Prerequisites

- Python 3.10 or later
- `pip` for package installation

## 3. Setup Instructions

1.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install Required Libraries:**
    All necessary libraries are listed in `requirements.txt`. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

## 4. How to Run the Case Study

Execute the scripts from the root directory (`/BCSE318L_Case_Study/`) in the following order:

1.  **Generate the Synthetic Dataset:**
    This script creates the raw dataset used in all subsequent steps.
    ```bash
    python scripts/generate_dataset.py
    ```
    - **Input:** None
    - **Output:** `data/original.csv` (500 records)

2.  **Run the Experiments and Analysis:**
    This is the main script that applies the privacy techniques, calculates metrics, and generates the final outputs.
    ```bash
    python scripts/experiments.py
    ```
    - **Input:** `data/original.csv`
    - **Outputs:**
        - `data/anonymized_k3_l2.csv`: The final anonymized dataset.
        - `report/privacy_utility_tradeoff.png`: A plot visualizing the trade-off between privacy (k) and utility (NCP, ML Accuracy).
        - Console output detailing the results of each experimental step (risk analysis, utility metrics, etc.).

## 5. File Structure