#!/bin/bash

# TDMS UML Diagram Generator Script
# This script generates PNG images from PlantUML files

echo "========================================="
echo "TDMS UML Diagram Generator"
echo "========================================="

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "Error: Java is not installed. Please install Java first."
    exit 1
fi

# Download PlantUML if not present
if [ ! -f "plantuml.jar" ]; then
    echo "Downloading PlantUML..."
    wget https://github.com/plantuml/plantuml/releases/download/v1.2024.0/plantuml-1.2024.0.jar -O plantuml.jar
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download PlantUML"
        exit 1
    fi
    echo "PlantUML downloaded successfully!"
fi

# Create output directory for PNGs
mkdir -p images

# Generate PNG for each PlantUML file
echo ""
echo "Generating PNG diagrams..."
echo "-----------------------------------------"

for puml_file in *.puml; do
    if [ -f "$puml_file" ]; then
        echo "Processing: $puml_file"
        java -jar plantuml.jar -tpng "$puml_file" -o images/
        if [ $? -eq 0 ]; then
            echo "  ✓ Generated: images/${puml_file%.puml}.png"
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
    ls -la images/*.png
else
    echo "❌ No PNG files were generated."
fi

echo ""
echo "========================================="
echo "Generation complete!"
echo "========================================="