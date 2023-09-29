from OpenMediaMatch.tests.utils import app, client


def test_status_response(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.data == b"I-AM-ALIVE\n"


def test_banks_index(client):
    response = client.get("/c/banks")
    assert response.status_code == 200
    assert response.json == []
