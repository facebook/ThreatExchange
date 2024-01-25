HMA uses the [Fetcher](Glossary#fetcher) to read [Signals](Glossary#hasher) and [Opinions](Glossary#writebacker) from [ThreatExchange](https://developers.facebook.com/docs/threat-exchange/getting-started) to build [Datasets](Glossary#matcher) and keep them in sync. The [Fetcher](Glossary#fetcher)(an AWS lambda function) runs every 15 minutes by default, fetching data through [ThreatExchange API](https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-privacy-groups/v11.0) based on which [PrivacyGroups](Glossary#fetcher) you have access to. For each PrivacyGroup, the Fetcher keeps an HMA Dataset in sync. You can find the python code [here](https://github.com/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/hmalib/lambdas/fetcher.py)

To Fetch Datasets from ThreatExchange, you need to ensure HMA has your ThreatExchange credentials. If you haven't already, you can [follow these steps](Installation#connect-to-threatexchange) to connect HMA to ThreatExchange: 

# Change the frequency of the Fetcher
We are using a Terraform variable to configure the frequency of fetching data from the [ThreatExchange](https://developers.facebook.com/docs/threat-exchange/getting-started). To change it, go to ```/ThreatExchange/hasher-matcher-actioner/terraform/terraform.tfvars``` and change the value of ```fetch_frequency```, rebuild and deploy the image. For example, if you want to change it to 10 minutes, you will do following steps: 
* update ```fetch_frequency = "10 minutes"``` in **terraform.tfvars**  

* go to terraform folder, run command ```terraform apply```
# Start/Stop Fetching data from ThreatExchange
You can start/stop fetching data from ThreatExchange for specific datasets.   
* Select _**Settings**_ in left bottom, go to ThreatExchange tab

![](https://github.com/facebook/ThreatExchange/blob/31d8c61a3f5c8f746db772157bf13f311bf1969c/hasher-matcher-actioner/docs/images/ThreatExchange%20tab.png)
* Toggle off the _**Fetcher Active**_ for specific datasets

![](https://github.com/facebook/ThreatExchange/blob/31d8c61a3f5c8f746db772157bf13f311bf1969c/hasher-matcher-actioner/docs/images/Fetcher%20Active.png)