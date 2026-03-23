#!/bin/bash
cd ~/Documents/dougs-dharma-index || {
    echo ""
    echo "ERROR: Could not find ~/Documents/dougs-dharma-index"
    echo "If your project folder is somewhere else, edit the path on line 2."
    echo ""
    read -p "Press Enter to close..."
    exit 1
}

echo ""
echo "Dougs Dharma Index -- Build Script"
echo "========================================"
echo ""
echo "Running build.py..."
echo ""
python3 build.py

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Build complete!"
    echo ""
    echo "NEXT STEPS:"
    echo "  1. Open GitHub Desktop"
    echo "  2. You should see changed files listed"
    echo "  3. Type a summary like: Added new video: Title Here"
    echo "  4. Click Commit to main"
    echo "  5. Click Push origin"
    echo ""
    echo "Your site will update within a minute or two."
    echo "========================================"
else
    echo ""
    echo "Build failed! Check the error messages above."
    echo "Common fixes:"
    echo "  - Make sure dougs_dharma_index.json has no syntax errors"
    echo "  - Try opening it in VS Code to check for red underlines"
fi

echo ""
read -p "Press Enter to close..."
