# Email Fetcher Application

This application connects to an email server using either IMAP or POP3, fetches new emails, and stores them in a PostgreSQL database. It also tracks whether each email has been processed using a `processed` flag.

## Features

- Fetches emails from an email server (IMAP/POP3).
- Stores email details in a PostgreSQL database.
- Creates a table if it does not exist and includes a `processed` flag.

## Requirements

- Python 3.11
- Docker (for containerization)
- Docker Compose (optional, for easier management)

## Configuration

Before running the application, set up a `.env` file in the `/app` directory with the following content:

```plaintext
# Mail Server Settings
IMAP_HOST=imap.mailserver.com
POP_HOST=pop.mailserver.com
MAIL_USERNAME=your-email@mail.com
MAIL_PASSWORD=your-password
MAIL_PROTOCOL=imap  # Set to 'imap' or 'pop3'

# Database Settings
DB_HOST=db  # Use the service name defined in the docker-compose.yml
DB_USER=user
DB_PASSWORD=password
DB_NAME=email_db
DB_PORT=5432
```

# Running with Docker Compose

To build and run the application with Docker Compose, follow these steps:

## Build and start the services:

```bash
docker-compose up --build
```

To stop the services, use:

```bash
docker-compose down
```
## Running Without Docker Compose

If you prefer to run the PostgreSQL database without Docker Compose, you can use the following command:

```bash
docker run -e POSTGRES_DB=email_db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -p 5432:5432 postgres
```

After starting the PostgreSQL container, run your application using the following command :

```bash
python app/app.py
```

# License

This project is licensed under the MIT License - see the LICENSE file for details.