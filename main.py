import sys
from pathlib import Path
from io import BytesIO

plugindir = Path.absolute(Path(__file__).parent)
lib_path = plugindir / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

import json
import os
import urllib.parse
import urllib.request
import subprocess
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class OpenLibraryPlugin:
    def __init__(self):
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_dir = os.path.join(self.plugin_dir, "img_cache")
        self.app_icon = os.path.join(self.plugin_dir, "app.png")
        self.default_book_icon = os.path.join(self.plugin_dir, "book.png")
        self.log_file = os.path.join(self.plugin_dir, "debug.log")
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        threading.Thread(target=self.cleanup_image_cache, daemon=True).start()

    def log_debug(self, message):
        """Log debug messages to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass

    def cleanup_image_cache(self):
        if not os.path.isdir(self.cache_dir):
            return
        now = time.time()
        age_limit_seconds = 3 * 24 * 60 * 60
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    file_mod_time = os.path.getmtime(file_path)
                    if (now - file_mod_time) > age_limit_seconds:
                        os.remove(file_path)
        except Exception:
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
            if 'docs' in data:
                for doc in data['docs']:
                    # Try multiple cover ID fields
                    cover_id = doc.get('cover_i') or doc.get('cover_edition_key')
                    
                    # If still no cover, try to get it from ISBN
                    if not cover_id and doc.get('isbn'):
                        isbn_list = doc.get('isbn', [])
                        if isbn_list:
                            cover_id = f"isbn_{isbn_list[0]}"
                    
                    book_info = {
                        'key': doc.get('key'),
                        'title': doc.get('title', 'Unknown Title'),
                        'author_name': doc.get('author_name', ['Unknown Author'])[0] if doc.get('author_name') else 'Unknown Author',
                        'cover_id': cover_id,
                        'first_publish_year': doc.get('first_publish_year'),
                        'isbn': doc.get('isbn', [None])[0] if doc.get('isbn') else None
                    }
                    
                    self.log_debug(f"Book: {book_info['title']}, Cover ID: {cover_id}")
                    books.append(book_info)
            
            return books[:5]  # Return only top 5
        except Exception as e:
            self.log_debug(f"API Error: {str(e)}")
            return []

    def download_cover(self, cover_id, save_path, isbn=None):
        """Try multiple methods to download cover"""
        urls_to_try = []
        
        # Method 1: Direct cover ID
        if cover_id and not str(cover_id).startswith('isbn_'):
            urls_to_try.append(f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg")
            urls_to_try.append(f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg")
        
        # Method 2: ISBN
        if isbn:
            urls_to_try.append(f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg")
        
        # Method 3: If cover_id is actually an ISBN
        if cover_id and str(cover_id).startswith('isbn_'):
            isbn_val = str(cover_id).replace('isbn_', '')
            urls_to_try.append(f"https://covers.openlibrary.org/b/isbn/{isbn_val}-M.jpg")
        
        for url in urls_to_try:
            try:
                self.log_debug(f"Trying to download: {url}")
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    content = response.read()
                    # Check if it's actually an image (not a placeholder)
                    if len(content) > 1000:  # Real covers are usually > 1KB
                        with open(save_path, 'wb') as out_file:
                            out_file.write(content)
                        self.log_debug(f"Successfully downloaded cover to {save_path}")
                        return True
            except Exception as e:
                self.log_debug(f"Failed to download from {url}: {str(e)}")
                continue
        
        return False

    def get_cover_image(self, cover_id, isbn=None):
        if not cover_id and not isbn:
            return self.default_book_icon
        
        # Create a unique cache filename
        cache_name = str(cover_id or isbn).replace('/', '_')
        cached_cover_path = os.path.join(self.cache_dir, f"{cache_name}.jpg")
        
        # Return cached cover if it exists and is valid
        if os.path.exists(cached_cover_path):
            try:
                # Check if file is not empty
                if os.path.getsize(cached_cover_path) > 1000:
                    return cached_cover_path
                else:
                    # Remove invalid cache file
                    os.remove(cached_cover_path)
            except:
                pass
        
        # Try to download the cover
        if self.download_cover(cover_id, cached_cover_path, isbn):
            return cached_cover_path
        
        return self.default_book_icon

    def process_book_data(self, book_data):
        title = book_data.get('title', 'Unknown Title')
        author = book_data.get('author_name', 'Unknown Author')
        cover_id = book_data.get('cover_id')
        isbn = book_data.get('isbn')
        book_key = book_data.get('key')
        year = book_data.get('first_publish_year', '')
        
        cover_path = self.get_cover_image(cover_id, isbn)
        
        subtitle = f"by {author}"
        if year:
            subtitle += f" ({year})"
        
        return {
            "Title": title,
            "SubTitle": subtitle,
            "IcoPath": cover_path,
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
            # Process books sequentially to ensure proper cover download
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

