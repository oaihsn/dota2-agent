import pyautogui
import time

# Небольшая задержка перед стартом (чтобы успеть переключиться в нужное окно)
time.sleep(3)

while True:
    # Зажимаем ЛКМ на 0.5 секунды
    pyautogui.mouseDown(button='left')
    time.sleep(0.35)
    pyautogui.mouseUp(button='left')
    
    time.sleep(1)
    
    # Очень быстро кликаем 50 раз
    for _ in range(15):
        pyautogui.click(button='left')
    
    # Небольшая пауза между циклами (можно убрать или изменить)
    time.sleep(1)
