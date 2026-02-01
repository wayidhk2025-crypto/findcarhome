"""
Firebase Authentication for Django REST Framework.
"""
import os
import firebase_admin
from firebase_admin import auth, credentials
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed


class FirebaseUser:
    """Simple user object for Firebase authenticated users."""
    
    def __init__(self, uid, email=None, name=None):
        self.uid = uid
        self.email = email
        self.name = name
        self.is_authenticated = True
    
    def get(self, key, default=None):
        return getattr(self, key, default)
    
    def __str__(self):
        return self.email or self.uid


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Firebase ID token authentication for DRF.
    
    Clients should authenticate by passing the Firebase ID token in the
    "Authorization" header using the "Bearer" scheme.
    """
    
    keyword = 'Bearer'
    
    def __init__(self):
        # Initialize Firebase Admin SDK once
        if not firebase_admin._apps:
            # 1. Try JSON string from environment variable (Common for Cloud/Render)
            cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
            print(f"DEBUG: FIREBASE_CREDENTIALS_JSON exists: {bool(cred_json)}")
            if cred_json:
                print(f"DEBUG: FIREBASE_CREDENTIALS_JSON length: {len(cred_json)}")
                print(f"DEBUG: FIREBASE_CREDENTIALS_JSON starts with: {cred_json[:50] if len(cred_json) > 50 else cred_json}")
                try:
                    import json
                    cred_dict = json.loads(cred_json)
                    print(f"DEBUG: Parsed JSON keys: {list(cred_dict.keys())}")
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    print("DEBUG: Firebase initialized from JSON string.")
                    return
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON parsing error: {str(e)}")
                except Exception as e:
                    print(f"DEBUG: Error initializing from JSON string: {str(e)}")

            # 2. Try file path
            cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
            if cred_path:
                cred_path = cred_path.strip('"').strip("'")
                
            print(f"DEBUG: Firebase path: {cred_path}")
            if cred_path and os.path.exists(cred_path):
                try:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    print("DEBUG: Firebase initialized from file.")
                    return
                except Exception as e:
                    print(f"DEBUG: Error initializing from file: {str(e)}")
            else:
                print(f"DEBUG: Firebase credentials file not found at {cred_path}")

            # 3. Fallback: Initialize with project ID from environment
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('FIREBASE_PROJECT_ID', 'findcarhome')
            print(f"DEBUG: Attempting fallback with project_id: {project_id}")
            try:
                # Initialize without credentials but with project ID
                firebase_admin.initialize_app(options={'projectId': project_id})
                print(f"DEBUG: Firebase initialized with project ID fallback: {project_id}")
            except Exception as e:
                print(f"DEBUG: Final fallback failed: {str(e)}")

    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        print(f"DEBUG: Auth header received: {auth_header[:20]}..." if auth_header else "DEBUG: No auth header")
        
        if not auth_header:
            return None
        
        # Check format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            print(f"DEBUG: Invalid auth header format: {auth_header[:20]}...")
            return None
        
        id_token = parts[1]
        
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            print(f"DEBUG: Token verified for UID: {decoded_token.get('uid')}")
            
            # Create user object
            user = FirebaseUser(
                uid=decoded_token['uid'],
                email=decoded_token.get('email', ''),
                name=decoded_token.get('name', '')
            )
            
            return (user, None)
            
        except auth.ExpiredIdTokenError:
            print("DEBUG: Token has expired")
            raise AuthenticationFailed('Token has expired')
        except auth.InvalidIdTokenError:
            print("DEBUG: Invalid token")
            raise AuthenticationFailed('Invalid token')
        except auth.RevokedIdTokenError:
            print("DEBUG: Token has been revoked")
            raise AuthenticationFailed('Token has been revoked')
        except Exception as e:
            print(f"DEBUG: Authentication failed error: {str(e)}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')

    
    def authenticate_header(self, request):
        return self.keyword
