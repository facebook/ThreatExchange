## Overview

DynamoDB is the primary database for the HMA system. As with any NoSQL database, the schema design affects what queries can be effectively run or at all.

# HashRecords

Of all the record types, this is the most common one. So, the design for these items is especially crucial.

## Primary Index
* Partition Key: `c#{key}`. Here key is content key.
* Sort Key: `s#{indicatorSource}#{descriptorId}`. For MVP, the indicator source can only be "te".

## Global Secondary Index I
* Partition Key: `s#{indicatorSource}#{descriptorId}`
* Sort Key: `c#{key}`

This is the reverse of the primary index.

## Global Secondary Index II
* Partition Key: `type#{hashingMethod}` 

	
# Issues with using FilterExpressions (@schatten's expeditions; very WIP)

It appears using `FilterExpressions` can be tremendously costly. I'm yet to figure out the impact of SKs being fully utilized. This is a WIP of findings and potential next steps.

Since the PK is used by Dynamo to physically partition, and it is hashed, the quickest and **only** Dynamo style query using this key is the "get me all matches for this content" query.

## Secondary Indexes
Because our SK is "s#{indicatorSource}#{descriptorId}", equality on that can be used to narrow down the data rapidly.

**References**
1: [https://www.alexdebrie.com/posts/dynamodb-filter-expressions/](https://www.alexdebrie.com/posts/dynamodb-filter-expressions/)

