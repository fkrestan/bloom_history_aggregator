Blooming History Aggregator Service
===================================

An aggragation REST API service for the Blooming History DDoS mitigation
project.

See:

- acompaniing *Blooming history* module in [NEMEA repo][1]
- [extended libbloom library][2] used both in this project and NEMEA plugin


REST API
--------

This application exposes two endpoints.

- `POST /<uuid:uuid>/<int:timestamp_from>/<int:timestamp_to>`
  Upload new Bloom filter. The POST data contains only in its binary serialized
  form as produced by [extended libbloom][2]).

  - `uuid` - assigned universally unique identifier according to RFC 4122.
  - `timestamp_from` - unix timestamp marking the start of the information
    contained in the Bloom filter beeing send.
  - `timestamp_to` - unix timestamp marking the end of the information contained
    in the Bloom filter beeing send.

  Content-type must be `application/octet-stream`.

- `GET /<uuid:uuid>/<int:timestamp_from>/<int:timestamp_to>`
  Get aggregated/merged Bloom filter spanning given time range. Response data
  contains only aggragated Bloom filter in binary serialized form as produced by
  [extended libbloom][2]).

  - `uuid` - assigned universally unique identifier according to RFC 4122.
  - `timestamp_from` - unix timestamp marking the start of the information
    contained in the aggregated Bloom filter. The timestamp is inclusive.
  - `timestamp_to` - unix timestamp marking the end of the ithe information
    contained in the aggregated Bloom filter. The timestamp is inclusive.

  _NOTE_ Internally, the bloom filters are stored as files with the given
  timestamp range. The bloom filter timestamp range must be fully included
  in the request timestamp range for it to be contained in the aggregated
  response. If the requested range does not include any Bloom filter file,
  a `404 Not Found` will be returned.

  Response Content-type is set to `application/octet-stream`.

- `GET /health`
  A simple health-check endpoint. Should return `200 OK` if the API is in a
  operational state.


Installation and Packaging
--------------------------

This application contains C extension module and needs C compiler, [extended libbloom][2]
library header files and Python3 header files installed on the system.

Example for `Python3.6` on Linux:

```
make dist
pip3 install dist/blooming_history_aggregator_service-0.0.1-cp36-cp36m-linux_x86_64.whl
```


[1]: https://github.com/CESNET/Nemea-Modules/
[2]: https://github.com/fkrestan/libbloom/
