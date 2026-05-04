import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify

# Initialize the Flask application
app = Flask(__name__)

# Basic category classification function
def classify_recipe(text):
    # Convert text to lowercase for easier keyword matching
    text_lower = text.lower()
    
    # Check for Non-Veg keywords
    if any(keyword in text_lower for keyword in ['chicken', 'fish', 'meat']):
        return "Non-Veg"
    # Check for Dairy keywords
    elif any(keyword in text_lower for keyword in ['milk', 'cheese', 'butter', 'cream']):
        return "Dairy"
    # Check for Salad keyword
    elif 'salad' in text_lower:
        return "Salad"
    # Otherwise default to Veg
    else:
        return "Veg"

# Define the route for the home page that accepts both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def index():
    # Check if the form was submitted (POST request)
    if request.method == 'POST':
        # Get the search query entered by the user
        if request.is_json:
            query = request.json.get('search_query')
        else:
            query = request.form.get('search_query')
            
        if not query:
            return jsonify({"error": "No search query provided"}), 400
            
        try:
            # --- DUAL FUNCTIONALITY: URL SCRAPING OR INGREDIENT SEARCH ---
            if query.startswith('http://') or query.startswith('https://'):
                # ---------------------------------------------
                # 1. ORIGINAL FEATURE: Scrape a specific blog
                # ---------------------------------------------
                
                # Check for social media restrictions
                if 'instagram.com' in query or 'facebook.com' in query:
                    return jsonify({
                        "error": "Social media sites cannot be scraped directly due to login walls. Please enter a different blog URL or a search ingredient."
                    }), 400
                    
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(query, headers=headers, timeout=10)
                response.raise_for_status() 
                
                soup = BeautifulSoup(response.text, 'html.parser')
                recipes = []
                
                for heading in soup.find_all(['h1', 'h2']):
                    title = heading.get_text().strip()
                    if not title:
                        continue 
                    
                    img_tag = heading.find_next('img')
                    image_url = img_tag.get('src') if img_tag else ""
                    if image_url and not image_url.startswith('http'):
                        image_url = ""
                    
                    p_tag = heading.find_next('p')
                    description = p_tag.get_text().strip() if p_tag else "No description available."
                    
                    combined_text = title + " " + description
                    category = classify_recipe(combined_text)
                    
                    recipes.append({
                        "title": title,
                        "image": image_url,
                        "description": description,
                        "category": category,
                        "link": query
                    })
                    
            else:
                # ---------------------------------------------
                # 2. NEW FEATURE: Search and scrape from various sites
                # ---------------------------------------------
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                search_url = f"https://www.bing.com/search?q={query}+recipe"
                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status() 
                
                soup = BeautifulSoup(response.text, 'html.parser')
                recipes = []
                
                for item in soup.select('li.b_algo')[:6]: 
                    title_elem = item.select_one('h2 a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text().strip()
                    link = title_elem.get('href')
                    
                    desc_elem = item.select_one('.b_caption p')
                    description = desc_elem.get_text().strip() if desc_elem else "No description available."
                    
                    combined_text = title + " " + description
                    category = classify_recipe(combined_text)
                    
                    import urllib.parse
                    safe_title = urllib.parse.quote(title + " recipe")
                    image_url = f"https://tse1.mm.bing.net/th?q={safe_title}&w=600&h=400&c=7&rs=1&p=0&dpr=3&pid=1.7"
                    
                    recipes.append({
                        "title": title,
                        "image": image_url,
                        "description": description,
                        "category": category,
                        "link": link
                    })
            
            # Common error handling
            if len(recipes) == 0:
                return jsonify({"error": f"No recipes found for '{query}'."}), 404
                
            return jsonify({"recipes": recipes})
            
        except Exception as e:
            return jsonify({"error": f"Error performing search: {str(e)}"}), 500

    # For a normal page visit (GET request), just render the empty frontend template
    return render_template('index.html')

# Run the application when this script is executed directly
if __name__ == '__main__':
    # Enable debug mode so changes to code reflect immediately without restarting the server
    app.run(debug=True)
