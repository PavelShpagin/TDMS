#!/bin/bash

# Simple PlantUML to PNG converter using PlantUML web service
# No dependencies required except curl

echo "========================================="
echo "TDMS UML Diagram Generator (Web Service)"
echo "========================================="

# Create output directory
mkdir -p images

# Function to encode PlantUML text for web service
encode_plantuml() {
    cat "$1" | python3 -c "
import sys
import base64
import zlib

text = sys.stdin.read()
compressed = zlib.compress(text.encode('utf-8'))[2:-4]
encoded = base64.b64encode(compressed).decode('ascii')

# PlantUML encoding alphabet
alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
standard = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

encoded_plantuml = encoded.translate(str.maketrans(standard, alphabet))
print(encoded_plantuml)
"
}

echo "Generating PNG diagrams..."
echo "-----------------------------------------"

for puml_file in *.puml; do
    if [ -f "$puml_file" ]; then
        echo "Processing: $puml_file"
        
        # Encode the PlantUML content
        encoded=$(encode_plantuml "$puml_file")
        
        # Generate PNG using PlantUML web service
        output_file="images/${puml_file%.puml}.png"
        curl -s "http://www.plantuml.com/plantuml/png/${encoded}" -o "$output_file"
        
        if [ -f "$output_file" ] && [ -s "$output_file" ]; then
            echo "  ✓ Generated: $output_file"
        else
            echo "  ✗ Failed to generate PNG for $puml_file"
        fi
    fi
done

echo "-----------------------------------------"
echo ""

# Count generated files
png_count=$(ls -1 images/*.png 2>/dev/null | wc -l)

if [ $png_count -gt 0 ]; then
    echo "✅ Successfully generated $png_count PNG diagrams!"
    echo ""
    echo "Generated files:"
    ls -lh images/*.png
else
    echo "❌ No PNG files were generated."
fi

echo ""
echo "========================================="
echo "Generation complete!"
echo "========================================="