import pandas as pd
import numpy as np
import hashlib
import hmac
from typing import List, Tuple, Dict, Any

# A hardcoded key for HMAC to ensure reproducibility.
# In real systems, this would be securely managed.
HMAC_SECRET_KEY = b'bcse318l-secret-key-for-reproducible-tokenization'


# --------------------------------------------------------
# Generalization Functions
# --------------------------------------------------------
def generalize_age(df: pd.DataFrame, bins: List[int], labels: List[str]) -> pd.DataFrame:
    """
    Generalizes the 'Age' column into predefined buckets.
    """
    df_copy = df.copy()
    df_copy['Age'] = pd.cut(df_copy['Age'], bins=bins, labels=labels, right=False)
    return df_copy


def generalize_zip(df: pd.DataFrame, precision: int) -> pd.DataFrame:
    """
    Generalizes the 'ZIP_Code' column by suppressing digits.
    """
    df_copy = df.copy()
    df_copy['ZIP_Code'] = (
        df_copy['ZIP_Code']
        .astype(str)
        .str.slice(0, precision)
        .str.pad(5, side='right', fillchar='*')
    )
    return df_copy


# --------------------------------------------------------
# k-Anonymity Functions
# --------------------------------------------------------
def get_equivalence_classes(df: pd.DataFrame, qis: List[str]) -> pd.core.groupby.generic.DataFrameGroupBy:
    """Groups the DataFrame by quasi-identifiers."""
    return df.groupby(qis, observed=True)


def check_k_anonymity(df: pd.DataFrame, qis: List[str], k: int) -> bool:
    """
    Checks if a DataFrame satisfies k-anonymity.
    """
    if df.empty:
        return True
    eq_classes = get_equivalence_classes(df, qis)
    return eq_classes.size().min() >= k


def apply_k_anonymity(df: pd.DataFrame, qis: List[str], k: int) -> pd.DataFrame:
    """
    Applies k-anonymity using simple generalization of 'Age' and 'ZIP_Code'.
    """
    anonymized_df = df.copy()
    
    # Define generalization levels.
    age_generalizations = [
        ([0, 20, 30, 40, 50, 60, 70, 80, 90, 100],
         ['0-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90-99']),
        ([0, 25, 50, 75, 100],
         ['0-24', '25-49', '50-74', '75-99']),
        ([0, 50, 100],
         ['0-49', '50-99']),
        ([0, 100],
         ['0-99']),
    ]
    zip_generalizations = [4, 3, 2, 1]

    gen_level = 0
    temp_df = df.copy()

    while not check_k_anonymity(anonymized_df, qis, k):
        print(f"k={k} not met. Applying generalization level {gen_level + 1}...")

        temp_df = df.copy()
        age_level_idx = gen_level // 2
        zip_level_idx = (gen_level - 1) // 2

        # Apply Age generalization
        if 'Age' in qis:
            current_age_level = min(age_level_idx, len(age_generalizations) - 1)
            age_bins, age_labels = age_generalizations[current_age_level]
            temp_df = generalize_age(temp_df, bins=age_bins, labels=age_labels)

        # Apply ZIP generalization
        if 'ZIP_Code' in qis and zip_level_idx >= 0:
            current_zip_level = min(zip_level_idx, len(zip_generalizations) - 1)
            zip_prec = zip_generalizations[current_zip_level]
            temp_df = generalize_zip(temp_df, precision=zip_prec)

        anonymized_df = temp_df.copy()
        gen_level += 1
        if gen_level > 10:
            print("Error: Could not achieve k-anonymity after multiple generalization steps.")
            return anonymized_df

    print(f"k={k} anonymity achieved.")
    return anonymized_df


# --------------------------------------------------------
# l-Diversity and Tokenization
# --------------------------------------------------------
def check_l_diversity(df: pd.DataFrame, sensitive_col: str, qis: List[str], l_val: int) -> Tuple[bool, List]:
    """
    Checks if a k-anonymous DataFrame satisfies l-diversity.
    """
    eq_classes = get_equivalence_classes(df, qis)
    failing_groups = []

    for name, group in eq_classes:
        diversity = group[sensitive_col].dropna().nunique()
        if diversity < l_val:
            failing_groups.append((name, diversity))

    return len(failing_groups) == 0, failing_groups


def tokenize_ids(df: pd.DataFrame, id_col: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Replaces a column of identifiers with non-reversible HMAC-based tokens.
    """
    df_tokenized = df.copy()

    def generate_token(value: str) -> str:
        return hmac.new(HMAC_SECRET_KEY, value.encode('utf-8'), hashlib.sha256).hexdigest()

    df_tokenized[id_col] = df_tokenized[id_col].apply(generate_token)
    token_vault = dict(zip(df[id_col], df_tokenized[id_col]))

    return df_tokenized, token_vault


# --------------------------------------------------------
# Risk and Utility Metrics
# --------------------------------------------------------
def simulate_linkage_attack(df: pd.DataFrame, attacker_qis: List[str]) -> float:
    """
    Simulates a linkage attack to calculate the re-identification risk.
    """
    eq_classes = get_equivalence_classes(df, attacker_qis)
    group_sizes = eq_classes.size()
    num_unique = (group_sizes == 1).sum()
    total_records = len(df)
    return num_unique / total_records if total_records > 0 else 0


def compute_ncp(original_df: pd.DataFrame, anonymized_df: pd.DataFrame, qis: List[str]) -> float:
    """
    Computes the Normalized Certainty Penalty (NCP) for the anonymized dataset.
    """
    total_ncp = 0.0
    num_qis = len(qis)

    for qi in qis:
        qi_ncp = 0.0
        # ** FIX: Check for 'Age' specifically for numeric logic **
        if pd.api.types.is_numeric_dtype(original_df[qi]) and qi == 'Age':
            # Numerical attribute (Age)
            min_val = original_df[qi].min()
            max_val = original_df[qi].max()
            total_range = max_val - min_val
            if total_range == 0:
                continue

            series_str = anonymized_df[qi].astype(str)
            intervals = series_str.str.split('-', expand=True)

            if intervals.shape[1] == 1:
                low = pd.to_numeric(intervals[0], errors='coerce')
                high = low.copy()
            else:
                low = pd.to_numeric(intervals[0], errors='coerce')
                high = pd.to_numeric(intervals[1], errors='coerce')

            high = high.fillna(low)
            generalized_ranges = (high - low).abs()
            qi_ncp = (generalized_ranges / total_range).sum()

        else:
            # Categorical attribute (ZIP_Code, Gender)
            if qi == 'ZIP_Code':
                masked_chars = anonymized_df[qi].astype(str).str.count(r'\*')
                qi_ncp = (masked_chars / 5).sum()
            # Gender is not generalized in this plan, so its NCP = 0

        total_ncp += qi_ncp

    # Normalize across records and QIs
    return total_ncp / (len(original_df) * num_qis) if len(original_df) > 0 else 0.0