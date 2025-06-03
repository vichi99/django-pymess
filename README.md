# Django-Pymess
[![Coverage Status](https://coveralls.io/repos/github/skip-pay/django-pymess/badge.svg?branch=add_test_scaffolding)](https://coveralls.io/github/skip-pay/django-pymess?branch=add_test_scaffolding)
[![PyPI version](https://badge.fury.io/py/skip-django-pymess.svg)](https://badge.fury.io/py/skip-django-pymess)

Django-pymess is a comprehensive Django framework for sending various types of messages including SMS, Push notifications, and E-mails. It provides a unified interface for multiple messaging services and backends.

## Features

- **Multiple Message Types Support**:
  - SMS messages
  - E-mail messages
  - Push notifications
  - Dialer messages (voice calls)

- **Flexible Backend System**:
  - Multiple backend support for each message type
  - Easy to implement custom backends
  - Built-in backends for popular services

- **Template System**:
  - Support for message templates
  - Context-based message rendering
  - Multi-language support

- **Message Management**:
  - Message state tracking
  - Delivery status monitoring
  - Batch sending capabilities
  - Message retry functionality

## Installation

Install using pip:

```bash
pip install skip-django-pymess
```

Add 'pymess' to your INSTALLED_APPS in settings.py:

```python
INSTALLED_APPS = (
    ...
    'pymess',
    ...
)
```

## Development Installation

For development purposes, follow these steps:

1. Create virtual environment for the project and activate it.

2. Clone the repository:
```bash
git clone https://github.com/skip-pay/django-pymess.git
cd django-pymess
```

3. Install development dependencies:
```bash
make install-dev
```

4. Run tests to verify your setup:
```bash
make test
```

## Documentation

For detailed documentation, please see:
[Documentation](https://github.com/skip-pay/django-pymess/tree/master/docs)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
