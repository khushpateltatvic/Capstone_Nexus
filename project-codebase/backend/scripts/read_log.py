
import os

def read_log():
    try:
        with open('server.log', 'r', encoding='utf-16') as f:
            print(f.read())
    except Exception as e:
        print(f"UTF-16 failed: {e}")
        try:
            with open('server.log', 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e2:
            print(f"UTF-8 failed: {e2}")

if __name__ == "__main__":
    read_log()
