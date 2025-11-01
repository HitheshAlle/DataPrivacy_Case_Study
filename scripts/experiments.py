import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import os
import json
from datetime import datetime
from typing import List

# Import our custom privacy functions
from anonymize import (
    apply_k_anonymity,
    check_l_diversity,
    tokenize_ids,
    simulate_linkage_attack,
    compute_ncp
)

# --- Configuration ---
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

INPUT_FILE = 'data/original.csv'
ANONYMIZED_OUTPUT_FILE = 'data/anonymized_k3_l2.csv'
PLOT_OUTPUT_FILE = 'report/privacy_utility_tradeoff.png'
METADATA_OUTPUT_FILE = 'metadata.json'

QUASI_IDENTIFIERS = ['Age', 'Gender', 'ZIP_Code']
SENSITIVE_ATTRIBUTE = 'Diagnosis'
ID_COLUMN = 'Patient_ID'
PII_TO_DROP = ['Name'] # Explicitly list PII to drop

def run_ml_utility_test(df: pd.DataFrame, qis: List[str], target: str, is_anonymized: bool) -> float:
    """
    Trains a Logistic Regression model and returns its accuracy.
    
    Args:
        df: The DataFrame to use for training.
        qis: List of feature columns (quasi-identifiers).
        target: The target column name.
        is_anonymized: Flag indicating if the data is generalized.
    
    Returns:
        The accuracy score of the model.
    """
    # Fill NA values in the target column to avoid errors during stratification
    df_ml = df.copy()
    if df_ml[target].isna().any():
        df_ml[target] = df_ml[target].fillna('Missing')

    if df_ml[target].nunique() < 2:
        print("Warning: Target variable has less than 2 unique classes. Cannot train model.")
        return 0.0

    X = df_ml[qis]
    y = df_ml[target]

    # The preprocessor needs to handle different data types
    # For original data: Age is numeric, others are categorical.
    # For anonymized data: All QIs are treated as categorical.
    if is_anonymized:
        categorical_features = qis
        numerical_features = []
    else:
        # ** FIX: Ensure ZIP_Code is treated as object for ML **
        categorical_features = [qi for qi in qis if df_ml[qi].dtype == 'object' or qi == 'ZIP_Code']
        numerical_features = [qi for qi in qis if df_ml[qi].dtype != 'object' and qi != 'ZIP_Code']

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('num', 'passthrough', numerical_features)
        ]
    )
    
    # Create the pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                               ('classifier', LogisticRegression(random_state=RANDOM_SEED, max_iter=1000))])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=RANDOM_SEED, stratify=y)
    
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    
    return accuracy_score(y_test, y_pred)

def main():
    """Main function to run all experiments."""
    print("--- BCSE318L Case Study Experiment Runner ---")
    
    # Load original dataset
    try:
        # ** FIX: Ensure ZIP_Code is read as a string **
        original_df = pd.read_csv(INPUT_FILE, dtype={'ZIP_Code': str})
    except FileNotFoundError:
        print(f"Error: '{INPUT_FILE}' not found. Please run 'generate_dataset.py' first.")
        return

    # --- 1. Baseline Risk Assessment ---
    print("\n--- 1. Baseline Risk Assessment (Original Data) ---")
    baseline_risk = simulate_linkage_attack(original_df, QUASI_IDENTIFIERS)
    print(f"Initial uniqueness rate (re-identification risk): {baseline_risk:.2%}")

    # --- 2. k-Anonymity Experiments ---
    print("\n--- 2. k-Anonymity Application and Risk Analysis ---")
    k_values = [2, 3, 5] # Sorted for plot
    anonymized_results = {}
    
    df_k3 = None # To store the k=3 result for l-diversity
    
    for k in k_values:
        print(f"\nApplying k-anonymity for k={k}...")
        anonymized_df = apply_k_anonymity(original_df, QUASI_IDENTIFIERS, k)
        risk_post_k = simulate_linkage_attack(anonymized_df, QUASI_IDENTIFIERS)
        print(f"Uniqueness rate for k={k}: {risk_post_k:.2%}")
        anonymized_results[k] = {'df': anonymized_df, 'risk': risk_post_k}
        if k == 3:
            df_k3 = anonymized_df.copy() # Use a copy

    # --- 3. l-Diversity Enforcement ---
    print("\n--- 3. l-Diversity Analysis (on k=3 data) ---")
    l_values = [2, 3] # Sorted for logic
    
    for l_val in l_values:
        is_diverse, failing_groups = check_l_diversity(df_k3, SENSITIVE_ATTRIBUTE, QUASI_IDENTIFIERS, l_val)
        if is_diverse:
            print(f"Dataset satisfies l-diversity for l={l_val}.")
        else:
            print(f"Dataset FAILS l-diversity for l={l_val}.")
            print(f"Number of failing groups: {len(failing_groups)}")
            if failing_groups:
                print(f"Example failing group: {failing_groups[0]}")
    
    # --- 4. Tokenization and Final File Creation ---
    # ** FIX: Apply tokenization and drop PII *before* saving **
    print("\n--- 4. Tokenizing IDs and Dropping PII ---")
    
    # Tokenize the ID column
    final_anonymized_df, token_vault = tokenize_ids(df_k3, ID_COLUMN)
    
    # Drop the other PII columns
    final_anonymized_df = final_anonymized_df.drop(columns=PII_TO_DROP, errors='ignore')
    
    # Save the *final, secure* dataset
    final_anonymized_df.to_csv(ANONYMIZED_OUTPUT_FILE, index=False)
    print(f"Saved *final, secure* anonymized data to '{ANONYMIZED_OUTPUT_FILE}'")
    
    print("Tokenization complete. Sample of secure token vault (first 5 entries):")
    for i, (original_id, token) in enumerate(token_vault.items()):
        if i >= 5: break
        print(f"  Original ID: {original_id} -> Token: {token[:20]}...")

    # --- 5. Data Utility Metrics ---
    print("\n--- 5. Data Utility Metrics ---")
    # 5a. Information Loss (NCP)
    ncp_k3_l2 = compute_ncp(original_df, final_anonymized_df, QUASI_IDENTIFIERS)
    print(f"Normalized Certainty Penalty (NCP) for k=3, l=2 data: {ncp_k3_l2:.4f}")
    
    # 5b. Machine Learning Utility
    print("Running Machine Learning utility tests...")
    accuracy_original = run_ml_utility_test(original_df, QUASI_IDENTIFIERS, SENSITIVE_ATTRIBUTE, is_anonymized=False)
    accuracy_k3_l2 = run_ml_utility_test(final_anonymized_df, QUASI_IDENTIFIERS, SENSITIVE_ATTRIBUTE, is_anonymized=True)
    print(f"ML Accuracy on Original Data: {accuracy_original:.4f}")
    print(f"ML Accuracy on Anonymized (k=3, l=2) Data: {accuracy_k3_l2:.4f}")

    # --- 6. Generate Privacy-Utility Plot ---
    print("\n--- 6. Generating Privacy-Utility Trade-off Plot ---")
    k_plot_values = [1] + k_values # k=1 represents the original data
    ncp_values = [0.0] # NCP for original data is 0
    accuracy_values = [accuracy_original]
    
    for k in k_values:
        df = anonymized_results[k]['df']
        ncp_values.append(compute_ncp(original_df, df, QUASI_IDENTIFIERS))
        accuracy_values.append(run_ml_utility_test(df, QUASI_IDENTIFIERS, SENSITIVE_ATTRIBUTE, is_anonymized=True))

    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:red'
    ax1.set_xlabel('k-Anonymity Parameter (k)')
    ax1.set_ylabel('NCP (Information Loss)', color=color)
    ax1.plot(k_plot_values, ncp_values, color=color, marker='o', label='NCP')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('ML Accuracy (Utility)', color=color)
    ax2.plot(k_plot_values, accuracy_values, color=color, marker='x', linestyle='--', label='ML Accuracy')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    plt.title('Privacy-Utility Trade-off in k-Anonymity')
    plt.xticks(k_plot_values)
    plt.grid(True)
    plt.savefig(PLOT_OUTPUT_FILE)
    print(f"Plot saved to '{PLOT_OUTPUT_FILE}'")
    
    # --- 7. Generate Metadata File ---
    print("\n--- 7. Generating Metadata File ---")
    metadata = {
      "dataset_rows": len(original_df),
      "k_values_tested": k_values,
      "l_values_tested": l_values,
      "final_run": {"k": 3, "l": 2},
      "ncp_k3_l2": round(ncp_k3_l2, 4),
      "uniqueness_pre": round(baseline_risk, 4),
      "uniqueness_post_k3": round(anonymized_results[3]['risk'], 4),
      "ml_accuracy_original": round(accuracy_original, 4),
      "ml_accuracy_k3_l2": round(accuracy_k3_l2, 4),
      "timestamp": datetime.utcnow().isoformat() + "Z",
      "python_version": "3.10"
    }
    
    with open(METADATA_OUTPUT_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to '{METADATA_OUTPUT_FILE}'")
    
    print("\n--- All experiments complete. ---")

if __name__ == "__main__":
    main()