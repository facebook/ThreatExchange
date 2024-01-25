HMA is all about Matching [Content](Glossary#hasher) but how can you learn when a [Match](Glossary#matcher) has occurred? Rather than constantly checking the [Matches Page](The-Matches-Page), we can notify your system directly. HMA uses [Webhooks](https://sendgrid.com/blog/whats-webhook/) as its notification framework.

Webhooks are configurable [HTTP requests](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) sent to your system that contain a JSON object describing the Match for your system to process. HMA allows you to configure under what conditions Webhooks are sent, what url address they are sent to, and with what parameters. In this tutorial, we'll show you how to set up a basic Webhook to notify your system of a Match.

## Step 1 - Set up an endpoint to consume the Webhooks
Let's say you've set up HMA to Match Content from a [ThreatExchange](Glossary#fetcher) "Cats" [Dataset](Glossary#matcher). Every time you [upload a photo](Submit Content) to HMA, it is compared to the other [Hashes](Glossary#hasher) in the Dataset to determine whether or not it is a cat (If you haven't set this up you'll want to first follow the tutorials for [Manually](Tutorial-Manually-Submitting-Photos-to-HMA) or [Programmatically](Tutorial-Programmatically-Submitting-Photos-to-HMA) submitting images). If a Match is found, you'll want to notify your system so that one of your reviewers can confirm that it is, in fact, a cat.

First, you need to set up a server-side endpoint on your infrastructure to receive the Webhooks from HMA so that when a Match occurs you can be notified. If you aren't sure how to do this, [here's a tutorial on consuming Webhooks using python](https://blog.bearer.sh/consume-webhooks-with-python/). For the payload response, see the [Webhooks Reference](Webhooks-Reference).

For this example, you'll want to set an endpoint on your system that sends the image for review after being notified of a Match.

If you'd like to skip this step for now, you can create a test Webhook at [webhook.site](webhook.site) and use the link provided there in the next step

## Step 2 - Create an Action to send a webhook
Now that you have your client endpoint set up, you'll want to configure HMA to notify your server of a Match. To do this, navigate to HMA and click on "Settings" in the bottom left and then navigate to the "Actions" tab. Press the "+" to create a new [Action](Glossary#actioner) and give it a unique name. Ensure that the "Actioner Type" is set to "WebhookActioner". In the URL field, add the endpoint URL from Step 1 that will consume the Webhook. Select the HTTP type your endpoint is expecting (usually `POST`). You can additionally specify any headers to be included in the Webhook payload. These headers can be used for authentication or additional server-side logic. Press the save checkmark when done.

![](https://github.com/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/docs/images/Create%20Action.png)

## Step 3 - Create [ActionRule](Glossary#actioner) to trigger your Action when a Match occurs
Having created an Action to notify our endpoint, you now need to specify when that Action should be called. ActionRules are how you define the logic for when to call an Action after a Match. Navigate to the "Action Rules" tab of the "Settings" page and press the "+" button to create an ActionRule.

Give the rule a unique name and, under the "Classification" column, add a [Classification](Glossary#matcher) specifying the cat Dataset. For example, if the cat Dataset has id `12345` add a Classifiation `DatasetID = 12345`. Checkout the [ActionRule Reference documentation](Action-Rule-Evaluation) for more descriptions of these fields and additional customization options.

Finally, set the "Action" column to the Action we created in step 2 and press the save checkmark when done.

![](https://github.com/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/docs/images/Create%20ActionRule.png)

## Step 4 - Confirm Your Webhook is called
Now that you've configured HMA to send a Webhook on a Match, you'll want to confirm it is being called correctly. [Send some images through the system and watch them match](Tutorial-Manually-Submitting-Photos-to-HMA). You should then see a Webhook sent to your client. You should also see "MyCatAction" appear in Action History section of the [content details page](Content-Details). Note, depending on how many images you upload there may be a delay in the Webhook being triggered of up to 4 minutes. Uploading more images can make HMA run faster.

![](https://github.com/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/docs/images/Content%20Details%20Page%20with%20ActionHistory.png)
