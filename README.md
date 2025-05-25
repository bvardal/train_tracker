# Train tracker

## Purpose
Fulfil my personal requirements for a service that can:
* List upcoming GWR train services from one station to another, ordered by arrival time
* Allow a user to track a selected service and provide updates if any details change until departure
* Send messages to the user (using Telegram because it allows me to do that for free)

## Dependencies
* Docker or local install of Python 3.13
* Python requests library
* Telegram bot token
* RailData access tokens for "Live Departure Board" and "Service" endpoints (requires an account)
