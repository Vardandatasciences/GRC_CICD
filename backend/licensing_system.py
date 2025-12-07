import requests
import secrets
import string
import json
from typing import Optional, Dict, Any
import hashlib
import time


class VardaanLicensingSystem:
    """
    Vardaan Licensing System for managing software licenses
    """
    
    def __init__(self, base_url: str = "https://backend.orcasho.com/"):
        """
        Initialize the licensing system
        
        Args:
            base_url (str): Base URL for the licensing API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'VardaanLicensingSystem/1.0'
        })
    
    def generate_license_code(self, length: int = 32) -> str:
        """
        Generate a random license code
        
        Args:
            length (int): Length of the license code (default: 32)
            
        Returns:
            str: Generated license code
        """
        # Use a combination of letters and numbers for better readability
        characters = string.ascii_letters + string.digits
        # Remove similar looking characters to avoid confusion
        characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('l', '').replace('I', '')
        
        # Generate random license code
        license_code = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Add some structure for better validation
        # Format: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
        formatted_license = '-'.join([license_code[i:i+4] for i in range(0, len(license_code), 4)])
        
        return formatted_license
    
    def generate_secure_license_code(self, length: int = 32) -> str:
        """
        Generate a more secure license code using hash-based approach
        
        Args:
            length (int): Length of the license code (default: 32)
            
        Returns:
            str: Generated secure license code
        """
        # Generate a random seed
        seed = secrets.token_hex(16)
        timestamp = str(int(time.time()))
        
        # Create a hash-based license
        combined = f"{seed}{timestamp}"
        hash_object = hashlib.sha256(combined.encode())
        license_hash = hash_object.hexdigest()[:length]
        
        # Format the license code
        formatted_license = '-'.join([license_hash[i:i+4] for i in range(0, len(license_hash), 4)])
        
        return formatted_license
    
    def verify_license(self, license_code: str) -> Dict[str, Any]:
        """
        Verify a license code via API
        
        Args:
            license_code (str): License code to verify
            
        Returns:
            Dict[str, Any]: Response from the verification API
        """
        try:
            url = f"{self.base_url}/licenseverification"
            params = {"license": license_code}
            
            response = self.session.get(url, params=params, timeout=30)
            
            # Return the response data
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "headers": dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "status_code": None,
                "data": None
            }
    
    def create_license(self, license_code: str) -> Dict[str, Any]:
        """
        Create a new license via API
        
        Args:
            license_code (str): License code to create
            
        Returns:
            Dict[str, Any]: Response from the creation API
        """
        try:
            url = f"{self.base_url}/license"
            payload = {"license": license_code}
            
            response = self.session.post(url, json=payload, timeout=30)
            
            # Return the response data
            return {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "headers": dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "status_code": None,
                "data": None
            }
    
    def generate_and_create_license(self, length: int = 32, secure: bool = True) -> Dict[str, Any]:
        """
        Generate a new license code and create it via API
        
        Args:
            length (int): Length of the license code
            secure (bool): Whether to use secure generation method
            
        Returns:
            Dict[str, Any]: Result of license generation and creation
        """
        # Generate license code
        if secure:
            license_code = self.generate_secure_license_code(length)
        else:
            license_code = self.generate_license_code(length)
        
        # Create the license via API
        creation_result = self.create_license(license_code)
        
        return {
            "license_code": license_code,
            "creation_result": creation_result,
            "success": creation_result.get("success", False)
        }
    
    def validate_license_format(self, license_code: str) -> bool:
        """
        Validate the format of a license code
        
        Args:
            license_code (str): License code to validate
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not license_code:
            return False
        
        # Remove hyphens for validation
        clean_license = license_code.replace('-', '')
        
        # Check if it contains only alphanumeric characters
        if not clean_license.isalnum():
            return False
        
        # Check length (assuming 32 characters without hyphens)
        if len(clean_license) != 32:
            return False
        
        return True
    
    def get_license_info(self, license_code: str) -> Dict[str, Any]:
        """
        Get detailed information about a license
        
        Args:
            license_code (str): License code to get info for
            
        Returns:
            Dict[str, Any]: License information
        """
        # First verify the license
        verification_result = self.verify_license(license_code)
        
        if not verification_result.get("success"):
            return {
                "valid": False,
                "error": verification_result.get("error", "Verification failed"),
                "license_code": license_code
            }
        
        return {
            "valid": True,
            "license_code": license_code,
            "verification_data": verification_result.get("data"),
            "last_verified": time.time()
        }


# Utility functions for easy use
def create_licensing_system(base_url: str = "https://backend.orcasho.com/") -> VardaanLicensingSystem:
    """
    Create a new licensing system instance
    
    Args:
        base_url (str): Base URL for the licensing API
        
    Returns:
        VardaanLicensingSystem: Licensing system instance
    """
    return VardaanLicensingSystem(base_url)


def generate_license_code(length: int = 32, secure: bool = True) -> str:
    """
    Generate a license code without creating a licensing system instance
    
    Args:
        length (int): Length of the license code
        secure (bool): Whether to use secure generation method
        
    Returns:
        str: Generated license code
    """
    system = VardaanLicensingSystem()
    if secure:
        return system.generate_secure_license_code(length)
    else:
        return system.generate_license_code(length)


def verify_license_code(license_code: str, base_url: str = "https://backend.orcasho.com/") -> Dict[str, Any]:
    """
    Verify a license code without creating a licensing system instance
    
    Args:
        license_code (str): License code to verify
        base_url (str): Base URL for the licensing API
        
    Returns:
        Dict[str, Any]: Verification result
    """
    system = VardaanLicensingSystem(base_url)
    return system.verify_license(license_code)


def create_license_code(license_code: str, base_url: str = "https://backend.orcasho.com/") -> Dict[str, Any]:
    """
    Create a license code without creating a licensing system instance
    
    Args:
        license_code (str): License code to create
        base_url (str): Base URL for the licensing API
        
    Returns:
        Dict[str, Any]: Creation result
    """
    system = VardaanLicensingSystem(base_url)
    return system.create_license(license_code)
