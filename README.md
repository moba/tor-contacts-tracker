# tor-contacts-tracker

Track Tor relay contacts over time and display changes (new and gone contacts). 

## Setup

    git clone https://github.com/moba/tor-contacts-tracker.git 

## Usage

    ./tor-contacts-tracker.py --download # downloads current dataset from onionoo
    ./tor-contacts-tracker.py --update [path_to_details_json] # import from details.json to local database 

    ./tor-contacts-tracker.py # prints changes within the last days (*)


## TODO

(*) currently, the timespan is not really useful apart from 'debugging' 
