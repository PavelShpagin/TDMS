#!/usr/bin/env python3
"""
Generate PNG images from PlantUML files using PlantUML Web Service
This method doesn't require Java or PlantUML JAR file
"""

import os
import base64
import zlib
import requests
from pathlib import Path

def encode_plantuml(text):
    """Encode PlantUML text for web service"""
    compressed = zlib.compress(text.encode('utf-8'))[2:-4]
    encoded = base64.b64encode(compressed).decode('ascii')
    # PlantUML encoding alphabet
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    standard = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    encoded_plantuml = encoded.translate(str.maketrans(standard, alphabet))
    return encoded_plantuml

def generate_png_from_puml(puml_file, output_dir):
    """Generate PNG from PlantUML file using web service"""
    try:
        # Read PlantUML content
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Encode for PlantUML server
        encoded = encode_plantuml(content)
        
        # Generate URL for PlantUML server
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        
        # Download PNG
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Save PNG file
            output_file = output_dir / f"{puml_file.stem}.png"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True, output_file
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 50)
    print("TDMS UML Diagram Generator (Python)")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path.cwd()
    
    # Create output directory
    output_dir = current_dir / "images"
    output_dir.mkdir(exist_ok=True)
    
    # Find all .puml files
    puml_files = list(current_dir.glob("*.puml"))
    
    if not puml_files:
        print("No .puml files found in current directory")
        return
    
    print(f"\nFound {len(puml_files)} PlantUML files")
    print("-" * 50)
    
    success_count = 0
    for puml_file in puml_files:
        print(f"Processing: {puml_file.name}")
        success, result = generate_png_from_puml(puml_file, output_dir)
        if success:
            print(f"  ✓ Generated: {result.name}")
            success_count += 1
        else:
            print(f"  ✗ Failed: {result}")
    
    print("-" * 50)
    print(f"\n✅ Successfully generated {success_count}/{len(puml_files)} diagrams")
    
    if success_count > 0:
        print("\nGenerated files:")
        for png_file in sorted(output_dir.glob("*.png")):
            size = png_file.stat().st_size / 1024  # Size in KB
            print(f"  - {png_file.name} ({size:.1f} KB)")

if __name__ == "__main__":
    main()