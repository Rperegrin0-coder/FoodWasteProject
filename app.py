import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import firebase_admin
from firebase_admin import credentials, db, auth
import logging
from google.auth.transport import requests
from flask_session import Session
import requests
from firebase_admin import storage
from datetime import datetime


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'pere'

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)  # Correct usage of Flask-Session

app.config['SERVER_NAME'] = '127.0.0.1:5000'
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https'

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# Firebase Admin SDK initialization
cred = credentials.Certificate(
    '/Users/macbook/PycharmProjects/finalyearproject/finalyearproject-bf7bf-firebase-adminsdk-bywl6-5377e448e6.json')
default_app = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://finalyearproject-bf7bf-default-rtdb.firebaseio.com/'
})

WEB_API_KEY = 'AIzaSyD0PGTaZiC3zJ4VeucasJ7NuSti9zNsLds'



# Define the custom filter function
def to_iso_string(value):
    """Convert a datetime object to ISO format string."""
    return value.isoformat() if isinstance(value, datetime) else value

app.jinja_env.filters['to_iso_string'] = to_iso_string


# Function to upload image and get URL
def upload_image_to_firebase(image_file, image_name):
    bucket = storage.bucket()
    blob = bucket.blob(image_name)
    blob.upload_from_filename(image_file)

    # Make the blob publicly viewable
    blob.make_public()

    return blob.public_url



# Note: Replace <DATABASE_NAME> with your actual database name from Firebase console.

# Function to add listings to Realtime Database
def add_listings_to_realtime_db(listings_data):
    logging.debug("Starting to add listings to Realtime Database.")
    ref = db.reference('/listings')
    for listing in listings_data:
        try:
            # Attempt to push each listing to the Realtime Database under 'listings' node
            push_result = ref.push().set(listing)
            # Log the successful addition of a listing
            print(f"Successfully added listing: {listing['name']}")  # Print to console
            logging.debug(f"Successfully added listing: {listing['name']} with push result: {push_result}")
        except Exception as e:
            # Log any errors encountered during the add operation
            print(f"Error adding listing {listing['name']}: {e}")  # Print to console
            logging.error(f"Error adding listing {listing['name']}: {e}")
    print("Finished adding listings to Realtime Database.")  # Print completion message to console
    logging.debug("Finished adding listings to Realtime Database.")


"""""
@app.route('/add-listings')
def add_listings_route():
    add_listings_to_realtime_db(listings)
    return "Listings added to Realtime Database", 200
"""


@app.route('/')
def home():
    ref = db.reference('/listings')
    # Retrieve 'listings' from Realtime Database
    listings_data = ref.get() or {}
    # Convert the listings data from dictionary to list of dictionaries for compatibility
    realtime_listings = [v for v in listings_data.values()]
    return render_template('welcome.html', listings=realtime_listings)


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        data = request.form.to_dict()
        ref = db.reference('/listings')
        ref.push().set(data)
        return redirect(url_for('home'))
    return render_template('submit_listing.html')





@app.route('/register_business')
def register_business():
    return render_template('register_business.html')



@app.route('/discounts')
def discounts():
    # Initialize logging
    logging.basicConfig(level=logging.DEBUG)

    # Reference to your Firebase Realtime Database listings
    ref = db.reference('/listings')
    listings_data = ref.get()

    # If listings are found, pass them to the template
    if listings_data:
        # Sort the listings by name
        sorted_listings = sorted(listings_data.items(), key=lambda item: item[1]['name'].lower())
        # Convert the sorted listings to a list including the 'id' key from Firebase
        listings = [{**value, 'id': key} for key, value in sorted_listings]
    else:
        # Handle the case where no listings are found
        listings = []

    # Log the image URLs for debugging
    for listing in listings:
        logging.debug(f"Image URL for {listing['name']}: {listing['image_url']}")

    # Render the discounts page with the sorted listings
    return render_template('discounts.html', listings=listings)




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return "Passwords do not match.", 400

        try:
            # Create user in Firebase Authentication
            user_record = auth.create_user(
                email=email,
                password=password
            )
            # UID can be used to uniquely identify the user
            user_id = user_record.uid

            # Store additional information in Realtime Database
            ref = db.reference('users')
            ref.child(user_id).set({
                'username': username,
                'email': email
            })

            return redirect(url_for('home'))
        except firebase_admin.exceptions.FirebaseError as e:
            return f"Firebase Error: {e}", 500
        except Exception as e:
            return f"An error occurred: {e}", 500

    return render_template('register.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}"

        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})

        response = requests.post(url, headers=headers, data=data)

        if response.ok:
            user_data = response.json()
            session['user_email'] = email
            session['user_id'] = user_data['localId']
            return redirect(url_for('home'))
        else:
            error_message = response.json()['error']['message']
            # Log for debugging
            app.logger.debug(f"Sign in failed with status code {response.status_code}: {error_message}")
            return f"Sign in failed: {error_message}", response.status_code  # Return the actual status code from Firebase

    return render_template('signin.html')


@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the home page
    return redirect(url_for('home'))


@app.route('/item_detail/<string:listing_id>')
def item_detail(listing_id):
    # Fetch the listing details from the database using the listing_id
    ref = db.reference(f'/listings/{listing_id}')  # Adjust the path according to your database structure
    listing = ref.get()
    if not listing:
        # Handle the case where the listing is not found
        return "Listing not found", 404

    # Render the item_detail template with the listing details
    return render_template('item_detail.html', listing=listing)


@app.route('/search_suggestions')
def search_suggestions():
    search_term = request.args.get('search_term', '').lower()
    print("Search term:", search_term)  # Log the search term
    ref = db.reference('listings')  # Adjust path according to your Firebase structure
    listings_data = ref.get()

    if listings_data:
        all_listings = [listing.get('name', '') for listing in listings_data.values()]
        suggestions = [name for name in all_listings if search_term in name.lower()]
        print("Suggestions:", suggestions)  # Log the suggestions
    else:
        suggestions = []

    return jsonify({'suggestions': suggestions})


def query_user_favorites(user_id):
    """
    Query the database for the user's favorites.

    :param user_id: The unique identifier for the user.
    :return: A list of favorite listings or None if there are no favorites.
    """
    ref = db.reference(f'users/{user_id}/favorites')
    user_favorites = ref.get()

    if user_favorites:
        # Assuming the favorites are stored as a list of listing IDs
        # Fetch the details of the listings
        listings_ref = db.reference('listings')
        favorite_listings = []
        for fav_id in user_favorites:
            listing = listings_ref.child(fav_id).get()
            if listing:
                favorite_listings.append(listing)
        return favorite_listings
    return None

@app.route('/favorites')
def favorites():
    user_id = session.get('user_id')
    print(f"Fetching favorites for user: {user_id}")

    if user_id:
        try:
            user_favorites = query_user_favorites(user_id)
            print(f"User favorites found: {user_favorites}")

            if user_favorites is not None:
                return render_template('favourite.html', user_favorites=user_favorites)
            else:
                print("No favorites found for the user.")
                return render_template('favourite.html', error="No favorites found.")
        except Exception as e:
            print(f"An error occurred while fetching user favorites: {e}")
            return render_template('favourite.html', error="An error occurred.")
    else:
        print("User not logged in, redirecting to login.")
        return redirect(url_for('login'))


@app.route('/toggle_favorite/<listing_id>', methods=['POST'])
def toggle_favorite(listing_id):
    user_id = session.get('user_id')
    print("User ID:", user_id)  # Debug print

    if user_id:
        try:
            result = toggle_user_favorite(user_id, listing_id)
            if result is None:
                return jsonify({'error': 'Failed to toggle favorite'}), 500

            print("Favorite Toggled Successfully")  # Debug print
            return jsonify({'isFavorite': result}), 200
        except Exception as e:
            print("Error:", str(e))  # Debug print
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'User not logged in'}), 401



def toggle_user_favorite(user_id, listing_id):
    try:
        print("User ID:", user_id)  # Debug print

        # Reference to the user's favorites in the database
        ref = db.reference(f'users/{user_id}/favorites')

        # Get the current list of favorites for the user
        favorites = ref.get() or []

        print("Current Favorites:", favorites)  # Debug print

        if listing_id in favorites:
            # If the listing is currently a favorite, remove it
            favorites.remove(listing_id)
            now_favorite = False
        else:
            # If the listing is not a favorite, add it
            favorites.append(listing_id)
            now_favorite = True

        # Update the database with the new list of favorites for the user
        ref.set(favorites)
        print("Favorites Updated Successfully")  # Debug print
        return now_favorite
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error toggling favorite for user {user_id} and listing {listing_id}: {str(e)}")
        return None

@app.route('/fetch_user_favorites', methods=['GET'])
def fetch_user_favorites():
    user_id = session.get('user_id')
    print("User ID:", user_id)  # Debug print

    if user_id:
        try:
            # Reference to the user's favorites in the database
            ref = db.reference(f'users/{user_id}/favorites')

            # Get the current list of favorites for the user
            favorites = ref.get() or []
            print("Favorites:", favorites)  # Debug print

            return jsonify({'favorites': favorites}), 200
        except Exception as e:
            print("Error:", str(e))  # Debug print
            return jsonify({'error': str(e)}), 500
    else:
        print("User not logged in")  # Debug print
        return jsonify({'error': 'User not logged in'}), 401

@app.route('/profile')
def profile():
    # Fetch user-specific data from the database based on the logged-in user's ID
    user_id = session.get('user_id')
    if user_id:
        user_ref = db.reference('users').child(user_id)
        user_data = user_ref.get()
        orders = user_data.get('orders', [])
        co2_saved = user_data.get('co2_saved', 0)
        money_saved = user_data.get('money_saved', 0)

        # Debugging: Print fetched user data
        print("User Profile Data:", user_data)

        # Render the profile page with the fetched data
        return render_template('profile.html', orders=orders, co2_saved=co2_saved, money_saved=money_saved)
    else:
        # Debugging: Print user not logged in message
        print("User not logged in")
        return "User not logged in", 401


@app.route('/make_reservation', methods=['POST'])
def make_reservation():
    if request.method == 'POST':
        data = request.form.to_dict()
        # Store reservation details in the database as an order
        order_ref = db.reference('/orders')
        order_ref.push().set(data)

        # Update user profile with CO2 saved and money saved
        user_id = session.get('user_id')
        if user_id:
            user_ref = db.reference('users').child(user_id)
            user_data = user_ref.get()

            # Update CO2 saved
            co2_saved = user_data.get('co2_saved', 0) + 20
            user_ref.update({'co2_saved': co2_saved})

            # Calculate money saved based on original and discounted prices
            original_price = float(data['original_price'])
            discounted_price = float(data['discounted_price'])
            money_saved = user_data.get('money_saved', 0) + (original_price - discounted_price)
            user_ref.update({'money_saved': money_saved})

            # Add the reservation to the user's profile orders
            orders_ref = user_ref.child('orders')
            orders_ref.push().set(data)

            # Debugging: Print reservation made successfully message
            print("Reservation made successfully")

            return "Reservation made successfully", 200
        else:
            # Debugging: Print user not logged in message
            print("User not logged in")
            return "User not logged in", 401


@app.route('/insights', methods=['GET', 'POST'])
def insights():
    try:
        # Query the Firebase Realtime Database for the insights data
        ref = db.reference('/insights')
        insights_data = ref.get()

        # Debugging: Print insights_data to the console
        print('Insights Data:', insights_data)

        if request.method == 'POST':
            # Process the posted form data and possibly filter insights_data
            selected_restaurant = request.form.get('restaurant')
            print('Selected Restaurant:', selected_restaurant)

            if selected_restaurant:
                # Filter the insights_data based on the selected restaurant
                insights_data = {key: value for key, value in insights_data.items()
                                 if value['restaurant_name'] == selected_restaurant}

            # Debugging: Print the filtered insights data to the console
            print('Filtered Insights Data:', insights_data)

        # Pass the insights data to the HTML template
        return render_template('insights.html', insights_data=insights_data)
    except Exception as e:
        # If any exceptions occur, print the stack trace to the console

        # Optionally, return a custom error message or template
        return jsonify({'error': 'An error occurred while processing insights data'}), 500

@app.route('/sustainability')
def sustainability():
    return render_template('about.html')

@app.route('/submit_business_registration', methods=['GET', 'POST'])
def register_business_two():
    if request.method == 'POST':
        # Extract data from form
        business_name = request.form.get('businessName')
        business_type = request.form.get('businessType')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        description = request.form.get('description')
        username = request.form.get('username')
        password = request.form.get('password')

        # Here, you should add the code to store this data in your database
        # For example, saving data to a SQL database or sending to an API

        # After storing data, you might want to send a confirmation email or log the registration

        flash('Business registered successfully!')
        return redirect(url_for('home'))  # Redirect to the homepage or a confirmation page
    else:
        # Render the form to register a business
        return render_template('register_business_two.html')


# Algolia Places API endpoint
ALGOLIA_PLACES_ENDPOINT = "https://places-dsn.algolia.net/1/places/query"

# Algolia Places API key
ALGOLIA_API_KEY = "YOUR_ALGOLIA_API_KEY_HERE"

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    input_text = request.args.get('input')  # Get the text input from the request
    print("Input Text:", input_text)  # Debug print

    # Make a request to the Algolia Places API
    headers = {
        "X-Algolia-API-Key": "e9ba53f8430b291ffb3e3674406349a6",
        "X-Algolia-Application-Id": "plY1TL7FHP8X"
    }
    params = {
        'query': input_text,
        'type': 'address',
        'countries': ['uk']  # Optionally, specify the countries to restrict the search
    }

    response = requests.post(ALGOLIA_PLACES_ENDPOINT, headers=headers, json=params)
    print("API Request URL:", response.url)  # Debug print

    data = response.json()
    print("API Response:", data)  # Debug print

    # Extract the suggestions from the response and return them
    if 'hits' in data:
        suggestions = [hit['locale_names'][0] for hit in data['hits']]
        print("Suggestions:", suggestions)  # Debug print
        return jsonify(suggestions)
    else:
        print("No suggestions found.")  # Debug print
        return jsonify([])  # Return an empty list if no suggestions are found


# Route for serving the charity registration form
@app.route('/register_charity', methods=['GET'])
def register_charity():
    return render_template('charity.html')

# Route for submitting the charity registration form
@app.route('/submit_charity_registration', methods=['POST'])
def submit_charity_registration():
    # Retrieve form data
    business_name = request.form.get('businessName')
    business_type = request.form.get('businessType')
    address = request.form.get('address')
    email = request.form.get('email')
    phone = request.form.get('phone')
    description = request.form.get('description')
    username = request.form.get('username')
    password = request.form.get('password')

    # Store the data in Firebase Realtime Database
    ref = db.reference('charity_registrations')  # Reference to the 'charity_registrations' node
    new_registration_ref = ref.push()  # Generate a new unique key for the registration
    new_registration_ref.set({
        'business_name': business_name,
        'business_type': business_type,
        'address': address,
        'email': email,
        'phone': phone,
        'description': description,
        'username': username,
        'password': password
    })

    return "Charity registration submitted successfully!"


if __name__ == '__main__':
    app.run(debug=True)
