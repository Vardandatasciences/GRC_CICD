"""
Quick script to check if tokens exist in the database
Run this to debug token issues: python check_tokens.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import PolicyAcknowledgementUser

def check_tokens():
    print("=" * 60)
    print("Checking Policy Acknowledgement Tokens")
    print("=" * 60)
    
    # Check if Token field exists
    try:
        total = PolicyAcknowledgementUser.objects.count()
        print(f"\nTotal acknowledgement records: {total}")
        
        with_tokens = PolicyAcknowledgementUser.objects.filter(Token__isnull=False).count()
        print(f"Records with tokens: {with_tokens}")
        
        without_tokens = PolicyAcknowledgementUser.objects.filter(Token__isnull=True).count()
        print(f"Records without tokens: {without_tokens}")
        
        # Show sample records
        print("\n" + "-" * 60)
        print("Sample records (last 5):")
        print("-" * 60)
        
        recent = PolicyAcknowledgementUser.objects.all().order_by('-AssignedAt')[:5]
        for record in recent:
            print(f"\nID: {record.AcknowledgementUserId}")
            print(f"  Status: {record.Status}")
            print(f"  Has Token: {record.Token is not None}")
            if record.Token:
                print(f"  Token: {record.Token[:30]}...")
            else:
                print(f"  Token: NULL")
            print(f"  Assigned At: {record.AssignedAt}")
        
        # Check if Token field exists in model
        print("\n" + "-" * 60)
        print("Model Check:")
        print("-" * 60)
        has_token_field = hasattr(PolicyAcknowledgementUser, 'Token')
        print(f"Model has 'Token' field: {has_token_field}")
        
        if has_token_field:
            field = PolicyAcknowledgementUser._meta.get_field('Token')
            print(f"  Field type: {type(field).__name__}")
            print(f"  Null allowed: {field.null}")
            print(f"  Unique: {field.unique}")
        
        # Recommendations
        print("\n" + "=" * 60)
        print("Recommendations:")
        print("=" * 60)
        
        if not has_token_field:
            print("❌ Token field does not exist in model!")
            print("   → Check if migration was run")
            print("   → Run: ALTER TABLE policy_acknowledgement_users ADD COLUMN Token VARCHAR(255) NULL UNIQUE;")
        elif without_tokens > 0:
            print(f"⚠️  {without_tokens} records don't have tokens")
            print("   → Old records won't have tokens (this is normal)")
            print("   → New acknowledgement requests should generate tokens automatically")
        else:
            print("✅ Token field exists and all records have tokens")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tokens()

