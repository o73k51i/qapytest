# Test Data Generation with Faker

QaPyTest includes the Python Faker library for generating realistic and diverse test data.

## What is Faker?

Faker is a library that generates fake but realistic data for testing purposes. It supports multiple locales and can generate:
- Personal information (names, emails, phone numbers)
- Addresses and locations
- Dates and times
- Text and paragraphs
- Internet data (URLs, domain names, IPs)
- Financial information (credit cards, IBANs)
- And much more

## Installation

Faker comes pre-installed with QaPyTest, no additional installation needed:

```python
from qapytest import Faker
```

## Basic Usage

```python
from qapytest import Faker

def test_user_creation():
    fake = Faker()
    
    # Generate different types of data
    user = {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address(),
        "username": fake.user_name()
    }
    
    # Use in test
    response = client.post("/users", json=user)
    assert response.status_code == 201
```

## Locale Support

Generate data in different languages and formats:

```python
from qapytest import Faker

# English (default)
fake_en = Faker('en_US')

# Other locales
fake_de = Faker('de_DE')        # German
fake_fr = Faker('fr_FR')        # French
fake_es = Faker('es_ES')        # Spanish
fake_uk = Faker('uk_UA')        # Ukrainian
fake_ja = Faker('ja_JP')        # Japanese
fake_zh = Faker('zh_CN')        # Chinese
```

## Faker Documentation

For more information about Faker:
- [Official Faker Documentation](https://faker.readthedocs.io/)