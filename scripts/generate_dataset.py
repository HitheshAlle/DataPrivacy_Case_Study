import pandas as pd
import numpy as np
from faker import Faker
import uuid
import os

# --- Configuration ---
NUM_ROWS = 500
RANDOM_SEED = 42
OUTPUT_DIR = 'data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'original.csv')

# --- Initialize for Reproducibility ---
np.random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)
fake = Faker()

def create_synthetic_dataset(num_rows: int) -> pd.DataFrame:
    """
    Generates a synthetic hospital dataset.

    Args:
        num_rows: The number of patient records to generate.

    Returns:
        A pandas DataFrame with synthetic patient data.
    """
    print(f"Generating {num_rows} synthetic patient records...")
    
    data = {
        'Patient_ID': [str(uuid.uuid4()) for _ in range(num_rows)],
        'Name': [fake.name() for _ in range(num_rows)],
        'Age': np.random.randint(18, 90, size=num_rows),
        'Gender': np.random.choice(['M', 'F', 'Other'], size=num_rows, p=[0.48, 0.48, 0.04]),
        'ZIP_Code': [fake.zipcode() for _ in range(num_rows)],
        'Diagnosis': np.random.choice(
           ['Asthma', 'Diabetes', 'Hypertension', 'None', 'Flu'],  # <-- This list was added
            size=num_rows,
            p=[0.15, 0.25, 0.10, 0.40, 0.10]
        )
    }
    
    df = pd.DataFrame(data)
    print("Dataset generation complete.")
    return df

def main():
    """Main function to generate and save the dataset."""
    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    dataset = create_synthetic_dataset(NUM_ROWS)
    
    # Save the dataset to a CSV file
    dataset.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully saved original dataset to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()