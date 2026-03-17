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
ENGINE_URL  = "https://github.com/zacxyonly/SimpleContext/archive/refs/heads/main.zip"
AGENTS_URL  = "https://github.com/zacxyonly/SimpleContext-Agents/archive/refs/heads/main.zip"
PLUGINS_URL = "https://github.com/zacxyonly/SimpleContext-Plugin/archive/refs/heads/main.zip"

# Registry plugin resmi
OFFICIAL_PLUGINS = {
    "vector-search": {
        "label":       "Vector Search",
        "description": "Semantic similarity search — temukan memory berdasarkan makna, bukan kata persis",
        "file":        "vector_search_plugin.py",
        "source_path": "official/plugin-vector-search/vector_search_plugin.py",
        "config": {
            "provider":         "local",
            "top_k":            5,
            "min_score":        0.15,
            "inject_as_system": True,
            "tiers":            ["semantic", "episodic"],
        },
    },
    "analytics": {
        "label":       "Analytics",
        "description": "Usage analytics — statistik pesan, agent, dan aktivitas per user",
        "file":        "analytics_plugin.py",
        "source_path": "official/plugin-analytics/analytics_plugin.py",
        "config":      {"track_agents": True, "track_hours": True, "retention_days": 30},
    },
    "summarizer": {
        "label":       "Summarizer",
        "description": "Ringkasan otomatis percakapan ke episodic memory via LLM",
        "file":        "summarizer_plugin.py",
        "source_path": "official/plugin-summarizer/summarizer_plugin.py",
        "config":      {"threshold": 20, "keep_last": 5, "language": "auto", "max_tokens": 300},
    },
    "web-search": {
        "label":       "Web Search",
        "description": "Pencarian internet real-time — DuckDuckGo (free), Bing, Google",
        "file":        "web_search_plugin.py",
        "source_path": "official/plugin-web-search/web_search_plugin.py",
        "config":      {"provider": "duckduckgo", "max_results": 3, "auto_search": True, "cache_ttl": 300},
    },
    "translate": {
        "label":       "Translate",
        "description": "Penerjemah multi-bahasa — auto-detect bahasa user, 20+ bahasa",
        "file":        "translate_plugin.py",
        "source_path": "official/plugin-translate/translate_plugin.py",
        "config":      {"provider": "llm", "agent_language": "en", "auto_detect": True},
    },
    "sentiment": {
        "label":       "Sentiment",
        "description": "Analisis sentimen user — adaptasi tone agent saat frustrasi",
        "file":        "sentiment_plugin.py",
        "source_path": "official/plugin-sentiment/sentiment_plugin.py",
        "config":      {"negative_threshold": -0.3, "inject_on_negative": True, "window_messages": 5},
    },
    "rate-limiter": {
        "label":       "Rate Limiter",
        "description": "Batasi request per jam/hari, estimasi token dan biaya",
        "file":        "rate_limiter_plugin.py",
        "source_path": "official/plugin-rate-limiter/rate_limiter_plugin.py",
        "config":      {"requests_per_hour": 20, "requests_per_day": 100, "estimate_tokens": True},
    },
}


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


def install_plugin(install_dir: Path, plugin_id: str) -> bool:
    """
    Download dan install satu plugin dari SimpleContext-Plugin registry.
    Salin file .py plugin ke install_dir/plugins/.
    """
    plugin_info = OFFICIAL_PLUGINS.get(plugin_id)
    if not plugin_info:
        print(f"  ❌ Plugin '{plugin_id}' tidak ada di registry.")
        return False

    plugins_dir = install_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    zip_path = install_dir / "_plugins.zip"
    if not zip_path.exists():
        if not download_file(PLUGINS_URL, zip_path, "SimpleContext-Plugin registry"):
            return False

    print(f"  📦 Installing {plugin_info['label']}...", end="", flush=True)
    try:
        tmp_dir = install_dir / "_tmp_plugins"
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        extracted_roots = list(tmp_dir.iterdir())
        if not extracted_roots:
            print(" ❌ Empty archive")
            return False

        source = extracted_roots[0] / plugin_info["source_path"]
        if not source.exists():
            print(f" ❌ File tidak ditemukan: {plugin_info['source_path']}")
            return False

        dest = plugins_dir / plugin_info["file"]
        import shutil as _sh
        _sh.copy2(source, dest)
        print(" ✅")
        return True

    except Exception as e:
        print(f" ❌ {e}")
        return False
    finally:
        if (install_dir / "_tmp_plugins").exists():
            import shutil as _sh
            _sh.rmtree(install_dir / "_tmp_plugins")
        # Hapus zip hanya setelah semua plugin selesai di-install
        # (dipanggil oleh install_selected_plugins)


def install_selected_plugins(install_dir: Path, plugin_ids: list[str]) -> dict[str, bool]:
    """
    Install beberapa plugin sekaligus. Hanya download zip sekali.
    Return: {plugin_id: success}
    """
    if not plugin_ids:
        return {}

    results = {}
    zip_path = install_dir / "_plugins.zip"

    # Download zip plugin registry sekali saja
    if not zip_path.exists():
        if not download_file(PLUGINS_URL, zip_path, "SimpleContext-Plugin registry"):
            return {pid: False for pid in plugin_ids}

    for pid in plugin_ids:
        results[pid] = install_plugin(install_dir, pid)

    # Cleanup zip setelah semua selesai
    if zip_path.exists():
        zip_path.unlink()

    return results


def check_plugin(install_dir: Path, plugin_id: str) -> bool:
    """Cek apakah plugin sudah terinstall."""
    plugin_info = OFFICIAL_PLUGINS.get(plugin_id)
    if not plugin_info:
        return False
    plugin_file = install_dir / "plugins" / plugin_info["file"]
    return plugin_file.exists()


def get_installed_plugins(install_dir: Path) -> list[str]:
    """Return daftar plugin_id yang sudah terinstall."""
    installed = []
    for pid, info in OFFICIAL_PLUGINS.items():
        if (install_dir / "plugins" / info["file"]).exists():
            installed.append(pid)
    return installed


def get_plugin_config(plugin_id: str) -> dict:
    """Return default config untuk plugin tertentu."""
    return OFFICIAL_PLUGINS.get(plugin_id, {}).get("config", {})


# ── Registry URL untuk fetch plugin list dinamis ──────────────────────────────
PLUGIN_REGISTRY_URL = "https://raw.githubusercontent.com/zacxyonly/SimpleContext-Plugin/main/official"
PLUGIN_INDEX_URL    = "https://api.github.com/repos/zacxyonly/SimpleContext-Plugin/contents/official"


def fetch_available_plugins() -> dict[str, dict]:
    """
    Fetch daftar plugin yang tersedia dari GitHub repo SimpleContext-Plugin.
    Scan folder official/ via GitHub API, baca metadata dari setiap plugin .py.
    Fallback ke OFFICIAL_PLUGINS jika tidak ada koneksi.
    Return: { "plugin-name": {"label", "description", "file", "source_path", "config"} }
    """
    import urllib.request
    import urllib.error
    import json as _json

    try:
        req  = urllib.request.Request(
            PLUGIN_INDEX_URL,
            headers={"Accept": "application/vnd.github.v3+json",
                     "User-Agent": "SimpleContext-Bot/1.3"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            contents = _json.loads(resp.read())

        plugins = {}
        for item in contents:
            if item["type"] != "dir" or not item["name"].startswith("plugin-"):
                continue

            folder    = item["name"]
            plugin_id = folder[len("plugin-"):]  # "plugin-vector-search" → "vector-search"

            # Cek apakah ada entry di OFFICIAL_PLUGINS (metadata lokal lebih lengkap)
            if plugin_id in OFFICIAL_PLUGINS:
                plugins[plugin_id] = OFFICIAL_PLUGINS[plugin_id]
                continue

            # Plugin baru yang belum di OFFICIAL_PLUGINS — buat entry minimal
            plugins[plugin_id] = {
                "label":       folder,
                "description": f"Plugin from SimpleContext-Plugin ({folder})",
                "file":        f"{plugin_id.replace('-', '_')}_plugin.py",
                "source_path": f"official/{folder}/{plugin_id.replace('-', '_')}_plugin.py",
                "config":      {},
            }

        return plugins if plugins else OFFICIAL_PLUGINS

    except Exception as e:
        # Fallback ke registry lokal jika tidak ada koneksi
        return OFFICIAL_PLUGINS


def update_plugins(install_dir: Path) -> bool:
    """Update semua plugin yang sudah terinstall ke versi terbaru."""
    from . import config as cfg
    installed_ids = cfg.get("plugins.installed", [])
    if not installed_ids:
        print("  ℹ️  No plugins installed to update.")
        return True

    print(f"  🔄 Updating {len(installed_ids)} plugin(s)...")
    results = install_selected_plugins(install_dir, installed_ids)
    ok = all(results.values())
    for pid, success in results.items():
        label = OFFICIAL_PLUGINS.get(pid, {}).get("label", pid)
        print(f"  {'✅' if success else '❌'} {label}")
    return ok
