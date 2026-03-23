from app import app


def login(client, username, password):
    response = client.post(
        '/login',
        data={'username': username, 'password': password},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert '/dashboard' in response.request.path


def run():
    with app.test_client() as client:
        public_paths = ['/', '/login', '/manifest.json', '/sw.js', '/offline']
        for path in public_paths:
            response = client.get(path)
            assert response.status_code == 200, f'{path} returned {response.status_code}'

        login(client, 'student1', 'student123')
        for path in ['/dashboard', '/attendance', '/performance-analyzer', '/transport', '/library', '/fees', '/events', '/syllabus', '/profile']:
            response = client.get(path)
            assert response.status_code == 200, f'student {path} returned {response.status_code}'
        client.get('/logout')

        login(client, 'faculty1', 'faculty123')
        for path in ['/dashboard', '/attendance', '/qr-attendance', '/performance-analyzer', '/transport', '/library', '/risk-analysis', '/events', '/syllabus', '/profile', '/manage-fees']:
            response = client.get(path)
            assert response.status_code == 200, f'faculty {path} returned {response.status_code}'

        response = client.post(
            '/generate-qr',
            data={'subject': 'Distributed Systems', 'latitude': '12.9716', 'longitude': '77.5946'},
            follow_redirects=True
        )
        assert response.status_code == 200

        response = client.post('/notify-risk/4', follow_redirects=True)
        assert response.status_code == 200

        response = client.post('/schedule-meeting/4', follow_redirects=True)
        assert response.status_code == 200

        response = client.post('/send-notification/1', follow_redirects=True)
        assert response.status_code == 200
        client.get('/logout')

        login(client, 'admin', 'admin123')
        for path in ['/dashboard', '/performance-analyzer', '/transport', '/library', '/manage-fees', '/events', '/syllabus', '/admin-panel', '/profile']:
            response = client.get(path)
            assert response.status_code == 200, f'admin {path} returned {response.status_code}'

        response = client.post(
            '/add-user',
            data={
                'username': 'student4',
                'email': 'student4@smartcampus.com',
                'password': 'student123',
                'role': 'student',
                'full_name': 'New Student',
                'roll_number': 'CS2024999'
            },
            follow_redirects=True
        )
        assert response.status_code == 200

        response = client.post('/delete-event/1', follow_redirects=True)
        assert response.status_code == 200


if __name__ == '__main__':
    run()
    print('smoke-test-ok')
