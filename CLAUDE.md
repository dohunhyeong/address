# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Korean address data processing pipeline that uses the Juso API (https://business.juso.go.kr) to standardize and validate address data. The pipeline processes large CSV datasets in batches, handles API failures with retry logic, and merges results.

## Environment Setup

1. Create a `.env` file with your Juso API key:
   ```
   ADDRESS_API_KEY=your_api_key_here
   ```

2. Install dependencies (not managed by requirements.txt):
   ```bash
   pip install pandas requests python-dotenv tqdm openpyxl notebook ipykernel
   ```

## Data Processing Workflow

The pipeline follows a 6-stage process:

### Stage 0: Data Preparation
**Script:** `preprocessing.ipynb` (Section 1: Excel to CSV conversion)

Converts Excel files to CSV format for processing.

```python
# Reads Excel files and outputs CSV
# Validates data structure and column names
```

### Stage 1: Data Splitting
**Script:** `data_splitting.py`

Splits large CSV files into batches of 5000-10000 records for parallel processing (5000 or 10000 recommended to avoid network errors).

```bash
python data_splitting.py
# Input: ./202201.csv
# Output: ./202201/1/1.csv, ./202201/2/2.csv, etc.
```

### Stage 2: Address API Sync
**Script:** `sync_address.py`

Processes each batch through the Juso API to convert addresses to standardized format (시/도, 시/군/구, 읍/면/동).

```bash
python sync_address.py
# Prompts for folder path (default: 202203) and file number
# Example: folder_path=202201, file_number=1
# Input: ./202201/1/1.csv (expects column "n_addr")
# Output: ./202201/1/final_address_1.csv, ./202201/1/error_address_1.csv
```

API calls use retry logic (3 attempts, 3-second delay) and log to `address_api_sync.log`.

### Stage 3: Error Reprocessing (1st Error Correction)
**Script:** `sync_error.py`

Reprocesses addresses that failed in Stage 2. Before running, manually correct `error_address_*.csv` files by fixing malformed addresses (remove 통/반, detailed addresses, regex artifacts). This is the 1st of 2 error correction passes.

```bash
python sync_error.py
# Prompts for folder path and file number
# Input: ./202203/1/error_address_1.csv (expects column "주소")
# Output: ./202203/1/post_error_1/post_final_1.csv, ./202203/1/post_error_1/post_error_1.csv
```

**Script:** `preprocessing.ipynb` (Section 2: Error content correction)

Merges successfully reprocessed addresses (post_final_*.csv) back into the main results (final_address_*.csv).

```python
# Appends post_final_{n}.csv to final_address_{n}.csv
# Must be run for each batch processed
```

**Alternative Script:** `error_merge.py`

Standalone script version for automated merging.

```bash
python error_merge.py
# Prompts for folder path and file number
# Updates final_address_{file_number}.csv with reprocessed results
```

### Stage 4: Final Merging
**Script:** `preprocessing.ipynb` (Section 3: File merging) or `merge.py`

Merges all batch results into a single Excel file.

```python
# preprocessing.ipynb approach:
# 1. Merges original batch CSV with final_address CSV (column-wise)
# 2. Concatenates all merged batches (row-wise)
# 3. Outputs final_merged_output.xlsx

# merge.py approach (standalone):
# python merge.py
# Input: All ./202201/*/merged_*.csv files
# Output: ./202201/final_merged_output.xlsx
```

### Stage 5: Manual Review (2nd Error Correction)

After the final merge, remaining NaN values in 시/도, 시/군/구, 읍/면/동 columns require manual human review. These are addresses that could not be resolved through the automated 1st error correction pass.

**Common causes of remaining NaN values:**
1. **Deprecated addresses** - Roads that have been renamed or abolished; not found by the API even after correction
2. **Regex processing errors** - Non-standard patterns missed during 1st error correction
3. **1st correction omissions** - Addresses overlooked during manual correction in Stage 3

**Manual review process:**
1. Open `final_merged_output.xlsx` and identify rows with NaN values in 시/도, 시/군/구, or 읍/면/동
2. Check the `n_addr` column for the original address data
3. Search on [주소정보누리집](https://www.juso.go.kr) with "폐지된 주소 정보 포함" checked
4. Extract 시/도, 시/군/구, 읍/면/동 from the 지번주소 (lot-based address) result
5. Manually enter the values into the Excel file

This stage requires human judgment and cannot be automated, as the remaining failures involve deprecated addresses, data entry errors in the original dataset, or edge cases not covered by automated correction rules.

## Key Files

| File | Purpose |
|------|---------|
| `preprocessing.ipynb` | Excel/CSV conversion, error correction merging, final data merging |
| `data_splitting.py` | Splits large CSV into manageable batches |
| `sync_address.py` | Main address API conversion |
| `sync_error.py` | Reprocesses failed addresses |
| `error_merge.py` | Alternative to preprocessing.ipynb Section 2 for merging corrections |
| `merge.py` | Alternative to preprocessing.ipynb Section 3 for final merging |
| `.env` | Stores ADDRESS_API_KEY |
| `address_api_sync.log` | API operation logs |

## Key Architecture Notes

### Workflow Options
The pipeline offers two approaches:

**Jupyter Notebook Approach** (Recommended for interactive use):
- `preprocessing.ipynb` handles data preparation (Stage 0), error merging (Stage 3), and final merging (Stage 4)
- Better for visualization and step-by-step verification

**Script Approach** (Recommended for automation):
- `error_merge.py` for Stage 3, `merge.py` for Stage 4
- Better for automated batch processing

Both approaches are functionally equivalent.

### File Structure Pattern
```
{YYYYMM}/
  {batch_num}/
    {batch_num}.csv                    # Original data batch
    final_address_{batch_num}.csv       # API results
    error_address_{batch_num}.csv       # Failed addresses
    post_error_{batch_num}/             # Reprocessing directory
      post_final_{batch_num}.csv        # Reprocessed results
      post_error_{batch_num}.csv        # Still-failing addresses
    merged_{batch_num}.csv              # Original + final_address combined
  final_merged_output.xlsx              # All batches merged
```

### Index Handling
- Original data uses "연번" column as index
- `sync_address.py` creates results with sequential index
- `sync_error.py` preserves original "Index" column for merging back
- `error_merge.py` matches on "Index" column to update NaN values in final results

### API Response Structure
The Juso API returns:
- `시/도` (Province/Metropolitan city)
- `시/군/구` (City/County/District)
- `읍/면/동` (Township/Town/Neighborhood)

### Common Address Format Issues
Addresses that fail API validation typically have:
1. **Extra administrative codes** - "통/반" (district/subdivision) appended to address
   - Example: "부산광역시 사상구 백양대로433번길 9 7통 4반"
   - Fix: Remove "7통 4반" → "부산광역시 사상구 백양대로433번길 9"

2. **Detailed addresses** - Building names, floor/unit numbers
   - Example: "부산광역시 동구 홍곡남로 6 동신탕 3층"
   - Fix: Remove "동신탕 3층" → "부산광역시 동구 홍곡남로 6"

3. **Regex processing errors** - Unit numbers caught in road name
   - Example: "부산광역시 해운대구 센텀3로 26 3009호"
   - Fix: Remove "3009호" → "부산광역시 해운대구 센텀3로 26"

4. **Deprecated addresses** - Verify using https://www.juso.go.kr with "폐지된 주소 정보 포함" option

### Logging
All API operations log to `address_api_sync.log` with timestamps and error details.
