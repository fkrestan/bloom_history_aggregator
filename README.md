Bloom History Aggregator Service
===================================

An aggregation REST API service for the Bloom History DDoS mitigation
project which builds on idea described in [the original whitepaper][4]. This
service is a "middleman" storage between Bloom filter producer such as
[Bloom History NEMEA plugin][1] and a Bloom filter user (e.g. DDoS
mitigation SW/HW). If you are unsure what this thing does, or why is it even
needed, keep reading - We will try to explain everything.

The short version of the above paper is, that during normal network
operations you can gather information about legitimate communication with the
protected network and use this information later during a DDoS attack to
prioritize communication of the "known good" IP addresses.

To keep the information about "good" IP addresses, we've decided to use
[Bloom filters][4] since they are very space efficient. Unfortunately there
is a catch; we most likely don't want to keep the information about IP
addresses forever. Certainly, there is a time limit after which, if the IP
did not communicate with the protected prefix, we would like to remove the
'white-listing" of such IP address. The catch is in the Bloom filters; once
an element is inserted, it can not be effectively removed from a Bloom filter.
On the other hand, Bloom filters can be merged together very easily and
efficiently without any information loss.

This is where this "middleman" service comes in. It stores Bloom filters
created by some producer and store them. The bloom filters are created and
send in relatively short intervals by the producer (e.g. 5-15 minutes),
depending on the required time granularity. When DDoS attack swoops in, the
filtering devices can request merged filter for longer period of time (e.g.
last 14 days). This aggregated filter contains information about all the
"good" addresses for that period of time... Magic :)

See:

- acompaniing *Bloom history* module in [NEMEA repo][1]
- [extended libbloom library][2] used both in this project and NEMEA plugin


REST API
--------

This application exposes two endpoints.

- `POST /<uuid:uuid>/<int:timestamp_from>/<int:timestamp_to>`
  Upload new Bloom filter. The POST shall contain only bloom filter in its
  binary serialized form as produced by [extended libbloom][2]).

  - `uuid` - assigned universally unique identifier according to RFC 4122.
  - `timestamp_from` - unix timestamp marking the start of the information
    contained in the Bloom filter being send.
  - `timestamp_to` - unix timestamp marking the end of the information
    contained in the Bloom filter being send.

  Content-type must be `application/octet-stream`.

- `DELETE /<uuid:uuid>/<int:timestamp_from>/<int:timestamp_to>`
  Delete Bloom filters in specified time-range. This endpoint is intended
  to be used for deletion of history in case a DDoS or any other malicious
  traffic got into the Bloom filters.

  - `uuid` - assigned universally unique identifier according to RFC 4122.
  - `timestamp_from` - unix timestamp marking the start of the time-range
    for Bloom filter deletion. The timestamp is inclusive.
  - `timestamp_to` - unix timestamp marking the end of the time-range
    for Bloom filter deletion. The timestamp is inclusive.

  Content-type must be `application/octet-stream`.

- `GET /<uuid:uuid>/<int:timestamp_from>/<int:timestamp_to>`
  Get aggregated/merged Bloom filter spanning given time range. Response data
  contains only aggregated Bloom filter in binary serialized form as produced
  by [extended libbloom][2]).

  - `uuid` - assigned universally unique identifier according to RFC 4122.
  - `timestamp_from` - unix timestamp marking the start of the information
    contained in the aggregated Bloom filter. The timestamp is inclusive.
  - `timestamp_to` - unix timestamp marking the end of the the information
    contained in the aggregated Bloom filter. The timestamp is inclusive.

  _NOTE_ Internally, the bloom filters are stored as files with the given
  timestamp range. The bloom filter timestamp range must be fully included in
  the request timestamp range for it to be contained in the aggregated
  response. If the requested range does not include any Bloom filter file, a
  `404 Not Found` will be returned.

  Response Content-type is set to `application/octet-stream`.

- `GET /health`
  A simple health-check endpoint. Should return `200 OK` if the API is in a
  operational state.


Installation and Packaging
--------------------------

This application contains C extension module and needs C compiler,
[extended libbloom][2] library header files and Python3 header files
installed on the system.

Example for `Python3.6` on Linux:

```
make dist
pip3 install dist/bloom_history_aggregator_service-0.0.1-cp36-cp36m-linux_x86_64.whl
```


[1]: https://github.com/CESNET/Nemea-Modules/
[2]: https://github.com/fkrestan/libbloom/
[3]: https://ieeexplore.ieee.org/document/1204223/
[4]: https://en.wikipedia.org/wiki/Bloom_filter
