from api import TATHashListAPI

api = TATHashListAPI(username='e3zTLn3L', password='6iA@EQg4BMH&zQD!')
response = api.get_hash_list('test')
print("Response >>> ", response)
