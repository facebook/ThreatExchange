# Introduction to Hasher-Matcher-Actioner UI

Hasher-Matcher-Actioner (aka HMA) includes a web app where users can configure their signal banks, connect to exchanges like NCMEC, StopNCII, GIFCT, ThreatExchange, and others, and debug matches. These features are available as demos to show the features and functionality of HMA.  

There are 4 pages in the app:

## **Dashboard (`/ui/`)**

* View system status  
* See signal types and content types  
* Check index statistics

There are 3 demo buttons and an option to do a factory reset:

1. **Sample API**: Creates synthetic/mock data for testing  
2. **Seed Banks:**: Generates 10,000 random hashes for performance testing  
3. **Setup Tx API**: Configures real ThreatExchange integration (but needs credentials for live data)

#### **“Setup Sample API”**

The Sample API (StaticSampleSignalExchangeAPI) is a testing and demonstration tool that provides pre-generated sample hash data for development and evaluation purposes.

##### Development Testing Tool

* Purpose: Provides a mock signal exchange that simulates real threat intelligence feeds without requiring external API credentials  
* No Authentication Required: Unlike real exchanges (NCMEC, GIFCT, ThreatExchange), it doesn't need API keys or credentials  
* Instant Setup: Creates sample data immediately for testing the system

##### Sample Data Provider

When you click "Setup Sample API" it:

1. Creates the Exchange: Sets up SEED\_SAMPLE exchange configuration  
1. Provides Sample Hashes: Returns a fixed set of example hashes for both PDQ (images) and MD5 (videos)  
1. Populates the System: Gives you 18 sample records initially (as seen in logs: "fetch\_iter() with 18 new records")  
1. Enables Matching: Allows you to test the matching functionality immediately

##### Fetching Simulation

From the logs, you can see it working:

```py
INFO in fetcher: SEED_SAMPLE[sample] Fetching signals for SEED_SAMPLE from sample
INFO in fetcher: SEED_SAMPLE[sample] No checkpoint, should be the first fetch.
DEBUG in fetcher: SEED_SAMPLE[sample] fetch_iter() with 18 new records
INFO in fetcher: SEED_SAMPLE[sample] Fetched all data! Up to date!
```

#### **Why a Sample API?**

##### Development Workflow

* When you're developing or evaluating HMA, you need hash data to test matching  
* Instead of configuring complex external APIs, you click "Setup Sample API"  
* It immediately provides workable test data

##### Demo Purpose

* **Shows System Functionality:** Demonstrates how external exchanges work without real credentials  
* **Testing Matching**: Provides known hashes you can test matching against  
* **Index Building**: Triggers the indexing process with sample data  
* **UI Validation:** Lets you see how the exchange status, fetching, and matching systems work

##### Educational Value

* **Example Implementation:** Shows how signal exchanges are structured  
* **API Pattern**: Demonstrates the exchange API interface without complexity  
* **No External Dependencies:** Works completely offline

#### **What You See in the UI:**

1. **Before Setup:** Button shows "Setup Sample API"  
2. **After Setup:** Button shows "✅ Sample API created" and is disabled  
3. **Exchange Status:** Shows SEED\_SAMPLE exchange in the exchanges page  
4. **Index Building:** Triggers automatic background indexing of the sample data  
5. **Matching Ready:** System now has data to match against

### Technical Implementation:

The StaticSampleSignalExchangeAPI is essentially a hardcoded data source that:

* Returns a fixed set of sample hashes (PDQ and MD5)  
* Simulates the behavior of real threat intelligence exchanges  
* Provides metadata and signal data that the system can index and match against  
* Requires no external network calls or authentication


## **"Seed Banks"**

Based on the code analysis and logs, the Seed Banks button:

### Creates Test Banks

* 2 Banks: SEED\_BANK\_0 and SEED\_BANK\_1  
* Full Matching: Both set to 100% matching enabled

### Generates Massive Sample Data

* 10,000 Total Hashes (5,000 per bank)  
* Mixed Types: PDQ perceptual hashes (\~5,004) \+ MD5 video hashes (\~5,000)  
* Synthetic but Realistic: Uses ThreatExchange library's random signal generators

### System Effects

* Triggers Index Rebuild: Background process takes \~30 seconds  
* Ready for Testing: Creates searchable data immediately  
* Performance Scale: Provides substantial dataset for realistic testing

### Use Cases

* Algorithm Testing: Test similarity matching algorithms  
* UI Development: Populate interface with realistic data volumes  
* Performance Testing: Benchmark system with substantial datasets  
* Demo Workflows: Enable full end-to-end testing without real uploads

The seeded data is stored in a PostgreSQL database that runs inside the dev container:

#### **Database Structure**

* Database: `media_match`  
* Tables: `bank`, `bank_content`, `content_signal`  
* Host: `localhost:5432` (inside the dev container)  
* Credentials: `media_match/hunter2`

#### **Data Organization**

* 2 Banks: SEED\_BANK\_0 and SEED\_BANK\_1  
* \~10,000 Total Hashes: 5,004 PDQ \+ 5,000 MD5  
* Each Content Item: Has a unique ID and associated signal/hash values


### “Setup Tx API"

 The “Setup Tx API” button creates a demo integration with [ThreatExchange](https://developers.facebook.com/docs/threat-exchange/). 

#### **Integration Details**

* **Exchange Name:** `TX_EXAMPLE_COLLAB`
* **API Type:** Facebook's ThreatExchange API (FBThreatExchangeSignalExchangeAPI)  
* **Target**: Privacy group ID 1012185296055235 (demo/test group)  
* **Real Connection**: Unlike Sample API, this API connects to actual ThreatExchange infrastructure (albeit a demo one)

#### **ThreatExchange Benefits**

* **Industry Scale:** Access to millions of real threat content hashes  
* **Collaborative Defense:** Shared threat intelligence across major platforms  
* **Live Updates:** Periodic sync with updated threat databases  
* **Multiple Signal Types:** PDQ, MD5, and other content signatures

#### **Technical Details**

* **Authentication Required:** Needs valid Facebook App credentials for production (more info [here](https://developers.facebook.com/docs/threat-exchange/getting-access/))  
* **Background Fetching:** Automatic periodic synchronization  
* **Bank Integration:** Imported data goes into dedicated bank  
* **API Limits:** Subject to ThreatExchange rate limiting

#### **Important Caveats**

* **Demo Mode:** Uses test privacy group that may not have live data  
* **Credentials Needed:** Won't fetch real data without valid API credentials, which users can apply for access for [here](https://developers.facebook.com/docs/threat-exchange/getting-access/).  
* **Production Setup:** Real deployments need proper app registration with Facebook for Developers.

## **Banks (`/ui/banks`)**

* See your test banks: `SEED_BANK_0` and `SEED_BANK_1`  
* Each contains 5,000 sample hashes  
* Try uploading images to test matching for content in hash banks


### Creating a Demo Bank

Users can create a hash bank separate from external hash exchanges like the NCMEC hash list or GIFCT hash list. Simply click “Create New Bank” and manually upload a few files to test.

Once you add content, you can test by uploading either the same or different image in the “Find Content in Banks” section. If there is a match, the UI will show which hash bank the content was found in.


### Browsing Hash Banks

The web UI only allows searching for specific files within the hash banks. If users want to explore an overview or browse content in the hash banks, they have to query the database directly.

#### **Database Table Stats (Quickest Overview)**

Run this command to see high-level statistics:

```shell
flask --app OpenMediaMatch.app table_stats
```

This shows counts of banks, contents, signals, etc.

#### **Direct Database Queries**

You can also connect to PostgreSQL directly to browse the data:

```shell
# Connect to database  
psql -h localhost -p 5432 -U media_match -d media_match
# Enter password: hunter2
# List all banks 
SELECT * FROM bank;
# See all content in a specific bank 
SELECT bc.id, bc.bank_id, b.name, cs.signal_type, cs.signal_val 
FROM bank_content bc 
JOIN bank b ON bc.bank_id = b.id 
JOIN content_signal cs ON bc.id = cs.content_id 
WHERE b.name = 'SEED_BANK_0';
# Count contents per bank 
SELECT b.name, COUNT(bc.id) as content_count 
FROM bank b 
LEFT JOIN bank_content bc ON b.id = bc.bank_id 
GROUP BY b.name;
```

#### **REST API Endpoints**

The API provides several endpoints to browse banks:  
**List all banks:**

```shell
curl http://localhost:5000/c/banks
```

**Get specific bank info:**

```shell
curl http://localhost:5000/c/bank/SEED_BANK_0
```

**Get specific content details:**

```shell
curl http://localhost:5000/c/bank/SEED_BANK_0/content/1
```

## **Exchanges (`/ui/exchanges`)**

The Exchanges page lets users configure external hash exchanges that are API based.


### Supported Hash Exchanges

**NCMEC (National Center for Missing & Exploited Children)**

* Child safety hash sharing program  
* Requires authentication credentials  
* Automated hash synchronization

**GIFCT (Global Internet Forum to Counter Terrorism)**

* Terrorist content hash database  
* Enterprise-level access required  
* Real-time threat intelligence updates

**Meta ThreatExchange**

* Comprehensive threat intelligence platform  
* API key authentication required  
* Multi-signal type support

**StopNCII**

* Non-consensual intimate image hashes  
* Privacy-focused hash sharing  
* Victim-centered approach

### Exchange Configuration

Several of the hash exchanges supported require credentials, provided in the form of a JSON blob:

1. Configure authentication credentials (API keys, certificates)  
2. Select signal types to synchronize  
3. Set fetch frequency and retry policies  
4. Monitor connection health and data flow


## **Match Debugging (`/ui/match`)**

The Match Debugging page allows users to do a side-by-side comparison of two images to test different hashing algorithms and see how perceptual hashing works. As of June 2025, the demo only supports PDQ. This is helpful to tune matching thresholds and validate algorithms, which is essential for understanding false positive/negative rates.


If the images are a match, it will show a distance of 0. If the images are NOT a match, it will show whether it’s a match and the related distance between the two images.
