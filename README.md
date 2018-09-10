Social app Python
---
Core
---
* Python 3.6.5
* Django 2.0.5
* Tastypie

Run Project (Using Visual Studio Code)
---
- Clone Project
- Open project, then open terminal and work as follows
    - manager.py makemigrations (create migrations)
    - manager.py migrate (create table based on migrations)
    - manager.py createsuperuser (create admin user)
    - manager.py runserver (start server, default: http://127.0.0.1:8000)

API Authentication
---
* Sign In (Post): http://127.0.0.1:8000/api/v1/authentication/sign_in/

    {
	"username": "your_username",
	"password": "your_password"
    }
    * If correct, data return:

        {
            "api_key": "user_apikey",
            "id": "user_id",
            "success": true,
            "username": "your_username"
        }
    * Else:

        {
            "reason": "incorrect",
            "success": false
        }
* Sign Out (Get): http://127.0.0.1:8000/api/v1/authentication/sign_out/
    * If you signin before, return:

        {
            "success": true
        }
    * Else:

        {
            "error_message": "You are not authenticated, False",
            "success": false
        }
* Sign Up (Post): http://127.0.0.1:8000/api/v1/authentication/sign_up/

    {
        "username":"your_username",
        "password":"your_password",
        "first_name":"some_thing",
        "last_name":"some_thing",
        "email":"some_thing",
        "other_name":"some_thing",
        "address":"some_thing",
        "phone_number":"your_phoneNumber"
        "birth_day":"your_birthday"
    }
    * If success:

        {
            "api_key": "account_apikey",
            "id": "account_id",
            "success": true,
            "username": "account_username"
        }
    * Else return error

User Profile
---
* To see profile of all user (GET): http://127.0.0.1:8000/api/v1/user-profile/?username={username}&api_key={api_key}
    - Data return is object list
* To update my profile (PUT): http://127.0.0.1:8000/api/v1/user-profile/{userprofile_id}/?username={username}&api_key={api_key}

    {
        "address": "some_thing",
        "other_name": "some_thing",
        "phone_number": "phone_number",
        "photo_url": "",
        "first_name":"some_thing",
        "last_name":"some_thing"
    }
    - If success: Status 204
    - Else, return error