# Telegram bot: Decide restaurant for lunch

## Introduction

Randomly decide restaurant for lunch every weekdays.

## How to use

1. Create a `.env` file in the root of project folder containing the environment variables, 

    ```
    TOKEN=<your token here>
    CHAT_ID=<your chat id here>
    MSG_TIME=12:15
    ```

2.  choose either option below to run the application:

    ### Option 1: Python

    1. Set your `MSG_TIME` in `app/main.py`
    2. Set your `TOKEN` and `CHAT_ID` in `app/tg/config.py`
    3. Start the application with the following command:

    ```sh
    cd app/
    pip install -r requirements.txt
    python main.py
    ```

    ### Option 2: Docker Compose

    1. Set your `MSG_TIME`, `TOKEN` and `CHAT_ID` in `docker-compose.yml`
    2. Start the container with the following command:

    ```sh
    docker-compose up -d
    ```
