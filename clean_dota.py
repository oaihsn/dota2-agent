import pandas as pd
import os

def clean_dota_data(input_file='dota_training_dataa.csv', output_file='dota_cleaned_data.csv'):
    if not os.path.exists(input_file):
        print("Файл не найден!")
        return

    # Загружаем данные
    cols = ['ts', 'e1x', 'e1y', 'e2x', 'e2y', 'e3x', 'e3y', 'e4x', 'e4y']
    df = pd.read_csv(input_file, names=cols, header=0)

    # 1. Удаляем строки, где все координаты = 0 (нет врагов)
    coord_cols = ['e1x', 'e1y', 'e2x', 'e2y', 'e3x', 'e3y', 'e4x', 'e4y']
    df = df[(df[coord_cols] != 0).any(axis=1)]

    # 2. Удаляем дубликаты (если данные не менялись, значит игра стояла на паузе)
    df = df.drop_duplicates(subset=coord_cols)

    # 3. Сохраняем
    df.to_csv(output_file, index=False)
    
    print(f"--- ОЧИСТКА ЗАВЕРШЕНА ---")
    print(f"Строк до: {len(pd.read_csv(input_file))}")
    print(f"Строк после: {len(df)}")
    print(f"Чистый файл: {output_file}")

if __name__ == "__main__":
    clean_dota_data()