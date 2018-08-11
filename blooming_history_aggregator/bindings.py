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

from cffi import FFI

# Passed to the real C compiler, contains implementation of things declared in cdef()
source = r"""
#include <bloom.h>

int bloom_merge_(struct bloom * bloom, const struct bloom * other) {
   return bloom_merge(bloom, other);
}

int bloom_serialize_(const struct bloom * bloom, uint8_t ** buffer, int32_t * size) {
   return bloom_serialize(bloom, buffer, size);
}

void bloom_free_serialized_buffer_(uint8_t ** buffer) {
    bloom_free_serialized_buffer(buffer);
}

int bloom_file_read_(struct bloom * bloom, const char * filename) {
    return bloom_file_read(bloom, filename);
}

int bloom_file_write_(const struct bloom * bloom, const char * filename) {
    return bloom_file_write(bloom, filename);
}

void bloom_print_(struct bloom * bloom) {
    return bloom_print(bloom);
}

void bloom_free_(struct bloom * bloom) {
    return bloom_free(bloom);
}
"""

# Declarations that are shared between Python and C
cdef = r"""
struct bloom
{
  // These fields are part of the public interface of this structure.
  // Client code may read these values if desired. Client code MUST NOT
  // modify any of these.
  int32_t entries;
  double error;
  int32_t bits;
  int32_t bytes;
  int32_t hashes;

  // Fields below are private to the implementation. These may go away or
  // change incompatibly at any moment. Client code MUST NOT access or rely
  // on these.
  double bpe;
  uint8_t * bf;
  int ready;
};

int bloom_merge(struct bloom * bloom, const struct bloom * other);
int bloom_merge_(struct bloom * bloom, const struct bloom * other);

int bloom_serialize(const struct bloom * bloom, uint8_t ** buffer, int32_t * size);
int bloom_serialize_(const struct bloom * bloom, uint8_t ** buffer, int32_t * size);

void bloom_free_serialized_buffer(uint8_t ** buffer);
void bloom_free_serialized_buffer_(uint8_t ** buffer);

int bloom_file_write(const struct bloom * bloom, const char * filename);
int bloom_file_write_(const struct bloom * bloom, const char * filename);

int bloom_file_read(struct bloom * bloom, const char * filename);
int bloom_file_read_(struct bloom * bloom, const char * filename);

void bloom_print(struct bloom * bloom);
void bloom_print_(struct bloom * bloom);

void bloom_free(struct bloom * bloom);
void bloom_free_(struct bloom * bloom);
"""

ffibuilder = FFI()
ffibuilder.set_source("libbloom_bindings", source, libraries=["bloom"], library_dirs=["."])
ffibuilder.cdef(cdef)


def generate():
    ffibuilder.compile(verbose=True)


if __name__ == "__main__":
    generate()
