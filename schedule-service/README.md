# JWTAuth

This is a REST API built using the Go programming language, leveraging the [Gin](https://github.com/gin-gonic/gin) framework for handling HTTP requests. The API provides several endpoints for working with schedule.

## 📖 Table of Contents

- [📥 Installation and Setup](#-installation-and-setup)
- [🌐 Base endpoints](#-base-endpoints)
- [✅ Testing](#-testing)
- [📜 License](#-license)

## 📥 Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/zefixed/raspyx2.git
cd raspyx2
```

> ❗ Before using rename `.env.example` to `.env` and set up your parameters

### 📦 Docker Setup

To run the application with Docker, follow these steps:

0. Set up the auth microservice: https://github.com/zefixed/JWTAuth

1. Run the docker-compose:

   ```bash
   make docker-build-up-local
   ```

2. Migrate the database:

   ```bash
   make migrate-up
   ```

## 🌐 Base Endpoints
After starting the service, the following endpoints will be available:

Base URL: `http://localhost:8080/raspyx/api/v2`  
[API Documentation](http://localhost:8080/raspyx/api/v2/swagger/index.html)

## ✅ Testing

To test the API, you can use [Postman](https://www.postman.com/) or [cURL](https://curl.se/). You can also set up unit tests in the project using:

```bash
go test -v ./...
```

## 📜 License

This project is licensed under the GNU License v3 - see the [LICENSE](LICENSE) file for details.
