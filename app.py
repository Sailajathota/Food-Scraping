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
        # Get the URL entered by the user. 
        # We handle both JSON data (from JS fetch) and standard form data.
        if request.is_json:
            url = request.json.get('blog_url')
        else:
            url = request.form.get('blog_url')
            
        if not url:
            # Return a JSON error if no URL was provided
            return jsonify({"error": "No URL provided"}), 400
            
        # Basic error handling: Check for an invalid URL
        if not url.startswith('http://') and not url.startswith('https://'):
            return jsonify({"error": "Invalid URL. Please include http:// or https://"}), 400
            
        # --- SOCIAL MEDIA RESTRICTION ---
        # We explicitly block scraping social media sites (like Instagram or Facebook).
        # Why? 
        # 1. Dynamic Rendering: They use heavy JavaScript to load content. Simple scraping tools 
        #    like 'requests' and 'BeautifulSoup' cannot read JS-rendered data.
        # 2. Login Walls & Anti-Bot: These platforms actively block bots and require authentication.
        # 3. Terms of Service: Scraping user data often violates their strict terms.
        if 'instagram.com' in url or 'facebook.com' in url:
            return jsonify({
                "error": "Social media sites cannot be scraped directly due to login walls and anti-bot measures. Please use a public food blog or enter the recipe manually."
            }), 400
        
        try:
            # 1. Fetch the webpage HTML using requests
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() 
            
            # 2. Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 3. Extract and group related data (Title, Image, Description)
            recipes = []
            
            # Find all headings (h1 or h2) to act as the starting point for each recipe
            for heading in soup.find_all(['h1', 'h2']):
                title = heading.get_text().strip()
                if not title:
                    continue  # Skip empty headings
                
                # Find the nearest image AFTER this heading
                # .find_next('img') searches the HTML immediately following the heading
                img_tag = heading.find_next('img')
                image_url = img_tag.get('src') if img_tag else ""
                
                # We only keep absolute URLs for simplicity
                if image_url and not image_url.startswith('http'):
                    image_url = ""
                
                # Find the nearest paragraph AFTER this heading for the description
                p_tag = heading.find_next('p')
                description = p_tag.get_text().strip() if p_tag else ""
                
                # Classify the recipe based on title and description
                combined_text = title + " " + description
                category = classify_recipe(combined_text)
                
                # Group them together into a single structured object
                recipes.append({
                    "title": title,
                    "image": image_url,
                    "description": description,
                    "category": category
                })
            
            # Basic error handling: If no recipes were found, return a simple error message
            if len(recipes) == 0:
                return jsonify({"error": "No data found."}), 404
                
            # Return the structured data as a JSON response
            return jsonify({"recipes": recipes})
            
        except Exception as e:
            # If an error occurs, return it as JSON
            return jsonify({"error": f"Error fetching the URL: {str(e)}"}), 500

    # For a normal page visit (GET request), just render the empty frontend template
    return render_template('index.html')

# Run the application when this script is executed directly
if __name__ == '__main__':
    # Enable debug mode so changes to code reflect immediately without restarting the server
    app.run(debug=True)
