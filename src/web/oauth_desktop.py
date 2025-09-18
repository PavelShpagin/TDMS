"""
Simple OAuth handler for desktop applications.
This module provides a clean OAuth flow for desktop apps using the loopback redirect.
"""

import asyncio
import hashlib
import base64
import secrets
import webbrowser
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from fastapi import HTTPException


class DesktopOAuthHandler:
    """Handles OAuth flow for desktop applications"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_port: int = 8001):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_port = redirect_port
        self.redirect_uri = f"http://127.0.0.1:{redirect_port}/oauth/callback"
        self.auth_state: Optional[Dict[str, Any]] = None
        
    def generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE verifier and challenge"""
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        return verifier, challenge
    
    def get_auth_url(self, scopes: list[str] = None) -> tuple[str, str, str]:
        """Generate authorization URL with PKCE"""
        if scopes is None:
            scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        
        state = secrets.token_urlsafe(32)
        verifier, challenge = self.generate_pkce()
        
        # Store state for verification
        self.auth_state = {
            "state": state,
            "verifier": verifier,
            "challenge": challenge
        }
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state, verifier
    
    async def exchange_code(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        if not self.auth_state or self.auth_state["state"] != state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": self.auth_state["verifier"]
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Token exchange failed: {response.text}"
                )
            
            return response.json()
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Token refresh failed: {response.text}"
                )
            
            return response.json()
