import random
import uuid
import ipaddress
from datetime import datetime, date, timedelta

import numpy as np
import rstr
from faker import Faker


fake = Faker("en_IN")


def generate_numeric_value(column):
    distribution = column.distribution

    min_value = column.min if column.min is not None else 1
    max_value = column.max if column.max is not None else 100

    if distribution is None:
        return float(np.random.uniform(min_value, max_value))

    distribution_type = distribution.type.lower()

    if distribution_type == "uniform":
        low = distribution.min if distribution.min is not None else min_value
        high = distribution.max if distribution.max is not None else max_value
        return float(np.random.uniform(low, high))

    if distribution_type == "normal":
        mean = distribution.mean if distribution.mean is not None else 50
        std = distribution.std if distribution.std is not None else 10

        value = float(np.random.normal(mean, std))
        value = max(value, min_value)
        value = min(value, max_value)
        return value

    if distribution_type == "exponential":
        scale = distribution.mean if distribution.mean is not None else 10

        value = float(np.random.exponential(scale))
        value = max(value, min_value)
        value = min(value, max_value)
        return value

    return float(np.random.uniform(min_value, max_value))


def generate_boolean_value(column):
    distribution = column.distribution

    if distribution and distribution.type.lower() == "boolean_probability":
        true_probability = distribution.true_probability

        if true_probability is None:
            true_probability = 50

        return random.randint(1, 100) <= true_probability

    return random.choice([True, False])


def generate_category_value(column):
    values = column.values or []

    if not values:
        return None

    distribution = column.distribution

    if distribution and distribution.type.lower() == "weighted" and distribution.weights:
        weights = [distribution.weights.get(str(value), 0) for value in values]

        if sum(weights) > 0:
            return random.choices(values, weights=weights, k=1)[0]

    return random.choice(values)


def parse_date_safe(date_text):
    if not date_text:
        return None

    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None


def generate_date_value(column):
    distribution = column.distribution

    if distribution and distribution.type.lower() == "date_range":
        start = parse_date_safe(distribution.start_date)
        end = parse_date_safe(distribution.end_date)

        if start and end and start <= end:
            days_between = (end - start).days
            random_days = random.randint(0, days_between)
            return str(start + timedelta(days=random_days))

    start_date = date.today() - timedelta(days=365 * 5)
    random_days = random.randint(0, 365 * 5)
    return str(start_date + timedelta(days=random_days))


def generate_datetime_value(column):
    distribution = column.distribution

    if distribution and distribution.type.lower() == "date_range":
        start = parse_date_safe(distribution.start_date)
        end = parse_date_safe(distribution.end_date)

        if start and end and start <= end:
            days_between = (end - start).days
            random_days = random.randint(0, days_between)
            generated_date = start + timedelta(days=random_days)

            random_hour = random.randint(0, 23)
            random_minute = random.randint(0, 59)
            random_second = random.randint(0, 59)

            generated_datetime = datetime(
                generated_date.year,
                generated_date.month,
                generated_date.day,
                random_hour,
                random_minute,
                random_second
            )

            return generated_datetime.isoformat()

    return fake.date_time_between(start_date="-5y", end_date="now").isoformat()


def apply_string_length_rules(value, column):
    value = str(value)

    if column.min_length is not None:
        while len(value) < column.min_length:
            value += fake.word()

    if column.max_length is not None:
        value = value[:column.max_length]

    return value


def generate_regex_value(column):
    try:
        return rstr.xeger(column.pattern)
    except Exception:
        return "REGEX_VALUE_001"


def generate_normal_value(column, row_index):
    column_type = column.type.lower()

    if column.nullable and random.randint(1, 100) <= 3:
        return None

    if column_type == "string":
        value = fake.word()
        return apply_string_length_rules(value, column)

    if column_type in ["integer", "number"]:
        value = generate_numeric_value(column)
        return int(round(value))

    if column_type in ["decimal", "float"]:
        value = generate_numeric_value(column)
        return round(value, 2)

    if column_type == "boolean":
        return generate_boolean_value(column)

    if column_type == "date":
        return generate_date_value(column)

    if column_type in ["datetime", "timestamp"]:
        return generate_datetime_value(column)

    if column_type == "category":
        return generate_category_value(column)

    if column_type == "name":
        return fake.name()

    if column_type == "first_name":
        return fake.first_name()

    if column_type == "last_name":
        return fake.last_name()

    if column_type == "email":
        return fake.email()

    if column_type == "phone":
        return fake.phone_number()

    if column_type == "address":
        return fake.address().replace("\n", ", ")

    if column_type == "city":
        return fake.city()

    if column_type == "state":
        return fake.state()

    if column_type == "country":
        return fake.country()

    if column_type in ["postal_code", "zip"]:
        return fake.postcode()

    if column_type == "company":
        return fake.company()

    if column_type == "job_title":
        return fake.job()

    if column_type == "uuid":
        return str(uuid.uuid4())

    if column_type == "id":
        prefix = column.prefix or "ID"
        return f"{prefix}{row_index + 1:05d}"

    if column_type == "url":
        return fake.url()

    if column_type == "ip_address":
        return str(ipaddress.IPv4Address(random.randint(0, 2**32 - 1)))

    if column_type == "currency_code":
        return random.choice(["INR", "USD", "EUR", "GBP", "AED", "SGD"])

    if column_type == "currency_amount":
        value = generate_numeric_value(column)
        return round(value, 2)

    if column_type == "long_text":
        value = fake.paragraph(nb_sentences=5)
        return apply_string_length_rules(value, column)

    if column_type == "regex":
        return generate_regex_value(column)

    return None