# 한국 주소 데이터 처리 파이프라인

## 프로젝트 개요

### 프로젝트 배경

#### 1. 프로젝트 개요 및 자원 현황 (Context & Constraints)

- **프로젝트**: 부산대학교병원 코로나19 환자 데이터(약 80만 건) 행정구역 정보(시/도, 시/군/구, 읍/면/동) 추출
- **가용 자원**: 인력 5명 / 가용 기간 약 3개월(약 60영업일)

정규식, 수동 웹 검색 등 여러 접근 방식을 검토하였으나, 제한된 인력과 기간 내에 80만 건을 처리하기 위해서는 자동화 파이프라인 구축이 필연적이라는 결론에 도달하였습니다.

#### 2. 데이터의 비정형성 및 오염도 (Data Complexity)

단순 파싱이 불가능했던 세 가지 핵심 품질 이슈:

- **입력 노이즈**: 수기 기록 과정에서의 오타(Typos) 및 비표준 띄어쓰기 혼입
- **데이터 노후화**: 주소 체계 개편으로 인한 폐지된 주소 및 변경된 행정구역 데이터 다수 존재
- **비정형 패턴**: 건물명, 상세주소(층/호), 통/반 정보 등이 혼재되어 표준화가 어려운 상태

#### 3. 기존 기술적 접근의 한계 (Technical Barriers)

**왜 단순 정규식만으로 안 되었는가:**

- **규칙의 충돌**: 도로명 주소(기하학적 규칙)와 지번 주소(관리 이력 규칙)의 근본적인 체계 차이로 단일 패턴 적용 불가
- **예외 처리의 한계**: 정규 표현식 기반 패턴 매칭은 비정형 주소 및 폐지된 주소에 대응 불가 → 정확도 결여 및 대규모 데이터 손실 위험

#### 4. 최종 의사결정: Human-In-The-Loop 기반 주소 데이터 전처리 파이프라인 구축

단순 반복 업무의 자동화와 데이터 신뢰성을 보장하는 전처리 체계를 구축하였습니다.

- **신뢰성**: 국가 표준 주소 DB인 Juso API 연동을 통해 데이터 정합성 확보
- **확장성**: 5,000건 단위 배치 처리(Batch Processing)로 대용량 데이터 처리 및 병렬 작업 흐름 확보. 한 배치의 API 처리가 진행되는 동안, 이전 배치의 수동 오류 정제 작업을 병행할 수 있도록 배치 크기를 설계하였습니다.
- **복구력**: 자동 처리가 불가한 실패 건에 한해 단계적 수기 개입을 허용하는 Human-In-The-Loop 2단계 에러 복구 구조(Stage 3 수기 정제 후 자동 재처리 → Stage 5 수동 검색)로 전처리 정확도 100% 달성

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

## 아키텍처 설계

### 6단계 파이프라인 다이어그램

```mermaid
flowchart TD
    A["📊 원본 Excel 파일"] -->|"Stage 0: 데이터 준비\npreprocessing.ipynb"| B["📄 CSV 파일\n인코딩 변환 / 컬럼 검증"]
    B -->|"Stage 1: 데이터 분할\ndata_splitting.py"| C["📦 배치 CSV들\n5,000건 단위 분할"]
    C -->|"Stage 2: API 동기화\nsync_address.py"| D["✅ final_address_N.csv\n변환 성공"]
    C -->|"Stage 2: API 동기화\nsync_address.py"| E["❌ error_address_N.csv\n변환 실패"]
    E --> F["✏️ 수동 주소 정제\n통/반·상세주소 제거"]
    F -->|"Stage 3: 에러 복구\nsync_error.py"| G["✅ post_final_N.csv\n복구 성공"]
    F -->|"Stage 3: 에러 복구\nsync_error.py"| H["❌ post_error_N.csv\n최종 실패"]
    G -->|"error_merge.py\nNaN 선택적 업데이트"| D
    D -->|"Stage 4: 최종 병합\nmerge.py"| I["🗂️ merged_N.csv\n원본 + 변환 결과"]
    I -->|"Stage 4: 최종 병합"| J["📋 final_merged_output.xlsx\n전체 배치 통합"]
    J -->|"Stage 5: 수동 검토\n2차 에러 복구"| K["🎯 완성 데이터\n전처리 정확도 100%"]
```

### 데이터 흐름도

```mermaid
flowchart LR
    subgraph Stage0["Stage 0"]
        A[Excel] -->|UTF-8 변환| B[CSV]
    end
    subgraph Stage1["Stage 1"]
        B -->|5,000건 단위 분할| C1[배치 1]
        B --> C2[배치 2]
        B --> CN[배치 N]
    end
    subgraph Stage2["Stage 2: API 동기화"]
        C1 --> D1[final_1.csv]
        C1 --> E1[error_1.csv]
        CN --> DN[final_N.csv]
        CN --> EN[error_N.csv]
    end
    subgraph Stage3["Stage 3: 에러 복구"]
        E1 -->|수동 정제 + sync_error.py| D1
        EN -->|수동 정제 + sync_error.py| DN
    end
    subgraph Stage4["Stage 4: 최종 병합"]
        D1 --> M1[merged_1.csv]
        DN --> MN[merged_N.csv]
        M1 --> FINAL[final_merged_output.xlsx]
        MN --> FINAL
    end
    subgraph Stage5["Stage 5: 수동 검토"]
        FINAL -->|NaN 값 수동 입력| DONE[완성 데이터]
    end
```

### 파일 구조

```
{YYYYMM}/
├── {batch_num}/
│   ├── {batch_num}.csv                    # 원본 배치 데이터
│   ├── final_address_{batch_num}.csv       # API 변환 성공 결과
│   ├── error_address_{batch_num}.csv       # 1차 실패 주소
│   ├── merged_{batch_num}.csv              # 원본 + 변환 결과 병합
│   └── post_error_{batch_num}/
│       ├── post_final_{batch_num}.csv      # 재처리 성공 결과
│       └── post_error_{batch_num}.csv      # 최종 실패 주소
└── final_merged_output.xlsx                # 최종 통합 결과
```

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

#### API 에러 핸들링 흐름

```mermaid
flowchart TD
    A[API 호출 시작] --> B{HTTP 200?}
    B -->|Yes| C{"errorCode == '0'\n& juso 결과 존재?"}
    B -->|No| D[HTTP 에러 로깅]
    C -->|Yes| E[✅ 결과 반환\n시/도, 시/군/구, 읍/면/동]
    C -->|No| F[API 에러 로깅]
    D --> G{attempt < retries - 1?}
    F --> G
    G -->|Yes| H[3초 대기 후 재시도]
    H --> A
    G -->|No| I[❌ None 반환\n에러 기록]
```

#### 기술적 의사결정

| 설정값 | 선택 근거 |
|--------|----------|
| `retries=3` | 일시적 네트워크 오류 대응. 3회 이상은 영구적 실패로 판단 |
| `delay=3` | API 서버 부하 방지 및 Rate Limit 회피 |
| `timeout=50` | 대용량 요청 시 응답 지연 고려 |
| `hstryYn="Y"` | 폐지된 주소도 검색하여 변환 성공률 향상 |

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

**5,000건 선택 이유:**
- **병렬 작업 흐름 확보**: API 호출 1건당 약 0.3~0.5초 소요 → 5,000건 처리 시 약 25~40분. 이 시간 동안 이전 배치의 수동 오류 정제 작업을 병행할 수 있어, 자동 처리와 수기 정제가 동시에 진행되는 워크플로우 설계 가능
- **장애 복구 비용 최소화**: 네트워크 불안정 발생 시 최대 손실 범위를 약 33분(5,000건 재처리)으로 제한
- 중간 결과물 저장으로 진행 상황 추적 용이

#### 배치 병합 흐름

```mermaid
flowchart LR
    subgraph col_merge["열 방향 병합 (배치별)"]
        direction TB
        df1["원본 배치\n연번 | n_addr"]
        df2["API 결과\n시/도 | 시/군/구 | 읍/면/동"]
        df1 -->|"pd.concat(axis=1)"| dfm["merged_N.csv"]
        df2 --> dfm
    end
    subgraph row_merge["행 방향 병합 (전체 통합)"]
        direction TB
        m1[merged_1.csv]
        m2[merged_2.csv]
        mn[merged_N.csv]
        m1 -->|"pd.concat(ignore_index=True)"| final[final_merged_output.xlsx]
        m2 --> final
        mn --> final
    end
    col_merge --> row_merge
```

---

### 3. 에러 복구 시스템

에러 복구는 총 2회에 걸쳐 수행됩니다.

```mermaid
flowchart TD
    A["Stage 2: sync_address.py\n1차 API 처리"] -->|성공| B[final_address_N.csv]
    A -->|실패| C[error_address_N.csv]
    C --> D["✏️ 수동 주소 정제\n통/반, 상세주소 제거"]
    D -->|"Stage 3: sync_error.py\n2차 API 처리"| E[post_final_N.csv]
    D -->|"Stage 3: sync_error.py\n2차 API 처리"| F[post_error_N.csv]
    E -->|"error_merge.py\nNaN 선택적 업데이트"| B
    B -->|Stage 4| G[final_merged_output.xlsx]
    G --> H{"NaN 값\n존재?"}
    H -->|Yes| I["Stage 5: 수동 검토\n주소정보누리집 검색\n폐지된 주소 포함 옵션"]
    H -->|No| J[✅ 완성 데이터]
    I --> J
```

#### 흐름 설명

**1차 처리 (Stage 2):** `sync_address.py`가 원본 배치 데이터를 Juso API로 처리합니다. 성공한 주소는 `final_address_N.csv`에 저장되고, 실패한 주소는 `error_address_N.csv`로 분리됩니다.

**수동 정제 개입:** 자동 분류된 실패 주소를 사람이 직접 검토하여 API 오류의 원인(통/반 정보 잔존, 상세주소·호수 포함 등)을 제거합니다. 자동화로 해결하기 어려운 비정형 패턴을 이 단계에서 처리합니다.

**2차 처리 (Stage 3):** `sync_error.py`가 정제된 주소를 재처리합니다. 복구에 성공한 주소는 `post_final_N.csv`에, 여전히 실패한 주소는 `post_error_N.csv`(NaN 처리)에 저장됩니다.

**결과 병합:** `error_merge.py`가 `post_final_N.csv`의 성공 결과를 `final_address_N.csv`의 NaN 행에 선택적으로 업데이트합니다. 이미 성공한 데이터는 덮어쓰지 않도록 `pd.isna()` 체크를 통해 보호합니다.

**최종 검토 (Stage 5):** 2단계 에러 복구를 거친 이후에도 NaN으로 남은 주소는 대부분 **폐지된 주소**입니다. 폐지된 주소는 Juso API로 조회가 불가능하기 때문에, 주소정보누리집에서 "폐지된 주소 정보 포함" 옵션을 적용하여 수동으로 검색하고, 담당자가 직접 행정구역 정보를 확인하여 입력합니다.

#### 주소 변환 실패 유형 및 수동 처리 전략

| 유형 | 실패 원인 | 원본 주소 예시 | 정제 후 주소 |
|------|----------|---------------|-------------|
| 폐지된 주소 | 도로명 변경/폐지 | 부산광역시 동래구 쇠미로 95 | 주소정보누리집에서 "폐지된 주소 정보 포함" 체크 후 검색 |
| 상세주소 포함 | 건물명/층/호수 잔존 | 부산광역시 동구 홍곡남로 6 동신탕 3층 | 부산광역시 동구 홍곡남로 6 |
| 정규식 처리 오류 | 숫자 패턴 오분류 | 부산광역시 해운대구 센텀3로 26 3009호 | 부산광역시 해운대구 센텀3로 26 |
| 통/반 정보 포함 | 행정 단위 잔존 | 부산광역시 사상구 백양대로433번길 9 7통 4반 | 부산광역시 사상구 백양대로433번길 9 |

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
                "Index": df.loc[idx, "Index"],
                "시/도": None, "시/군/구": None, "읍/면/동": None,
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

---

## 기술적 의사결정 및 근거

### 1. 배치 크기 선정 (5,000건)

**문제 상황:**
- 전체 데이터셋: 80만 건
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
- **80만 건** 코로나19 환자 주소 데이터 전처리 완료 및 행정구역 정보(시/도, 시/군/구, 읍/면/동) 표준화
- **전처리 정확도 100% 달성**: API 자동 처리 + Human-In-The-Loop 2단계 에러 복구 병행
- **업무 프로세스 표준화**: 파이프라인 구축 및 팀 활용 가이드 제공으로 반복 업무의 일관된 처리 체계 확립

### 기술적 성장
- REST API 통합 및 에러 핸들링 패턴 습득
- 대용량 데이터 파이프라인 설계 경험
- Python 데이터 처리 라이브러리 활용 능력 향상
- 팀 협업을 위한 기술 가이드라인 작성 및 배포 경험
