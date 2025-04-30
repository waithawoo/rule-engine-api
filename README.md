# Issara Rule Engine API

This is a lightweight Rule Engine API by using Django and Django REST Framework.

## Setup Instructions

Follow the steps below to set up the project on the local machine.

### 1. Clone the repository

```bash
git clone https://github.com/waithawoo/rule-engine-api.git
cd rule-engine-api
```

### 2. Prepare environment variables

Copy the example environment files. The default values are sufficient for local testing.

```bash
cp .env.example .env
cp src/.env.example src/.env
```

### 3. Start the Docker containers

Make the startup script executable and run it.

```bash
chmod +x start_docker.sh
./start_docker.sh
```

Wait until all services are up and running with **healthy** status.

### 4. Apply database migrations

Run the migrations inside the Docker container.

```bash
docker exec -it issara_api_server python manage.py migrate
```

### 5. Create user accounts

- **Admin account:**

```bash
docker exec -it issara_api_server python manage.py create_admin_user --email=admin@gmail.com --password=password
```

- **Client account:**

```bash
docker exec -it issara_api_server python manage.py create_client_user --email=client1@gmail.com --password=password
```

---

## **Once everything is set up,**

### Running Tests

To run unit and integration tests:

```bash
docker exec -it issara_api_server python manage.py test
```

### API Usage

To access the Swagger API documentation:

Go to [http://127.0.0.1:8000/swagger](http://127.0.0.1:8000/swagger)

For testing apis of rule evaluations, an example flow with the sample rule condition and payload will be provided.

- Login with admin acount in `/api/auth/login/`
- get the access token, use that token as 'Bearer {token}' to authenticate.
- create the following rule in `/api/rules`

```json
{
    "name": "Complex Eligibility",
    "condition": {
        "AND": [
            {
                "field": "applicant.age",
                "operator": ">=",
                "value": 18
            },
            {
                "OR": [
                    {
                        "AND": [
                            {
                                "field": "applicant.employment.status",
                                "operator": "==",
                                "value": "employed"
                            },
                            {
                                "field": "applicant.employment.years",
                                "operator": ">=",
                                "value": 2
                            }
                        ]
                    },
                    {
                        "AND": [
                            {
                                "field": "applicant.student",
                                "operator": "==",
                                "value": true
                            },
                            {
                                "field": "applicant.gpa",
                                "operator": ">=",
                                "value": 3.0
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "is_active": true
}
```

- Then evaluate the following payload in `/api/rule-evaluation/evaluate/`
- At this point, we can also use client user account in addtion to admin account.

```json
{
    "rules": [
        "Complex Eligibility"
    ],
    "payload": {
        "applicant": {
            "age": 30,
            "employment": {
                "status": "employed",
                "years": 5,
                "position": "Developer"
            },
            "student": false
        }
    }
}
```

- The response should be as follows.

```json
{
  "result": "APPROVED",
  "passed_rules": [
    "Complex Eligibility"
  ],
  "failed_rules": []
}
```

### Note on Asynchronous Evaluation

In addition to the synchronous rule evaluation endpoint, a separate asynchronous endpoint (`/api/rule-evaluation/evaluate_async/`) is provided. This allows long-running rule evaluations to be processed in the background using Celery.

The asynchronous evaluation flow is as follows:

- Call `/api/rule-evaluation/evaluate_async/` with rules and payload
- It will return a `task_id`
- Use the `task_id` in `/api/rule-evaluation/task_result/?task_id=...` to get the task result.
- The response should be task status or final evaluation result
