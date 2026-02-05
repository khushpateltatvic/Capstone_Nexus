try:
    print("Attempting to import app.main...")
    from app.main import app
    print("Success! App imported.")
except Exception as e:
    print(f"FAILED with Exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
except BaseException as e:
    print(f"FAILED with BaseException: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
