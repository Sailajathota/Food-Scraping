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
                
                # To ensure beautiful, accurate images for every single recipe, 
                # we generate a dynamic image URL based on the scraped recipe title!
                import urllib.parse
                safe_title = urllib.parse.quote(title + " recipe")
                image_url = f"https://tse1.mm.bing.net/th?q={safe_title}&w=600&h=400&c=7&rs=1&p=0&dpr=3&pid=1.7"
                
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
