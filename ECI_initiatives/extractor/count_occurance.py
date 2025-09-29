import re
import os
import glob
from typing import Optional, List
from bs4 import BeautifulSoup


class ECIExtractor:
    def _extract_annex(self, soup: BeautifulSoup) -> Optional[str]:
        """Return full Annex text (concatenated paragraphs) or None."""
        
        # Find the Annex h2 header (case insensitive)
        annex_h2 = soup.find('h3', string=re.compile(r'^\s*Legal entity created for the purpose of managing the initiative\s*$', re.I))
        
        if not annex_h2:
            return None
        
        return " "


def count_annex_occurrences():
    """Count occurrences of Annex sections in all HTML files."""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create relative path to the initiative_pages directory
    initiative_pages_dir = os.path.join(
        script_dir, 
        "..", 
        "data", 
        "2025-09-18_16-33-57", 
        "initiative_pages"
    )
    
    # Normalize the path
    initiative_pages_dir = os.path.normpath(initiative_pages_dir)
    
    # Find all HTML files recursively
    html_pattern = os.path.join(initiative_pages_dir, "**", "*.html")
    html_files = glob.glob(html_pattern, recursive=True)
    
    if not html_files:
        print(f"No HTML files found in {initiative_pages_dir}")
        return
    
    print(f"Found {len(html_files)} HTML files to process")
    print(f"Searching in directory: {initiative_pages_dir}")
    print("=" * 80)
    
    # Initialize counters
    total_files = 0
    files_with_annex = 0
    files_without_annex = 0
    
    # Lists to store results
    files_with_annex_list = []
    files_without_annex_list = []
    
    # Create extractor instance
    extractor = ECIExtractor()
    
    # Process each HTML file
    for html_file in sorted(html_files):
        total_files += 1
        
        try:
            # Read the HTML file
            with open(html_file, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Create BeautifulSoup object
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check for Annex section
            annex_text = extractor._extract_annex(soup)
            
            # Get relative path for display
            relative_path = os.path.relpath(html_file, initiative_pages_dir)
            
            if annex_text:
                files_with_annex += 1
                files_with_annex_list.append(relative_path)
            else:
                files_without_annex += 1
                files_without_annex_list.append(relative_path)
                
        except Exception as e:
            print(f"ERROR processing {html_file}: {e}")
            files_without_annex += 1
            files_without_annex_list.append(os.path.relpath(html_file, initiative_pages_dir))
    
    # Print summary
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total HTML files processed: {total_files}")
    print(f"Files with Annex sections: {files_with_annex}")
    print(f"Files without Annex sections: {files_without_annex}")
    print(f"Percentage with Annex: {(files_with_annex/total_files)*100:.1f}%")


if __name__ == "__main__":
    count_annex_occurrences()
