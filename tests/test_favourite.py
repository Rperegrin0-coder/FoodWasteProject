def test_favorites_page(client):
    """ Test that the favorites page loads correctly """
    client.post('/signin', data={
        'email': 'test@example.com',
        'password': 'securepassword'
    })
    response = client.get('/favorites')
    assert response.status_code == 200
    assert b"Favorites" in response.data  # Check for favorites content

def test_add_to_favorites(client):
    """ Simulate adding an item to favorites """
    client.post('/signin', data={
        'email': 'test@example.com',
        'password': 'securepassword'
    })
    response = client.post('/toggle_favorite/1')  # Assuming '1' is a valid listing ID
    assert b"successfully added" in response.data  # Adjust assertion based on actual response
