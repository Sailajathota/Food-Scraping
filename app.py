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
            # 1. Fetch search results from Bing (acting as our scraper for various websites)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            # We add "+recipe" to ensure we get food recipes
            search_url = f"https://www.bing.com/search?q={query}+recipe"
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status() 
            
            # 2. Parse the search engine HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 3. Extract and group related data (Title, Image, Description) from different websites
            recipes = []
            
            # In Bing, search results are stored in list items with class 'b_algo'
            for item in soup.select('li.b_algo')[:6]: # Let's get top 6 results
                # Find the title (usually an <h2> containing an <a> tag)
                title_elem = item.select_one('h2 a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text().strip()
                link = title_elem.get('href')
                
                # Find the description snippet
                desc_elem = item.select_one('.b_caption p')
                description = desc_elem.get_text().strip() if desc_elem else "No description available."
                
                # Classify the recipe based on title and description
                combined_text = title + " " + description
                category = classify_recipe(combined_text)
                
                # For search engine scraping, extracting high quality images is difficult without navigating
                # to the actual website. So we use a reliable placeholder image that fits the pastel theme,
                # or extract thumbnail if available.
                img_elem = item.select_one('img')
                image_url = None
                
                if img_elem:
                    # Bing often hides real images in data-src for lazy loading, or uses data URIs
                    src = img_elem.get('data-src') or img_elem.get('src')
                    if src and (src.startswith('http') or src.startswith('data:image')):
                        # Upgrade HTTP to HTTPS to prevent Vercel mixed-content blocking
                        if src.startswith('http://'):
                            src = src.replace('http://', 'https://', 1)
                        image_url = src
                        
                # Provide a beautiful fallback if no valid image was found
                if not image_url:
                    image_url = "https://images.unsplash.com/photo-1495147466023-e6a494129bb1?auto=format&fit=crop&w=600&q=80"
                
                # Group them together into a single structured object
                recipes.append({
                    "title": title,
                    "image": image_url,
                    "description": description,
                    "category": category,
                    "link": link
                })
            
            # Basic error handling: If no recipes were found, return a simple error message
            if len(recipes) == 0:
                return jsonify({"error": f"No recipes found for '{query}'."}), 404
                
            # Return the structured data as a JSON response
            return jsonify({"recipes": recipes})
            
        except Exception as e:
            # If an error occurs, return it as JSON
            return jsonify({"error": f"Error performing search: {str(e)}"}), 500

    # For a normal page visit (GET request), just render the empty frontend template
    return render_template('index.html')

# Run the application when this script is executed directly
if __name__ == '__main__':
    # Enable debug mode so changes to code reflect immediately without restarting the server
    app.run(debug=True)
