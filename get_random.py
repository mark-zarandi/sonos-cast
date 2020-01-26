import json
import requests

if __name__ == "__main__":
	r = requests.get('http://localhost:5000/random/1')
	the_choice = r.json()
	print the_choice['location']