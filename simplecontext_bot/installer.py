"""
installer.py — Download dan install SimpleContext engine + agents
dari GitHub secara otomatis.
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import urllib.error
from pathlib import Path

# GitHub release URLs
ENGINE_URL = "https://github.com/zacxyonly/SimpleContext/archive/refs/heads/main.zip"
AGENTS_URL = "https://github.com/zacxyonly/SimpleContext-Agents/archive/refs/heads/main.zip"


def download_file(url: str, dest: Path, label: str = ""):
    """Download file dari URL dengan progress indicator."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    label = label or url.split("/")[-1]

    print(f"  ⬇️  Downloading {label}...", end="", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print(" ✅")
        return True
    except urllib.error.URLError as e:
        print(f" ❌ Failed: {e}")
        return False
    except Exception as e:
        print(f" ❌ Error: {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path, subfolder: str = ""):
    """Extract ZIP dan pindahkan konten ke target directory."""
    extract_to.mkdir(parents=True, exist_ok=True)
    tmp_dir = zip_path.parent / "_tmp_extract"

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        # Cari subfolder (biasanya nama-repo-main/)
        extracted = list(tmp_dir.iterdir())
        if not extracted:
            return False

        source = extracted[0]
        if subfolder:
            source = source / subfolder

        if not source.exists():
            return False

        # Copy ke target
        if extract_to.exists():
            shutil.rmtree(extract_to)
        shutil.copytree(source, extract_to)
        return True

    finally:
        # Cleanup
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        if zip_path.exists():
            zip_path.unlink()


def install_engine(install_dir: Path) -> bool:
    """
    Download dan install SimpleContext engine.
    Extract hanya folder simplecontext/ ke install_dir/simplecontext/
    """
    engine_dir = install_dir / "simplecontext"
    zip_path   = install_dir / "_engine.zip"

    install_dir.mkdir(parents=True, exist_ok=True)

    if not download_file(ENGINE_URL, zip_path, "SimpleContext engine"):
        return False

    print(f"  📦 Installing engine to {engine_dir}...", end="", flush=True)
    try:
        tmp_dir = install_dir / "_tmp_engine"
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        # Cari SimpleContext-main/simplecontext/
        extracted_roots = list(tmp_dir.iterdir())
        if not extracted_roots:
            print(" ❌ Empty archive")
            return False

        source = extracted_roots[0] / "simplecontext"
        if not source.exists():
            print(" ❌ simplecontext/ folder not found in archive")
            return False

        if engine_dir.exists():
            shutil.rmtree(engine_dir)
        shutil.copytree(source, engine_dir)

        print(" ✅")
        return True

    except Exception as e:
        print(f" ❌ {e}")
        return False
    finally:
        if (install_dir / "_tmp_engine").exists():
            shutil.rmtree(install_dir / "_tmp_engine")
        if zip_path.exists():
            zip_path.unlink()


def install_agents(install_dir: Path) -> bool:
    """
    Download dan install agent YAML dari SimpleContext-Agents.
    Extract folder agents/ ke install_dir/agents/
    """
    agents_dir = install_dir / "agents"
    zip_path   = install_dir / "_agents.zip"

    if not download_file(AGENTS_URL, zip_path, "SimpleContext-Agents"):
        return False

    print(f"  📦 Installing agents to {agents_dir}...", end="", flush=True)
    try:
        tmp_dir = install_dir / "_tmp_agents"
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        extracted_roots = list(tmp_dir.iterdir())
        if not extracted_roots:
            print(" ❌ Empty archive")
            return False

        source = extracted_roots[0] / "agents"
        if not source.exists():
            print(" ❌ agents/ folder not found in archive")
            return False

        if agents_dir.exists():
            shutil.rmtree(agents_dir)
        shutil.copytree(source, agents_dir)

        agent_count = len(list(agents_dir.glob("*.yaml")))
        print(f" ✅ ({agent_count} agents)")
        return True

    except Exception as e:
        print(f" ❌ {e}")
        return False
    finally:
        if (install_dir / "_tmp_agents").exists():
            shutil.rmtree(install_dir / "_tmp_agents")
        if zip_path.exists():
            zip_path.unlink()


def update_engine(install_dir: Path) -> bool:
    """Update SimpleContext engine ke versi terbaru."""
    print("🔄 Updating SimpleContext engine...")
    return install_engine(install_dir)


def update_agents(install_dir: Path) -> bool:
    """Update agents ke versi terbaru."""
    print("🔄 Updating agents...")
    return install_agents(install_dir)


def check_engine(install_dir: Path) -> bool:
    """Cek apakah engine sudah terinstall."""
    engine_dir = install_dir / "simplecontext"
    return (engine_dir / "__init__.py").exists()


def check_agents(install_dir: Path) -> bool:
    """Cek apakah agents sudah terinstall."""
    agents_dir = install_dir / "agents"
    return agents_dir.exists() and len(list(agents_dir.glob("*.yaml"))) > 0


def get_installed_agents(install_dir: Path) -> list[str]:
    """Return daftar nama agent yang terinstall."""
    agents_dir = install_dir / "agents"
    if not agents_dir.exists():
        return []
    return [f.stem for f in agents_dir.glob("*.yaml")]
