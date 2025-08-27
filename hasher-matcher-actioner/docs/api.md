# API

As HMA is not planning to provide a production UI, the API is the key point of integration. We hope that users are able to treat it as a “black box” with the API defining the inputs and outputs.

### Fetching / Exchanges

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

### Banking / Hash Lists

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

### Hashing

What ContentTypes and SignalTypes are supported are configured on deployment.

- Hash Content
  - Input
    - Content type (`string`)
    - `byte[]`
    - Optional `list<string>` list of SignalTypes to use
    - Optional file extension hint (needed sometimes for photos/videos for underlying libraries)
  - Output
    - List of signals. Signals include
      - Signal type
      - Signal value (`string`)
- [TBD] Hash+Match (may be slow / require long polling)
  - Inputs
    - Content type (`string`)
    - `byte[]`
    - Optional `list<string>` of SignalTypes to use
    - Optional `list<string>` of Bank/List names to restrict search to
    - Optional file extension hint (needed sometimes for photos/videos for underlying libraries)
  - Outputs
    - List of Bank content IDs

### Matching

What SignalTypes, and what similarity settings to use (e.g. PDQ distance) are configured on deployment.

Additional SignalTypes can be made available by setting the `SIGNAL_TYPES` variable in the config.
Here is an example with CLIP signal type, after installing it with `pip install tx-extension-clip`:

```
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from tx_extension_clip.signal import CLIPSignal

SIGNAL_TYPES = [PdqSignal, VideoMD5Signal, CLIPSignal]
```

- Lookup
  - Input
    - Signal type
    - Signal value (`string`)
    - Optional `list<string>` of Bank/List names to restrict search to
  - Output
    - List of Bank content ID
- Index Status
  - Input
    - SignalType (`string`)
  - Output
    - Time of last index build

### Recording Review Results

- Record review led to discovery of harm - will communicate with exchanges if the exchange is configured to do so
  - Input
    - `list<string>` of Bank Content IDs
    - Optional `list<string>` of labels - if the label doesn’t match a bank labels it will change or prevent which information is recorded back to the exchange
- Record review did not lead to the discovery of harm
  - Input
    - `list<string>` of Bank Content IDs
    - Optional `list<string>` of labels - if the label doesn’t match a bank labels it will change or prevent which information is recorded back to the exchange
