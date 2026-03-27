
CLUSTERS = [
    # 1. CI/CD Pipeline
    [
        "Jenkinsfile, configuration file, /project-root, opened with VSCode, defines CI/CD pipeline stages",
        "docker build -t myapp:latest ., command, executed in terminal, builds a Docker image from Dockerfile",
        "docker push myapp:latest, command, executed in terminal, pushes image to container registry",
        "pytest tests/, command, executed in terminal, runs automated test suite",
        "github-actions, website, /actions, browser, monitors workflow execution and logs",
        "sonarqube, application, /usr/local/bin, code quality tool, analyzes code coverage and issues",
        "kubectl apply -f deployment.yaml, command, executed in terminal, deploys application to Kubernetes",
    ],

=> Cluster 01 — CI/CD Pipeline
  Items    : 7
  Prédit   : Configure and manage CI/CD pipelines for applications



    # 2. Data Science / ML Experiment
    [
        "notebook.ipynb, Jupyter notebook, /experiments, opened with JupyterLab, contains data exploration and model training code",
        "dataset.csv, CSV file, /data/raw, opened with pandas, stores raw training data",
        "sklearn, application, /site-packages, Python library, provides machine learning algorithms",
        "matplotlib, application, /site-packages, Python library, generates plots and visualizations",
        "pip install xgboost, command, executed in terminal, installs gradient boosting library",
        "mlflow, application, /usr/local/bin, experiment tracking tool, logs model metrics and parameters",
        "model.pkl, pickle file, /models, saved artifact, stores trained model for deployment",
        "wandb, website, /dashboard, browser, visualizes training metrics and experiment comparisons",
    ],

=> Cluster 02 — Data Science / ML Experiment
  Items    : 8
  Prédit   : Monitor and manage model training and performance



    # 3. Database Migration
    [
        "migration_v2.sql, SQL file, /db/migrations, opened with VSCode, contains schema alteration scripts",
        "pg_dump -U admin mydb > backup.sql, command, executed in terminal, creates a database backup",
        "psql -U admin mydb < migration_v2.sql, command, executed in terminal, applies migration to database",
        "dbeaver, application, /usr/local/bin, database GUI, browses tables and runs queries",
        "schema.dbml, DBML file, /docs, opened with VSCode, documents new database structure",
        "alembic upgrade head, command, executed in terminal, runs pending migration scripts",
    ],

=> Cluster 03 — Database Migration
    Items    : 6
    Prédit   : Deploy and manage database schema migrations


    # 4. Security Audit
    [
        "nmap -sV 192.168.1.0/24, command, executed in terminal, scans network for open ports and services",
        "burpsuite, application, /opt, security testing tool, intercepts and analyzes HTTP traffic",
        "audit-report.md, markdown file, /reports, opened with VSCode, documents identified vulnerabilities",
        "owasp-zap, application, /opt, vulnerability scanner, detects common web application flaws",
        "nessus, website, /scan, browser, displays vulnerability assessment results",
        "ssh-keygen -t ed25519, command, executed in terminal, generates a secure SSH key pair",
        "openssl s_client -connect example.com:443, command, executed in terminal, checks SSL certificate details",
    ],

=> Cluster 04 — Security Audit
  Items    : 7
  Prédit   : Audit and analyze web application vulnerabilities



    # 5. Mobile App Development (React Native)
    [
        "App.tsx, TypeScript file, /src, opened with VSCode, main entry point of the React Native application",
        "styles.ts, TypeScript file, /src/styles, opened with VSCode, defines global styling constants",
        "npx react-native run-android, command, executed in terminal, builds and launches app on Android emulator",
        "expo, application, /node_modules, JavaScript framework, provides development and preview tools",
        "figma, website, /design, browser, displays UI mockups and component specifications",
        "redux-toolkit, application, /node_modules, JavaScript library, manages global application state",
        "adb logcat, command, executed in terminal, streams device logs for debugging",
        "jest --watchAll, command, executed in terminal, runs unit tests in watch mode",
    ],

=> Cluster 05 — Mobile App Development
  Items    : 8
  Prédit   : Build and test a React Native application for Android and Android


    # 6. Cloud Infrastructure (AWS)
    [
        "main.tf, Terraform file, /infra, opened with VSCode, defines AWS infrastructure as code",
        "terraform plan, command, executed in terminal, previews infrastructure changes before applying",
        "terraform apply, command, executed in terminal, provisions cloud resources on AWS",
        "aws s3 sync ./dist s3://my-bucket, command, executed in terminal, uploads build artifacts to S3",
        "aws-console, website, /ec2, browser, monitors running instances and resource usage",
        "cloudwatch, website, /logs, browser, streams application logs and sets up alerts",
        "variables.tf, Terraform file, /infra, opened with VSCode, stores environment-specific configuration values",
    ],

=> Cluster 06 — Cloud Infrastructure (AWS)
  Items    : 7
  Prédit   : Set up and manage AWS infrastructure changes


    # 7. Technical Documentation
    [
        "api-reference.md, markdown file, /docs, opened with VSCode, documents REST API endpoints and parameters",
        "swagger.yaml, YAML file, /docs, opened with VSCode, defines OpenAPI specification for the API",
        "confluence, website, /wiki, browser, hosts internal technical documentation and runbooks",
        "readme.md, markdown file, /project-root, opened with VSCode, describes project setup and usage",
        "mkdocs serve, command, executed in terminal, previews documentation site locally",
        "draw.io, website, /diagrams, browser, creates architecture and flow diagrams",
        "grammarly, application, /browser-extension, writing assistant, checks grammar and clarity of docs",
    ],

=> Cluster 07 — Technical Documentation
  Items    : 7
  Prédit   : Write and manage technical documentation and runbooks


    # 8. E-commerce Backend
    [
        "product-service.py, Python file, /src/services, opened with VSCode, handles product CRUD operations",
        "payment-gateway.py, Python file, /src/integrations, opened with VSCode, integrates Stripe payment processing",
        "orders.json, JSON file, /src/fixtures, opened with VSCode, stores test order data for development",
        "stripe, website, /dashboard, browser, monitors transactions and payment events",
        "celery worker, command, executed in terminal, starts async task queue for order processing",
        "redis-cli, command, executed in terminal, inspects cache keys and session data",
        "postman, application, /usr/local/bin, API testing tool, sends HTTP requests to backend endpoints",
        "uvicorn main:app --reload, command, executed in terminal, starts FastAPI development server",
    ],
=>  Cluster 08 — E-commerce Backend
  Items    : 8
  Prédit   : Build and manage product services and payments


    # 9. Log Analysis & Debugging
    [
        "error.log, log file, /var/log/app, opened with VSCode, contains application error traces",
        "grep -r 'NullPointerException' ./logs, command, executed in terminal, searches for specific errors in log files",
        "kibana, website, /discover, browser, visualizes and filters log data from Elasticsearch",
        "sentry, website, /issues, browser, tracks and groups application exceptions in production",
        "strace -p 1234, command, executed in terminal, traces system calls of a running process",
        "journalctl -u myapp.service -f, command, executed in terminal, streams live service logs from systemd",
        "datadog, website, /apm, browser, displays distributed traces and performance metrics",
    ],

=>  Cluster 09 — Log Analysis & Debugging
  Items    : 7
  Prédit   : Monitor and analyze application error logs


        # 10. Team Onboarding Setup
    [
        "onboarding-checklist.md, markdown file, /docs/hr, opened with VSCode, lists setup steps for new developers",
        "git clone https://github.com/org/repo.git, command, executed in terminal, clones the main project repository",
        "npm install, command, executed in terminal, installs all project dependencies",
        "cp .env.example .env, command, executed in terminal, creates local environment configuration file",
        "notion, website, /workspace, browser, accesses company wiki and internal processes",
        "slack, website, /channels, browser, joins team communication channels",
        "1password, application, /usr/local/bin, password manager, retrieves shared credentials and API keys",
        ".env, environment file, /project-root, opened with VSCode, stores local development environment variables",
    ],

=> Cluster 10 — Team Onboarding Setup
  Items    : 8
  Prédit   : Configure and manage a new developer docs and environment configuration
]
