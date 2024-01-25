
In this article, you'll learn.
1. What are banks?
2. How you can use banks to scan your platform for copies of media.

---

To scan your submissions for copies of photos or videos, you use the Banks feature in HMA. `Banks` are collections of `BankMembers`. Each BankMember is a photo or a video that you want to scan for.

Once you upload a photo or a video, all future submissions to HMA are scanned for copies. Copies, if found, can be reported to your APIs.

![](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/docs/images/HMA-Banks-illustration.png?raw=true)

## Creating a bank

Head over to the HMA home page for a deployed instance. Click on 'Banks' in the left side bar. Now, click on the 'Add Bank' or 'Create Bank' button.

In the form:
a. add a bank name. Bank names are required to be unique. 
b. add a description. This helps others in your team understand what this bank does.
c. turn matching on or keep it off. If matching is kept off, matches against this bank's members will not be reported. You can always turn this on later.
d. optionally, add tags. These tags help the [[actions|The-Action-Rules-Page]] determine whether to report a match or not. We recommend using the bank's category, or the reason why the members are violating your policies as tags. Eg. 'puppies' is a great tag if images of puppies are not allowed on your site.

## Adding Bank Members

Once a bank is created, it shows up when you click 'Banks' on the HMA sidebar. You can click on the bank's tile to see its details. There are three tabs when you open a bank. Bank Details, Video Memberships and Photo Memberships.

To add photos, click on Photo Memberships → 'Add Member', or to add videos, click on Video Memberships → 'Add Member'.

## Rebuild index manually

Within a minute of adding a member, its fingerprints (or hashes) are extracted. To start matching against these new fingerprints, HMA needs to rebuild the index. HMA automatically does rebuilds every fifteen minutes. However, if it is important to you that the rebuild happen sooner (if you are dealing with a crisis for example), rebuild the index manually by heading over to the 'Settings' page on the sidebar. Click on the 'Indexes' tab and then click on 'Rebuild Indexes'.

Note: HMA will only match if the bank's 'Active' toggle is set to true. However, you don't need to rebuild indexes when changing the 'Active' toggle.

## Configuring an action rule for banks

Check out how to create action rules [[The-Action-Rules-Page]]. For bank matches, the conditions look as such:

| Condition Name | Condition Value  |
|-----------------|------|
| `Dataset Source` | `bnk`|
| `Dataset ID` | `<bank_id>` ⬅️ Get this from the Bank's details page. | 
| `Matched Signal ID` | `<bank_member's id>` ⬅️ Get this from by clicking on 'View Member` on any Video or Photo Member |
| `Matched Signal` | tags attached to banks and bank members will come here. Use one 'Matched Signal' row per tag.  |

Any action rule configured using the source, bank_id or bank_member_id can be used along with a specific action. You can define actions as shown in [[The-Action-Page]] and then use an action to notify when submissions from your site match bank members.
