import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
    # Пробуем создать тензор и умножить его на GPU
    try:
        a = torch.ones(3, 3).cuda()
        b = a @ a
        print("GPU Computation: SUCCESS!")
    except Exception as e:
        print(f"GPU Computation FAILED: {e}")