#!/usr/bin/env python
import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InvestorProfileParser:
    """Parser for investor profile HTML files."""
    
    def __init__(self, html_content: str, source_file: str):
        """
        Initialize the parser with HTML content.
        
        Args:
            html_content: The HTML content of the investor profile page
            source_file: The filename of the source HTML file
        """
        self.html = html_content
        self.source_file = source_file
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.apollo_state = None
        self.investor_id = None
        self.person_id = None
        self._extract_apollo_state()
    
    def _extract_apollo_state(self) -> None:
        """Extract Apollo state from the HTML."""
        try:
            # Find the Apollo state in the script tags
            for script in self.soup.find_all('script'):
                if script.string and '__APOLLO_STATE__' in script.string:
                    match = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        self.apollo_state = json.loads(match.group(1))
                        # Try to find the investor profile ID
                        for key, value in self.apollo_state.items():
                            if key.startswith('PublicInvestorProfile:'):
                                self.investor_id = key.split(':')[1]
                                if 'person' in value and value['person'].get('id'):
                                    self.person_id = value['person']['id']
                        break
        except Exception as e:
            logger.error(f"Failed to extract Apollo state: {e}")
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the investor profile and extract data.
        
        Returns:
            A dictionary of investor data
        """
        # Start with base data structure
        data = {
            "name": None,
            "position": None,
            "firm": None,
            "location": None,
            "investment_range": {
                "min": None,
                "max": None,
                "target": None
            },
            "areas_of_interest": [],
            "not_interested_in": [],
            "investments": [],
            "investment_count": 0,
            "links": {},
            "extraction_method": None,
            "source_file": self.source_file
        }
        
        # Try to extract data from Apollo state first (more complete)
        if self.apollo_state and self.investor_id:
            data.update(self._parse_from_apollo_state())
            data["extraction_method"] = "apollo_state"
        
        # Fall back to HTML extraction if needed
        if not data["name"] or not data["investments"]:
            html_data = self._parse_from_html()
            
            # Only update fields that weren't extracted from Apollo state
            for field, value in html_data.items():
                if field == "investment_range":
                    # Special handling for investment_range to merge values
                    for range_type, range_value in value.items():
                        if not data["investment_range"].get(range_type) and range_value:
                            data["investment_range"][range_type] = range_value
                elif not data.get(field) and value:
                    data[field] = value
            
            # If we didn't use Apollo state at all, set the extraction method
            if data["extraction_method"] is None:
                data["extraction_method"] = "html"
            else:
                data["extraction_method"] = "mixed"
        
        return data
    
    def _parse_from_apollo_state(self) -> Dict[str, Any]:
        """
        Parse investor data from Apollo state.
        
        Returns:
            A dictionary of investor data extracted from Apollo state
        """
        data = {
            "name": None,
            "position": None,
            "firm": None,
            "location": None,
            "investment_range": {
                "min": None,
                "max": None,
                "target": None
            },
            "areas_of_interest": [],
            "not_interested_in": [],
            "investments": [],
            "investment_count": 0,
            "links": {},
        }
        
        try:
            # Get investor profile data
            investor_profile = self.apollo_state.get(f"PublicInvestorProfile:{self.investor_id}")
            if not investor_profile:
                logger.warning(f"No investor profile found in Apollo state for ID {self.investor_id}")
                return data
            
            # Get person data
            person_id = None
            if 'person' in investor_profile:
                person_type_id = investor_profile['person']['id']
                person_type = investor_profile['person']['typename']
                person_id = f"{person_type}:{person_type_id}"
            
            person = self.apollo_state.get(person_id) if person_id else None
            
            # Extract basic info
            if person:
                data["name"] = person.get("name")
                
                # Extract links
                for link_type in ['linkedin_url', 'twitter_url', 'facebook_url', 'crunchbase_url', 'angellist_url', 'url']:
                    if person.get(link_type):
                        link_name = link_type.replace('_url', '')
                        data["links"][link_name] = person[link_type]
            
            # Extract position and firm
            data["position"] = investor_profile.get("position")
            
            # If the firm is an object reference, look it up
            firm_ref = investor_profile.get("firm")
            if firm_ref and isinstance(firm_ref, dict) and 'typename' in firm_ref:
                firm_id = f"{firm_ref['typename']}:{firm_ref['id']}"
                firm = self.apollo_state.get(firm_id)
                if firm:
                    data["firm"] = firm.get("name")
            
            # Extract location
            location_ref = investor_profile.get("location")
            if location_ref and isinstance(location_ref, dict) and 'typename' in location_ref:
                location_id = f"{location_ref['typename']}:{location_ref['id']}"
                location = self.apollo_state.get(location_id)
                if location:
                    data["location"] = location.get("display_name")
            
            # Extract investment range
            min_investment = investor_profile.get("min_investment")
            max_investment = investor_profile.get("max_investment")
            target_investment = investor_profile.get("target_investment")
            
            # Convert string values to integers where possible
            if isinstance(min_investment, str):
                data["investment_range"]["min"] = self._parse_amount(min_investment)
            elif isinstance(min_investment, (int, float)):
                data["investment_range"]["min"] = int(min_investment)
            
            if isinstance(max_investment, str):
                data["investment_range"]["max"] = self._parse_amount(max_investment)
            elif isinstance(max_investment, (int, float)):
                data["investment_range"]["max"] = int(max_investment)
            
            if isinstance(target_investment, str):
                data["investment_range"]["target"] = self._parse_amount(target_investment)
            elif isinstance(target_investment, (int, float)) and target_investment > 0:
                data["investment_range"]["target"] = int(target_investment)
            
            # Extract areas of interest
            areas_text = investor_profile.get("areas_of_interest_freeform")
            if areas_text:
                data["areas_of_interest"] = [area.strip() for area in areas_text.split(',')]
            
            # Extract not interested in
            not_interested_text = investor_profile.get("no_current_interest_freeform")
            if not_interested_text:
                data["not_interested_in"] = [area.strip() for area in not_interested_text.split(',')]
            
            # Extract investments
            investments_ref = None
            for key, value in investor_profile.items():
                if key.startswith('investments_on_record'):
                    investments_ref = value
                    break
            
            if investments_ref and isinstance(investments_ref, dict):
                data["investment_count"] = investments_ref.get("record_count", 0)
                
                # Get the edges (investments)
                edges = investments_ref.get("edges", [])
                for edge in edges:
                    if edge and "node" in edge:
                        node = edge["node"]
                        
                        # Look up the referenced company
                        company_name = None
                        company_ref = node.get("company")
                        if company_ref and isinstance(company_ref, dict):
                            company_id = f"{company_ref['typename']}:{company_ref['id']}"
                            company = self.apollo_state.get(company_id)
                            if company:
                                company_name = company.get("name")
                        
                        # Extract funding round details
                        round_name = None
                        amount = None
                        funding_round_ref = node.get("funding_round")
                        if funding_round_ref and isinstance(funding_round_ref, dict):
                            round_id = f"{funding_round_ref['typename']}:{funding_round_ref['id']}"
                            funding_round = self.apollo_state.get(round_id)
                            if funding_round:
                                round_name = funding_round.get("round_name")
                                
                                # Also get the funding amount if available
                                if funding_round.get("amount"):
                                    amount = funding_round.get("amount")
                        
                        # Create the investment entry
                        if company_name:
                            investment = {
                                "company": company_name,
                                "round": round_name,
                                "date": node.get("date"),
                                "amount": amount,
                                "is_lead": node.get("is_lead", False)
                            }
                            
                            data["investments"].append(investment)
        
        except Exception as e:
            logger.error(f"Error parsing Apollo state: {e}")
        
        return data
    
    def _parse_from_html(self) -> Dict[str, Any]:
        """
        Parse investor data from the HTML structure.
        
        Returns:
            A dictionary of investor data extracted from HTML
        """
        data = {
            "name": None,
            "position": None,
            "firm": None,
            "location": None,
            "investment_range": {
                "min": None,
                "max": None,
                "target": None
            },
            "areas_of_interest": [],
            "investments": [],
            "investment_count": 0,
            "current_fund_size": None,
            "links": {},
            "roles": [],
            "co_investors": [],
            "scouts_angels": [],
        }
        
        try:
            # Extract name
            name_el = self.soup.select_one('h1.f3.f1-ns.mv1')
            if name_el:
                data["name"] = name_el.text.strip()
            
            # Extract roles
            roles_container = self.soup.find('div', class_='subheader white-subheader b pb1')
            if roles_container:
                role_spans = roles_container.find_all('span')
                for span in role_spans:
                    if 'middot-separator' not in span.get('class', []):
                        role_text = span.text.strip()
                        if role_text:
                            data["roles"].append(role_text)
            
            # Extract position and firm from the Current Investing Position row
            position_rows = self.soup.select('div.line-separated-row.row')
            for row in position_rows:
                label = row.select_one('div.col-xs-5 span')
                value = row.select_one('div.col-xs-7 span')
                if label and value and "CURRENT INVESTING POSITION" in label.text.strip().upper():
                    position_text = value.text.strip()
                    # Check for format: "Signia Venture Partners · Partner"
                    if '·' in position_text:
                        parts = position_text.split('·')
                        data["firm"] = parts[0].strip()
                        if len(parts) > 1:
                            data["position"] = parts[1].strip()
                    # Check for format with no separator
                    else:
                        # If there's a link, it's likely the firm name
                        firm_link = row.select_one('div.col-xs-7 a')
                        if firm_link:
                            data["firm"] = firm_link.text.strip()
                            # Position is the remaining text
                            position_text = position_text.replace(data["firm"], '').strip()
                            # Remove leading/trailing separators
                            position_text = position_text.strip('· ')
                            if position_text:
                                data["position"] = position_text
            
            # If position/firm still not found, try the subheader
            if not data["position"] or not data["firm"]:
                subheader = self.soup.find('div', class_='subheader lower-subheader pb2')
                if subheader and 'at' in subheader.text:
                    text = subheader.text.strip()
                    parts = text.split('at', 1)
                    if len(parts) == 2:
                        data["position"] = parts[0].strip()
                        data["firm"] = parts[1].strip()
            
            # Extract location
            location_span = self.soup.select_one('span.f6.glyphicon.glyphicon-map-marker + span')
            if location_span:
                data["location"] = location_span.text.strip()
            
            # Extract investment range, sweet spot, and fund size from table
            range_rows = self.soup.select('div.line-separated-row.row')
            for row in range_rows:
                label = row.select_one('div.col-xs-5 span')
                value = row.select_one('div.col-xs-7 span')
                if label and value:
                    label_text = label.text.strip().upper()
                    value_text = value.text.strip()
                    
                    if "INVESTMENT RANGE" in label_text:
                        range_parts = value_text.split('-')
                        if len(range_parts) == 2:
                            min_str = range_parts[0].strip()
                            max_str = range_parts[1].strip()
                            data["investment_range"]["min"] = self._parse_amount(min_str)
                            data["investment_range"]["max"] = self._parse_amount(max_str)
                    
                    elif "SWEET SPOT" in label_text:
                        data["investment_range"]["target"] = self._parse_amount(value_text)
                    
                    elif "CURRENT FUND SIZE" in label_text:
                        data["current_fund_size"] = self._parse_amount(value_text)
                    
                    elif "INVESTMENTS ON RECORD" in label_text:
                        try:
                            data["investment_count"] = int(value_text)
                        except:
                            pass
            
            # Extract areas of interest from Sector & Stage Rankings section
            sector_section = self.soup.find(string=lambda text: text and 'Sector & Stage Rankings' in text)
            if sector_section:
                sector_container = sector_section.find_parent('div')
                if sector_container:
                    chips = sector_container.find_next('div').find_all('a', class_='vc-list-chip')
                    for chip in chips:
                        chip_text = chip.text.strip()
                        # Extract only the sector name (before parenthesis)
                        if '(' in chip_text:
                            sector = chip_text.split('(')[0].strip()
                            if sector and sector not in data["areas_of_interest"]:
                                data["areas_of_interest"].append(sector)
                        elif chip_text and chip_text not in data["areas_of_interest"]:
                            data["areas_of_interest"].append(chip_text)
            
            # Extract co-investors
            co_investors_section = self.soup.find(string=lambda text: text and 'Investors who invest with' in text)
            if co_investors_section:
                investor_container = co_investors_section.find_parent('div')
                if investor_container:
                    investor_rows = investor_container.find_all('div', class_='network-row')
                    for i, row in enumerate(investor_rows):
                        if i >= 5:  # Limit to 5 co-investors
                            break
                        investor_name_link = row.find('a', class_='network-row-investor-name')
                        if investor_name_link:
                            data["co_investors"].append(investor_name_link.text.strip())
            
            # Extract scouts and angels
            scouts_section = self.soup.find(string=lambda text: text and 'Scouts & Angels Affiliated With' in text)
            if scouts_section:
                scouts_container = scouts_section.find_parent('div')
                if scouts_container:
                    scout_rows = scouts_container.find_all('div', class_='network-row')
                    for i, row in enumerate(scout_rows):
                        if i >= 5:  # Limit to 5 scouts/angels
                            break
                        scout_name_link = row.find('a', class_='network-row-investor-name')
                        if scout_name_link:
                            data["scouts_angels"].append(scout_name_link.text.strip())
            
            # Extract investments from the investments table
            investments_dict = {}  # Use a dictionary to track companies by name

            # Find the past-investments-table
            table = self.soup.find('table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    current_company = None
                    
                    # Go through rows in the table
                    rows = tbody.find_all('tr')
                    i = 0
                    while i < len(rows):
                        row = rows[i]
                        
                        # Check if this is a company row (not a co-investor row)
                        row_classes = row.get('class', [])
                        is_coinvestor_row = any('coinvestor' in cls for cls in row_classes)
                        
                        if not is_coinvestor_row:
                            # This is a company row
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                # Extract company name
                                company_div = cells[0].find('div')
                                if company_div:
                                    company_name = company_div.text.strip()
                                    current_company = company_name
                                    
                                    # Create entry if doesn't exist
                                    if company_name not in investments_dict:
                                        investments_dict[company_name] = {
                                            'company': company_name,
                                            'rounds': [],
                                            'total_raised': None,
                                            'coinvestors': []
                                        }
                                    
                                    # Extract total raised from the third column
                                    total_raised_div = cells[2].find('div')
                                    if total_raised_div:
                                        investments_dict[company_name]['total_raised'] = total_raised_div.text.strip()
                                    
                                    # Extract rounds information from the second column
                                    rounds_cell = cells[1]
                                    round_divs = rounds_cell.find_all('div')
                                    for round_div in round_divs:
                                        round_text = round_div.text.strip()
                                        # Try to split by bullet character (•)
                                        if '•' in round_text:
                                            parts = [p.strip() for p in round_text.split('•')]
                                        else:
                                            # Try other common separators
                                            parts = [p.strip() for p in round_text.split(' - ')]
                                            if len(parts) == 1:
                                                # If no separator found, try to parse based on patterns
                                                parts = []
                                                # Look for round name pattern
                                                round_match = re.search(r'(Seed|Pre-Seed|Series [A-Z]|Angel)', round_text)
                                                if round_match:
                                                    parts.append(round_match.group(0))
                                                # Look for date pattern
                                                date_match = re.search(r'([A-Z][a-z]{2}\s+\d{4})', round_text)
                                                if date_match:
                                                    parts.append(date_match.group(0))
                                                # Look for amount pattern
                                                amount_match = re.search(r'(\$\d+[KMB]?)', round_text)
                                                if amount_match:
                                                    parts.append(amount_match.group(0))
                                        
                                        if len(parts) >= 3:
                                            stage = parts[0].strip()
                                            date = parts[1].strip()
                                            amount = parts[2].strip()
                                        elif len(parts) == 2:
                                            # Handle case with only two parts (likely stage and date)
                                            stage = parts[0].strip()
                                            date = parts[1].strip()
                                            amount = None
                                        elif len(parts) == 1 and parts[0]:
                                            # Handle case with only one part (likely just stage)
                                            stage = parts[0].strip()
                                            date = None
                                            amount = None
                                        else:
                                            # Use the full text as stage if parsing failed
                                            stage = round_text
                                            date = None
                                            amount = None
                                        
                                        # Check if this is a lead investment (has chair icon)
                                        is_lead = bool(round_div.find('img'))
                                        
                                        # Add round to the company
                                        investments_dict[company_name]['rounds'].append({
                                            'stage': stage,
                                            'date': date,
                                            'amount': amount,
                                            'is_lead': is_lead
                                        })
                        
                            # Check if next row is a co-investors row
                            if current_company and i+1 < len(rows):
                                next_row = rows[i+1]
                                colspan_td = next_row.find('td', attrs={'colspan': '3'})
                                
                                if colspan_td:
                                    coinvestor_span = colspan_td.find('span')
                                    if coinvestor_span and 'Co-investors:' in coinvestor_span.text:
                                        coinvestor_text = coinvestor_span.text.strip()
                                        # Extract co-investor names
                                        coinvestors_text = coinvestor_text.split('Co-investors:')[1].strip()
                                        
                                        if coinvestors_text:
                                            coinvestors = []
                                            # Parse the co-investors - they might have affiliations in parentheses
                                            for investor in coinvestors_text.split(','):
                                                investor = investor.strip()
                                                if '(' in investor:
                                                    # Extract just the name without affiliation
                                                    name = investor.split('(')[0].strip()
                                                    coinvestors.append(name)
                                                else:
                                                    coinvestors.append(investor)
                                            
                                            investments_dict[current_company]['coinvestors'] = coinvestors
                                        else:
                                            investments_dict[current_company]['coinvestors'] = []
                                        
                                        # Skip the co-investor row since we processed it
                                        i += 1
                            i += 1  # Move to next row
                    
                    # Convert dictionary to list for the final data structure
                    data['investments'] = list(investments_dict.values())
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
        
        return data
    
    @staticmethod
    def _parse_amount(amount_str: str) -> Optional[int]:
        """
        Parse amount strings like $1M, $500K into integers.
        
        Args:
            amount_str: The amount string to parse
        
        Returns:
            The amount in dollars as an integer, or None if parsing fails
        """
        if not amount_str:
            return None
            
        # Remove the currency symbol and any commas
        amount_str = amount_str.replace('$', '').replace(',', '').strip()
        
        try:
            # Handle K, M, B suffixes
            if amount_str.endswith('K'):
                return int(float(amount_str[:-1]) * 1000)
            elif amount_str.endswith('M'):
                return int(float(amount_str[:-1]) * 1000000)
            elif amount_str.endswith('B'):
                return int(float(amount_str[:-1]) * 1000000000)
            else:
                return int(float(amount_str))
        except (ValueError, TypeError):
            return None


def parse_investor_profile(html_content: str, source_file: str) -> Dict[str, Any]:
    """
    Parse an investor profile from HTML content.
    
    Args:
        html_content: The HTML content to parse
        source_file: The filename of the source HTML file
    
    Returns:
        A dictionary of parsed investor data
    """
    parser = InvestorProfileParser(html_content, source_file)
    return parser.parse() 