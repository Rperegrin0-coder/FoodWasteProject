from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db
import logging

# Initialize Flask app
app = Flask(__name__)

app.config['SERVER_NAME'] = '127.0.0.1:5000'
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https'


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# Firebase Admin SDK initialization
cred = credentials.Certificate('/Users/macbook/PycharmProjects/finalyearproject/finalyearproject-bf7bf-firebase-adminsdk-bywl6-5377e448e6.json')
default_app = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://finalyearproject-bf7bf-default-rtdb.firebaseio.com/'
})



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

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    # Perform search logic, possibly using a database search or a filter on 'listings'
    return render_template('search_results.html', results=search_results)


@app.route('/discounts')
def discounts():
    listings = [
        {'name': 'Café Good Beans',
         'description': 'Assorted pastry box',
         'original_price': '20.00',
         'discounted_price': '10.00',
         'pickup_time': '5 PM - 6 PM',
         'image_url': url_for('static', filename='coffee.jpg')
         },
        {'name': 'Green Grocers', 'description': 'Vegetable surprise pack', 'original_price': '15.00',
         'discounted_price': '7.50', 'pickup_time': '6 PM - 7 PM',
         'image_url': url_for('static', filename='retailer1.jpg')

         },
        {'name': 'Mama’s Pizzeria', 'description': 'Mystery pizza combo', 'original_price': '25.00',
         'discounted_price': '12.50', 'pickup_time': '8 PM - 9 PM',
         'image_url': url_for('static', filename='Pizza.jpg')

         },
        {'name': 'The Soup Kitchen', 'description': 'Homestyle soup selection', 'original_price': '18.00',
         'discounted_price': '9.00', 'pickup_time': '2 PM - 3 PM',
         'image_url': url_for('static', filename='soup.webp')

         },
        {'name': 'Bread and Butter', 'description': 'Artisan bread basket', 'original_price': '12.00',
         'discounted_price': '6.00', 'pickup_time': '10 AM - 11 AM',
        'image_url': url_for('static', filename='bread.jpg')
         },
        {'name': 'Sweet Tooth', 'description': 'Assorted cupcakes and sweets', 'original_price': '22.00',
         'discounted_price': '11.00', 'pickup_time': '3 PM - 4 PM'},
        {'name': 'Daily Deli', 'description': 'Deli sandwich platter', 'original_price': '30.00',
         'discounted_price': '15.00', 'pickup_time': '1 PM - 2 PM'},
        {'name': 'Healthy Habits', 'description': 'Mixed fruit and veggie crate', 'original_price': '20.00',
         'discounted_price': '10.00', 'pickup_time': '9 AM - 10 AM'},
        {'name': 'Grill Masters', 'description': 'BBQ family pack', 'original_price': '45.00',
         'discounted_price': '22.50', 'pickup_time': '7 PM - 8 PM'},
        {'name': 'Ocean Bites', 'description': 'Seafood sampler', 'original_price': '50.00',
         'discounted_price': '25.00', 'pickup_time': '6 PM - 7 PM'}
        # Continue adding more listings as necessary
    ]

    # Your route implementation
    return render_template('discounts.html', listings=listings)


if __name__ == '__main__':
    app.run(debug=True)

