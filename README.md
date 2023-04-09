# Documentation
Grabs financial data via AlphaVantage with the get_raw_data script and inserts it into the database. Data can be retrieved
via the /api/financial_data or /api/statistics routes. 

Requirements found via: https://github.com/G123-jp/python_assignment

### Technology Details
MySQL 8 (Adminer 4.8.1)
Python 3.6 (Local machine current version)
Docker 4.18.0 (104112)
Windows 10
GitHub https://github.com/arguingcrab/g123


### Quickstart
Make virtual local env to run get_raw_data
`py -3 -m venv env`

To activate the local environment and successfully run get_raw_data
`. env/Scripts/activate`

Upgrade pip and install requirements
`python -m pip install --upgrade pip`
`pip install -r requirements.txt`

Start Docker
`docker compose up -d`
or `docker compose up --force-recreate -d --build` to rebuild 

When docker is finished starting, grab data from the API
`python get_raw_data.py`
duplicate data will not be pulled into the db

Get data from database via curl or front end
http://localhost:5000/api/statistics
http://localhost:5000/api/financial_data

example:
`curl -X GET 'http://localhost:5000/api/financial_data?start_date=2023-01-01&end_date=2023-01-14&symbol=IBM&limit=3&page=2'`
`curl -X GET http://localhost:5000/api/statistics?start_date=2023-01-01&end_date=2023-01-31&symbol=IBM`

### Exception Handling
	- Prevent sql injection in the getter of the url when using the financial_data or statistics routes
	- Returns "No Data" when no data is found within date range and symbol
	- Returns 400 Bad request "format is invalid" when start_date, end_date, limit, page is invalid type


### API
Local key is kept in the config.py file unless an environment key is provided from the server


# General
### DB
URL: http://localhost:8080/
System: MySQL
Server: db
Username: root
Password: password
Database: dev


### Front End
URL: http://localhost:5000/

# Commands
`. env/Scripts/activate` for the environment
`py get_raw_data.py` to grab data

`docker compose up -d`
or `docker compose up --force-recreate -d --build` to rebuild 

`docker compose down` to break down containers: app, db, adminer (front end db)


### Troubleshooting
Docker compose erroring?
End process and run this in powershell
`wsl --unregister docker-desktop`
`wsl --unregister docker-desktop-data`