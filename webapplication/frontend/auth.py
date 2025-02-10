import os
from numpy import void
import streamlit as st
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
REDIRECT_URI = os.environ['REDIRECT_URI']


async def get_authorization_url(client: GoogleOAuth2, redirect_uri: str):
    authorization_url = await client.get_authorization_url(redirect_uri, scope=["profile", "email"])
    return authorization_url


async def get_access_token(client: GoogleOAuth2, redirect_uri: str, code: str):
    token = await client.get_access_token(code, redirect_uri)
    return token


async def get_email(client: GoogleOAuth2, token: str):
    user_id, user_email = await client.get_id_email(token)
    return user_id, user_email


def set_google_login_btn():
    client: GoogleOAuth2 = GoogleOAuth2(CLIENT_ID, CLIENT_SECRET)
    authorization_url = asyncio.run(
        get_authorization_url(client, REDIRECT_URI))
    return f"""
            <style>
                .google-button {{
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }}
                .google-button:hover {{
                    background-color: #357AE8; /* 호버 시 색상 변경 */
                }}
            </style>

            <a href="{authorization_url}" target="_self">
                <button class="google-button">Login with Google</button>
            </a>
            """
