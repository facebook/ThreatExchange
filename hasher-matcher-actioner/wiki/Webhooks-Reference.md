A [Webhook](Glossary#actioner) is a configurable [HTTP request](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) sent to a [Platform](Glossary#terms-and-concepts-used-in-hma)'s system that contains a JSON object describing the [Match](Glossary#matcher) for the Platform to process. HMA allows you to configure Action Rules and Actions that control when Webhooks are called, and what URL address they are sent to (and with what parameters and headers), respectively. Read more about Webhooks as a concept [here](https://sendgrid.com/blog/whats-webhook/). Read more about configuring Webhook Actions in HMA [here](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-How-to-Notify-My-System-when-My-Content-Matches-a-Dataset).

# Webhook Response Payload
When HMA calls a Webhook in response to a Match, the payload will look something like this:

```javascript
{
  "content_key": "images/storm-2021-05-27-1f3d9958-cfb5-40c8-9cc8-5f4c96ac08e1-200100.jpg",
  "content_hash": "361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
  "matching_banked_signals": [
    {
      "banked_content_id": "3898865936872123",
      "bank_id": "258601789084078",
      "bank_source": "te",
      "classifications": [
        {
          "key": "Classification",
          "value": "true_positive"
        },
        {
          "key": "BankIDClassification",
          "value": "258601789084078"
        },
        {
          "key": "BankSourceClassification",
          "value": "te"
        },
        {
          "key": "BankedContentIDClassification",
          "value": "3898865936872123"
        }
      ]
    },
    {
      "banked_content_id": "3898865936872123",
      "bank_id": "303636684709969",
      "bank_source": "te",
      "classifications": [
        {
          "key": "Classification",
          "value": "true_positive"
        },
        {
          "key": "BankSourceClassification",
          "value": "te"
        },
        {
          "key": "BankIDClassification",
          "value": "303636684709969"
        },
        {
          "key": "BankedContentIDClassification",
          "value": "3898865936872123"
        }
      ]
    }
  ],
  "action_label": {
    "key": "Action",
    "value": "TryWebhookSite"
  },
  "action_rules": [
    {
      "name": "Push to Webhook",
      "action_label": {
        "key": "Action",
        "value": "TryWebhookSite"
      },
      "must_have_labels": [
        {
          "key": "BankIDClassification",
          "value": "303636684709969"
        }
      ],
      "must_not_have_labels": []
    }
  ]
}
```



## Fields in Payload
- **`content_key`** : A unique identifier for the [Content](Glossary#hasher) the Match resulted from.
- **`content_hash`** : The [Signal](Glossary#hasher) derived from the Content which generated the Match. Currently always a [Hash](Glossary#hasher).
- **`matching_banked_signals`** : A collection of [Signals](Glossary#hasher) which the Content matched (aka the [MatchedSignals](Glossary#matcher)). Note that a single piece of Content can match one or more Signals in one or more [Datasets](Glossary#matcher).
   - `banked_content_id` : The ID of the MatchedSignal which the content Matched .
   - `bank_id`: The ID of the Dataset which the MatchedSignal is present in.
   - `source_id` : The Source of the Dataset. `te` implies the Source is [ThreatExchange](Glossary#fetcher).
   - `classifications` : [Classifications](Glossary#matcher) of the present about the MatchedSignal stored as key-value pairs. 
- **`action_label`** : The name of the [Action](Glossary#actioner) which triggered the Webhook to be called at the time it was triggered. See above for payload type.
- **`action_rules`** : A collection of [ActionRules](Glossary#actioner) which triggered the Action. Note that there may be multiple ActionRules which, when evaluated, all trigger the same Action. In this case, the Action will only be executed once.
   - `name`: The name of the ActionRule at the time it was evaluated.
   - `action_label`: The Action which the ActionRule was configured to trigger.
   - `must_have_labels` : A collection of [Classifications](Glossary#matcher) which must be present on the Match for the Action to be invoked. Read more about how the Actioner uses Classifications [here](Action-Rule-Evaluation).
   - `must_not_have_labels` : A collection of [Classifications](Glossary#matcher) which must NOT be present on the Match for the Action to be invoked. Read more about how the Actioner uses Classifications [here](Action-Rule-Evaluation).
