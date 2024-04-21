def test_discounts_loading(client):
    """ Test the discounts page loads correctly """
    response = client.get('/discounts')
    assert response.status_code == 200
    assert b"Discounts" in response.data  # Ensure some part of the discounts content is in the response
