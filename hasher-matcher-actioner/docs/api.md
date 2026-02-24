# API

While HMA provides a simple UI for debugging and development, scanning content at scale will require API integration. Additionally, if you wish to provide a UI with more capabilities like access control, you can use the API to build a more featureful version of the debugging UI.

Note that there are multiple ways to set up a production deployment with their own cost tradeoffs. See [architecture.md](./architecture.md) for more details, especially about which stage to do hashing.

## Accessing the API

Some endpoints may only be available to specific roles. All endpoints are based upon the HMA process's base URL.
In the monolithic docker compose setup from this repository, that will be `http://localhost:5100`.

**Note**: The API docs are a work in progress and may be missing some (useful) endpoints.

### Status/Information

When HMA has started up, it will respond 200 OK to `GET /status`.

The full list of paths available to the caller can be found at `GET /site-map`. The response will be a JSON array similar to the following:
```json
[
  "/",
  "/c/bank/<bank_name>",
  "/c/bank/<bank_name>/content",
  "/c/bank/<bank_name>/content/<content_id>",
  "/c/bank/<bank_name>/content/<int:content_id>",
  "/c/bank/<bank_name>/signal",
  "/c/banks",
  "/c/content_type",
  "/c/exchange/<string:exchange_name>",
  "/c/exchange/<string:exchange_name>/status",
  "/c/exchanges",
  "/c/exchanges/api/<string:api_name>",
  "/c/exchanges/api/<string:api_name>/schema",
  "/c/exchanges/apis",
  "/c/signal_type",
  "/c/signal_type/<signal_type_name>",
  "/c/signal_type/index",
  "/h/hash",
  "/m/compare",
  "/m/index/status",
  "/m/lookup",
  "/m/raw_lookup",
  "/site-map",
  "/status",
  "/ui/",
]
```

## Fetching / Exchanges

Which exchanges (SignalExchangeAPI) are supported by the instance of HMA are configured on deployment. During runtime, configs for fetching from new sources can be created and edited.

- Create Exchange Configuration
  - Inputs:
    - Configuration name in `CAPS_AND_UNDERSCORE` (must not be the same as an existing bank name)
    - Exchange type
    - Exchange-specific arguments (depends on SignalExchangeAPI)
- List all configs
  - Output:
    - List of all config names
- Get Exchange Configuration
  - Inputs:
    - Configuration name
  - Output: JSON serialization of configuration
    - Includes exchange type
- Get Exchange Fetch Status
  - Inputs
    - Configuration name
  - Outputs
    - Time of last fetch in unix time
    - Time of checkpoint in unix time
    - Whether the last run resulted in an error
- Get Exchange-specific Metadata
  - Input:
    - Configuration name
    - Exchange-specific ID
  - Output
    - JSON serialization of metadata specific to Exchange
- Edit Runtime Configuration properties
  - Inputs:
    - Configuration name
    - Optional Bool enable/disable fetching
    - Optional Bool enable SEEN status
    - Optional Bool enable True Positive / False Positive reporting
- Delete Exchange Configuration
  - Inputs
    - Configuration name
    - Optional - whether to also delete the bank (defaults to true)
- [TBD] Submit content directly to exchange
  - Inputs
    - SignalType
    - `string` Signal value
    - Status (`positive_class`, `negative_class`, `investigation_seed`)
    - List of tags

## Banking / Hash Lists

What algorithms are used, and what similarity settings to use (e.g. PDQ distance) are configured on deployment.

- Create Bank / Hash List
  - Inputs
    - Bank/List name in `CAPS_AND_UNDERSCORE` (must not be the same as an existing bank name)
- Edit Runtime Configuration properties
  - Inputs
    - Bank/List name
    - Optional `bool` enable/disable matching
    - Optional `list<string>` bank labels
  - Get Bank/List Configuration properties
    - Inputs
      - Bank/List name
    - Outputs:
      - JSON serialization of bank properties
        - Includes if it is connected to an Exchange
- Get Bank/List Metadata
  - Inputs
    - Bank/List name
  - Outputs
    - Number of items in the bank/list
    - Number of signals in the bank broken down by type
- Get Bank/List Contents (ordered by modification time)
  - Inputs
    - Bank/List name
    - Page size
    - Optional pagination token
  - Outputs
    - A list of bank contents. A bank item includes
      - Bank Content ID
      - List of signals. A signal includes
        - Signal type (string)
        - Signal value (string)
    - A pagination token for getting the next page of data
- Add content to Bank/hash list
  - Inputs
    - Bank Name
    - One of the following:
      - Bank content ID
      - Signal type, value
      - Content type, bytes
    - Optional platform-specific content ID
    - Optional `list<string>` of review labels
  - Output:
    - Bank content ID
- Remove/Disable content from bank/hash list (exchange-backed banks will retain a disabled record)
  - Inputs
    - Bank content ID
- Get Bank Content
  - Inputs
    - Bank content ID
  - Outputs
    - Bank Name
    - Bank labels
    - List of Exchange-specific IDs
- Delete Bank (will error if attached to an Exchange - must be deleted at the exchange level)
  - Inputs
    - Bank name

## Hashing

What ContentTypes and SignalTypes are supported are configured on deployment.

### Hashing content by URL

Endpoint: `GET /h/hash?url=<your_url>`
Sample JSON response (SignalType to value):
```json
{"pdq":"d811ac390bfa6005d08543fe27fd5a11f6b55bdd2603000dc26476fc79fc76b5"}
```

Example:
```bash
curl -s -X GET http://localhost:5100/h/hash?url=https://example.org/path/to/file.png
```

### Hashing content by bytes

This endpoint uses a `multipart/form-data` request body. The field name is the ContentType (typically `photo` or `video`) to hash with.

Endpoint: `POST /h/hash`
Sample JSON response (SignalType to value):
```json
{"pdq":"d811ac390bfa6005d08543fe27fd5a11f6b55bdd2603000dc26476fc79fc76b5"}
```

Example:
```bash
curl -s -X POST --form photo='@example.png' http://localhost:5100/h/hash
```

### Hashing and matching

**Warning**: This endpoint may be slow. Large timeout values or long-polling are recommended.

This endpoint will hash *and* match in the same operation. Some deployments may prefer to split these functions and use dedicated endpoints described throughout this document.

This endpoint uses a `multipart/form-data` request body. The field name is the ContentType (typically `photo` or `video`) to hash with.

Endpoint: `POST /m/lookup`
Sample JSON response (SignalType to Bank Name to content matches):
```json
{
  "pdq":{
    "TEST_BANK":[
      {"bank_content_id":1,"distance":"0"}
    ]
  }
}
```

**Note**: An internal coinflip will be performed and compared to the enabled ratio of each bank. Only banks which pass this coinflip (1.0 being always include, 0.0 being never include) will be checked. The coinflip can be bypassed with a `?bypass_coinflip=true` query string parameter to the endpoint. A consistent seed can be supplied to the coinflip via the `?seed=1234` query string parameter.

Example:
```bash
curl -s -X POST --form photo='@example.png' http://localhost:5100/m/lookup?bypass_coinflip=false
```

## Matching

What SignalTypes, and what similarity settings to use (e.g. PDQ distance) are configured on deployment.

Additional SignalTypes can be made available by setting the `SIGNAL_TYPES` variable in the config.
Here is an example with CLIP signal type, after installing it with `pip install tx-extension-clip`:

```
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from tx_extension_clip.signal import CLIPSignal

SIGNAL_TYPES = [PdqSignal, VideoMD5Signal, CLIPSignal]
```

- Index Status
  - Input
    - SignalType (`string`)
  - Output
    - Time of last index build

### Looking up a hash

Content matches in banks can be looked up by SignalType and value.

Endpoint: `GET /m/lookup?signal_type=<type>&signal=<value>`
Sample JSON response (Bank Name to content matches):
```json
{
  "TEST_BANK":[
    {"bank_content_id":1,"distance":"0"}
  ]
}
```

**Note**: An internal coinflip will be performed and compared to the enabled ratio of each bank. Only banks which pass this coinflip (1.0 being always include, 0.0 being never include) will be checked. The coinflip can be bypassed with a `?bypass_coinflip=true` query string parameter to the endpoint. A consistent seed can be supplied to the coinflip via the `?seed=1234` query string parameter.

Example:
```bash
curl -s -X GET "http://localhost:5100/m/lookup?signal_type=pdq&signal=d811ac390bfa6005d08543fe27fd5a11f6b55bdd2603000dc26476fc79fc76b5"
```

## Recording Review Results

- Record review led to discovery of harm - will communicate with exchanges if the exchange is configured to do so
  - Input
    - `list<string>` of Bank Content IDs
    - Optional `list<string>` of labels - if the label doesn’t match a bank labels it will change or prevent which information is recorded back to the exchange
- Record review did not lead to the discovery of harm
  - Input
    - `list<string>` of Bank Content IDs
    - Optional `list<string>` of labels - if the label doesn’t match a bank labels it will change or prevent which information is recorded back to the exchange
