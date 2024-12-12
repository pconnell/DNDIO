import time, json, subprocess
import pandas as pd
cmd = "kubectl get --raw \"/apis/metrics.k8s.io/v1beta1/namespaces/default/pods\" "

arr = []
def proc_item(item:dict):
    return dict(
        dep_name = item['metadata']['name'],
        timestamp = item['timestamp'],
        cr_timestamp = item['metadata']['creationTimestamp'],
        time_window = item['window'],
        container_name = item['containers'][0]['name'],
        cpu_use = item['containers'][0]['usage']['cpu'],
        mem_use = item['containers'][0]['usage']['memory']
    )

while True:
    try:
        res = json.loads(subprocess.check_output(cmd,shell=True).decode())
        # print(res)
        for item in res['items']:
            # print(item)
            dat = proc_item(item)
            arr.append(dat)
            print(json.dumps(dat,indent=4))
        time.sleep(5)
    except:
        x = pd.DataFrame(arr)
        x.to_csv('./pod_metrics.csv',index=False)
        break