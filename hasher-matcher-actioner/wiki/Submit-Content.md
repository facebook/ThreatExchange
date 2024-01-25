Content Enters HMA in two ways: the [Content Submissions API](Content-Submissions-API) and the Content Submission UI page. Currently, Content submitted will be copied to the HMA datastore and passed along to the rest of the system for [Hashing](Glossary#hasher), [Matching](Glossary#matcher), and possibly [Actioning](Glossary#actioner).

![](https://github.com/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/docs/images/Submit%20Content.png)

Form Details
--------
To submit Content from the UI, first select a submission type. Currently we support three methods Content submission: 
- Upload
   - Basic upload of an image to the system (Implementation detail: 2 step request using signed s3 urls).
- From URL
   - Provide the system a URL from which it will send a get request for the content data.

You must then provide a unique ID for the Content. This unique identifier is used to track content through the system and is used to create a record upon submission.
   - Warning: The UI will overwrite old Content uploaded with the same `content_id`. HMA will replace the existing Content metadata and Hash with the newly uploaded Content. 
        - If matches and actions are already being propagated based on the original submission system, behavior is no longer well defined. 
        - This functionality is not restricted to allow for easy resubmission of the same content and id pair. It is important to be mindful of this. 
        - Best practice is submitting the same unique identifier used in the system submitting content to your deployed HMA. 

Along with a unique ID, you can also submit additional fields that will be recorded along with the Content and propagated through out HMA and to [Actions](Glossary#actioner) on the other end. On submission:
- The form takes each entry as a string
- Appends them to a record for that Content id

On Submit
---------
You will be prompted with a link to a new page with the submitted [Content Details](Content-Details). Once processed, this details page and [the Match page](The-Matches-Page) will be populated with any [Matches](Glossary#matcher) found and resulting Actions the system triggers.