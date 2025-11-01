---
## Slide 1: Title
# Anonymization and Tokenization of Hospital Data for Secure Research Sharing
### BCSE318L: Data Privacy Case Study

---
## Slide 2: Problem and Objectives
**Scenario:** A hospital needs to share patient data for a medical research study without compromising patient privacy.

**Threat Model:**
* An attacker knows a target's **Age, Gender, and ZIP Code**.
* **Goal:** Link this public information to the hospital dataset to learn the target's **Diagnosis**.

**Objectives:**
1.  Apply **k-Anonymity & l-Diversity** to de-identify data.
2.  Use **Tokenization** to protect patient IDs.
3.  Analyze the **Privacy vs. Utility** trade-off.

---
## Slide 3: Methodology
**Attribute Classification:**
* **PII:** `Name`, `Patient_ID` (Removed/Tokenized)
* **Quasi-Identifiers (QIs):** `Age`, `Gender`, `ZIP_Code` (Generalized)
* **Sensitive:** `Diagnosis` (Protected)

**k-Anonymity (Identity Protection):**
* Generalized QIs until every record was indistinguishable from at least *k-1* others.
* Example: `Age 34` -> `0-99`, `ZIP 90210` -> `9****`

**l-Diversity (Attribute Protection):**
* Ensured each group of *k* records had at least *l* different diagnoses.
* Prevents homogeneity attacks.

**Tokenization (Identifier Protection):**
* Replaced `Patient_ID` with a non-reversible HMAC-SHA256 hash.

---
## Slide 4: Results - Privacy Risk Reduction
**The Problem:** The original dataset was extremely vulnerable.
* **100.00%** of records were unique based on Age, Gender, and ZIP Code.
* A linkage attack would succeed for **every patient** in the dataset.

**The Solution:** k-Anonymity (via heavy generalization) drastically reduced this risk.
* Re-identification Risk drops from 100% to **0.80%**.
* The k-anonymity script was forced to apply its maximum generalization level.

| k-Value | Uniqueness Rate (Risk) |
| :--- | :--- |
| **1 (Original)** | **100.00%** |
| 2 | 0.80% |
| 3 | 0.80% |
| 5 | 0.80% |

---
## Slide 5: Results - The Privacy-Utility Trade-off
Stronger privacy comes at a cost. Our experiment showed:

![Privacy-Utility Tradeoff Plot](report/privacy_utility_tradeoff.png)

* As **k** increases (more privacy), **Information Loss (NCP)** jumps dramatically to **0.7315** and flatlines.
* This high information loss caused a *measurable* drop in **Practical Utility (ML Accuracy)**, which fell from **0.4067** to **0.3600**.

---
## Slide 6: Why k-Anonymity Is Not Enough
**The Homogeneity Attack**

Imagine a 3-anonymous dataset where an attacker knows their target is in the blue group.

| Age | ZIP | Diagnosis |
| :--- | :--- | :--- |
| 40-49 | 123** | **Cancer** |
| 40-49 | 123** | **Cancer** |
| 40-49 | 123** | **Cancer** |
| 20-29 | 456** | Flu |
| 20-29 | 456** | Hypertension |

The dataset is 3-anonymous, but privacy is broken.
The attacker learns the target's diagnosis with **100% certainty**.

**l-Diversity** solves this by requiring variety in the `Diagnosis` column for each group.

---
## Slide 7: Lessons from Real-World Failures
* **AOL (2006):** Released "anonymized" search logs. Users were re-identified from the content of their searches (e.g., searching for local services).
    * **Lesson:** PII is everywhere. Simply removing a user ID is not enough.

* **Netflix Prize (2007):** Released "anonymized" movie ratings. Users were re-identified by linking their unique rating patterns to public IMDb profiles.
    * **Lesson:** Behavioral data can be a powerful fingerprint.

---
## Slide 8: Conclusion & Recommendations
**Conclusion:**
* A 100% unique dataset required *maximum generalization* to even approach k-anonymity.
* This high generalization (NCP: 0.73) caused a **measurable drop in ML utility** (40.7% -> 36.0%), clearly showing the privacy-utility trade-off.
* Even with maximum generalization, the data **still failed l-diversity**, proving k-anonymity alone is insufficient.

**Recommendations for the Hospital:**
1.  **Always Enforce l-Diversity:** Never rely on k-anonymity alone.
2.  **Tokenize All IDs:** The final pipeline correctly tokenized `Patient_ID` and dropped `Name`, which is a mandatory step.
3.  **Adopt a Risk-Based Approach:** For highly unique data like this, simple generalization fails. The hospital should explore differential privacy or synthetic data generation.