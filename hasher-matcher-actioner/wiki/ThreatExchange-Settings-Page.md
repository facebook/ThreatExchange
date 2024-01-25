The ThreatExchange tab on the Settings page is used to configure Datasets read from ThreatExchange PrivacyGroups. 
# Dataset Details
A dataset is a collection of Signals who's Content is purportedly all related. HMA uses dataset as the data source for the [Matcher](https://github.com/facebook/ThreatExchange/wiki/Glossary#Matcher). In the ThreatExchange tab, we are displaying some information and configuration settings for each dataset. 
* **Dataset Name** : Read from the PrivacyGroup in ThreatExchange, currently non-editable. If the PrivacyGroup is currently in use, the background color is blue. If not, it's gray.
* **Information** : shows the description of each dataset.
* **ID** : Read from the PrivacyGroup in ThreatExchange, currently non-editable.
* **HashCount** : how many Signals are in the Dataset contains in S3 bucket.
* **MatchCount** : How many Matches have occurred against this Dataset.
* **Fetcher Active** : this toggle is used to control Fetching from the ThreatExchange PrivacyGroup to keep Datasets in Sync. If switched on, the Fetcher will keep the given Dataset in sync with the ThreatExchange PrivacyGroup. If switched off, the Dataset will remain unchanged until it is switched on again. Can only be toggled if Dataset is active. For more information, please refer to [this page](Fetching-data-from-ThreatExchange). 
* **Matcher Active** : this toggle is used to control matching against the Dataset. If on, Signals will be matched against the dataset. If off, the Dataset will be ignored by the Matcher. Can only be toggled if Dataset is active.
* **Writeback (Seen?)**: Controls whether or not the [Writebacker](https://github.com/facebook/ThreatExchange/wiki/Glossary#writebacker) will writeback to ThreatExchange after a Match occurs. Can only be toggled if Dataset is active. For more Information, please refer to [this page](How-to-disable-writebacks-to-ThreatExchange).
* **save button** : if fetcher active or write back is changed, **_Save_** button shows.
* **delete button** : if the Dataset is not currently in use, _**Delete**_ button shows.
![](https://github.com/facebook/ThreatExchange/blob/72689d65457d66085a9d1b073d596fc04c92f722/hasher-matcher-actioner/docs/images/Dataset.png)

# Sync Button
 When **_Sync_** button is clicked, HMA will update the list of Datasets available from ThreatExchange. If a new Dataset is available it will be added to this page. If a Datasets that was available is no longer available it will be disabled.

# Delete Button
 When _**Delete**_ button is clicked, the Dataset will be removed from HMA

# Test Photos
* Instructions on how to download images from copydays and use them to match.
* Select _**Create**_ button to create the testing config from copydays.
![](https://github.com/facebook/ThreatExchange/blob/901a487ae42bbe59dad18be4d091481a771dbc2c/hasher-matcher-actioner/docs/images/testphotos.png)