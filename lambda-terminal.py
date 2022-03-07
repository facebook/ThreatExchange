import subprocess
import json

for x in range(100):
    itemCount = 87672000+(x*1000)
    payload ={
        "index": "PDQFlatIndex",
        "itemCount": f"{itemCount}"
        }
    payload_obj = json.dumps(payload)   
    invoke_command = f"""aws lambda invoke --function-name franklin_eat_memory --cli-binary-format raw-in-base64-out --payload '{payload_obj}' response.json """
    print("Item Count: ",itemCount)

    status = subprocess.Popen(invoke_command,shell=True,stdout=subprocess.PIPE)

    status_string = (str(status.stdout.read()))
    if "FunctionError" not in status_string:
        print(status_string)
    else:
        print(status_string)
        break