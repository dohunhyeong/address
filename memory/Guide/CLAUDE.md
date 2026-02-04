# 🌅 Address_API_guide

# API 변환 가이드

한국 주소기반산업지원서비스 API를 활용하여 도로명 주소를 시/도, 시/군/구, 읍/면/동 정보로 변환하는 방법을 단계별로 안내합니다.

---

## 1. 설치

### 1-1 VScode 설치 (설치되어있다면 pass)

- [VScode 다운로드 링크](https://code.visualstudio.com/)

> 💡 **그림 설명**  
> VSCode 공식 웹사이트에서 운영체제에 맞는 버전을 다운로드하여 설치합니다.

---

## 2. API KEY 신청

### 2-1 주소기반산업지원서비스 접속

- [주소기반산업지원서비스](https://business.juso.go.kr/addrlink/main.do)

### 2-2 API 신청

1. 상단 배너의 **기술제공 - API 신청** 클릭

### 2-3 API 신청 및 API 키 발급

- 위에 보이는 사진처럼만 작성하고 **신청하기** 클릭
- URL 부분은 학교 홈페이지 URL을 넣으면 됩니다
  - 예: [https://www.pknu.ac.kr/main](https://www.pknu.ac.kr/main)

---

## 3. VScode 실행 및 Extension 설치

### 3-1 GitHub 레파지토리 클론 해오기

- 레파지토리 주소: [https://github.com/dohunhyeong/address](https://github.com/dohunhyeong/address)

**절차:**

1. VS code 열고 왼쪽 사이드바의 소스 컨트롤 아이콘 클릭
2. **Clone Repository** 클릭
3. [https://github.com/dohunhyeong/address](https://github.com/dohunhyeong/address) ← 여기 링크의 URL을 복사해서 붙여넣기

### 3-2 Extension 설치

> ⚠️ **설치해야할 Extension:**
> - Python
> - Rainbow CSV
> - Code Runner
> - Excel Viewer
> - Jupyter Notebook

---

## 4. 가상환경 생성 및 개발파일 세팅

### 4-1 PowerShell 터미널 실행

- **Terminal - New Terminal** 클릭
- 단축키: `Ctrl + Shift + `` ` ``

### 4-2 가상환경 세팅

```powershell
# 가상환경 생성
python -m venv "가상환경 이름"

# 예시
python -m venv address_env
```

### 4-3 가상환경 활성화 및 필요한 패키지 다운로드

```powershell
# 아래의 1,2를 순서대로 실행

# 1. 가상환경 활성화
가상환경이름\Scripts\Activate

## 예시
address_env\Scripts\Activate

# 2. 활성화된 가상환경에 패키지 다운로드
pip install requests pandas numpy python-dotenv openpyxl

# 2-2. 두번 나눠서 다운로드 (한번에 다운하고 싶으면 하셔도 됩니다.)
pip install notebook ipykernel tqdm
```

### 4-4 .env 파일 생성

- 주소 API 신청 사이트에서 API_KEY를 받아와서 "API 입력" 부분에 그대로 적어넣기

```plaintext
ADDRESS_API_KEY = API 입력
```

> 💡 **참고:** 실제 API key 입력할 때 따옴표 없이 그대로 적어넣으면 됩니다.

---

## 5. 엑셀을 CSV로 변환

### 5-1 본인이 변환해야 할 엑셀 파일을 폴더에 업로드

### 5-2 preprocessing.ipynb 파일을 열고 실행해서 Excel 파일을 CSV 파일로 변환

### 5-3 CSV 파일을 읽어와서 잘 처리가 되었는지 확인해보기

---

## 6. 주소 변환

### 6-1 PowerShell 터미널 실행

- 단축키: `Ctrl + Shift + `` ` ``

### 6-2 가상환경 활성화

```powershell
가상환경이름\Scripts\Activate
```

### 6-3 데이터 쪼개기

#### 3-1 data_splitting.py 세팅

- **batch size 설정:** `data_splitting.py` 파일에서 batch_size를 설정
- batch_size = 10000 이면, 10000개씩 쪼갠다는 의미 (본인이 원하는 만큼 설정 가능)
- batch_size는 **5000개 또는 10000개**로 하는 것을 추천
  - 한번에 많은 양을 변환하다보면 네트워크 오류가 발생해서 처리 과정에서 문제가 생길 수 있음

#### 3-2 폴더명 지정

- 자신이 처리하고자 하는 데이터의 연도(예: 202201, 202205)를 `file_path`, `output_folder`에 입력

#### 3-3 터미널 창에서 data_splitting.py 파일 실행

> ⚠️ 실행 전, 가상환경 활성화!

```powershell
python data_splitting.py
```

#### 3-4 실행 결과

- `202201.csv` 파일이 batch_size 만큼 쪼개져서 생성됨
- 예: `202201/1/1.csv`, `202201/2/2.csv`, `202201/3/3.csv` 세 개의 파일들이 생성됨

### 6-4 주소 변환

터미널 창에서 `sync_address.py` 실행:

```powershell
python sync_address.py
```

1. `data_splitting.py` 파일에 적어놓은 `output_folder`의 번호를 입력
2. 배치 단위로 쪼개 놓은 폴더 중 몇 번째 파일을 변환할 것인지 입력
3. 변환이 완료될 때까지 기다리기

---

## 7. error_address_*.csv 파일 확인 후, 올바른 도로명 주소 양식으로 변환

### 올바른 도로명 주소의 예시

도로명주소가 [주소정보누리집](https://www.juso.go.kr/openIndexPage.do)에서 제대로 검색되기 위해서는 올바른 도로명 주소 양식으로 입력을 해주어야 합니다.

#### ✅ 올바른 도로명 주소 예시

**예시 1:** 부산광역시 동래구 충렬대로107번길 54
- 시/도: 부산광역시
- 시/군/구: 동래구
- 도로명: 충렬대로107번길
- 건물번호: 54

**예시 2:** 부산광역시 서구 보수대로 155-1
- 시/도: 부산광역시
- 시/군/구: 서구
- 도로명: 보수대로
- 건물번호: 155-1

**예시 3:** 부산광역시 기장군 기장읍 기장대로 470
- 시/도: 부산광역시
- 시/군/구: 기장군
- 읍/면: 기장읍
- 도로명: 기장대로
- 건물번호: 470

**예시 4:** 경기도 성남시 분당구 돌마로 51
- 시/도: 경기도
- 시/군/구: 성남시 분당구
- 도로명: 돌마로
- 건물번호: 51

#### ❌ 올바르지 않은 도로명 주소 예시

"부산광역시 사상구 백양대로433번길 9 7통 4반"의 경우:
- 시/도: 부산광역시
- 시/군/구: 사상구
- 도로명: 백양대로433번길
- 건물번호: 9
- > ⚠️ **"7통 4반"은 도로명주소 양식에 맞지 않으니 제외**

**올바른 도로명 주소:** 부산광역시 사상구 백양대로433번길 9

### 수정 방법

1. **수정 전:** error_address_*.csv 파일 확인
2. **수정 후:** 올바른 도로명 주소 양식으로 수정

> ⚠️ **모든 error_address_*.csv 파일들에 대해서 수정!!**

---

## 8. 오류 수정 후 주소 재변환

### 8-1 sync_error.py 실행

올바른 도로명 주소로 변환한 `error_address_*.csv` 파일들의 주소들을 재변환합니다.

```powershell
python sync_error.py
```

변환이 완료되면 아래와 같은 결과가 생성됩니다:
- `202201/1` 폴더에 `post_error_1` 폴더가 생성
- `post_error_1` 폴더에 `post_final_1.csv`, `post_error_1.csv`가 생성

> 📌 **쪼개놓은 폴더 개수만큼 sync_error.py로 변환 실행**

### 변환 결과 설명

#### post_final_1.csv
- `error_address_1.csv` 파일에서 올바른 도로명 주소 양식으로만 변환시켜줬더니 재변환이 됨
- (도로명 주소 양식이 잘못되어서 변환이 안되었던 것)

#### post_error_1.csv
- 도로명 주소 양식을 올바르게 변환했는데도 처리가 되지 않은 주소들
- 폐지된 주소이거나 데이터 자체가 잘못 입력되었을 가능성이 높음
- 이러한 경우는 직접 검색해야 함

### 8-2 preprocessing.ipynb의 [2. Error 내용 수정] 부분 실행

- `post_final_1.csv`를 `final_address_1.csv`에 추가해주는 부분

> 📌 **쪼개놓은 파일 수만큼 반복을 해주어야 합니다**

---

## 9. 파일 병합

`data_splitting.py`로 쪼개서 변환을 하였기 때문에 쪼갠 데이터들을 병합해줘야 합니다.

### preprocessing.ipynb의 [3. 파일 병합] 부분 실행

- `file_path`만 본인이 처리한 폴더(예시: 202201)에 맞게끔 변경해주고 실행하면 됩니다.

```python
import pandas as pd
import os

# Base path
file_path = './202201/'
file_list = os.listdir(file_path)
merged_list = []

# Step 1: 기존 코드로 각 파일 병합
for file_name in file_list:
    b_path = os.path.join(file_path, file_name)
    original_csv_name = f'{file_name}.csv'
    completed_csv_name = f'final_address_{file_name}.csv'
    main_name = os.path.join(b_path, original_csv_name)
    after_name = os.path.join(b_path, completed_csv_name)
    
    if os.path.exists(main_name) and os.path.exists(after_name):
        try:
            df1 = pd.read_csv(main_name, low_memory=False)
            df2 = pd.read_csv(after_name, index_col=0)
            df_final = pd.concat([df1, df2], axis=1)
            merged_csv_name = os.path.join(b_path, f'merged_{file_name}.csv')
            df_final.to_csv(merged_csv_name, index=False)
            merged_list.append(merged_csv_name)
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    else:
        print(f"Files {main_name} or {after_name} do not exist.")

# Step 2: 병합된 파일들 로드 및 행 기준으로 통합
merged_dfs = []

for merged_csv in merged_list:
    try:
        df = pd.read_csv(merged_csv, low_memory=False)
        merged_dfs.append(df)
    except Exception as e:
        print(f"Error reading {merged_csv}: {e}")

# 모든 병합된 데이터프레임을 하나로 결합
final_merged_df = pd.concat(merged_dfs, ignore_index=True)

# Step 3: 엑셀 파일로 저장 (통합된 인덱스 사용)
output_excel_path = os.path.join(file_path, 'final_merged_output.xlsx')
final_merged_df.to_excel(output_excel_path, index=False)

print(f"Final merged Excel file saved at: {output_excel_path}")
```

실행 결과: `final_merged_output.xlsx` 파일이 생성됩니다.

---

## 10. 폐지된 주소, 마지막까지도 변환이 되지 않은 주소 처리(사람이 개입하여 직접 처리해야하는 부분)

시/도, 시/군/구, 읍/면/동 컬럼들을 확인하고 null 값이 있으면 해당 데이터의 `n_addr` 컬럼을 확인해서 올바른 도로명 주소로 바꾼 후 해당 주소를 [주소정보누리집](https://www.juso.go.kr/openIndexPage.do)에서 검색해서 알아내면 됩니다.

> ⚠️ **"폐지된 주소 정보 포함"에 체크!**

### 예시 1

**폐지된 주소 예시 : 부산광역시 동래구 쇠미로 95**

- 지번 주소 확인해서 시/도, 시/군/구, 읍/면/동 추출해서 엑셀 파일 속 null 값에 직접 입력
- 시/도: 부산광역시
- 시/군/구: 동래구
- 읍/면/동: 사직동

### 예시 2

1. 엑셀 파일의 null 값 확인
2. null 값이 존재하는 행의 `n_addr` 컬럼값(n_addr 컬럼값은 전처리를 실행하기 전의 해당 주소의 원본 주소 데이터를 나타내기 때문에 이 데이터를 검색에 활용합니다.) 확인해보기 - 부산광역시 동래구 쇠미로 95
3. 주소정보누리집 링크를 통해서 검색(폐지된 주소 검색 포함 부분을 체크하여 검색하면 폐지된 주소도 검색이 된다)
4. 지번주소 확인해서 "시/도", "시/군/구", "읍/면/동" 추출해서 엑셀 파일에 채워넣기

### 예시 3 - 상세주소가 입력된 경우의 처리방법

**상세주소가 입력된 경우 예시 : 부산광역시 동구 홍곡남로 6 동신탕 3층**

null 값이 발생한 이유는 "부산광역시 동구 홍곡남로 6 동신탕 3층"에서 "동신탕 3층"이 상세주소이기 때문입니다.

이러한 경우에는 상세주소 부분을 제외한 **"부산광역시 동구 홍곡남로 6"**을 주소정보누리집에 검색하고 검색결과의 지번주소를 받아오면 됩니다.

- 마찬가지로 지번주소의 내용들을 시/도, 시/군/구, 읍/면/동에 넣어주시면 됩니다.

### 예시 4 - 정규식 처리 오류


**정규식 처리 오류가 발생한 예시 : 부산광역시 해운대구 센텀3로 26 3009 3009호**

"3009"라는 숫자가 정규식 처리 과정에서 처리가 되지 않아서 추가되었고, "3009호"라는 상세주소가 처리되지 않아서 생긴 오류들입니다.

따라서 **"부산광역시 해운대구 센텀3로 26"**을 검색하면 됩니다.

---

## 📚 주요 링크 모음

| 링크 | 설명 |
|------|------|
| [VSCode](https://code.visualstudio.com/) | 개발 환경 설치 |
| [주소기반산업지원서비스](https://business.juso.go.kr/addrlink/main.do) | API KEY 신청 |
| [GitHub 레파지토리](https://github.com/dohunhyeong/address) | 소스 코드 |
| [주소정보누리집](https://www.juso.go.kr/openIndexPage.do) | 주소 검색 |

---

## 📦 필요 패키지

```
requests
pandas
numpy
python-dotenv
openpyxl
notebook
ipykernel
tqdm
```

---

## 🔑 핵심 파일 목록

| 파일명 | 용도 |
|--------|------|
| `preprocessing.ipynb` | Excel/CSV 변환 및 데이터 병합 |
| `data_splitting.py` | 대용량 데이터 배치 분할 |
| `sync_address.py` | 주소 API 변환 실행 |
| `sync_error.py` | 오류 주소 재변환 |
| `.env` | API 키 저장 |

---

## ⚠️ 주의사항

1. **batch_size**는 5000~10000개 권장 (네트워크 오류 방지)
2. **API KEY** 입력 시 따옴표 없이 입력
3. **도로명 주소 형식**이 올바르지 않으면 변환 실패
4. **"통/반", 상세주소**(층, 호수, 건물명 등)는 제거 후 변환 필요
5. 폐지된 주소 검색 시 **"폐지된 주소 정보 포함"** 체크 필수