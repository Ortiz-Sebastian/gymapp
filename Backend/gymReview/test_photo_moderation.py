#!/usr/bin/env python
"""
Test script for photo moderation logic
Tests the ImageModerationService with various scenarios
"""
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymReview.settings')
django.setup()

from gymapp.services import ImageModerationService


def test_moderation_logic():
    """Test the moderation decision logic with various scenarios"""
    
    service = ImageModerationService()
    
    print("=" * 80)
    print("PHOTO MODERATION LOGIC TESTS")
    print("=" * 80)
    print(f"\nThresholds:")
    print(f"  Auto-approve: confidence >= {service.auto_approve_threshold}")
    print(f"  Auto-reject: confidence <= {service.auto_reject_threshold}")
    print("=" * 80)
    
    # Test scenarios
    test_cases = [
        {
            'name': '✅ Clean gym photo (high confidence)',
            'result': {'confidence': 0.95, 'flags': []},
            'expected': 'approved'
        },
        {
            'name': '✅ Clean gym photo (medium-high confidence)',
            'result': {'confidence': 0.75, 'flags': []},
            'expected': 'approved'
        },
        {
            'name': '✅ Clean gym photo (medium confidence)',
            'result': {'confidence': 0.5, 'flags': []},
            'expected': 'approved'
        },
        {
            'name': '❌ Nudity detected',
            'result': {'confidence': 0.9, 'flags': ['nudity']},
            'expected': 'rejected'
        },
        {
            'name': '❌ Violence detected',
            'result': {'confidence': 0.85, 'flags': ['violence']},
            'expected': 'rejected'
        },
        {
            'name': '❌ Inappropriate objects',
            'result': {'confidence': 0.7, 'flags': ['inappropriate_objects']},
            'expected': 'rejected'
        },
        {
            'name': '❌ Racy/suggestive content',
            'result': {'confidence': 0.8, 'flags': ['racy']},
            'expected': 'rejected'
        },
        {
            'name': '❌ Very low confidence',
            'result': {'confidence': 0.2, 'flags': []},
            'expected': 'rejected'
        },
        {
            'name': '❌ Low confidence with minor flag',
            'result': {'confidence': 0.25, 'flags': ['blurry']},
            'expected': 'rejected'
        },
        {
            'name': '✅ Medium confidence, no serious flags',
            'result': {'confidence': 0.6, 'flags': ['blurry']},
            'expected': 'approved'
        },
        {
            'name': '❌ Multiple serious flags',
            'result': {'confidence': 0.5, 'flags': ['nudity', 'racy']},
            'expected': 'rejected'
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Input: confidence={test_case['result']['confidence']}, flags={test_case['result']['flags']}")
        
        # Get moderation decision
        action = service.determine_moderation_action(test_case['result'])
        
        # Check if it matches expected
        if action == test_case['expected']:
            print(f"   ✅ PASS: {action}")
            passed += 1
        else:
            print(f"   ❌ FAIL: Expected '{test_case['expected']}' but got '{action}'")
            failed += 1
        
        # Show rejection reason if applicable
        if action == 'rejected':
            reason = service.get_rejection_reason(test_case['result'])
            print(f"   Rejection reason: {reason}")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed - review logic above")
    
    return failed == 0


def test_with_sample_images():
    """
    Test with actual image files (if available)
    Place test images in: Backend/test_images/
    """
    
    service = ImageModerationService()
    test_images_dir = os.path.join(os.path.dirname(__file__), 'test_images')
    
    if not os.path.exists(test_images_dir):
        print("\n" + "=" * 80)
        print("SAMPLE IMAGE TESTING")
        print("=" * 80)
        print(f"ℹ️  To test with real images:")
        print(f"   1. Create folder: {test_images_dir}")
        print(f"   2. Add test images (gym photos, inappropriate images, etc.)")
        print(f"   3. Run this script again")
        print("=" * 80)
        return
    
    print("\n" + "=" * 80)
    print("TESTING WITH SAMPLE IMAGES")
    print("=" * 80)
    
    # Get all image files
    image_files = [f for f in os.listdir(test_images_dir) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
    
    if not image_files:
        print("No image files found in test_images folder")
        return
    
    for image_file in image_files:
        image_path = os.path.join(test_images_dir, image_file)
        print(f"\n📷 Testing: {image_file}")
        
        try:
            # Run moderation
            result = service.moderate_image(image_path)
            action = service.determine_moderation_action(result)
            
            print(f"   Provider: {result.get('provider', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Flags: {result.get('flags', [])}")
            print(f"   Decision: {action.upper()}")
            
            if action == 'rejected':
                reason = service.get_rejection_reason(result)
                print(f"   Rejection reason: {reason}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


def interactive_test():
    """Interactive mode to test specific scenarios"""
    
    service = ImageModerationService()
    
    print("\n" + "=" * 80)
    print("INTERACTIVE MODERATION TEST")
    print("=" * 80)
    print("\nEnter custom moderation scenarios to test the logic")
    print("(Press Ctrl+C to exit)\n")
    
    try:
        while True:
            # Get confidence score
            try:
                confidence = float(input("Enter confidence score (0.0 - 1.0): "))
                if not 0 <= confidence <= 1:
                    print("⚠️  Confidence must be between 0 and 1")
                    continue
            except ValueError:
                print("⚠️  Invalid number")
                continue
            
            # Get flags
            flags_input = input("Enter flags (comma-separated, or press Enter for none): ").strip()
            flags = [f.strip() for f in flags_input.split(',') if f.strip()]
            
            # Test
            result = {'confidence': confidence, 'flags': flags}
            action = service.determine_moderation_action(result)
            
            print(f"\n📊 Result: {action.upper()}")
            if action == 'rejected':
                reason = service.get_rejection_reason(result)
                print(f"   Rejection reason: {reason}")
            print()
            
    except KeyboardInterrupt:
        print("\n\n👋 Exiting interactive mode")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test photo moderation logic')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('--images', action='store_true',
                       help='Test with sample images from test_images/ folder')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_test()
    elif args.images:
        test_with_sample_images()
    else:
        # Run logic tests by default
        success = test_moderation_logic()
        
        # Also check for sample images
        test_with_sample_images()
        
        sys.exit(0 if success else 1)

