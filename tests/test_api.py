#   Copyright 2018 Filip Krestan <krestfi1@fit.cvut.cz>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import glob
from unittest import mock

import pytest

from context import blooming_history_aggregator as bha
import libbloom_bindings


@pytest.mark.parametrize("timestamp_from, timestamp_to, expected", [
    (123, 456, '123-456.bloom'),
    ('123', '456', '123-456.bloom'),
])
def test_filename_make(timestamp_from, timestamp_to, expected):
    assert bha.api.filename_make(timestamp_from, timestamp_to) == expected


@pytest.mark.parametrize("timestamp_from, timestamp_to, error_type", [
    ('aaa', 456, ValueError),
    ('123', 'lkjsad', ValueError),
    (None, 1, TypeError),
])
def test_filename_make_fail(timestamp_from, timestamp_to, error_type):
    with pytest.raises(error_type):
        bha.api.filename_make(timestamp_from, timestamp_to)


@pytest.mark.parametrize("timestamp_from, timestamp_to, filename", [
    (123, 456, '123-456.bloom'),
    (1, 4, '1-4.bloom'),
    (1, 2, 'a/1-2.bloom'),
    (1, 2, '../a/1-2.bloom'),
    (1, 2, '/var/lib/blooming_history_aggregator/0932778e-90a4-445c-a8a3-311817b6e0ba/1-2.bloom'),
])
def test_filename_parse(timestamp_from, timestamp_to, filename):
    assert bha.api.filename_parse(filename) == [timestamp_from, timestamp_to]


@pytest.mark.parametrize("filename, error_type", [
    ('a-b.bloom', AttributeError),
    ('-.bloom', AttributeError),
    ('.bloom', AttributeError),
    ('11.bloom', AttributeError),
    (None, TypeError),
    ('1-1', AttributeError),
    ('/var/lib/blooming_history_aggregator/0932778e-90a4-445c-a8a3-311817b6e0ba/.boom',
     AttributeError),
    ('/var/lib/blooming_history_aggregator/0932778e-90a4-445c-a8a3-311817b6e0ba/a-1.boom',
     AttributeError),
])
def test_filename_parse_fail(filename, error_type):
    with pytest.raises(error_type):
        bha.api.filename_parse(filename)


@pytest.mark.parametrize("glob_ret, dirname, timestamp_from, timestamp_to, expected", [
    ([], 'a', 123, 456, []),
    (['1-2.bloom'], '', 1, 2, ['1-2.bloom']),
    (['a/a', 'a/b'], 'a', 123, 456, []),
    (['a/b', 'a/b'], 'a', 123, 456, []),
    (['a/1-2.bloom'], 'a', 1, 2, ['a/1-2.bloom']),
    (['a/1-2.bloom'], 'a', '1', '2', ['a/1-2.bloom']),
    (['a/0-1.bloom', 'a/1-2.bloom', 'a/2-3.bloom'], 'a', 1, 2, ['a/1-2.bloom']),
    (['a/0-1.bloom', 'a/1-2.bloom', 'a/2-3.bloom'], 'a', 0, 2, ['a/0-1.bloom', 'a/1-2.bloom']),
    (['a/0-1.bloom', 'a/1-2.bloom', 'a/2-3.bloom'], 'a', 0, 5,
     ['a/0-1.bloom', 'a/1-2.bloom', 'a/2-3.bloom']),
    (['a/0-3.bloom', 'a/1-2.bloom', 'a/2-3.bloom'], 'a', 1, 2, ['a/1-2.bloom']),
    (['a/0-3.bloom', 'a/1-2.bloom', 'a/.bloom'], 'a', 1, 2, ['a/1-2.bloom']),
])
@mock.patch('glob.glob')
def test_filename_filter(mock_glob, glob_ret, dirname, timestamp_from, timestamp_to, expected):
    mock_glob.return_value = glob_ret
    assert list(bha.api.filename_filter(dirname, timestamp_from, timestamp_to)) == expected
    mock_glob.assert_called_with(dirname + '/*.bloom')


def make_tests_relative_path(*args):
    here = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(here, *args)


@pytest.mark.parametrize('bloom_filename', glob.glob(make_tests_relative_path('bloom/*.bloom')))
def test_bloom_serialize(bloom_filename):
    bloom = libbloom_bindings.ffi.new('struct bloom *')
    libbloom_bindings.lib.bloom_file_read_(bloom, bloom_filename.encode('utf-8'))

    bloom_buffer = bha.api.bloom_serialize(bloom)

    with open(bloom_filename, 'rb') as f:
        bloom_buffer_file = f.read()

    assert isinstance(bloom_buffer, bytes)
    assert len(bloom_buffer) == len(bloom_buffer_file)
    assert bloom_buffer == bloom_buffer_file


def test_bloom_serialize_uninitialized_bloom():
    bloom = libbloom_bindings.ffi.new('struct bloom *')

    with pytest.raises(bha.api.LibbloomError):
        bha.api.bloom_serialize(bloom)


@pytest.mark.parametrize("bloom_filenames, bloom_expected_filename", [
    (['test-1000-0.100000.bloom'], 'test-1000-0.100000.bloom'),
    (['test-1000-0.100000.bloom', 'test-1000-0.100000.bloom'], 'test-1000-0.100000.bloom'),
    (['test-1000-0.010000.bloom'], 'test-1000-0.010000.bloom'),
    (['test-1000-0.010000.bloom', 'test-1000-0.010000.bloom'], 'test-1000-0.010000.bloom'),
    (['test-100000-0.010000.bloom'], 'test-100000-0.010000.bloom'),
    (['test-100000-0.010000.bloom', 'test-100000-0.010000.bloom'], 'test-100000-0.010000.bloom'),
    (['test-1000-0.100000.bloom', 'alkdjfalsdk', 'lakdjflkadj'], 'test-1000-0.100000.bloom'),
    (['test-1000-0.100000.bloom', 'test-100000-0.010000.bloom'], 'test-1000-0.100000.bloom'),
    (['test-10000-0.01-1-2-3-4.bloom', 'test-10000-0.01-4-5-6-7.bloom'],
     'test-10000-0.01-1-2-3-4-5-6-7.bloom'),
])
def test_bloom_merge_all(bloom_filenames, bloom_expected_filename):
    bloom_file_paths = (make_tests_relative_path('bloom/', f) for f in bloom_filenames)

    bloom_merged_serialized = bha.api.bloom_merge_all(bloom_file_paths)

    with open(make_tests_relative_path('bloom/', bloom_expected_filename), 'rb') as f:
        bloom_expected_serialized = f.read()

    assert bloom_merged_serialized == bloom_expected_serialized


@pytest.mark.parametrize("bloom_filenames, error_type", [
    ([], bha.api.LibbloomError),
    (['asdlkfjalkdsf'], bha.api.LibbloomError),
    (['asdlkfjalkdsf', 'rqweqpo'], bha.api.LibbloomError),
])
def test_bloom_merge_all_fail(bloom_filenames, error_type):
    bloom_file_paths = (make_tests_relative_path('bloom/', f) for f in bloom_filenames)

    with pytest.raises(error_type):
        bha.api.bloom_merge_all(bloom_file_paths)


@pytest.fixture()
def app_client(tmpdir):
    app = bha.api.app

    app.instance_path = tmpdir
    app.testing = True
    testing_client = app.test_client()
    ctx = app.app_context()
    ctx.push()

    yield testing_client

    ctx.pop()


def test_health(app_client):
    assert app_client.get('/health').status_code == 200


@pytest.mark.parametrize('timestamp_from, timestamp_to', [
    ('0', '4'),
    ('1', '3'),
    ('2', '3'),
])
def test_delete_bloom(timestamp_from, timestamp_to, app_client, tmpdir):
    uuid_ = 'a21fd80d-4c7a-48c5-975f-0940e1ad3841'
    directory = os.path.join(tmpdir, uuid_)
    os.makedirs(directory, exist_ok=True)

    open(os.path.join(directory, bha.api.filename_make(1, 2)), 'a').close()
    open(os.path.join(directory, bha.api.filename_make(3, 4)), 'a').close()

    app_client.delete('{}/{}/{}/'.format(uuid_, timestamp_from, timestamp_to))
    files = bha.api.filename_filter('a21fd80d-4c7a-48c5-975f-0940e1ad3841', 2, 4)

    assert list(files) == []


@pytest.mark.parametrize('input_file, timestamp_from, timestamp_to, uuid_', [
    ('test-10000-0.01-1-2-3-4.bloom', '1', '2', 'a21fd80d-4c7a-48c5-975f-0940e1ad3841'),
])
def test_bloom_post(app_client, tmpdir, input_file, timestamp_from, timestamp_to, uuid_):
    input_file_path = make_tests_relative_path('bloom', input_file)

    result_file = bha.api.filename_make(timestamp_from, timestamp_to)
    result_directory = str(tmpdir.join(uuid_))

    with open(input_file_path, 'rb') as f:
        input_data = f.read()

    response = bha.api.post_bloom(result_directory, timestamp_from, timestamp_to, input_data)
    assert response.status_code == 200

    result_file_path = os.path.join(result_directory, result_file)
    assert os.path.isfile(result_file_path)

    with open(result_file_path, 'rb') as f:
        result_data = f.read()
    assert result_data == input_data


@pytest.fixture()
def populated_bloom_dir(tmpdir):
    uuid_ = 'a21fd80d-4c7a-48c5-975f-0940e1ad3841'
    result_directory = str(tmpdir.join(uuid_))
    input_ = [('test-10000-0.01-1-2-3-4.bloom', '1', '2'), ('test-10000-0.01-4-5-6-7.bloom', '2',
                                                            '3')]

    for input_file, timestamp_from, timestamp_to in input_:
        with open(make_tests_relative_path('bloom', input_file), 'rb') as f:
            input_data = f.read()

        response = bha.api.post_bloom(result_directory, timestamp_from, timestamp_to, input_data)
        assert response.status_code == 200

    return result_directory


@pytest.mark.parametrize('expected_bloom, timestamp_from, timestamp_to', [
    ('test-10000-0.01-1-2-3-4.bloom', '1', '2'),
    ('test-10000-0.01-1-2-3-4.bloom', '0', '2'),
    ('test-10000-0.01-4-5-6-7.bloom', '2', '3'),
    ('test-10000-0.01-4-5-6-7.bloom', '2', '4'),
    ('test-10000-0.01-1-2-3-4-5-6-7.bloom', '1', '3'),
    ('test-10000-0.01-1-2-3-4-5-6-7.bloom', '0', '4'),
])
def test_get_merged(app_client, populated_bloom_dir, timestamp_from, timestamp_to, expected_bloom):
    response = bha.api.get_merged(populated_bloom_dir, timestamp_from, timestamp_to)
    assert response.status_code == 200
    expected_bloom_data = open(make_tests_relative_path('bloom', expected_bloom), 'rb').read()
    assert response.data == expected_bloom_data


@pytest.mark.parametrize('timestamp_from, timestamp_to', [
    ('4', '42'),
])
def test_get_merged_empty_range_fail(app_client, populated_bloom_dir, timestamp_from, timestamp_to):
    with pytest.raises(bha.api.LibbloomError):
        bha.api.get_merged(populated_bloom_dir, timestamp_from, timestamp_to)


@pytest.mark.parametrize('timestamp_from, timestamp_to', [
    ('4', '42'),
])
def test_get_merged_empty_dir_fail(app_client, tmpdir, timestamp_from, timestamp_to):
    with pytest.raises(bha.api.LibbloomError):
        bha.api.get_merged(str(tmpdir), timestamp_from, timestamp_to)
