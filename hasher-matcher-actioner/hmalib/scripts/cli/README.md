# Set of scripts used to interact with a deployed HMA Instance

More details on each script to be added as needed.

## How to run a soak test of a deployed instance

First you will want to make sure the following settings are enabled in terraform if you want a dashboard to be available    
`measure_performance = true`

We will need the following things
- A deployed HMA instance 
- ec2 instance with a port open to recieve http requests

After deployment you will need the following values:
(`terraform -chdir='terraform' output` or `source scripts/set_tf_outputs_in_local_env.sh` can be of help here.)

- API_URL the URL for the HMA instance's API & CLIENT_ID associated with the HMA instance's userpool
    - `terraform -chdir='terraform' output` or `source scripts/set_tf_outputs_in_local_env.sh` can be of help here.
- REFRESH_TOKEN that can be used to get and refresh access to the API
    - `./scripts/get_auth_token --pwd 'Example$Passw0rd' --refresh_token` 
- HOSTNAME & PORT of the ec2 instance from which you want to run the soak test
    - PORT is which every you have open in your ec2 security group 
    - HOSTNAME is visable in the AWS console but you can also use `export EXTERNAL_HOSTNAME=$(ec2metadata --public-hostname)`


On your ec2 instance
`mkdir hma-dir`
`export EXTERNAL_HOSTNAME=$(ec2metadata --public-hostname)`

From your local copy of `hasher-matcher-actioner`
`# update scripts/soak_test_system values for API_URL, REFRESH_TOKEN, CLIENT_ID`
`scp -r hmalib ubuntu@<hostname>:hma-dir`
`scp -r scripts ubuntu@<hostname>:hma-dir`

Back on the ec2 instance
`cd hma-dir && python3 scripts/soak_test_system`

If everything is configured correctly you will be greated with an interactive cli. Here is some example usage
```
Listener server started <hostname>:8080
Welcome! enter 'start' to begin submitting and 'info' to see current counts. Type help or ? to list commands.

> start
Started Submitter
> latency
Rough delay between submit to action request received (10 most recent)
avg: 87.71843880000002 seconds
> info
Submitter Settings: 5 items every 5 seconds.
TOTAL SUBMITTED: 115
TOTAL POST requests received: 38
> stop
Stopped Submitter
TOTAL SUBMITTED: 115
> exit
Wait for listener to catch up before exiting? (y/N): y
TOTAL SUBMITTED: 115
        Waiting on 2 more requestss
Closing Shell...

Listener server stopped
Submitter and listener stopped.
FINAL TOTAL SUBMITTED: 115
FINAL TOTAL POST requests received: 115
Breaking down completed action's latency by time received in 1 min buckets
                           avg        p50         p90
times
2021-07-16 15:55:00  92.510531  92.343823  108.016659
2021-07-16 15:56:00  74.495645  74.778046   93.235091
2021-07-16 15:57:00  73.991881  72.678328  105.053203
Writing times to soak_test_timestamps.txt
Format: time_submitted, time_action_recevied, delta_in_seconds
Test Run Complete. Thanks!

```
If you want the test to be long running, I recommend using something like [EternalTerminal](https://github.com/MisterTea/EternalTerminal) so disconnecting from ssh/a broken pipe won't end the run.
