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
   pip install pandas requests python-dotenv tqdm openpyxl
   ```

## Data Processing Workflow

The pipeline follows a 4-stage process:

### Stage 1: Data Splitting
**Script:** `data_splitting.py`

Splits large CSV files into batches of 5000 records for parallel processing.

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

### Stage 3: Error Reprocessing
**Script:** `sync_error.py`

Reprocesses addresses that failed in Stage 2 (usually due to malformed addresses that need manual correction).

```bash
python sync_error.py
# Prompts for folder path and file number
# Input: ./202203/1/error_address_1.csv (expects column "주소")
# Output: ./202203/1/post_error_1/post_final_1.csv, ./202203/1/post_error_1/post_error_1.csv
```

**Script:** `error_merge.py`

Merges successfully reprocessed addresses back into the main results.

```bash
python error_merge.py
# Prompts for folder path and file number
# Updates final_address_{file_number}.csv with reprocessed results
```

### Stage 4: Final Merging
**Script:** `merge.py`

Merges all batch results into a single Excel file.

```bash
python merge.py
# Input: All ./202201/*/merged_*.csv files
# Output: ./202201/final_merged_output.xlsx
```

## Key Architecture Notes

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

### Logging
All API operations log to `address_api_sync.log` with timestamps and error details.
