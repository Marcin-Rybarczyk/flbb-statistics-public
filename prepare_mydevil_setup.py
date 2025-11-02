import os
import re
from pathlib import Path

# === CONFIG ===
SRC_DIR = Path("src")
MAIN_APP_FILE = SRC_DIR / "app.py"
WSGI_FILE = Path("wsgi.py")
REQUIREMENTS_FILE = Path("requirements.txt")
ENV_FILE = Path(".env.example")

# === UTILITIES ===
def ensure_init_files(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            path = Path(root) / d
            init_file = path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"✅ Added {init_file}")

def fix_relative_imports(base_dir):
    """Convert relative imports like from .utils import X → from src.utils import X"""
    for py_file in base_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        text = py_file.read_text(encoding="utf-8")
        new_text = re.sub(r"from\s+\.(\S+)", r"from src.\1", text)
        if text != new_text:
            py_file.write_text(new_text, encoding="utf-8")
            print(f"🔧 Fixed relative imports in {py_file}")

def create_wsgi():
    if WSGI_FILE.exists():
        print(f"ℹ️ {WSGI_FILE} already exists — skipping")
        return
    content = (
        "from src.app import app as application\n"
        "\n"
        "# MyDevil WSGI entrypoint\n"
        "# You can restart the app using:\n"
        "#   touch tmp/restart.txt\n"
    )
    WSGI_FILE.write_text(content, encoding="utf-8")
    print(f"✅ Created {WSGI_FILE}")

def ensure_requirements():
    if not REQUIREMENTS_FILE.exists():
        REQUIREMENTS_FILE.write_text("Flask==3.1.2\ngunicorn==23.0.0\n", encoding="utf-8")
        print("✅ Created minimal requirements.txt")
    else:
        text = REQUIREMENTS_FILE.read_text()
        missing = []
        for pkg in ["Flask", "gunicorn"]:
            if pkg.lower() not in text.lower():
                missing.append(pkg)
        if missing:
            with open(REQUIREMENTS_FILE, "a", encoding="utf-8") as f:
                for pkg in missing:
                    f.write(f"{pkg}\n")
            print(f"🔧 Added missing packages: {', '.join(missing)}")
        else:
            print("✅ requirements.txt already contains Flask & gunicorn")

def create_env_example():
    if ENV_FILE.exists():
        print(f"ℹ️ {ENV_FILE} already exists — skipping")
        return
    ENV_FILE.write_text(
        "FLASK_ENV=production\n"
        "DEBUG=False\n"
        "# Add your environment variables here\n"
    )
    print(f"✅ Created {ENV_FILE}")

def main():
    print("🚀 Preparing Flask app for MyDevil.net deployment...\n")
    if not MAIN_APP_FILE.exists():
        print(f"❌ ERROR: {MAIN_APP_FILE} not found. Please check SRC_DIR.")
        return

    ensure_init_files(SRC_DIR)
    fix_relative_imports(SRC_DIR)
    create_wsgi()
    ensure_requirements()
    create_env_example()

    print("\n🎉 Done! Your project is ready for MyDevil deployment.\n")
    print("👉 Next steps on MyDevil:")
    print("1. SSH into your account:")
    print("   ssh yourlogin@server.mydevil.net")
    print("2. Create a virtual environment:")
    print("   python3.11 -m venv ~/flaskenv && source ~/flaskenv/bin/activate")
    print("3. Upload your project (via git or sftp).")
    print("4. Install requirements:")
    print("   pip install -r requirements.txt")
    print("5. Add webapp in panel or SSH:")
    print("   devil www add myflaskapp python3.11 ~/path/to/wsgi.py")
    print("6. Restart the app if needed:")
    print("   touch tmp/restart.txt\n")
    print("🌍 Once done, access it via:")
    print("   https://myflaskapp.YOURUSERNAME.mydevil.net\n")

if __name__ == "__main__":
    main()
