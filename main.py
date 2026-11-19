import sys
from pathlib import Path

plugindir = Path.absolute(Path(__file__).parent)
lib_path = plugindir / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

import json
import os
import time
import urllib.parse
import urllib.request

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COVERS_BASE_URL = "https://covers.openlibrary.org/b"
COVER_SIZE = "M"

class OpenLibraryPlugin:
    def __init__(self):
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.app_icon = os.path.join(self.plugin_dir, "app.png")
        book_icon = os.path.join(self.plugin_dir, "book.png")
        self.default_book_icon = book_icon if os.path.exists(book_icon) else self.app_icon
        self.log_file = os.path.join(self.plugin_dir, "debug.log")

    def log_debug(self, message):
        """Log debug messages to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass

    def search_openlibrary_api(self, search_term):
        try:
            search_term = search_term.strip()
            if not search_term:
                return []

            encoded_term = urllib.parse.quote(search_term)
            api_url = f"https://openlibrary.org/search.json?title={encoded_term}&limit=10"

            self.log_debug(f"Searching for: {search_term}")

            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))

            books = []
            for doc in data.get('docs', []):
                isbn_list = doc.get('isbn') or []
                book_info = {
                    'key': doc.get('key'),
                    'title': doc.get('title', 'Unknown Title'),
                    'author_name': doc.get('author_name', ['Unknown Author'])[0] if doc.get('author_name') else 'Unknown Author',
                    'cover_id': doc.get('cover_i'),
                    'cover_edition_key': doc.get('cover_edition_key'),
                    'first_publish_year': doc.get('first_publish_year'),
                    'isbn': isbn_list[0] if isbn_list else None,
                }

                self.log_debug(f"Book: {book_info['title']}, Cover ID: {book_info['cover_id']}")
                books.append(book_info)

            return books[:5]  # Return only top 5
        except Exception as e:
            self.log_debug(f"API Error: {str(e)}")
            return []

    def get_cover_url(self, cover_id=None, cover_edition_key=None, isbn=None):
        """Build the remote cover URL for the best available identifier.

        Flow Launcher loads HTTP(S) IcoPath values itself, so the plugin no
        longer downloads and caches cover images.
        """
        if cover_id:
            cover_type, identifier = "id", cover_id
        elif cover_edition_key:
            cover_type, identifier = "olid", cover_edition_key
        elif isbn:
            cover_type, identifier = "isbn", isbn
        else:
            return self.default_book_icon

        identifier = urllib.parse.quote(str(identifier), safe="")
        return f"{COVERS_BASE_URL}/{cover_type}/{identifier}-{COVER_SIZE}.jpg?default=false"

    def process_book_data(self, book_data):
        title = book_data.get('title', 'Unknown Title')
        author = book_data.get('author_name', 'Unknown Author')
        book_key = book_data.get('key')
        year = book_data.get('first_publish_year', '')

        cover_url = self.get_cover_url(
            cover_id=book_data.get('cover_id'),
            cover_edition_key=book_data.get('cover_edition_key'),
            isbn=book_data.get('isbn'),
        )

        subtitle = f"by {author}"
        if year:
            subtitle += f" ({year})"

        return {
            "Title": title,
            "SubTitle": subtitle,
            "IcoPath": cover_url,
            "JsonRPCAction": {"method": "open_openlibrary_page", "parameters": [book_key]}
        }

    def query(self, search_term):
        results = []
        
        if not search_term:
            return [{
                "Title": "OpenLibrary Book Search",
                "SubTitle": "Start typing a book title to search...",
                "IcoPath": self.app_icon
            }]
        
        api_results = self.search_openlibrary_api(search_term)
        
        if api_results:
            for book_data in api_results:
                try:
                    result = self.process_book_data(book_data)
                    if result:
                        results.append(result)
                except Exception as e:
                    self.log_debug(f"Error processing book: {str(e)}")
                    pass
        
        if not results:
            results.append({
                "Title": f"No books found for '{search_term}'",
                "SubTitle": "Try a different search term",
                "IcoPath": self.app_icon
            })
        
        return results

    def open_openlibrary_page(self, book_key):
        try:
            if not book_key:
                return "No book key provided"
            
            openlibrary_url = f"https://openlibrary.org{book_key}"
            import webbrowser
            webbrowser.open(openlibrary_url)
            return f"Opened: {openlibrary_url}"
        except Exception as e:
            return f"Failed to open book page: {str(e)}"

    def safe_print_json(self, data):
        try:
            json_str = json.dumps(data, ensure_ascii=True)
            print(json_str)
            sys.stdout.flush()
        except Exception as e:
            fallback = {
                "result": [{
                    "Title": "Encoding Error",
                    "SubTitle": f"Failed to encode output: {str(e)}",
                    "IcoPath": self.app_icon
                }]
            }
            print(json.dumps(fallback, ensure_ascii=True))
            sys.stdout.flush()

def main():
    plugin = OpenLibraryPlugin()
    try:
        input_data = sys.stdin.read() if sys.stdin and not sys.stdin.isatty() else (
            sys.argv[1] if len(sys.argv) > 1 else '{"method": "query", "parameters": [""]}'
        )
        request = json.loads(input_data.strip() or '{}')
        method = request.get("method", "query")
        parameters = request.get("parameters", [""])
        
        result = None
        if method == "query":
            result = plugin.query(parameters[0] if parameters else "")
        elif method == "open_openlibrary_page":
            result = plugin.open_openlibrary_page(parameters[0] if parameters else "")
        
        if result:
            plugin.safe_print_json({"result": result})
            
    except Exception as e:
        plugin = OpenLibraryPlugin()
        plugin.safe_print_json({
            "result": [{
                "Title": "OpenLibrary Plugin Error",
                "SubTitle": f"Critical error: {str(e)}",
                "IcoPath": plugin.app_icon
            }]
        })

if __name__ == "__main__":
    main()

