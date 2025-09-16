from app.ui import RecorderApp, AppConfig

def main():
    cfg = AppConfig()
    app = RecorderApp(cfg)
    app.mainloop()

if __name__ == "__main__":
    main()
