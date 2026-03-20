"""
A.N.N. Enterprise Cloud Database Client
Syncs generated broadcast scripts to Supabase (PostgreSQL) in real-time.
Allows front-end reactivity and completely unburdens the FastAPI server.
"""

from supabase import create_client, Client
from config import get_settings
from models.schemas import BroadcastScript
from utils.logger import get_logger
import asyncio

log = get_logger("supabase_sync")

class SupabaseSyncService:
    def __init__(self):
        self.settings = get_settings()
        self.client: Client | None = None
        
        if self.settings.supabase_url and self.settings.supabase_key:
            try:
                self.client = create_client(
                    self.settings.supabase_url,
                    self.settings.supabase_key
                )
                log.info("supabase_connected", url=self.settings.supabase_url)
            except Exception as e:
                log.error("supabase_connection_failed", error=str(e))
        else:
            log.warning("supabase_credentials_missing", msg="Skipping cloud sync.")

    async def sync_script(self, script: BroadcastScript):
        """
        Pushes a finished broadcast script to the 'broadcast_scripts' table 
        on Supabase for real-time edge delivery.
        """
        if not self.client:
            return

        # Run the synchronous Supabase API call in an async executor
        def _insert():
            payload = {
                "id": script.id,
                "headline": script.headline,
                "english_script": script.english_script,
                "translations_json": script.translations,
                "category": script.category.value,
                "source_url": script.source_url,
                "duration_seconds": script.estimated_duration_seconds,
            }
            # Perform upsert (insert or update based on id)
            self.client.table("broadcast_scripts").upsert(payload).execute()

        try:
            await asyncio.to_thread(_insert)
            log.info("supabase_sync_success", script_id=script.id)
        except Exception as e:
            log.error("supabase_sync_failed", script_id=script.id, error=str(e))

# Global singleton
supabase_sync = SupabaseSyncService()
