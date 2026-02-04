# 한국 주소 데이터 처리 파이프라인

## 프로젝트 개요

### 프로젝트 배경
본 프로젝트는 2024년 부산대학교 병원에서 의뢰한 총 40만영 가량의 코로나 19 감염 환자 데이터의 전처리 과정에서 실행한 프로젝트입니다.
구체적으로는 부산대학교 병원에서 의뢰한 요구사항 중에서 도로명 주소에서 행정 구역 정보(시/도, 시/군/구, 음/면동) 정보를 추출하는 것이 있었습니다. 데이터의 크기가 40만 건에 달했기 때문에, 40만명의 도로명 주소를 일일이 찾아서 행정 구역 정보를 추출하는 것에는 시간적 부담이 많이 컸습니다. 따라서 행정안전부에서 제공하는 주소 API 를 활용하여 도로명 주소에서 행정 구역 정보를 추출하는 데이터 처리  파이프라인을 만들게 되었습니다.

### 프로젝트 소개
행정안전부에서 제공하는 주소 API(Juso API)를 활용하여 비정형 주소 데이터를 표준화된 행정구역 체계(시/도, 시/군/구, 읍/면/동)로 변환하는 데이터 처리 파이프라인입니다.

### 기술 스택
- **언어**: Python 3.x
- **데이터 처리**: Pandas
- **API 통신**: Requests
- **환경 변수 관리**: python-dotenv
- **진행 상황 표시**: tqdm
- **로깅**: Python logging 모듈

### 핵심 기능
- REST API 연동 및 자동 재시도 로직
- 대용량 데이터 배치 분할 처리
- 2단계 에러 복구 시스템
- 인덱스 기반 데이터 병합

---

## 기술적 하이라이트

### 1. API 통합 및 재시도 로직

#### 구현 코드

```python
def call_juso_api(address, retries=3, delay=3):
    params = {
        "currentPage": 1,
        "countPerPage": 1,
        "keyword": address,
        "confmKey": CONFIRM_KEY,
        "resultType": "json",
        "hstryYn": "Y",
    }

    for attempt in range(retries):
        try:
            response = requests.get(API_URL, params=params, timeout=50)
            if response.status_code == 200:
                data = response.json()
                if (
                    data["results"]["common"]["errorCode"] == "0"
                    and data["results"]["juso"]
                ):
                    juso = data["results"]["juso"][0]
                    return {
                        "시/도": juso.get("siNm", None),
                        "시/군/구": juso.get("sggNm", None),
                        "읍/면/동": juso.get("emdNm", None),
                    }
                else:
                    logger.error(
                        f"API Error: {data['results']['common']['errorMessage']} for address: {address}"
                    )
            else:
                logger.error(
                    f"HTTP Error: {response.status_code} for address: {address}"
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException: {e} for address: {address}")

        # 재시도 전 대기
        if attempt < retries - 1:
            logger.info(f"Retrying ({attempt + 1}/{retries}) for address: {address}")
            time.sleep(delay)

    logger.error(f"All retries failed for address: {address}")
    return None
```

#### 기술적 의사결정

| 설정값 | 선택 근거 |
|--------|----------|
| `retries=3` | 일시적 네트워크 오류 대응. 3회 이상은 영구적 실패로 판단 |
| `delay=3` | API 서버 부하 방지 및 Rate Limit 회피 |
| `timeout=50` | 대용량 요청 시 응답 지연 고려 |
| `hstryYn="Y"` | 폐지된 주소도 검색하여 변환 성공률 향상 |

#### 에러 핸들링 전략

```
┌─────────────────────────────────────────────────────────────┐
│                    API 호출 시작                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              HTTP 상태 코드 확인                              │
│         (status_code == 200 ?)                              │
└─────────────────────────────────────────────────────────────┘
           │                              │
        200 OK                      HTTP Error
           │                              │
           ▼                              ▼
┌─────────────────────┐        ┌─────────────────────┐
│   API 에러코드 확인   │        │   HTTP 에러 로깅     │
│  (errorCode == "0"?) │        │   재시도 대기        │
└─────────────────────┘        └─────────────────────┘
     │            │
  성공          실패
     │            │
     ▼            ▼
┌──────────┐  ┌─────────────────────┐
│ 결과 반환 │  │   API 에러 로깅      │
└──────────┘  │   재시도 대기        │
              └─────────────────────┘
```

**3단계 에러 분류:**
1. **HTTP 에러**: 서버 연결 실패, 500 에러 등 → 재시도
2. **API 에러**: 유효하지 않은 주소, 검색 결과 없음 → 로깅 후 재시도
3. **네트워크 에러**: `RequestException` 발생 → 로깅 후 재시도

---

### 2. 배치 처리 아키텍처

#### 데이터 분할 전략

```python
# 배치 크기 설정
BATCH_SIZE = 5000

# batch_size 만큼의 배치가 총 몇개 필요한지를 계산하는 로직
total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE

# enumerate()의 start=1 옵션을 사용하여 1부터 시작하는 인덱스를 사용함
for batch_num, start in enumerate(range(0, len(df), BATCH_SIZE), start=1):
    batch_df = df.iloc[start : start + BATCH_SIZE]
    folder_path = os.path.join(output_folder, str(batch_num))
    os.makedirs(folder_path, exist_ok=True)
    batch_df.to_csv(os.path.join(folder_path, f"{batch_num}.csv"), index=True)
```

#### 배치 크기 선정 근거

| 배치 크기 | 장점 | 단점 |
|----------|------|------|
| 1,000건 | 빠른 실패 복구 | 파일 수 과다, I/O 오버헤드 |
| **5,000건** | 균형잡힌 처리 단위 | - |
| 10,000건 | 파일 수 감소 | 실패 시 재처리 비용 증가 |
| 50,000건+ | - | 네트워크 타임아웃 위험 |

**5,000~10,000건 선택 이유:**
- API 호출 1건당 약 0.3~0.5초 소요 → 5,000건 처리 시 약 25~40분
- 네트워크 불안정 시 최대 손실 범위를 관리 가능한 수준으로 제한
- 중간 결과물 저장으로 진행 상황 추적 용이

#### 인덱스 추적 메커니즘

```python
# 원본 데이터 처리 시: 순차 인덱스로 결과 생성
def process_addresses(df):
    results = []
    error_records = []

    for idx, address in tqdm(df["n_addr"].items(), total=len(df)):
        result = call_juso_api(address)
        if result is None:
            error_records.append({
                "Index": idx,          # 원본 인덱스 보존
                "주소": address,
                "오류": "No result or error",
            })
            results.append({"시/도": None, "시/군/구": None, "읍/면/동": None})
        else:
            results.append(result)

    return results, error_records
```

**인덱스 관리 원칙:**
- 원본 CSV의 "연번" 컬럼을 기준으로 추적
- 에러 레코드에 원본 인덱스(`Index`) 저장
- 재처리 시 인덱스 기반 매칭으로 정확한 위치에 결과 병합

---

### 3. 에러 복구 시스템

에러 복구는 총 2회에 걸쳐 수행됩니다. **1차 에러 복구**는 API 변환 실패 주소(`error_address_*.csv`)를 수동 정제 후 재변환하는 자동화된 파이프라인이고, **2차 에러 복구**는 최종 병합 파일에 남아있는 NaN 값을 사람이 직접 검토하여 수정하는 단계입니다. 2차 에러 복구 대상은 대부분 폐지된 주소, 정규식 처리 오류, 1차 정제 과정에서 누락된 주소 등 자동 처리가 불가능한 데이터입니다.

#### 주소 변환 실패 유형 및 수동 처리 전략

API 변환에 실패한 주소는 `error_address_*.csv`에 기록되며, 원본 주소 데이터(`n_addr` 컬럼)를 기반으로 수동 정제 후 재변환합니다. `n_addr` 컬럼은 전처리 실행 전의 원본 주소 데이터를 나타내기 때문에 이 데이터를 검색에 활용합니다.

**주요 실패 유형별 처리 방법:**

| 유형 | 실패 원인 | 원본 주소 예시 | 정제 후 주소 |
|------|----------|---------------|-------------|
| 폐지된 주소 | 도로명 변경/폐지 | 부산광역시 동래구 쇠미로 95 | [주소정보누리집](https://www.juso.go.kr)에서 "폐지된 주소 정보 포함" 체크 후 검색 → 지번주소에서 행정구역 추출 |
| 상세주소 포함 | 건물명/층/호수 잔존 | 부산광역시 동구 홍곡남로 6 동신탕 3층 | 부산광역시 동구 홍곡남로 6 |
| 정규식 처리 오류 | 숫자 패턴 오분류 | 부산광역시 해운대구 센텀3로 26 3009 3009호 | 부산광역시 해운대구 센텀3로 26 |
| 통/반 정보 포함 | 행정 단위 잔존 | 부산광역시 사상구 백양대로433번길 9 7통 4반 | 부산광역시 사상구 백양대로433번길 9 |

#### 1차 에러 복구: 자동 재처리 파이프라인

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Stage 2: 1차 API 처리                            │
│                         (sync_address.py)                               │
└─────────────────────────────────────────────────────────────────────────┘
                    │                              │
                 성공                            실패
                    │                              │
                    ▼                              ▼
        ┌─────────────────────┐        ┌─────────────────────┐
        │ final_address_N.csv │        │ error_address_N.csv │
        │   (표준화된 주소)     │        │   (실패한 주소)      │
        └─────────────────────┘        └─────────────────────┘
                                                  │
                                       ┌──────────┴──────────┐
                                       │ 수동 주소 정제       │
                                       │ (통/반, 상세주소 제거)│
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Stage 3: 2차 API 처리                            │
│                         (sync_error.py)                                 │
└─────────────────────────────────────────────────────────────────────────┘
                    │                              │
                 성공                            실패
                    │                              │
                    ▼                              ▼
        ┌─────────────────────┐        ┌─────────────────────┐
        │  post_final_N.csv   │        │  post_error_N.csv   │
        │   (복구된 주소)       │        │   (최종 실패)        │
        └─────────────────────┘        └─────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────────────┐
        │       error_merge.py                    │
        │ final_address_N.csv에 결과 병합          │
        └─────────────────────────────────────────┘
```

#### 원본 인덱스 보존 로직 (sync_error.py)

```python
def process_addresses(df):
    results = []
    error_records = []

    for idx, address in tqdm(df["주소"].items(), total=len(df)):
        result = call_juso_api(address)
        if result is None:
            error_records.append({
                "Index": df.loc[idx, "Index"],  # 원본 인덱스 보존
                "주소": address,
                "오류": "No result or error",
            })
            results.append({
                "Index": df.loc[idx, "Index"],  # 결과에도 인덱스 포함
                "시/도": None,
                "시/군/구": None,
                "읍/면/동": None,
            })
        else:
            results.append({
                "Index": df.loc[idx, "Index"],
                "시/도": result["시/도"],
                "시/군/구": result["시/군/구"],
                "읍/면/동": result["읍/면/동"]
            })

    return results, error_records
```

**sync_address.py vs sync_error.py 비교:**

| 항목 | sync_address.py | sync_error.py |
|------|-----------------|---------------|
| 입력 컬럼 | `n_addr` (전처리 전 원본 주소) | `주소` (수동 정제된 주소) |
| 인덱스 처리 | 순차 인덱스 생성 | 원본 `Index` 컬럼 보존 |
| 출력 구조 | `index, 시/도, 시/군/구, 읍/면/동` | `Index, 시/도, 시/군/구, 읍/면/동` |

#### NaN 값 선택적 업데이트 (error_merge.py)

```python
def main():
    final_df = pd.read_csv(final_path)
    error_df = pd.read_csv(error_path)

    for _, row in error_df.iterrows():
        idx = row["Index"]

        # final_df의 'index' 컬럼에서 해당 Index 값을 가진 행 찾기
        matching_rows = final_df[final_df["index"] == idx]
        if not matching_rows.empty:
            final_idx = matching_rows.index[0]
            # 해당 행의 '시/도' 값이 비어 있으면 업데이트
            if pd.isna(final_df.loc[final_idx, "시/도"]):
                final_df.loc[final_idx, ["시/도", "시/군/구", "읍/면/동"]] = row[
                    ["시/도", "시/군/구", "읍/면/동"]
                ]

    final_df.to_csv(final_path, index=False, encoding="utf-8-sig")
```

**선택적 업데이트 로직:**
- `pd.isna()` 체크로 이미 성공한 데이터 보호
- 인덱스 기반 정확한 위치 매칭
- 원본 파일 직접 업데이트로 데이터 일관성 유지

#### 2차 에러 복구: 최종 수동 검토

1차 에러 복구와 최종 병합(Stage 4)이 완료된 후에도 변환되지 않은 데이터가 NaN 값으로 남아있을 수 있습니다. 이러한 데이터는 1차 에러 복구의 자동 재처리로는 해결할 수 없는 경우로, 사람이 직접 검토하여 수정해야 합니다.

**2차 에러 복구 대상:**

| 유형 | 설명 | 처리 방법 |
|------|------|----------|
| 폐지된 주소 | 도로명이 변경/폐지되어 API에서 검색 불가 | [주소정보누리집](https://www.juso.go.kr)에서 "폐지된 주소 정보 포함" 체크 후 지번주소에서 행정구역 추출 |
| 정규식 처리 오류 | 1차 정제에서 누락된 비정형 패턴 | 원본 주소(`n_addr`) 확인 후 수동 정제 |
| 1차 정제 누락 | 1차 에러 복구 과정에서 미처 수정하지 못한 주소 | 원본 주소 확인 후 주소정보누리집에서 검색 |

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Stage 4: 최종 병합 완료                                │
│                    (final_merged_output.xlsx)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    2차 에러 복구: 수동 검토                                │
│                                                                         │
│    1. 시/도, 시/군/구, 읍/면/동 컬럼에서 NaN 값이 존재하는 행 식별        │
│    2. 해당 행의 n_addr(원본 주소) 컬럼 확인                               │
│    3. 주소정보누리집에서 검색 (폐지된 주소 포함 옵션 체크)                  │
│    4. 지번주소에서 시/도, 시/군/구, 읍/면/동 추출                         │
│    5. 엑셀 파일의 NaN 값에 직접 입력                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

**2차 에러 복구가 필요한 이유:**
- 1차 에러 복구는 주소 형식 오류(상세주소, 통/반 등)를 정제하여 API 재변환하는 자동화된 프로세스
- 그러나 폐지된 주소, 1차 정제에서 누락된 오류, 데이터 자체의 오류 등은 자동 처리가 불가능
- 따라서 최종 병합 후 남아있는 NaN 값에 대해 사람이 직접 검토하고 수정하는 단계가 필요

---

### 4. 데이터 병합 전략

#### 열 기준 병합 (원본 + API 결과)

```python
# 각 배치별 병합
df1 = pd.read_csv(main_name, low_memory=False)      # 원본 데이터
df2 = pd.read_csv(after_name, index_col=0)          # API 결과
df_final = pd.concat([df1, df2], axis=1)            # 열 방향 병합
```

```
원본 데이터 (df1)                API 결과 (df2)
┌────────┬───────────────┐      ┌────────┬────────┬────────┐
│ 연번   │ n_addr        │      │ 시/도  │시/군/구│읍/면/동│
├────────┼───────────────┤  +   ├────────┼────────┼────────┤
│ 1      │ 서울시 강남구 │      │ 서울   │ 강남구 │ 역삼동 │
│ 2      │ 부산시 해운대 │      │ 부산   │ 해운대 │ 우동   │
└────────┴───────────────┘      └────────┴────────┴────────┘

                    ↓ pd.concat(axis=1)

병합 결과 (df_final)
┌────────┬───────────────┬────────┬────────┬────────┐
│ 연번   │ n_addr        │ 시/도  │시/군/구│읍/면/동│
├────────┼───────────────┼────────┼────────┼────────┤
│ 1      │ 서울시 강남구 │ 서울   │ 강남구 │ 역삼동 │
│ 2      │ 부산시 해운대 │ 부산   │ 해운대 │ 우동   │
└────────┴───────────────┴────────┴────────┴────────┘
```

#### 행 기준 병합 (전체 배치 통합)

```python
# 모든 병합된 파일 수집
merged_dfs = []
for merged_csv in merged_list:
    df = pd.read_csv(merged_csv, low_memory=False)
    merged_dfs.append(df)

# 행 방향 통합
final_merged_df = pd.concat(merged_dfs, ignore_index=True)

# 최종 엑셀 출력
final_merged_df.to_excel(output_excel_path, index=False)
```

```
배치 1                           배치 2
┌────────┬────────┬────────┐    ┌────────┬────────┬────────┐
│ 연번   │ 시/도  │ ...    │    │ 연번   │ 시/도  │ ...    │
├────────┼────────┼────────┤    ├────────┼────────┼────────┤
│ 1-5000 │ ...    │ ...    │    │5001-   │ ...    │ ...    │
└────────┴────────┴────────┘    └────────┴────────┴────────┘
              │                         │
              └────────────┬────────────┘
                           ▼
              pd.concat(ignore_index=True)
                           ▼
┌──────────────────────────────────────────────────────────┐
│              final_merged_output.xlsx                    │
│                    (전체 데이터)                          │
└──────────────────────────────────────────────────────────┘
```

---

## 아키텍처 설계

### 5단계 파이프라인 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Stage 0: 데이터 준비                                  │
│                    (preprocessing.ipynb)                                │
│                                                                         │
│    [Excel 파일] ──────────────────────────────▶ [CSV 파일]              │
│                     - 인코딩 변환 (UTF-8)                                │
│                     - 컬럼 구조 검증                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Stage 1: 데이터 분할                                  │
│                    (data_splitting.py)                                  │
│                                                                         │
│    [대용량 CSV] ──────────────────────────────▶ [배치 CSV들]            │
│    (202201.csv)       - 5,000건 단위 분할        ./202201/1/1.csv      │
│                       - 폴더 구조 생성           ./202201/2/2.csv      │
│                                                  ./202201/3/3.csv      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Stage 2: API 동기화                                   │
│                    (sync_address.py)                                    │
│                                                                         │
│    [배치 CSV] ──▶ [Juso API] ──▶ [final_address_N.csv]                 │
│                       │                                                 │
│                       └────────▶ [error_address_N.csv]                 │
│                                                                         │
│    - 재시도 로직 (3회, 3초 간격)                                         │
│    - 진행 상황 로깅                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Stage 3: 에러 복구                                    │
│                    (sync_error.py + error_merge.py)                     │
│                                                                         │
│    [error_address_N.csv] ──▶ [수동 정제] ──▶ [sync_error.py]           │
│                                                    │                    │
│                                    ┌───────────────┴───────────────┐    │
│                                    ▼                               ▼    │
│                          [post_final_N.csv]              [post_error_N] │
│                                    │                                    │
│                                    ▼                                    │
│                          [error_merge.py]                               │
│                                    │                                    │
│                                    ▼                                    │
│                    [final_address_N.csv 업데이트]                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Stage 4: 최종 병합                                    │
│                    (merge.py)                                           │
│                                                                         │
│    [N.csv] + [final_address_N.csv] ──▶ [merged_N.csv]                  │
│                                              │                          │
│                                              ▼                          │
│    [merged_1.csv] ─┐                                                    │
│    [merged_2.csv] ─┼──────────────────▶ [final_merged_output.xlsx]     │
│    [merged_3.csv] ─┘                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 파일 구조 설계

```
{YYYYMM}/                              # 월별 데이터 디렉토리
├── {batch_num}/                       # 배치 번호별 디렉토리
│   ├── {batch_num}.csv                # 원본 배치 데이터
│   ├── final_address_{batch_num}.csv  # API 변환 성공 결과
│   ├── error_address_{batch_num}.csv  # 1차 실패 주소
│   ├── merged_{batch_num}.csv         # 원본 + 변환 결과 병합
│   └── post_error_{batch_num}/        # 재처리 디렉토리
│       ├── post_final_{batch_num}.csv # 재처리 성공 결과
│       └── post_error_{batch_num}.csv # 최종 실패 주소
└── final_merged_output.xlsx           # 최종 통합 결과
```

### 데이터 흐름도

```
┌──────────────┐
│ 원본 Excel   │
└──────┬───────┘
       │ Stage 0
       ▼
┌──────────────┐
│ 원본 CSV     │
└──────┬───────┘
       │ Stage 1
       ▼
┌──────────────┐     ┌──────────────┐
│ 배치 1.csv   │ ... │ 배치 N.csv   │
└──────┬───────┘     └──────┬───────┘
       │ Stage 2            │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│ final_1.csv  │     │ final_N.csv  │
│ error_1.csv  │     │ error_N.csv  │
└──────┬───────┘     └──────┬───────┘
       │ Stage 3            │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│ final_1.csv  │     │ final_N.csv  │
│ (업데이트됨)  │     │ (업데이트됨)  │
└──────┬───────┘     └──────┬───────┘
       │ Stage 4            │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│ merged_1.csv │     │ merged_N.csv │
└──────┬───────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                ▼
┌───────────────────────────┐
│ final_merged_output.xlsx  │
└───────────────────────────┘
```

---

## 기술적 의사결정 및 근거

### 1. 배치 크기 선정 (5,000건)

**문제 상황:**
- 전체 데이터셋: 수만~수십만 건
- API 호출당 응답 시간: 0.3~0.5초
- 네트워크 불안정 시 전체 재처리 위험

**의사결정:**
```
전체 처리 시간 = 데이터 수 × (API 응답 시간 + 처리 오버헤드)
50,000건 × 0.4초 ≈ 5.5시간 (단일 배치 시)

실패 시 손실 비용:
- 50,000건 배치: 최대 5.5시간 손실
- 5,000건 배치: 최대 33분 손실
```

**결론:** 5,000건 배치로 실패 시 최대 손실을 33분으로 제한

### 2. 재시도 전략 (3회, 3초 간격)

**고려 요소:**
| 요소 | 값 | 근거 |
|------|-----|------|
| 재시도 횟수 | 3회 | 일시적 오류는 보통 1-2회 내 복구 |
| 대기 시간 | 3초 | API Rate Limit 고려, 서버 부하 분산 |
| 타임아웃 | 50초 | 대용량 응답 시 지연 허용 |

**실패 분류:**
```
재시도로 해결 가능: 네트워크 타임아웃, 일시적 서버 오류
재시도로 해결 불가: 잘못된 주소 형식, 존재하지 않는 주소
```

### 3. 인덱스 관리 방식

**요구사항:**
- 원본 데이터와 API 결과의 정확한 매칭
- 에러 재처리 후 올바른 위치에 병합
- 전체 배치 통합 시 순서 유지

**해결 방안:**
```python
# sync_address.py: 순차 인덱스 생성 (결과와 원본 행 순서 일치)
df_final = pd.DataFrame(results).reset_index()

# sync_error.py: 원본 인덱스 컬럼 보존
results.append({
    "Index": df.loc[idx, "Index"],  # 원본 인덱스 유지
    ...
})

# error_merge.py: 인덱스 기반 매칭 업데이트
matching_rows = final_df[final_df["index"] == idx]
```

### 4. 로깅 전략

```python
logging.basicConfig(
    filename="address_api_sync.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
```

**로깅 대상:**
- API 에러 메시지 (디버깅용)
- HTTP 상태 코드 (서버 문제 추적)
- 재시도 시도 횟수 (성능 분석)
- 최종 실패 주소 (수동 처리 대상 식별)

---

## 확장성 및 개선 가능성

### 현재 한계점

| 한계점 | 영향 | 원인 |
|--------|------|------|
| 단일 스레드 처리 | 처리 속도 제한 | API Rate Limit 우회 불가 |
| 수동 에러 정제 | 인력 비용 발생 | 폐지된 주소, 상세주소, 정규식 오류 등 비정형 주소 패턴 다양성 |
| 메모리 내 전체 로드 | 초대용량 데이터 처리 제한 | Pandas 기본 동작 방식 |

### 향후 개선 방향

#### 1. 비동기 처리 도입
```python
# 현재: 동기 처리
for address in addresses:
    result = call_juso_api(address)  # 블로킹

# 개선: 비동기 처리 (asyncio + aiohttp)
async def process_batch(addresses):
    tasks = [call_juso_api_async(addr) for addr in addresses]
    return await asyncio.gather(*tasks)
```

#### 2. 자동 주소 정제 규칙
```python
# 통/반 패턴 자동 제거
address = re.sub(r'\s+\d+통\s*\d*반?$', '', address)

# 상세주소 패턴 자동 제거
address = re.sub(r'\s+\d+층$', '', address)
address = re.sub(r'\s+\d+호$', '', address)
```

#### 3. 청크 단위 스트리밍 처리
```python
# 대용량 파일 청크 처리
for chunk in pd.read_csv(file_path, chunksize=1000):
    process_chunk(chunk)
    save_intermediate_result(chunk)
```

#### 4. 캐싱 레이어 추가
```python
# Redis 기반 주소 캐싱
def call_juso_api_cached(address):
    cached = redis_client.get(address)
    if cached:
        return json.loads(cached)

    result = call_juso_api(address)
    redis_client.setex(address, 86400, json.dumps(result))
    return result
```

---

## 프로젝트 성과

### 정량적 성과
- 대용량 주소 데이터 표준화 자동화
- 에러 복구 시스템으로 데이터 품질 향상
- 배치 처리로 안정적인 대규모 데이터 처리

### 기술적 성장
- REST API 통합 및 에러 핸들링 패턴 습득
- 대용량 데이터 파이프라인 설계 경험
- Python 데이터 처리 라이브러리 활용 능력 향상
