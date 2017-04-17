# ThreatExchangeUI

A Ruby on Rails user interface for Facebook ThreatExchange. Easily query and share share threat indicators using Facebook ThreatExchange.

For info on FB ThreatExchange: [https://developers.facebook.com/products/threat-exchange] (https://developers.facebook.com/products/threat-exchange)

A functional version of ThreatExchangeUI is available at [https://threatexchangeui.seventwentynine.com] (https://threatexchangeui.seventwentynine.com)


Implemented Features:

* Query threat indicators
* Show threat descriptors
* Render IP indicators on a world map
* Submit threat descriptors

## Getting started

Facebook App ID and App Secret are needed to interact with Facebook ThreatExchange. PostgresSQL is also needed to use ThreatExchangeUI. Add relevant types data to IndicatorType, PrivacyType, SeverityType, ShareLevelType, StatusType and ThreatType tables. See [https://developers.facebook.com/docs/threat-exchange/reference/apis/v2.5] (https://developers.facebook.com/docs/threat-exchange/reference/apis/v2.5) for details.

## Installation

Install required dependencies 

    bundle install
    rake db:create
    rake db:migrate

## Bug reports

If you discover a bug with ThreatExchangeUI, please let me know (Twitter: @skills4ever)

## Contributing

1. Fork it ( https://github.com/skills4ever/ThreatExchangeUI/fork )
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request