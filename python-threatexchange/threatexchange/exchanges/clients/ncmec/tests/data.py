STATUS_XML = """
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<status xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <ipAddress>127.0.0.1</ipAddress>
    <username>testington</username>
    <member id="1">Sir Testington</member>
</status>
""".strip()

NEXT_UNESCAPED = (
    "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z"
    "&to=2017-10-30T00%3A00%3A00.000Z&start=2001&size=1000&max=3000"
)

NEXT_UNESCAPED2 = (
    "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z"
    "&to=2017-10-30T00%3A00%3A00.000Z&start=3001&size=1000&max=4000"
)
NEXT_UNESCAPED3 = (
    "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z"
    "&to=2017-10-30T00%3A00%3A00.000Z&start=4001&size=1000&max=5000"
)

ENTRIES_XML = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <images count="2" maxTimestamp="2017-10-24T15:10:00Z">
        <image>
            <member id="42">Example Member</member>
            <timestamp>2017-10-24T15:00:00Z</timestamp>
            <id>image1</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</md5>
                <sha1>a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</sha1>
                <pdna>a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1...</pdna>
            </fingerprints>
            <feedback lastUpdateTimestamp="2023-06-01T12:48:14Z">
                <affirmativeFeedback type="Md5" lastUpdateTimestamp="2023-06-01T12:48:14Z">
                <members timestamp="2023-06-01T12:48:14Z">
                    <member id="42">Example Member</member>
                </members>
                </affirmativeFeedback>
                <negativeFeedback type="Sha1" lastUpdateTimestamp="2023-05-31T19:41:51Z">
                <reasons>
                    <reason guid="01234567-abcd-0123-4567-012345678900" name="Example Reason 1" type="Sha1"/>
                    <members timestamp="2023-06-01T12:48:14Z">
                        <member id="42">Example Member</member>
                    </members>
                </reasons>
                </negativeFeedback>
            </feedback>
        </image>
        <deletedImage>
            <member id="43">Example Member2</member>
            <id>image4</id>
            <timestamp>2017-10-24T15:10:00Z</timestamp>
        </deletedImage>
    </images>
    <videos count="2" maxTimestamp="2017-10-24T15:20:00Z">
        <video>
            <member id="42">Example Member</member>
            <timestamp>2017-10-24T15:00:00Z</timestamp>
            <id>video1</id>
            <fingerprints>
                <md5>b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1</md5>
                <sha1>b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1</sha1>
            </fingerprints>
        </video>
        <deletedVideo>
            <member id="42">Example Member</member>
            <id>video4</id>
            <timestamp>2017-10-24T15:20:00Z</timestamp>
        </deletedVideo>
    </videos>
    <paging>
        <next>/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&amp;to=2017-10-30T00%3A00%3A00.000Z&amp;start=2001&amp;size=1000&amp;max=3000</next>
    </paging>
</queryResult>
""".strip()


ENTRIES_XML2 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <images count="1" maxTimestamp="2019-10-24T15:10:00Z">
        <image>
            <member id="42">Example Member</member>
            <timestamp>2019-10-24T15:00:00Z</timestamp>
            <id>image10</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</md5>
                <sha1>b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</sha1>
                <pdna>b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1...</pdna>
            </fingerprints>
            <feedback />
        </image>
    </images>
    <paging>
        <next>/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&amp;to=2017-10-30T00%3A00%3A00.000Z&amp;start=3001&amp;size=1000&amp;max=4000</next>
    </paging>
</queryResult>
""".strip()

# This example isn't in the documentation, but shows how updates work
ENTRIES_XML3 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <videos count="2" maxTimestamp="2019-11-25T15:10:00Z">
        <video>
            <member id="101">TX Example</member>
            <timestamp>2019-11-25T15:10:00Z</timestamp>
            <id>willupdate</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>facefacefacefacefacefacefaceface</md5>
            </fingerprints>
        </video>
        <video>
            <member id="101">TX Example</member>
            <timestamp>2019-11-24T15:10:00Z</timestamp>
            <id>willdelete</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>bacebacebacebacebacebacebacebace</md5>
            </fingerprints>
        </video>
    </videos>
    <paging>
        <next>/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&amp;to=2017-10-30T00%3A00%3A00.000Z&amp;start=4001&amp;size=1000&amp;max=5000</next>
    </paging>
</queryResult>
""".strip()

ENTRIES_XML4 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <videos count="2" maxTimestamp="2019-11-24T15:10:00Z">
        <video>
            <member id="101">TX Example</member>
            <timestamp>2019-11-24T15:10:00Z</timestamp>
            <id>willupdate</id>
            <classification>A2</classification>
            <fingerprints>
                <md5>facefacefacefacefacefacefaceface</md5>
            </fingerprints>
        </video>
        <deletedVideo>
            <member id="101">TX Example</member>
            <timestamp>2019-11-25T15:10:00Z</timestamp>
            <id>willdelete</id>
        </deletedVideo>
    </videos>
</queryResult>
""".strip()

ENTRIES_LARGE_FINGERPRINTS = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <videos count="1" maxTimestamp="2019-11-24T15:10:00Z">
        <video>
            <member id="101">TX Example</member>
            <timestamp>2019-11-24T15:10:00Z</timestamp>
            <id>largetags</id>
            <classification>A2</classification>
            <fingerprints>
                <md5>facefacefacefacefacefacefaceface</md5>
                <tmk-pdqf rel="self" href="/v2/entries/1/fingerprints/TMK_PDQF"/>
				<videntifier rel="self" href="/v2/entries/1/fingerprints/VIDENTIFIER"/>
            </fingerprints>
        </video>
    </videos>
</queryResult>
""".strip()

AFFIRMATIVE_FEEDBACK_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<feedbackSubmission xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <affirmative>
        <!-- Intentionally left blank -->
    </affirmative>
</feedbackSubmission>
""".strip()

NEGATIVE_FEEDBACK_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<feedbackSubmission xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <negative>
        <reasonIds>
            <guid>01234567-abcd-0123-4567-012345678900</guid>
        </reasonIds>
    </negative>
</feedbackSubmission>
""".strip()

UPDATE_FEEDBACK_RESULT_XML = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<submissionResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
  <!-- What this returns is not documented -->
</submissionResult>
""".strip()
