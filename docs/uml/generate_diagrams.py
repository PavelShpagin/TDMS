#!/usr/bin/env python3
"""
TDMS UML Diagram Generator
Generates PNG images from Mermaid .mmd files using mermaid-cli
"""

import os
import subprocess
import sys
from pathlib import Path

def check_mermaid_cli():
    """Return the CLI command to run Mermaid (mmdc or npx fallback), or None if unavailable."""
    try:
        result = subprocess.run(['mmdc', '--version'], capture_output=True, text=True, check=True)
        print(f"✅ Mermaid CLI found: {result.stdout.strip()}")
        return ['mmdc']
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        result = subprocess.run(['npx', '-y', '@mermaid-js/mermaid-cli', '--version'],
                                capture_output=True, text=True, check=True)
        print(f"✅ Mermaid via npx found: {result.stdout.strip()}")
        return ['npx', '-y', '@mermaid-js/mermaid-cli']
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Mermaid CLI not found and npx fallback unavailable!")
        print("📦 Install with: npm install -g @mermaid-js/mermaid-cli or install Node.js to use npx")
        return None

def generate_diagram(cli_cmd, mmd_file, output_dir):
    """Generate PNG from Mermaid file"""
    mmd_path = Path(mmd_file)
    output_path = output_dir / f"{mmd_path.stem}.png"
    
    try:
        cmd = [
            *cli_cmd,
            '-i', str(mmd_path),
            '-o', str(output_path),
            '-t', 'neutral',
            '-b', 'white',
            '--width', '1200',
            '--height', '800'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Generated: {output_path.name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate {mmd_path.name}: {e.stderr}")
        return False

def main():
    """Main function to generate all UML diagrams"""
    print("🎨 TDMS UML Diagram Generator")
    print("=" * 40)
    
    # Determine Mermaid CLI command (mmdc or npx fallback)
    cli_cmd = check_mermaid_cli()
    if cli_cmd is None:
        return 1
    
    # Setup paths
    script_dir = Path(__file__).parent
    output_dir = script_dir / 'images'
    output_dir.mkdir(exist_ok=True)
    
    # Find all .mmd files
    mmd_files = list(script_dir.glob('*.mmd'))
    
    if not mmd_files:
        print("❌ No .mmd files found in current directory")
        return 1
    
    print(f"📁 Found {len(mmd_files)} Mermaid files")
    print(f"📂 Output directory: {output_dir}")
    print()
    
    # Generate diagrams
    success_count = 0
    total_count = len(mmd_files)
    
    for mmd_file in sorted(mmd_files):
        if generate_diagram(cli_cmd, mmd_file, output_dir):
            success_count += 1
    
    print()
    print("=" * 40)
    print(f"📊 Results: {success_count}/{total_count} diagrams generated")
    
    if success_count == total_count:
        print("🎉 All diagrams generated successfully!")
        return 0
    else:
        print("⚠️  Some diagrams failed to generate")
        return 1

if __name__ == "__main__":
    sys.exit(main())
