You have many options for integrating with HMA to scan content on your platform. Just because HMA has features for different content types or a rules engine doesn't mean you have to use it. Here are some different configurations or setups that you might use to search for content on your platform.

Note that these are not mutually exclusive. You may integrate with your HMA instance in multiple ways depending on the needs of your platform.

# Simplest Test Integration
![test integration](https://user-images.githubusercontent.com/1654004/135461547-08e3c9f0-2701-4f7f-98a6-4a3882781435.png)

The fastest way to test the potential value from HMA is to use it as part of a collaborative integrity project where you can get pre-existing datasets, and then route a fraction of your content through it. Simply by tracking the number of matches, you can get an idea of the potential value.

Testing about 100,000 images (in our load testing, about $10-100 of AWS runtime) would give you a good idea of the value of a dataset even on relatively rare events. You also have the option of using a script to sample content from your backend (see the "Retroaction" case below). 


**Usecase**: Test out HMA, new dataset, hash type, or content type.

**Where to call HMA APIs From**: Where content is created, probably a webserver.

**What is passed into HMA**: A pointer to the content - a URL that can be used to fetch the content, or in some cases the raw content itself. 


# End-To-End Integration - HMA Does the Hashing
![simple e2e](https://user-images.githubusercontent.com/1654004/127726728-54817b9e-4534-486e-ab22-9ccfae98f22b.png)

This is the simplest integration, and the one that uses all the features of HMA. It allows you to scan new content on your platform and call back into your own admin tools if you need to quarantine or hide any content that is matched. This is often a useful integration for testing HMA features (such as experimenting with a new hash or content type) by only sending it a sample of incoming traffic.

**Usecase**: Realtime content moderation of new content.

**Where to call HMA APIs From**: Where content is created, probably a webserver.

**What is passed into HMA**: An ID that you can track this content later and a URL that can be used to fetch the image from either your CDN or backend storage.

## End-To-End Special Case: S3 Backend

![s3](https://user-images.githubusercontent.com/1654004/127726926-55136ed6-d3d2-4716-96d5-bf13a3f7c9e1.png)

As a special case, if your media backend is Amazon S3, there's a simpler integration path, described at [[How to Connect your s3 Bucket to HMA | How-to-Connect-your-s3-Bucket-to-HMA?]].

**Usecase**: Realtime content moderation of new content.

**Where to call HMA APIs From**: Nowhere! It will trigger from Amazon's s3 events.

**What is passed into HMA**: The s3 bucket name and filename.

# Highest Throughput End-to-End Integration - You Do the Hashing

![Graphic showing hashing and webserver skipping the hasher component](https://user-images.githubusercontent.com/1654004/135461033-ea328131-3c5a-4798-8626-cd85f5554c35.png)

If operating at high scale (greater than 1300 images/sec), the cost of transmitting the original media to HMA will start to become a bottleneck. To solve this, if you do the hashing of the image at the point of upload (often a webserver), you can call into HMA at the matcher component instead, which will unlock 4000 images/sec or greater throughput, but also may save you cash. The downside is that this increases the cost of trying out new hashing algorithms, but you can always sample and fall back to the Simple End-to-End integration.

Another usecase that looks similar to this is live video. Segments or key frames can be hashed by the same service that is handling transcoding, and those segments can be then run through HMA.

**Usecase**: High volume or cost optimizing integration.

**Where to call HMA APIs From**: Where new content is created, but after running it through an on-server copy of the hashing algorithm.

**What is passed into HMA**: An ID that you can track this content later and the hash of the content.

# Running On Historic Content: Retroaction 
![image](https://user-images.githubusercontent.com/1654004/135461059-dba6a5e9-95d7-4f93-98f7-ddd2402e8d23.png)

Often running on only live content is not enough. Content may take some time to be flagged by users, or time to make it through your review queue, and if it's already gone viral on your site, you may need to replay recent uploads back to HMA. You may also want to consider running the entire content of the site through HMA at some frequency (i.e. 30d).

Note: It's possible to instead call at the hasher instead of at the matcher as well, but throughput and cost will start to become a greater issue at the volume of "all the content on your platform". 

**Usecase**: Scanning the entirety of content on your platform, or re-running a circular buffer (3 hours, 24 hours, 72 hours, or more) of recent hashes.

**Where to call HMA APIs From**: A service (or even a script) that iterates through all the items stored in the backend.

**What is passed into HMA**: An ID that you can track this content later and the hash of the content.

# Index Queries
![image](https://user-images.githubusercontent.com/1654004/135461094-beb7a6fa-1ccc-47b5-b67f-332637b99dc4.png)

In some cases, you may want to just ask whether a piece of content is known by HMA already. This might be for custom purposes, but one common one is to prevent content that matches a trusted dataset to ever be stored on the site. Image, text, and URLs can be hashed and queried reliably in realtime, though videos cannot. 

**Usecase**: Blocking content before it's stored on your backend, deduping items in your review queue, and many more

**Where to call HMA APIs From**: Where new content is created, but after running it through an on-server copy of the hashing algorithm.

**What is passed into HMA**: The hash of the content

# Locally Managed Datasets
![local content](https://user-images.githubusercontent.com/1654004/135461972-b5dbdf24-178f-42ab-8239-3b2fbaa327d9.png)

HMA is primarily designed as a tool for collaborative integrity. However, as part of that it contains a robust content moderation system. There are some types of harm that it may not make sense to collaborate on, but that may benefit from content moderation. Many other integrations work just fine with only local data.

**Usecase**: Content moderation without collaboration.

**Where to call HMA APIs From**: Wherever you are doing your content review.

**What is passed into HMA**: A URL or hash of the content, which dataset to add it to or remove it from.

# Expanding to New Datasets
![fetcher only](https://user-images.githubusercontent.com/1654004/127727012-6ebdaa0b-079a-4a1c-bcd5-9a987d010b37.png)

Many different entities host datasets for trust and safety purposes. HMA was initially built for Facebook's ThreatExchange, but maybe you'd like to connect to NCMEC's industry hash database, or GIFCT's Media Hash Sharing database. These can be synced to HMA for your usage in any of the above usecases.