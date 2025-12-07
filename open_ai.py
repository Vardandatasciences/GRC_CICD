import os
import sys
from openai import OpenAI
from openai import APIError, AuthenticationError

# ============================================
# SET YOUR OPENAI API KEY HERE FOR TESTING
==========================

def test_openai_key(api_key=None):
    """
    Test if OpenAI API key is working.
    
    Args:
        api_key: OpenAI API key. If None, will try to get from environment variable OPENAI_API_KEY
    
    Returns:
        bool: True if key is working, False otherwise
    """
    # Get API key from parameter, environment variable, or testing variable
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY') or OPENAI_API_KEY_FOR_TESTING
    
    if not api_key:
        print("❌ Error: No API key provided!")
        print("   Please either:")
        print("   1. Set OPENAI_API_KEY environment variable, or")
        print("   2. Pass your API key as an argument to the function")
        return False
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        print("🔄 Testing OpenAI API key...")
        
        # Make a simple API call to test the key
        # Using a minimal request to check authentication
        response = client.models.list()
        
        # If we get here, the API key is valid
        print("✅ OpenAI API key is working correctly!")
        print(f"   Successfully connected to OpenAI API")
        
        # Optional: Show available models (first 5)
        models = list(response.data)[:5]
        if models:
            print(f"\n   Available models (showing first 5):")
            for model in models:
                print(f"   - {model.id}")
        
        return True
        
    except AuthenticationError as e:
        print("❌ Authentication Error: Invalid API key!")
        print(f"   Error details: {str(e)}")
        return False
    
    except APIError as e:
        print(f"❌ API Error: {str(e)}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False


def test_with_simple_completion(api_key=None):
    """
    Test OpenAI API key with a simple completion request.
    
    Args:
        api_key: OpenAI API key. If None, will try to get from environment variable OPENAI_API_KEY
    
    Returns:
        bool: True if key is working, False otherwise
    """
    # Get API key from parameter, environment variable, or testing variable
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY') or OPENAI_API_KEY_FOR_TESTING
    
    if not api_key:
        print("❌ Error: No API key provided!")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        
        print("\n🔄 Testing with a simple completion request...")
        
        # Make a simple chat completion request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, API key is working!' if you can read this."}
            ],
            max_tokens=20
        )
        
        message = response.choices[0].message.content
        print(f"✅ Completion test successful!")
        print(f"   Response: {message}")
        
        return True
        
    except AuthenticationError as e:
        print("❌ Authentication Error: Invalid API key!")
        print(f"   Error details: {str(e)}")
        return False
    
    except APIError as e:
        print(f"❌ API Error: {str(e)}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("OpenAI API Key Test")
    print("=" * 50)
    
    # Check if API key is provided as command line argument
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"Using API key from command line argument")
    elif os.getenv('OPENAI_API_KEY'):
        api_key = os.getenv('OPENAI_API_KEY')
        print("Using API key from OPENAI_API_KEY environment variable...")
    else:
        api_key = OPENAI_API_KEY_FOR_TESTING
        print("Using API key from OPENAI_API_KEY_FOR_TESTING variable...")
    
    # Test 1: List models (lightweight test)
    result1 = test_openai_key(api_key)
    
    # Test 2: Simple completion (more comprehensive test)
    if result1:
        result2 = test_with_simple_completion(api_key)
        
        if result1 and result2:
            print("\n" + "=" * 50)
            print("✅ All tests passed! Your OpenAI API key is working correctly.")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("⚠️  Some tests failed. Please check your API key.")
            print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ API key test failed. Please verify your API key.")
        print("=" * 50)
        sys.exit(1)

