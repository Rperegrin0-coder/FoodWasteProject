import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, db, auth
import logging
from google.auth.transport import requests
from flask_session import Session
import requests
from firebase_admin import storage

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

        # Correctly use the requests.post method
        response = requests.post(url, headers=headers, data=data)

        if response.ok:
            user_data = response.json()
            session['user_email'] = email
            session['user_id'] = user_data['localId']
            # Redirect to home page or wherever you like
            return redirect(url_for('home'))
        else:
            # Extract error message
            error_message = response.json()['error']['message']
            return f"Sign in failed: {error_message}", 400

    # Render the sign-in page if method is GET or authentication fails
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




if __name__ == '__main__':
    app.run(debug=True)
