# Credit Exchange

[![Python 3.9](https://img.shields.io/badge/Python-3.9-green.svg)](https://shields.io/)
[![Django](https://img.shields.io/badge/Django_Rest_Framework-3.14-355E3B)](https://shields.io/)

This is a Django Rest Framework project for selling charges and keeping logs for them.

## Data Model

We have two tables in the project; Seller and Transaction. Seller table keeps each business information,
and Transaction keeps the log of transactions.

#### Sellers

| Name       | Type         | Optional |
|------------|--------------|----------|
| id         | INTEGER      | False    |
| username   | varchar(50)  | False    |
| password   | varchar(128) | False    |
| credit     | INTEGER      | False    |
| is_active  | BOOL         | False    |
| is_staff   | BOOL         | False    |
| created_at | DATETIME     | False    |
| updated_at | DATETIME     | False    |

#### Transactions

| Name           | Type        | Optional |
|----------------|-------------|----------|
| id             | INTEGER     | False    |
| user           | Seller      | False    |
| type           | varchar(2)  | False    |
| datetime       | DATETIME    | False    |
| receiver       | VARCHAR(20) | True     |
| amount         | INTEGER     | False    |
