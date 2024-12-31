import pandas as pd
import os

# 원본 데이터 파일 경로
file_path = "./202202.csv"

# 저장할 폴더 경로
output_folder = "./202202"

# 배치 크기 설정
BATCH_SIZE = 10000

# 폴더 생성
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 데이터 분할 및 저장
df = pd.read_csv(file_path, index_col=0)

# batch_size 만큼의 배치가 총 몇개 필요한지를 계산하는 로직
total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE

# enumerate()의 start=1 옵션을 사용하여 1부터 시작하는 인덱스를 사용함 -> batch_num
# range() 함수를 사용하여 BATCH_SIZE 만큼 데이터를 끊었을때의 시작점을 불러옴 -> start
# 만약 BATCH_SIZE ==10000이면, start 는 0, 10000, 20000, 30000, ... 이런식으로 불러옴
for batch_num, start in enumerate(range(0, len(df), BATCH_SIZE), start=1):
    batch_df = df.iloc[start : start + BATCH_SIZE] # start 부터 start부터 start+ BATCH_SIZE-1 번쨰의 데이터까지 불러옴
    folder_path = os.path.join(output_folder, str(batch_num))
    os.makedirs(folder_path, exist_ok=True)  # 폴더 생성
    batch_df.to_csv(os.path.join(folder_path, f"{batch_num}.csv"), index=True)
    print(f"Saved batch {batch_num}.csv to {folder_path}")
