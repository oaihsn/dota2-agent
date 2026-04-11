import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 1. Загрузка данных
def train_brain():
    df = pd.read_csv('dota_cleaned_data.csv')
    
    # Входные данные (X): координаты 4 врагов (8 чисел)
    # Выходные данные (y): мы будем учить модель предсказывать те же координаты на следующий шаг
    # (Это простая модель автоэнкодера/предиктора для теста)
    X = df[['e1x', 'e1y', 'e2x', 'e2y', 'e3x', 'e3y', 'e4x', 'e4y']].values
    y = X.copy() # В этой версии учим модель просто "понимать" структуру позиций

    # Масштабирование (нормализация данных от 0 до 1)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Конвертация в тензоры PyTorch
    X_train = torch.FloatTensor(X_train)
    y_train = torch.FloatTensor(y_train)
    X_test = torch.FloatTensor(X_test)
    y_test = torch.FloatTensor(y_test)

    # 2. Архитектура нейросети
    class DotaBrain(nn.Module):
        def __init__(self):
            super(DotaBrain, self).__init__()
            self.net = nn.Sequential(
                nn.Linear(8, 64),  # Вход: 8 координат
                nn.ReLU(),
                nn.Linear(64, 32), # Скрытый слой
                nn.ReLU(),
                nn.Linear(32, 8)   # Выход: 8 предсказанных координат
            )

        def forward(self, x):
            return self.net(x)

    model = DotaBrain()
    criterion = nn.MSELoss() # Среднеквадратичная ошибка
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 3. Цикл обучения
    print("Начинаю обучение...")
    epochs = 100
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()
        
        if (epoch+1) % 10 == 0:
            print(f'Эпоха [{epoch+1}/{epochs}], Ошибка: {loss.item():.4f}')

    # 4. Сохранение модели и скалера
    torch.save(model.state_dict(), 'dota_model.pth')
    # Сохраняем параметры скалера, чтобы потом правильно обрабатывать новые данные
    import joblib
    joblib.dump(scaler, 'scaler.pkg')
    
    print("--- ОБУЧЕНИЕ ЗАВЕРШЕНО ---")
    print("Модель сохранена в dota_model.pth")

if __name__ == "__main__":
    train_brain()