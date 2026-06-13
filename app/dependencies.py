"""
FastAPI dependencies — injectable auth & role checks.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.supabase_client import get_supabase_client, get_supabase_admin

# Define the security scheme
security = HTTPBearer(auto_error=True)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Extract and verify the JWT from the Authorization header using HTTPBearer.
    Returns the full profile row from the `profiles` table.
    """
    token = credentials.credentials

    # Verify JWT with Supabase
    supabase = get_supabase_client()
    try:
        user_response = supabase.auth.get_user(token)
        auth_user = user_response.user
        if auth_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(exc)}",
        )

    # Fetch profile from DB
    admin_client = get_supabase_admin()
    result = (
        admin_client.table("profiles")
        .select("*")
        .eq("user_id", str(auth_user.id))
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for authenticated user",
        )

    return result.data[0]



def require_role(*allowed_roles: str):
    """
    Returns a dependency that checks if the current user has one of the
    allowed roles.

    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def admin_only():
            ...
    """

    async def _check_role(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {', '.join(allowed_roles)}",
            )
        return user

    return _check_role
