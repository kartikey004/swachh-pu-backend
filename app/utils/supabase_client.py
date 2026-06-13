"""
Supabase client initialisation.

Two clients are exposed:
- `get_supabase_client()`  → uses the **anon key** (respects RLS, used for
  auth operations where the user JWT is attached).
- `get_supabase_admin()`   → uses the **service-role key** (bypasses RLS,
  used for server-side inserts during signup, admin operations, etc.).
"""

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Public / anon-key Supabase client (RLS-aware)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache()
def get_supabase_admin() -> Client:
    """Service-role Supabase client (bypasses RLS)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
