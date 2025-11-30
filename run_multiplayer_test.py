import subprocess
import sys
import time
import os

def main():
    # 获取当前 Python 解释器路径
    python_exe = sys.executable
    
    # 获取 main.py 的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(current_dir, "main.py")
    
    print(f"Starting Instance 1 (Host)...")
    # 启动第一个实例
    p1 = subprocess.Popen([python_exe, main_script], cwd=current_dir)
    
    # 等待几秒钟让第一个实例启动
    time.sleep(2)
    
    print(f"Starting Instance 2 (Client)...")
    # 启动第二个实例
    p2 = subprocess.Popen([python_exe, main_script], cwd=current_dir)
    
    print("Both instances started.")
    print("Please manually set one as Host (Create Room) and the other as Client (Join Room).")
    
    try:
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        print("Stopping instances...")
        p1.terminate()
        p2.terminate()

if __name__ == "__main__":
    main()
