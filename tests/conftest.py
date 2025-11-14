import pytest
from app import create_app, db
from config import TestingConfig

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('TestingConfig')
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(autouse=True)
def setup_database(app):
    """Setup and teardown database for each test"""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing"""
    # Register test user
    user_data = {
        'email': 'test@example.com',
        'username': 'testuser',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    client.post('/api/auth/register', json=user_data)
    
    # Login to get token
    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    if login_response.status_code == 200:
        token = login_response.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    return {}

@pytest.fixture
def sample_hotel():
    """Create a sample hotel for testing"""
    from app.models import Hotel
    
    hotel = Hotel(
        name='Test Hotel',
        description='A test hotel for testing',
        address='123 Test Street',
        city='Windhoek',
        country='Namibia',
        star_rating=4,
        amenities=['WiFi', 'Pool'],
        images=['hotel1.jpg']
    )
    
    db.session.add(hotel)
    db.session.commit()
    
    return hotel

@pytest.fixture
def sample_room_type(sample_hotel):
    """Create a sample room type for testing"""
    from app.models import RoomType
    
    room_type = RoomType(
        hotel_id=sample_hotel.id,
        name='Standard Room',
        description='A standard room',
        base_price=100.00,
        max_occupancy=2,
        bed_type='Queen'
    )
    
    db.session.add(room_type)
    db.session.commit()
    
    return room_type

@pytest.fixture
def sample_rooms(sample_room_type):
    """Create sample rooms for testing"""
    from app.models import Room
    
    rooms = []
    for i in range(3):
        room = Room(
            hotel_id=sample_room_type.hotel_id,
            room_type_id=sample_room_type.id,
            room_number=f'10{i+1}',
            floor=1
        )
        rooms.append(room)
        db.session.add(room)
    
    db.session.commit()
    return rooms
