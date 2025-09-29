import re
import os
from typing import Optional, List
from bs4 import BeautifulSoup


class ECIExtractor:
    def _extract_annex(self, soup: BeautifulSoup) -> Optional[str]:
        """Return full Annex text (concatenated paragraphs) or None."""
        
        # Find the Annex h2 header (case insensitive)
        annex_h2 = soup.find('h2', string=re.compile(r'^\s*Annex\s*$', re.I))
        
        if not annex_h2:
            return None
        
        texts: List[str] = []
        node = annex_h2.find_next_sibling()
        
        while node and not (node.name == 'h2'):
            # grab paragraph–level text, skip empty / whitespace nodes
            if node.name in {'p', 'ul', 'ol'}:
                txt = node.get_text(' ', strip=True)
                
                if txt:
                    texts.append(txt)
                    
            node = node.find_next_sibling()
        
        joined = ' '.join(texts).strip()
        return joined or None


def test_extract_annex():
    """Test function to extract and print annex from the HTML file."""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create relative path to the HTML file
    html_file_path = os.path.join(
        script_dir, 
        "..", 
        "data", 
        "2025-09-18_16-33-57", 
        "initiative_pages", 
        "2024", 
        "2024_000004_en.html"
    )
    
    # Normalize the path
    html_file_path = os.path.normpath(html_file_path)

    if not os.path.exists(html_file_path):
        raise ValueError("html_file_path:\n" + html_file_path)
    
    try:
        # Read the HTML file
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Create BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create extractor instance and extract annex
        extractor = ECIExtractor()
        annex_text = extractor._extract_annex(soup)
        
        if annex_text:
            print("=" * 80)
            print("EXTRACTED ANNEX TEXT:")
            print("=" * 80)
            print(annex_text[:500] + "\n...")
            print("=" * 80)
            print(f"Total characters: {len(annex_text)}")
        else:
            print("No Annex section found in the HTML file.")
            
    except FileNotFoundError:
        print(f"Error: HTML file not found at {html_file_path}")
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    test_extract_annex()
