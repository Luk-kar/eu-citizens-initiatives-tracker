import re
import os
from typing import Optional, List, Dict
from bs4 import BeautifulSoup


class ECIExtractor:
    def __init__(self):
        pass

    def extract_organisers_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract organiser data from the HTML including representatives, substitutes, members, etc."""

        # Find the Organisers section
        organisers_h2 = soup.find('h2', string=re.compile(r'\s*Organisers\s*$', re.I))
        if not organisers_h2:
            return None

        result = {}

        # Helper function to extract text from next element after a heading
        def get_text_after_heading(heading_text: str) -> List[str]:
            heading = soup.find('h3', string=re.compile(rf'\s*{heading_text}\s*$', re.I))
            if not heading:
                return []

            next_element = heading.find_next_sibling()
            if not next_element or next_element.name != 'ul':
                return []

            items = []
            for li in next_element.find_all('li'):
                text = li.get_text(strip=True)
                if text:
                    items.append(text)
            return items
        # Extract Legal Entity information
        # Look for the exact heading "Legal entity created for the purpose of managing the initiative"
        legal_entity_heading = soup.find('h3', string=re.compile(r'^\s*Legal entity created for the purpose of managing the initiative\s*$', re.I))

        result['legal_entity'] = {
            'name': None,
            'country_of_residence': None
        }

        if legal_entity_heading:
            # Find the next sibling which should be a <ul> element
            next_element = legal_entity_heading.find_next_sibling()
            if next_element and next_element.name == 'ul':
                # Find the <li> element within the <ul>
                li_element = next_element.find('li')
                if li_element:
                    # Get the full text content
                    full_text = li_element.get_text(separator=' ', strip=True)

                    # Split on "Country of the seat:" to separate name and country
                    if 'Country of the seat:' in full_text:
                        parts = full_text.split('Country of the seat:', 1)
                        if len(parts) == 2:
                            result['legal_entity']['name'] = parts[0].strip()
                            result['legal_entity']['country_of_residence'] = parts[1].strip()
                    else:
                        # Fallback: use the entire text as name if no country pattern found
                        result['legal_entity']['name'] = full_text

        # Extract Representative information
        representatives = get_text_after_heading('Representative')
        result['representative'] = {
            'number_of_people': len(representatives),
            'countries_of_residence': {}
        }

        for rep in representatives:
            # Extract country information from the representative text
            # Pattern: "Name - email Country of residence: CountryName"
            country_match = re.search(r'Country of residence[:\s]+([A-Za-z\s]+)', rep)
            if country_match:
                country = country_match.group(1).strip()
                if country in result['representative']['countries_of_residence']:
                    result['representative']['countries_of_residence'][country] += 1
                else:
                    result['representative']['countries_of_residence'][country] = 1

        # Extract Substitute information
        substitutes = get_text_after_heading('Substitute')
        result['substitute'] = {
            'number_of_people': len(substitutes)
        }

        # Extract Members information
        members = get_text_after_heading('Members')
        result['members'] = {
            'number_of_people': len(members)
        }

        # Extract Others information
        others = get_text_after_heading('Others')
        result['others'] = {
            'number_of_people': len(others)
        }

        # Extract DPO information (Data Protection Officer)
        dpo = get_text_after_heading('DPO')
        if not dpo:
            # Also try alternative headings
            dpo = get_text_after_heading('Data Protection Officer')

        result['dpo'] = {
            'number_of_people': len(dpo)
        }

        return result

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
        extracted_content = extractor.extract_organisers_data(soup)
        
        if extracted_content:
            print("=" * 80)
            print("EXTRACTED:")
            print("=" * 80)
            print(extracted_content)
            print("=" * 80)
        else:
            print("No Annex section found in the HTML file.")
            
    except FileNotFoundError:
        print(f"Error: HTML file not found at {html_file_path}")
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    test_extract_annex()
