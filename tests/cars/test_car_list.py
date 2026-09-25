import pytest
from django.urls import reverse

from apps.cars.models import Car

URL = reverse('car-list')


def make_car(**overrides):
    fields = {
        'title': 'BMW 3 Series', 'subtitle': '320d M Sport',
        'make': 'BMW', 'model': '3 Series', 'body_type': 'Saloon',
        'fuel': 'Diesel', 'transmission': 'Automatic', 'colour': 'Black',
        'year': 2019, 'engine_cc': 1995, 'mileage': 40000, 'price': 15000,
        'image': 'cars/test.jpg',
    }
    fields.update(overrides)
    return Car.objects.create(**fields)


def ids(results):
    return [car['id'] for car in results]


@pytest.mark.django_db
class TestPlainList:
    def test_no_page_param_returns_plain_array_of_all_cars(self, api_client):
        cars = [make_car() for _ in range(15)]
        response = api_client.get(URL)
        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert len(response.data) == 15
        assert set(ids(response.data)) == {car.id for car in cars}

    def test_plain_array_is_newest_first(self, api_client):
        first, second, third = make_car(), make_car(), make_car()
        assert ids(api_client.get(URL).data) == [third.id, second.id, first.id]

    def test_filters_apply_without_page_param(self, api_client):
        cheap = make_car(price=2000)
        make_car(price=20000)
        response = api_client.get(URL, {'price_max': 5000})
        assert ids(response.data) == [cheap.id]

    def test_card_shape_matches_paginated_results(self, api_client):
        make_car()
        plain = api_client.get(URL).data[0]
        paged = api_client.get(URL, {'page': 1}).data['results'][0]
        assert plain == paged


@pytest.mark.django_db
class TestPagination:
    def test_envelope_defaults(self, api_client):
        for _ in range(30):
            make_car()
        data = api_client.get(URL, {'page': 1}).data
        assert data['count'] == 30
        assert data['page'] == 1
        assert data['page_size'] == 12
        assert data['total_pages'] == 3
        assert len(data['results']) == 12
        assert data['previous'] is None
        assert 'page=2' in data['next']

    def test_last_page(self, api_client):
        for _ in range(30):
            make_car()
        data = api_client.get(URL, {'page': 3}).data
        assert len(data['results']) == 6
        assert data['next'] is None
        assert 'page=2' in data['previous']

    def test_page_past_last_is_empty_not_404(self, api_client):
        make_car()
        response = api_client.get(URL, {'page': 5})
        assert response.status_code == 200
        assert response.data['results'] == []
        assert response.data['count'] == 1
        assert response.data['next'] is None
        assert 'page=1' in response.data['previous']

    def test_page_size_override_and_cap(self, api_client):
        for _ in range(60):
            make_car()
        assert api_client.get(URL, {'page': 1, 'page_size': 5}).data['page_size'] == 5
        data = api_client.get(URL, {'page': 1, 'page_size': 500}).data
        assert data['page_size'] == 48
        assert len(data['results']) == 48

    def test_invalid_page_values_fall_back(self, api_client):
        make_car()
        data = api_client.get(URL, {'page': 'abc', 'page_size': 'x'}).data
        assert data['page'] == 1
        assert data['page_size'] == 12
        assert api_client.get(URL, {'page': 0}).data['page'] == 1

    def test_next_link_keeps_filters(self, api_client):
        for _ in range(3):
            make_car(fuel='Petrol')
        data = api_client.get(URL, {'page': 1, 'page_size': 2, 'fuel': 'Petrol'}).data
        assert 'fuel=Petrol' in data['next']
        assert 'page_size=2' in data['next']

    def test_empty_result(self, api_client):
        data = api_client.get(URL, {'page': 1}).data
        assert data['count'] == 0
        assert data['total_pages'] == 1
        assert data['results'] == []

    def test_pages_do_not_overlap_when_sort_values_tie(self, api_client):
        cars = [make_car(price=10000) for _ in range(25)]
        seen = []
        for page in (1, 2, 3):
            seen += ids(api_client.get(URL, {'page': page, 'ordering': 'price'}).data['results'])
        assert sorted(seen) == sorted(car.id for car in cars)


@pytest.mark.django_db
class TestFilters:
    @pytest.mark.parametrize('field,value,other', [
        ('model', 'X5', '3 Series'),
        ('body_type', 'SUV', 'Saloon'),
        ('fuel', 'Electric', 'Diesel'),
        ('transmission', 'Manual', 'Automatic'),
        ('colour', 'Red', 'Black'),
    ])
    def test_exact_filters(self, api_client, field, value, other):
        match = make_car(**{field: value})
        make_car(**{field: other})
        data = api_client.get(URL, {'page': 1, field: value}).data
        assert data['count'] == 1
        assert ids(data['results']) == [match.id]

    def test_make_is_case_insensitive(self, api_client):
        bmw = make_car(make='BMW')
        make_car(make='Audi')
        assert ids(api_client.get(URL, {'make': 'bmw'}).data) == [bmw.id]

    def test_status_filter(self, api_client):
        sold = make_car(status='sold')
        make_car(status='available')
        make_car(status='reserved')
        assert ids(api_client.get(URL, {'status': 'sold'}).data) == [sold.id]
        assert api_client.get(URL, {'status': 'reserved'}).data == []

    def test_ranges_are_inclusive(self, api_client):
        low = make_car(price=5000, mileage=10000)
        mid = make_car(price=10000, mileage=50000)
        make_car(price=20000, mileage=90000)
        data = api_client.get(URL, {'page': 1, 'price_min': 5000, 'price_max': 10000}).data
        assert set(ids(data['results'])) == {low.id, mid.id}
        data = api_client.get(URL, {'page': 1, 'mileage_min': 50000, 'mileage_max': 50000}).data
        assert ids(data['results']) == [mid.id]

    def test_non_numeric_range_is_ignored(self, api_client):
        make_car()
        assert len(api_client.get(URL, {'price_min': 'cheap'}).data) == 1

    def test_brand_prefix_matches_at_word_boundary(self, api_client):
        mini = make_car(make='MINI')
        hatch = make_car(make='MINI Hatch')
        make_car(make='Minix')
        make_car(make='BMW')
        assert set(ids(api_client.get(URL, {'brand': 'mini'}).data)) == {mini.id, hatch.id}

    def test_brand_multiword_slug(self, api_client):
        merc = make_car(make='Mercedes-Benz')
        assert ids(api_client.get(URL, {'brand': 'mercedes-benz'}).data) == [merc.id]

    def test_unknown_brand_is_empty(self, api_client):
        make_car()
        assert api_client.get(URL, {'brand': 'nope'}).data == []

    def test_filters_combine_and_count_is_after_filtering(self, api_client):
        for _ in range(20):
            make_car(fuel='Diesel', price=8000)
        for _ in range(5):
            make_car(fuel='Petrol', price=8000)
        make_car(fuel='Diesel', price=30000)
        data = api_client.get(URL, {'page': 1, 'fuel': 'Diesel', 'price_max': 10000}).data
        assert data['count'] == 20
        assert data['total_pages'] == 2


@pytest.mark.django_db
class TestOrdering:
    def test_price_ascending_and_descending(self, api_client):
        mid, low, high = make_car(price=10000), make_car(price=5000), make_car(price=20000)
        assert ids(api_client.get(URL, {'ordering': 'price'}).data) == [low.id, mid.id, high.id]
        assert ids(api_client.get(URL, {'ordering': '-price'}).data) == [high.id, mid.id, low.id]

    def test_year_and_mileage(self, api_client):
        old = make_car(year=2015, mileage=90000)
        new = make_car(year=2022, mileage=10000)
        assert ids(api_client.get(URL, {'ordering': '-year'}).data) == [new.id, old.id]
        assert ids(api_client.get(URL, {'ordering': 'mileage'}).data) == [new.id, old.id]

    def test_unknown_ordering_falls_back_to_newest_first(self, api_client):
        first, second = make_car(), make_car()
        assert ids(api_client.get(URL, {'ordering': 'title'}).data) == [second.id, first.id]
