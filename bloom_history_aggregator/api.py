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
import re
import glob

from flask import abort, request, make_response

from . import app
from libbloom_bindings import lib, ffi

GET_MERGED_HEADERS = {'Content-Type': 'application/octet-stream'}
RE_BLOOM_FILENAME = re.compile(r'(\d+)-(\d+)\.bloom')


class LibbloomError(ValueError):
    def __init__(self, message, return_code):
        super().__init__(message)
        self.rc = return_code


def filename_make(timestamp_from, timestamp_to):
    return '{}-{}.bloom'.format(int(timestamp_from), int(timestamp_to))


def filename_parse(file_path):
    filename = os.path.basename(file_path)
    return [int(x) for x in RE_BLOOM_FILENAME.match(filename).groups()]


def filename_filter(dirname, timestamp_from, timestamp_to):
    for file_path in glob.glob(str(dirname) + '/*.bloom'):
        try:
            file_timestamp_from, file_timestamp_to = filename_parse(file_path)
            if int(timestamp_from) <= file_timestamp_from and int(timestamp_to) >= file_timestamp_to:
                yield file_path
        except (AttributeError, TypeError, ValueError):
            app.logger.error('Invalid filename encountered: "%s"', file_path)


def bloom_serialize(bloom):
    """Serialize bloom struct to a Python bytes.

    :param bloom: Pointer to a CData 'struct bloom *' Bloom filter
    :returns: Serialized Bloom filter as bytes buffer
    :raises LibbloomError: When libbloom serialization returns non-zero return code
    """
    try:
        bloom_serialized_c = ffi.new('uint8_t **')
        bloom_serialized_size_c = ffi.new('int32_t *')

        rc = lib.bloom_serialize_(bloom, bloom_serialized_c, bloom_serialized_size_c)
        if rc != 0:
            app.logger.error(
                'Serialization of merged bloom filter returned non-zero return code: %d!', rc)
            raise LibbloomError('Could not read any of the specified files', rc)

        bloom_serialized_size = bloom_serialized_size_c[
            0]  # cffi unwieldy way of dereferencing a pointer
        return bytes(ffi.unpack(bloom_serialized_c[0],
                                bloom_serialized_size))  # again dereference a pointer
    finally:
        lib.bloom_free_serialized_buffer_(bloom_serialized_c)


def bloom_merge_all(filenames):
    """Merge all Bloom filters from provided file names.

    :param filenames: File names to be merged toghether
    :returns: Merged and serialized Bloom filter as bytes buffer
    :raises LibbloomError: When libbloom serialization returns non-zero return code
    """
    bloom_merged = ffi.new('struct bloom *')
    bloom_current = ffi.new('struct bloom *')
    filenames_iter = iter(filenames)
    rc = 0

    try:
        # Find first good bloom file
        for filename in filenames_iter:
            rc = lib.bloom_file_read_(bloom_merged, filename.encode('utf-8'))
            if rc == 0:
                break
            app.logger.error(
                'Reading bloom filter from file "%s" returned non-zero return code: %d!', filename,
                rc)
        else:
            raise LibbloomError('Could not read any of the specified files', rc)

        # Try to merge the rest of bloom files
        for filename in filenames_iter:
            rc = lib.bloom_file_read_(bloom_current, filename.encode('utf-8'))
            if rc != 0:
                app.logger.error(
                    'Reading bloom filter from file "%s" returned non-zero return code: %d!',
                    filename, rc)

            rc = lib.bloom_merge_(bloom_merged, bloom_current)
            if rc != 0:
                app.logger.error(
                    'Merging bloom filter from file "%s" returned non-zero return code: %d!',
                    filename, rc)

            lib.bloom_free_(bloom_current)

        return bloom_serialize(bloom_merged)
    finally:
        lib.bloom_free_(bloom_current)  # bloom_free handles potentional double free
        lib.bloom_free_(bloom_merged)


def post_bloom(directory, timestamp_from, timestamp_to, bloom_data):
    filename = filename_make(timestamp_from, timestamp_to)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, filename), 'wb') as f:
        f.write(bloom_data)

    return make_response('OK', 200)


def delete_bloom(directory, timestamp_from, timestamp_to):
    files = filename_filter(directory, timestamp_from, timestamp_to)

    if not os.path.exists(directory):
        abort(404)

    if not files:
        abort(404)

    for file_name in files:
        os.remove(file_name)

    return make_response("OK", 200)


def get_merged(directory, timestamp_from, timestamp_to):
    files = filename_filter(directory, timestamp_from, timestamp_to)

    if not os.path.exists(directory):
        abort(404)

    if not files:
        abort(404)

    merged = bloom_merge_all(files)
    return make_response(merged, 200, GET_MERGED_HEADERS)


@app.route('/<int:prefix_id>/<int:timestamp_from>/<int:timestamp_to>/', methods=['GET', 'POST', 'DELETE'])
def ednpoint_bloom(prefix_id, timestamp_from, timestamp_to):
    if timestamp_from >= timestamp_to:
        abort(400)

    directory = os.path.join(app.instance_path, str(prefix_id))

    if request.method == 'POST':
        return post_bloom(directory, timestamp_from, timestamp_to, request.data)
    if request.method == 'DELETE':
        return delete_bloom(directory, timestamp_from, timestamp_to)

    return get_merged(directory, timestamp_from, timestamp_to)


@app.route('/health', methods=['GET'])
def get_health():
    return make_response('OK', 200)
