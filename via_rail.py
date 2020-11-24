import requests, json, re, textwrap
from tzwhere import tzwhere
from string import ascii_lowercase
from bs4 import BeautifulSoup

class Station:
    """Takes a VIA 4 letter 'station code' and fetches the details online"""
    details_url = "http://www.viarail.ca/en/embedded/station/detail"

    def __init__(self, station_code, tz):
        self.url = self.details_url + '/' + station_code
        soup = self.fetch_page(self.url)
        
        self.name = self.fetch_name(soup)
        self.address = self.fetch_address(soup)
        (self.latitude, self.longitude) = self.fetch_latlong(soup)
        if self.latitude == "" or self.longitude == "":
            self.timezone = ""
        else:
            self.timezone = tz.tzNameAt(float(self.latitude), float(self.longitude), forceTZ=True)
        self.city = self.fetch_city(soup)
    
    def fetch_name(self, soup):
        """Full name"""
        """<h1 class="heading-large-bold--drupal">name</h1>"""

        try:
            return soup.find("h1", { "class": "station-title" }).get_text()
        except Exception as e:
            print(e)
            return ""

    def fetch_city(self, soup):
        """City name"""
        """<span itemprop="addressLocality">Trenton</span>"""

        try:
            return soup.find("span", { "itemprop": "addressLocality" }).get_text()
        except Exception as e:
            print(e)
            return ""

    def fetch_address(self, soup):
        """Get the address"""
        """<div id='adress'> (sic). Merge multiple lines."""
        
        try:
            adresss_string_list = []
            address_strings = soup.find(id="adressTop").stripped_strings
            # Clean: ignore ',' elements. Left/right strip ',' and then ' ' from others.
            adresss_string_list = [s.strip(',').strip() for s in address_strings if s != ","]
            return ", ".join(adresss_string_list)
        except Exception as e:
            print(e)
            return ""

    def fetch_latlong(self, soup):
        """Get geographical coordinates"""
        """Extract from the only Google Maps link, if any"""
        """<a [...] href="https://www.google.com/maps?q=45.5001,-73.5662+(...)">[...]</a>"""

        try:
            # Get the coordinates, between '=' and '+'
            googlemap_href = soup.find("a", href=re.compile("google.com/maps"))['href']
            coordinates_string = re.search(r'\=(.*)\+', googlemap_href).group(1)
            coordinates_list = coordinates_string.split(',')
            return (coordinates_list[0], coordinates_list[1])
        except Exception as e:
            print(e)
            return ("", "")

    def fetch_page(self, url):
        """Fetch the page into a Soup"""
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup

    def get_dict(self):
        return { "name": self.name, "address": self.address, "city": self.city,
                 "lat": self.latitude, "long" : self.longitude,
                 "url": self.url, "timezone" : self.timezone }

    def __repr__(self):
        return str(self.get_dict())

class VIA:
    """Generate json from raw VIA Rail station data"""
    via_stations_url = "http://reservia.viarail.ca/GetStations.aspx"
    tz = tzwhere.tzwhere(forceTZ=True)

    def save_stations(self, filename="stations_via.json", full=False):
        """Requests stations starting from A to Z
        http://reservia.viarail.ca/GetStations.aspx?q=<str>
        full: set to True to complete with station details"""
        
        stations = []
        for l in ascii_lowercase:
            r = requests.get(self.via_stations_url + '?q=' + l)
            print("Processing stations starting with '{0}'".format(l.upper()))
            
            if not full:
                # Use as is    
                stations += r.json()
            else:
                # Agument data from a Station object
                stations_subset = r.json()
                for station in stations_subset:
                    details = Station(station['sc'], self.tz).get_dict() # sc: station code
                    station.update(details)
                    print("Processed '{}'".format(station['name']))
                    if details['lat']:
                        stations.append(station)
        
        self.save(stations, filename)

    def save(self, json_struct, filename):
        """Dumps JSON then save to file"""

        with open(filename, 'w') as f:
            json.dump(json_struct, f)
        print("Fetched {0} stations to: {1}".format(len(json_struct), filename))

def main():
    pass

if __name__ == "__main__":
    main()
