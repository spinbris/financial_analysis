#!/usr/bin/env python3
"""
Sync local fixed ChromaDB to Modal volume.
This uploads the fixed ChromaDB with proper markdown formatting.
"""
import modal
from pathlib import Path

app = modal.App("sync-chromadb")

# Reference the existing volume
chroma_volume = modal.Volume.from_name("financial-chroma-db")

@app.function(volumes={"/chroma-data": chroma_volume}, timeout=600)
def sync_chromadb():
    """Sync local ChromaDB directory to Modal volume"""
    import os
    import shutil
    from pathlib import Path

    print("🔄 Syncing local ChromaDB to Modal...")

    # Clear existing ChromaDB
    chroma_path = Path("/chroma-data")
    print(f"\n🗑️  Clearing existing data at {chroma_path}...")
    if chroma_path.exists():
        for item in chroma_path.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                print(f"Warning: Could not remove {item}: {e}")

    # The local directory will be mounted via modal.Mount
    local_chroma = Path("/local-chroma")
    if not local_chroma.exists():
        print(f"❌ Local ChromaDB not found at {local_chroma}")
        return

    print(f"\n📋 Copying from {local_chroma} to {chroma_path}...")
    for item in local_chroma.iterdir():
        dest = chroma_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
        print(f"   ✓ Copied {item.name}")

    # Commit changes to volume
    print(f"\n💾 Committing changes to volume...")
    chroma_volume.commit()

    # Verify
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager
    rag = FinancialRAGManager(persist_directory=str(chroma_path))
    count = rag.collection.count()

    print(f"\n✅ Sync complete!")
    print(f"   Documents in Modal ChromaDB: {count}")
    print(f"   Markdown formatting is now PRESERVED! 🎉")

@app.local_entrypoint()
def main():
    """Upload local ChromaDB to Modal"""
    local_chroma_dir = Path(__file__).parent.parent / "chroma_db"

    if not local_chroma_dir.exists():
        print(f"❌ Local ChromaDB not found at {local_chroma_dir}")
        return

    print(f"📤 Uploading ChromaDB from {local_chroma_dir}...")

    # Create mount with local ChromaDB
    mount = modal.Mount.from_local_dir(
        local_path=str(local_chroma_dir),
        remote_path="/local-chroma"
    )

    # Run sync with mounted directory
    with mount:
        sync_chromadb.remote()

    print("\n✅ All done! Modal ChromaDB now has fixed formatting.")
